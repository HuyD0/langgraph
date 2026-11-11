"""Saving progress to the account (page.html, "progress"): two tabs or devices must not wipe each other's work,
a failed save must say so, and one failed read at the start must not turn the account off for the whole visit.
The page's own saving code is lifted from the source and run by node, once per tab, against a stand-in account
copy that can be made to fail."""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from drill.content.build import PAGE_PARTS, page_source

START, END = "// ---------- progress (account when signed in, this browser otherwise) ----------", "const started = id => "

# A stand-in for the account copy (db.doc(...) on claude.ai or drill-server): get() and set() of one document,
# each of which can be made to fail.
HARNESS = r"""
const toasts = [], timers = [];
let clock = 1000; Date.now = () => ++clock;  // a steady clock: each save is later than the one before
globalThis.setTimeout = (f) => { timers.push(f); return timers.length; };
globalThis.clearTimeout = () => {};
function account(start) {
  let data = start === undefined ? null : structuredClone(start);
  const doc = { fail: { get: false, set: false }, writes: 0,
    get: async () => { if (doc.fail.get) throw new Error("offline"); const copy = structuredClone(data); return { exists: copy !== null, data: () => copy }; },
    set: async d => { if (doc.fail.set) throw new Error("offline"); const copy = structuredClone(d);  // sent now
                      if (doc.slow) await doc.slow; const gate = doc.gate; doc.gate = null; if (gate) await gate;  // gate: hold this one write
                      doc.writes++; data = copy; },
    now: () => data };
  return doc;
}
function tab(saved) {
  const store = saved || new Map(), localStorage = { getItem: k => store.has(k) ? store.get(k) : null, setItem: (k, v) => store.set(k, v) };
  const migrateAliases = () => {}, renderTop = () => {}, renderHome = () => {}, cur = null;
  /*BOARD*/
  const toast = msg => toasts.push(msg);
  /*CODE*/
  if (saved) loadLocal();  // as the page does when it opens
  return { get progress() { return progress; }, lp, saveProgress, connectProgress, saved: () => JSON.parse(store.get("drill-progress") || "null"),
           reopen: () => tab(new Map(store)) };  // the same browser opening the page again: its saved copies, a fresh page
}
"""


