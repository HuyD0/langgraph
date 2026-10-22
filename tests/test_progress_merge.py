"""Progress from the claude.ai account stays editable after it is merged with this device's.

The artifact runtime freezes what a database read delivers. Merged in as it came, a frozen lesson
quietly ignored every later change: "Next question" and "Try the check again" did nothing.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess

import pytest

from drill.content.build import page_source

CHECK = """
const deepFreeze = o => { Object.values(o).forEach(v => v && typeof v === "object" && deepFreeze(v)); return Object.freeze(o); };
const remote = deepFreeze({
  lessons: {
    only_there: { step: 1, checked: 0, done: true, checks: { at: 1, solved: [true, true], tried: [[2]], help: [0, 2], marks: [] } },
    both: { step: 3, checked: 1, done: true, checks: { at: 0, solved: [true], tried: [], help: [], marks: [] } },
  },
  solved: { p1: true }, days: ["2026-10-01"], gotchas: {}, mine: { updatedAt: 5, text: "account" },
  board: { on: true, snooze: "2026-10-05", asked: { "2026-10-01": 3 }, trial: { "2026-10-01": { id: "x", marks: ["sign"] } } },
});
const local = { lessons: { both: { step: 1, checked: null, done: false } }, solved: {}, days: ["2026-10-02"], gotchas: {}, mine: {},
  board: { asked: { "2026-10-01": 1, "2026-10-02": 2 }, snooze: "2026-10-09" } };
const p = mergeProgress(local, remote);
const st = p.lessons.only_there.checks;
st.at = Math.min(st.at + 1, 2);                                 // Next question
p.lessons.both.checks = { at: 0, solved: [], tried: [], help: [], marks: [] };  // Try the check again
p.lessons.only_there.step = 2;
p.board.trial["2026-10-01"].marks.push("knot");                 // the next trial question
console.log(JSON.stringify({
  at: st.at, retried: p.lessons.both.checks.solved.length, step: p.lessons.only_there.step,
  done: p.lessons.both.done, days: p.days, mine: p.mine.text, remoteAt: remote.lessons.only_there.checks.at,
  board: p.board,
}));
"""


def merge_function() -> str:
    """mergeProgress, and mergeBoard (page/board.js), which it calls for the leaderboard's counts."""
    found = [re.search(rf"^function {name}\(.*?^}}\n", page_source(), re.S | re.M) for name in ("mergeProgress", "mergeBoard")]
    assert all(found), "page.html no longer has mergeProgress() or mergeBoard()"
    return "".join(m.group(0) for m in found)


def test_a_frozen_account_copy_is_cloned_so_lessons_stay_editable():
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    done = subprocess.run([node, "-e", '"use strict";\n' + merge_function() + CHECK],
                          capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stderr[-800:]  # strict mode: writing to a frozen object throws
    out = json.loads(done.stdout)
    assert out["at"] == 2, "moving on to the next check question was lost"
    assert out["retried"] == 0, "trying the check again was lost"
    assert out["step"] == 2
    assert out["done"] is True and out["days"] == ["2026-10-01", "2026-10-02"]
    assert out["mine"] == "account"
    assert out["remoteAt"] == 1, "the account's own copy is never changed in place"
    board = out["board"]
    assert board["on"] is True, "joined on another device: still joined here"
    assert board["asked"] == {"2026-10-01": 3, "2026-10-02": 2}, "each day keeps the larger count"
    assert board["snooze"] == "2026-10-09", "Not now on either device holds until the later date"
    assert board["trial"]["2026-10-01"]["marks"] == ["sign", "knot"], "the trial stays editable after the merge"