def run(js: str) -> object:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    page = page_source()
    code = page[page.index(START):page.index(END)]
    board = (PAGE_PARTS / "board.js").read_text(encoding="utf-8")
    merge_board = board[board.index("function mergeBoard("):board.index("function boardTrim(")]  # the real one
    script = HARNESS.replace("/*CODE*/", code).replace("/*BOARD*/", merge_board) + "\n(async () => { const out = await (async () => { " + js + " })(); console.log(JSON.stringify(out)); })();"
    out = subprocess.run([node, "-e", script], capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr[-1500:]
    return json.loads(out.stdout)


def test_two_tabs_saving_one_after_the_other_keep_both_lessons():
    got = run("""
      const doc = account();
      const a = tab(), b = tab();
      await a.connectProgress(doc); await b.connectProgress(doc);  // both open, both read the same copy
      a.lp("first").done = true; await a.saveProgress();          // finished in one tab
      b.lp("second").step = 2; await b.saveProgress();             // the other tab saves later
      return { lessons: doc.now().lessons, bHas: !!b.progress.lessons.first };
    """)
    assert got["lessons"]["first"]["done"] is True, "the later tab's save wiped a lesson finished in the other"
    assert got["lessons"]["second"]["step"] == 2
    assert got["bHas"], "the tab that saved later also has the other tab's lesson now"


def test_with_no_other_writer_a_save_is_written_as_it_is():
    """A reset (try a Check question again, a gotcha cleared) is kept: the merge runs only when someone else saved."""
    got = run("""
      const doc = account();
      const a = tab();
      a.progress.gotchas.lesson = "picked";
      await a.connectProgress(doc);
      delete a.progress.gotchas.lesson; await a.saveProgress();
      return doc.now().gotchas;
    """)
    assert got == {}


def test_a_failed_save_says_so_once_keeps_it_here_and_tries_again():
    got = run("""
      const doc = account();
      const a = tab();
      await a.connectProgress(doc);
      doc.fail.set = true;
      a.lp("x").done = true; await a.saveProgress(); await a.saveProgress();
      const failedToasts = toasts.slice(), here = a.saved().lessons.x.done, retries = timers.length;
      doc.fail.set = false;
      await timers[timers.length - 1]();  // the retry, half a minute later
      return { failedToasts, here, retries, after: toasts.slice(failedToasts.length), there: doc.now().lessons.x.done };
    """)
    assert len(got["failedToasts"]) == 1 and "Not saved to your account" in got["failedToasts"][0], got["failedToasts"]
    assert got["here"] is True, "kept in this browser"
    assert got["retries"] >= 1, "a retry is planned"
    assert got["after"] == ["Saved to your account."] and got["there"] is True


def test_one_failed_read_at_the_start_does_not_turn_the_account_off():
    got = run("""
      const doc = account({ solved: {}, days: [], lessons: { other: { step: 3, checked: null, done: true } }, gotchas: {} });
      const a = tab();
      doc.fail.get = true;
      const joined = await a.connectProgress(doc);
      a.lp("here").done = true; await a.saveProgress();           // saved in this browser only, for now
      const writesWhileDown = doc.writes, saidSo = toasts.length;
      doc.fail.get = false;
      await a.saveProgress();                                      // the next save reads the account and joins it
      return { joined, writesWhileDown, saidSo, lessons: doc.now().lessons, mine: Object.keys(a.progress.lessons).sort() };
    """)
    assert got["joined"] is False and got["writesWhileDown"] == 0, "never write before the account copy is read"
    assert got["saidSo"] == 1
    assert got["lessons"]["other"]["done"] is True and got["lessons"]["here"]["done"] is True
    assert got["mine"] == ["here", "other"]


def test_saves_asked_for_while_one_runs_end_with_the_latest_progress():
    got = run("""
      const doc = account();
      const a = tab();
      await a.connectProgress(doc);
      a.lp("one").step = 1; const first = a.saveProgress();
      a.lp("one").step = 2; const second = a.saveProgress();      // asked for while the first is still running
      await Promise.all([first, second]);
      return doc.now().lessons.one.step;
    """)
    assert got == 2


def test_a_burst_of_saves_is_one_at_a_time_not_one_write_each():
    """Every step of a lesson saves. Saves run one at a time, and the ones asked for meanwhile become one more."""
    got = run("""
      const doc = account();
      const a = tab();
      await a.connectProgress(doc);
      const before = doc.writes;
      await Promise.all([1, 2, 3, 4, 5].map(n => { a.lp("one").step = n; return a.saveProgress(); }));
      return { writes: doc.writes - before, step: doc.now().lessons.one.step };
    """)
    assert got == {"writes": 2, "step": 5}


def test_a_reset_stays_reset_after_another_tab_has_saved():
    """The merge starts from the copy both tabs last saw, so what this tab cleared on purpose doesn't come back."""
    got = run("""
      const doc = account();
      const a = tab(), b = tab();
      a.progress.gotchas.g = "picked"; a.progress.current = "L";
      a.lp("L").checks = { at: 2, solved: [0, 1], tried: [], help: [], marks: [] };
      await a.connectProgress(doc); await b.connectProgress(doc);
      b.lp("other").done = true; await b.saveProgress();            // someone else saves first
      delete a.progress.gotchas.g; a.progress.current = null;       // then this tab clears things on purpose
      a.lp("L").checks = { at: 0, solved: [], tried: [], help: [], marks: [] };
      await a.saveProgress();
      const afterA = structuredClone(doc.now());
      b.lp("other").step = 4; await b.saveProgress();               // and the other tab, which never touched them, saves again
      return { afterA, now: doc.now() };
    """)
    for copy in (got["afterA"], got["now"]):
        assert copy["gotchas"] == {} and copy["current"] is None, "a cleared value came back"
        assert copy["lessons"]["L"]["checks"]["at"] == 0
        assert copy["lessons"]["other"]["done"] is True
    assert got["now"]["lessons"]["other"]["step"] == 4


def test_an_older_tab_never_takes_back_what_the_other_one_did():
    got = run("""
      const doc = account();
      const a = tab(), b = tab();
      await a.connectProgress(doc); await b.connectProgress(doc);
      a.lp("L").checks = { at: 2, solved: [0, 1], tried: [], help: [], marks: [] }; a.lp("L").step = 3; await a.saveProgress();
      b.lp("M").step = 1; await b.saveProgress();                   // b has the old copy of L and never touched it
      return doc.now().lessons;
    """)
    assert got["L"]["checks"]["at"] == 2 and got["L"]["step"] == 3 and got["M"]["step"] == 1


def test_both_tabs_change_the_same_lesson():
    got = run("""
      const doc = account();
      const a = tab(), b = tab();
      await a.connectProgress(doc); await b.connectProgress(doc);
      a.lp("L").done = true; a.lp("L").step = 3; await a.saveProgress();
      b.lp("L").step = 1; await b.saveProgress();
      return doc.now().lessons.L;
    """)
    assert got["done"] is True and got["step"] == 3, "done anywhere stays done; the further step counts"


def test_a_change_made_while_a_save_is_on_its_way_is_sent_next_and_never_undone():
    """With one tab: clear something while a write is still sending, then save again."""
    got = run("""
      const doc = account();
      const a = tab();
      a.progress.gotchas.g = "picked";
      await a.connectProgress(doc);
      let release; doc.slow = new Promise(r => { release = r; });
      a.lp("x").step = 1; const first = a.saveProgress();
      await new Promise(r => setImmediate(r));                       // the write has left, and is still on its way
      delete a.progress.gotchas.g; const second = a.saveProgress();
      release(); doc.slow = null; await Promise.all([first, second]);
      await a.saveProgress();
      return { there: doc.now().gotchas, here: a.progress.gotchas };
    """)
    assert got == {"there": {}, "here": {}}


def test_the_leaderboard_waits_for_the_account_copy():
    """A row built from this device's progress alone may be behind: boardSave waits until the account is read."""
    board = (PAGE_PARTS / "board.js").read_text(encoding="utf-8")
    assert "if (!boardOn() || progressWaiting) return;" in board


def test_two_saves_that_cross_never_lose_a_finished_lesson():
    """Tab b reads, tab a reads and writes, then b's write (made from its older read) lands. a's finished lesson
    is missing from the account for a moment, but nothing treats that as deleted: lessons only ever grow."""
    got = run("""
      const doc = account();
      const a = tab(), b = tab();
      await a.connectProgress(doc); await b.connectProgress(doc);
      let release; doc.gate = new Promise(r => { release = r; });
      b.lp("second").step = 1; const bSave = b.saveProgress();      // b's write leaves, and is held
      await new Promise(r => setImmediate(r));
      a.lp("first").done = true; await a.saveProgress();             // a reads and writes meanwhile
      release(); await bSave;                                        // b's older write lands last
      a.lp("third").step = 1; await a.saveProgress();
      return { account: Object.keys(doc.now().lessons).sort(), aFirst: !!(a.progress.lessons.first || {}).done,
               done: !!doc.now().lessons.first.done };
    """)
    assert got == {"account": ["first", "second", "third"], "aFirst": True, "done": True}


def test_leaving_the_leaderboard_sticks_when_the_other_tab_counts_a_question():
    got = run("""
      const doc = account();
      const a = tab(), b = tab();
      a.progress.board = { on: true, snooze: null, asked: {}, reviews: {}, trial: {} };
      await a.connectProgress(doc); await b.connectProgress(doc);
      b.progress.board.on = false; await b.saveProgress();          // leave in one tab
      a.progress.board.asked["2026-11-11"] = 1; await a.saveProgress();  // a question counted in the other
      return doc.now().board;
    """)
    assert got["on"] is False, "leaving came undone"
    assert got["asked"] == {"2026-11-11": 1}, "the count still joins"


def test_a_lessons_check_attempts_are_never_mixed_from_two_tabs():
    got = run("""
      const doc = account();
      const a = tab(), b = tab();
      a.lp("L").checks = { at: 2, solved: [0, 1], tried: [], help: [], marks: [] };
      await a.connectProgress(doc); await b.connectProgress(doc);
      const fresh = { at: 0, solved: [], tried: [], help: [], marks: [] };
      a.lp("L").checks = structuredClone(fresh); await a.saveProgress();        // try again here
      b.lp("L").checks = { at: 2, solved: [0, 1], tried: [], help: [2], marks: [] }; await b.saveProgress();  // a clue there
      return { now: doc.now().lessons.L.checks, fresh, bs: b.progress.lessons.L.checks };
    """)
    assert got["now"] in (got["fresh"], got["bs"]), f"a mix of two attempts: {got['now']}"


def test_a_save_that_lands_late_never_rolls_back_what_this_tab_did_since():
    """Both tabs are on lesson L. b's save is held; meanwhile a finishes L (its sentence, its Explain record, its
    Check attempts), clears a gotcha, joins the leaderboard and moves on. Then b's older write lands."""
    got = run("""
      const doc = account();
      const a = tab(), b = tab();
      for (const t of [a, b]) { t.lp("L").step = 1; t.progress.gotchas.g = "picked"; t.progress.board = { on: false, snooze: null, asked: {}, reviews: {}, trial: {} }; }
      await a.connectProgress(doc); await b.connectProgress(doc);
      let release; doc.gate = new Promise(r => { release = r; });
      b.lp("M").step = 1; const bSave = b.saveProgress();
      await new Promise(r => setImmediate(r));
      Object.assign(a.lp("L"), { done: true, step: 3, checked: 2, said: "In my words.", explain: { wrong: 0, clues: 0, answers: 0, done: true },
                                 checks: { at: 3, solved: [0, 1, 2], tried: [], help: [], marks: [] } });
      delete a.progress.gotchas.g; a.progress.board.on = true; a.progress.current = "N";
      await a.saveProgress();
      release(); await bSave;                                      // b's older write lands last
      await a.saveProgress();
      const n = doc.now();
      return { L: n.lessons.L, M: !!n.lessons.M, gotchas: n.gotchas, on: n.board.on, current: n.current, aSaid: a.progress.lessons.L.said };
    """)
    assert got["L"]["done"] is True and got["L"]["said"] == "In my words." and got["L"]["checked"] == 2
    assert got["L"]["checks"]["solved"] == [0, 1, 2] and got["L"]["explain"]["done"] is True
    assert got["gotchas"] == {} and got["on"] is True and got["current"] == "N" and got["M"] is True
    assert got["aSaid"] == "In my words."


def test_a_lesson_only_opened_in_one_tab_takes_nothing_from_the_other():
    got = run("""
      const doc = account();
      const a = tab(), b = tab();
      await a.connectProgress(doc); await b.connectProgress(doc);
      Object.assign(a.lp("L"), { done: true, step: 3, checked: 2 }); await a.saveProgress();
      b.lp("L"); await b.saveProgress();                            // b opens L: { step: 0, checked: null, done: false }
      return doc.now().lessons.L;
    """)
    assert got["checked"] == 2 and got["done"] is True


def test_a_copy_with_no_leaderboard_doesnt_undo_a_join():
    got = run("""
      const doc = account();
      const a = tab(), b = tab();
      await a.connectProgress(doc); await b.connectProgress(doc);
      a.progress.board = { on: true, snooze: null, asked: {}, reviews: {}, trial: {} }; await a.saveProgress();
      delete b.progress.board; b.lp("x").step = 1; await b.saveProgress();
      return doc.now().board.on;
    """)
    assert got is True


def test_a_tab_opened_later_keeps_the_time_stamps():
    """The stamps say which change is newer; a tab that joins the account copy must keep them, or its next merge guesses."""
    got = run("""
      const doc = account();
      const a = tab();
      a.progress.gotchas.g = "picked";
      await a.connectProgress(doc);
      delete a.progress.gotchas.g; await a.saveProgress();          // a reset, stamped
      const b = tab(); await b.connectProgress(doc);                 // a tab opened afterwards
      b.lp("x").step = 1; await b.saveProgress();
      return { stamped: "g:g" in (doc.now().stamps || {}), inB: "g:g" in (b.progress.stamps || {}) };
    """)
    assert got == {"stamped": True, "inB": True}


def test_an_old_copy_on_a_device_doesnt_bring_back_resets_made_elsewhere():
    """The phone's browser keeps an older copy. On the laptop the learner tries the Check again, clears a gotcha and
    moves on. When the phone opens again, it has changed nothing, so it claims nothing."""
    got = run("""
      const doc = account();
      const phone = tab();
      phone.lp("L").checks = { at: 3, solved: [0, 1, 2], tried: [], help: [], marks: [] };
      phone.progress.gotchas.g = "picked"; phone.progress.current = "L";
      await phone.connectProgress(doc);                              // saved: the account has the phone's copy
      const laptop = tab(); await laptop.connectProgress(doc);
      laptop.lp("L").checks = { at: 0, solved: [], tried: [], help: [], marks: [] };
      delete laptop.progress.gotchas.g; laptop.progress.current = "N"; await laptop.saveProgress();
      const again = phone.reopen(); await again.connectProgress(doc);  // the phone's page opens again, with its old copy
      laptop.lp("N").step = 1; await laptop.saveProgress();
      const n = doc.now();
      return { at: n.lessons.L.checks.at, gotchas: n.gotchas, current: n.current, phone: again.progress.current };
    """)
    assert got == {"at": 0, "gotchas": {}, "current": "N", "phone": "N"}


def test_a_device_whose_clock_is_behind_still_wins_with_a_later_change():
    got = run("""
      const doc = account();
      const a = tab(), b = tab();
      await a.connectProgress(doc); await b.connectProgress(doc);
      a.lp("L").checks = { at: 0, solved: [], tried: [], help: [], marks: [] }; await a.saveProgress();   // "try again"
      clock -= 100000;                                               // b's clock is well behind
      b.lp("x").step = 1; await b.saveProgress();                     // b sees a's change...
      b.lp("L").checks = { at: 2, solved: [0, 1], tried: [], help: [], marks: [] }; await b.saveProgress();  // ...then answers
      a.lp("y").step = 1; await a.saveProgress();
      return doc.now().lessons.L.checks.at;
    """)
    assert got == 2


def test_a_change_merged_in_from_another_tab_is_never_claimed_as_this_tabs():
    """a takes in b's cleared gotcha. c then picks a new answer. a's next save must not re-claim the clearing as its
    own (a newer stamp) and undo c's newer choice."""
    got = run("""
      const doc = account();
      const a = tab(), b = tab(), c = tab();
      for (const t of [a, b, c]) t.progress.gotchas.g = "first";
      await a.connectProgress(doc); await b.connectProgress(doc); await c.connectProgress(doc);
      delete b.progress.gotchas.g; await b.saveProgress();           // b clears it
      a.lp("x").step = 1; await a.saveProgress();                     // a takes that in
      c.progress.gotchas.g = "second"; await c.saveProgress();        // c picks again, later
      a.lp("y").step = 1; await a.saveProgress();
      return doc.now().gotchas;
    """)
    assert got == {"g": "second"}
