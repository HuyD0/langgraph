// ---------- the leaderboard: this week's grade league, last week's seals, and the daily trial ----------
// Friendly competition built on the marks a lesson already leaves (page/share.js). Your page works
// out your week from your own progress and saves one row, `board/<your id>`; everyone who joined
// reads everyone's rows. On claude.ai that is the artifact's database (each person writes only
// their own row); from drill-server it is /api/board. Joining is off until you switch it on.
//
// Points, the same for everyone:
//   a lesson finished, the first time  10
//   each Check, Practice or Explain mark: on your own 3, with a clue or another go 2, answer shown 1
//   each question of the daily trial: the same 3 / 2 / 1
//   a study-list review                2
// Hints never cost points, and only a day's best 3 lessons count (BOARD_DAY_LESSONS): little and
// often is what makes it stick, and the board must not reward cramming a week into a Sunday.
const BOARD_PTS = { lesson: 10, sign: 3, knot: 2, curtain: 1, review: 2 };
const BOARD_DAY_LESSONS = 3;
const BOARD_LEAGUE_MIN = 3;  // a grade league needs 3 people to be a race; fewer, and everyone races together
// Last week's seals, stamped on Monday. Each goes to a different person where it can, so being
// first at everything isn't the only way to win; "Curious" makes asking for help a win.
const SEALS = [
  { key: "unbroken", name: "Unbroken", icon: "clock", says: "Studied on the most days", of: w => w.days },
  { key: "sure", name: "Sure hand", icon: "sign", says: "Most answers on their own", of: w => w.tally[0] },
  { key: "curious", name: "Curious", icon: "chat", says: "Asked the tutor the most", of: w => w.asked },
  { key: "spark", name: "Spark", icon: "spark", says: "Most lessons with every step on their own", of: w => w.spark },
];
const TRIAL_QS = 3;

const keyDate = k => { const [y, m, d] = k.split("-").map(Number); return new Date(y, m - 1, d); };
const addDays = (k, n) => { const x = keyDate(k); x.setDate(x.getDate() + n); return dayKey(x); };
const mondayOf = k => addDays(k, -((keyDate(k).getDay() + 6) % 7));
const markPts = marks => (Array.isArray(marks) ? marks : []).reduce((a, m) => a + (BOARD_PTS[m] || 0), 0);

// One week of your progress, from its Monday: points, marks, and what the seals count.
// `lessons` is progress.lessons; `extra` is progress.board (asked, reviews and trial, by day).
function boardWeek(lessons, extra, monday) {
  const dates = Array.from({ length: 7 }, (_, i) => addDays(monday, i)), inWeek = new Set(dates);
  const ex = extra || {}, perDay = {}, tally = [0, 0, 0], active = new Set();
  let spark = 0, asked = 0, reviews = 0, pts = 0, count = 0;
  const add = marks => (marks || []).forEach(m => { const i = MARKS.indexOf(m); if (i >= 0) tally[i]++; });
  for (const s of Object.values(lessons || {})) {
    const f = s && s.first;
    if (!f || !f.day || !inWeek.has(f.date)) continue;
    const steps = [f.check, f.build, f.explain];
    steps.forEach(add);
    if (steps.every(m => Array.isArray(m) && m.length && m.every(x => x === "sign"))) spark++;
    (perDay[f.date] = perDay[f.date] || []).push(BOARD_PTS.lesson + steps.reduce((a, m) => a + markPts(m), 0));
    active.add(f.date);
  }
  for (const [d, list] of Object.entries(perDay)) {
    const best = list.sort((a, b) => b - a).slice(0, BOARD_DAY_LESSONS);
    count += best.length; pts += best.reduce((a, b) => a + b, 0);
  }
  for (const d of dates) {
    const t = (ex.trial || {})[d], n = (ex.asked || {})[d] || 0, r = (ex.reviews || {})[d] || 0;
    if (t && t.marks && t.marks.length) { add(t.marks); pts += markPts(t.marks); active.add(d); }
    if (n) { asked += n; active.add(d); }
    if (r) { reviews += r; pts += r * BOARD_PTS.review; active.add(d); }
  }
  return { week: monday, pts, tally, days: active.size, asked, spark, lessons: count, reviews };
}

// The row you share: this week, last week (for the seals), your grade and today's trial.
function boardRow(p, doneCount, day) {
  const monday = mondayOf(day), t = ((p.board || {}).trial || {})[day];
  return { v: 1, week: boardWeek(p.lessons, p.board, monday), last: boardWeek(p.lessons, p.board, addDays(monday, -7)),
    grade: gradeAt(doneCount), trial: t ? { date: day, marks: (t.marks || []).slice(0, TRIAL_QS) } : null };
}

// Your league: the people at your grade this week, ranked by points (equal points share a place).
// `rows` are [{id, name, row}]; a league smaller than BOARD_LEAGUE_MIN becomes everyone.
function boardLeague(rows, me, monday) {
  const now = rows.filter(r => r.row && r.row.week && r.row.week.week === monday);
  const mine = now.find(r => r.id === me);
  const grade = mine ? mine.row.grade : null;
  const same = grade == null ? [] : now.filter(r => r.row.grade === grade);
  const own = same.length >= BOARD_LEAGUE_MIN, list = (own ? same : now).slice();
  list.sort((a, b) => b.row.week.pts - a.row.week.pts || String(a.name).localeCompare(String(b.name)));
  let place = 0;
  const ranked = list.map((r, i) => { if (!i || r.row.week.pts < list[i - 1].row.week.pts) place = i + 1; return { ...r, place }; });
  const others = {};
  if (own) now.filter(r => r.row.grade !== grade).forEach(r => { others[r.row.grade] = (others[r.row.grade] || 0) + 1; });
  return { grade: own ? grade : null, rows: ranked, others };
}

// Last week's seals: for each in turn, the highest count among people without a seal yet (more
// than zero, ties to the most points); if everyone with a count has one, the overall leader.
function boardSeals(rows, lastMonday) {
  const last = rows.filter(r => r.row && r.row.last && r.row.last.week === lastMonday);
  const held = new Set(), out = [];
  for (const seal of SEALS) {
    const ranked = last.filter(r => seal.of(r.row.last) > 0)
      .sort((a, b) => seal.of(b.row.last) - seal.of(a.row.last) || b.row.last.pts - a.row.last.pts || String(a.name).localeCompare(String(b.name)));
    const who = ranked.find(r => !held.has(r.id)) || ranked[0];
    if (!who) continue;
    held.add(who.id);
    out.push({ seal, id: who.id, value: seal.of(who.row.last) });
  }
  return out;
}

// Today's trial: the same lesson for everyone on the same day, picked from the lessons with at
// least three Check questions, by the date alone.
function trialLesson(day, pool) {
  if (!pool.length) return null;
  const h = [...day].reduce((a, c) => (Math.imul(a, 31) + c.charCodeAt(0)) >>> 0, 2166136261);
  return pool[h % pool.length];
}

// ---------- the board on screen ----------
let boardApi = null, boardRows = [], boardMe = null, boardLoaded = false, boardSaving = null;
const TRIAL = { day: null, started: false, solved: false, tried: [], help: 0 };  // the question on screen; marks are saved in progress.board.trial
const boardState = () => progress.board || (progress.board = {});
const boardOn = () => !!boardApi && !!boardState().on;
const trialPool = () => ALL_LESSONS.filter(id => checkQs(id).length >= TRIAL_QS);
const myTrial = (day = today()) => (boardState().trial || {})[day] || null;
const trialDone = (day = today()) => { const t = myTrial(day); return !!t && (t.marks || []).length >= TRIAL_QS; };
const placeWord = n => n + (n % 100 >= 11 && n % 100 <= 13 ? "th" : ["th", "st", "nd", "rd"][n % 10] || "th");
const boardName = r => r.id === boardMe ? "You" : (r.name || "Someone");

function connectBoard(api) {
  boardApi = api;
  $("boardSetting").hidden = false;
  drawBoardSetting();
  boardRefresh();
}
async function boardRefresh() {
  if (!boardApi) return;
  try { const got = await boardApi.list(); boardRows = got.rows || []; boardMe = got.me; boardLoaded = true; } catch { return; }
  if (!$("board").hidden) renderBoard(); else if (!cur) renderHome();
}
// Your row, saved after anything that changes your week. Joined only: leaving deletes it.
function boardCount(kind) {
  const b = boardState(), d = today();
  b[kind] = b[kind] || {};
  b[kind][d] = (b[kind][d] || 0) + 1;
  boardTrim(b);
  saveProgress(); boardSave();
}
// Two devices' counts: the larger count each day, the trial with more marks, and this device's switch.
function mergeBoard(a, b) {
  a = a || {}; b = b || {};
  const out = { on: a.on !== undefined ? a.on : !!b.on };
  for (const kind of ["asked", "reviews"]) {
    out[kind] = Object.assign({}, b[kind] || {});
    for (const [d, n] of Object.entries(a[kind] || {})) out[kind][d] = Math.max(n, out[kind][d] || 0);
  }
  out.trial = Object.assign({}, b.trial || {});
  for (const [d, t] of Object.entries(a.trial || {})) if (!out.trial[d] || (t.marks || []).length > (out.trial[d].marks || []).length) out.trial[d] = t;
  return out;
}
function boardTrim(b) {  // only the last three weeks matter: this one, last one (seals), and a spare
  const from = addDays(mondayOf(today()), -14);
  for (const kind of ["asked", "reviews", "trial"]) for (const d of Object.keys(b[kind] || {})) if (d < from) delete b[kind][d];
}
async function boardSave() {
  if (!boardOn()) return;
  const row = boardRow(progress, ALL_LESSONS.filter(isDoneL).length, today());
  clearTimeout(boardSaving);
  boardSaving = setTimeout(async () => { try { await boardApi.save(row); } catch {} boardRefresh(); }, 400);
}
async function boardJoin(on) {
  boardState().on = on; await saveProgress();
  drawBoardSetting();
  if (on) { await boardSave(); toast("You're on this week's leaderboard"); }
  else { try { await boardApi.leave(); } catch {} toast("You've left the leaderboard"); boardRefresh(); }
  if (!$("board").hidden) renderBoard(); else if (!cur) renderHome();
}
function drawBoardSetting() {
  document.querySelectorAll("[data-board-pick]").forEach(b => b.setAttribute("aria-pressed", String((b.dataset.boardPick === "on") === !!boardState().on)));
}

const tallyHtml = t => `<span class="lb-tally">${MARKS.map((m, i) => `<span title="${t[i]} ${MARK_WORDS[m]}">${markTile(m)}${t[i]}</span>`).join("")}</span>`;
function sealHtml(seal, sm) { return `<span class="seal s-${seal.key}${sm ? " sm" : ""}" aria-hidden="true">${ic(seal.icon)}</span>`; }
function boardNow() {
  const monday = mondayOf(today()), league = boardLeague(boardRows, boardMe, monday);
  const seals = boardSeals(boardRows, addDays(monday, -7)), sealOf = {};
  seals.forEach(s => { sealOf[s.id] = s.seal; });
  const me = league.rows.find(r => r.id === boardMe);
  return { monday, league, seals, sealOf, me, ahead: me ? league.rows.filter(r => r.row.week.pts > me.row.week.pts).pop() : null };
}
const leagueName = l => l.grade == null ? "Everyone" : gradeName(l.grade) + " league";
const daysLeft = () => 7 - (new Date().getDay() + 6) % 7;

// Home: a small card under Today. Joined, it shows your place; not joined, a quiet invitation,
// only when someone is already racing.
function boardCardHtml() {
  if (!boardApi || !boardLoaded) return "";
  const n = boardNow();
  if (!boardOn()) {
    const racing = n.league.rows.length;
    return racing ? `<section class="card lb-home"><span class="eyebrow">This week's leaderboard</span><p>${racing} ${racing === 1 ? "person is" : "people are"} racing this week. Join to see where you'd be.</p><span class="meta">Shows your name and weekly points. Your answers and questions stay private.</span><button class="btn" data-board-join>Join the leaderboard</button></section>` : "";
  }
  if (!n.me) return "";
  const top = n.league.rows.slice(0, 3);
  if (!top.includes(n.me)) top.push(n.me);
  const gap = n.ahead ? `${n.ahead.row.week.pts - n.me.row.week.pts} behind ${esc(boardName(n.ahead))}` : n.league.rows.length > 1 ? "Out in front" : "The first one here this week";
  return `<section class="card lb-home"><span class="eyebrow">This week · ${esc(leagueName(n.league))}</span>
    <div class="lb-home-main"><span class="lb-big">${placeWord(n.me.place)}</span><span class="meta">of ${n.league.rows.length} · ${n.me.row.week.pts} points<br>${gap}</span></div>
    <ol class="lb-mini">${top.map(r => `<li class="${r.id === boardMe ? "me" : ""}"><span>${r.place}</span>${esc(boardName(r))}<b>${r.row.week.pts}</b></li>`).join("")}</ol>
    <span class="meta lb-trialline">${ic("sign")}${trialDone() ? "Today's trial: done." : "Today's trial is ready."}</span>
    <button class="btn" data-board-open>See the board</button></section>`;
}

// The done screen: one quiet line, never a second card.
function boardDoneLine(id) {
  if (!boardOn() || !boardLoaded) return "";
  const f = (progress.lessons[id] || {}).first, n = boardNow();
  if (!f || f.date !== today() || !n.me) return "";
  const got = BOARD_PTS.lesson + [f.check, f.build, f.explain].reduce((a, m) => a + markPts(m), 0);
  return `<p class="lb-done"><b>+${got}</b> this lesson · you're ${placeWord(n.me.place)} this week</p>`;
}

function openBoard() { closeNotebook(); show("board"); renderBoard(); boardRefresh(); }
function renderBoard() {
  const box = $("board");
  const back = `<div class="lessonbar"><button class="btn quiet" data-board-back aria-label="Back to your path">${ic("arrowl")}</button><span class="lb-t">Leaderboard</span></div>`;
  if (!boardOn()) {
    box.innerHTML = `${back}<div class="lb-head"><span class="eyebrow">This week</span><h1 class="lb-title">The leaderboard</h1>
      <p class="meta">A friendly race that starts fresh every Monday, against people at your own grade. Points come from your marks: on your own, with a clue, or the answer shown all count. Hints never cost points.</p></div>
      <p class="meta">Joining shows your name and weekly points to everyone on the board. Your answers and questions stay private. You can leave any time in the Notebook's Settings.</p>
      <button class="btn primary lb-cta" data-board-join>Join the leaderboard</button>`;
    return;
  }
  const n = boardNow(), L = n.league, me = n.me;
  const title = me ? `You're ${placeWord(me.place)} of ${L.rows.length}` : "Saving your row…";
  const coach = !me ? "" : n.ahead
    ? `You're ${n.ahead.row.week.pts - me.row.week.pts} points behind ${esc(boardName(n.ahead))}. A lesson with every step on your own is worth about ${BOARD_PTS.lesson + 7 * BOARD_PTS.sign}.`
    : L.rows.length > 1 ? "You're out in front. Today's trial keeps you there." : "You're the first one here this week. Others show up as they join.";
  const rows = L.rows.map(r => { const s = n.sealOf[r.id];
    return `<li class="${r.id === boardMe ? "me" : ""}"><span class="lb-rank">${r.place}</span><span class="lb-name">${esc(boardName(r))}${s ? `<span class="lb-seal s-${s.key}" title="${esc(s.name)}">${ic(s.icon)}</span>` : ""}</span>${tallyHtml(r.row.week.tally)}<span class="lb-pts">${r.row.week.pts}</span></li>`; }).join("");
  const others = Object.entries(L.others).sort((a, b) => b[0] - a[0]).map(([g, c]) => `<span class="chip">${esc(gradeName(+g))} · ${c}</span>`).join("");
  const seals = n.seals.length ? `<section class="lb-sec"><span class="eyebrow">Last week's seals · stamped Monday</span><div class="seal-grid">${n.seals.map(s => `<div class="seal-cell${s.id === boardMe ? " mine" : ""}">${sealHtml(s.seal)}<b>${esc(s.seal.name)}</b><span class="meta">${esc(s.seal.says)}</span><span class="seal-who">${esc(boardName(boardRows.find(r => r.id === s.id) || { id: s.id }))}</span></div>`).join("")}</div></section>` : "";
  box.innerHTML = `${back}<div class="lb-head"><span class="eyebrow">This week · ${esc(leagueName(L))}</span><h1 class="lb-title">${title}</h1><p class="meta">Starts fresh on Monday. ${daysLeft() === 1 ? "Last day." : daysLeft() + " days left."}</p></div>
    ${coach ? hzCoach("clue", `<p class="lb-coach">${coach}</p>`) : ""}
    <ol class="lb-rows">${rows}</ol>
    ${others ? `<div class="lb-leagues"><span class="eyebrow">Other leagues</span>${others}</div>` : ""}
    <section class="card lb-trial" id="trialBox">${trialHtml()}</section>
    ${seals}
    <details class="lb-how"><summary>How points work</summary><ul>
      <li>A lesson finished, the first time: ${BOARD_PTS.lesson}</li>
      <li>Each Check, Practice or Explain mark: on your own ${BOARD_PTS.sign}, with a clue or another go ${BOARD_PTS.knot}, answer shown ${BOARD_PTS.curtain}</li>
      <li>Each question of the daily trial: the same</li>
      <li>A study-list review: ${BOARD_PTS.review}</li>
      <li>Hints never cost points. Only your best ${BOARD_DAY_LESSONS} lessons a day count: a little every day is what makes it stick.</li>
    </ul></details>
    <button class="linkbtn lb-leave" data-board-leave>Leave the leaderboard</button>`;
}

// ---------- the daily trial: three Check questions, one at a time, clue first, then the answer ----------
function trialHtml() {
  const day = today(), id = trialLesson(day, trialPool());
  if (!id) return "";
  const L = LESSONS[id], t = myTrial(day), marks = (t && t.marks) || [];
  const head = `<span class="eyebrow">Today's trial</span><h2>${esc(L.title)}</h2>`;
  const played = boardRows.filter(r => r.id !== boardMe && r.row && r.row.trial && r.row.trial.date === day && (r.row.trial.marks || []).length);
  if (marks.length >= TRIAL_QS && !TRIAL.solved) {
    const mine = { id: boardMe, row: { trial: { marks } } };
    return `${head}<ol class="trial-rows">${[mine, ...played].map(r => `<li class="${r.id === boardMe ? "me" : ""}"><span>${esc(boardName(r))}</span><span class="trial-marks">${r.row.trial.marks.map(markTile).join("")}</span><span class="lb-pts">+${markPts(r.row.trial.marks)}</span></li>`).join("")}</ol>
      <div class="resshare"><button class="linkbtn" data-trial-copy>${ic("copy")}Copy as text</button></div>`;
  }
  if (!marks.length && !(TRIAL.started && TRIAL.day === day)) {
    const veil = played.slice(0, 5).map(r => `<li><span>${esc(boardName(r))}</span><span class="trial-marks">${"<span class=\"vtile\"></span>".repeat(TRIAL_QS)}</span></li>`).join("");
    return `${head}<p class="meta">${TRIAL_QS} Check questions from this lesson, the same for everyone today. Only your first try counts.${isDoneL(id) ? "" : ` New to it? <button class="linkbtn inline" data-open="${id}">Read the lesson first</button>`}</p>
      ${veil ? `<ol class="trial-rows veiled">${veil}</ol><p class="meta">${played.length} ${played.length === 1 ? "has" : "have"} played. Their marks show once you've answered.</p>` : ""}
      <button class="btn primary lb-cta" data-trial-start>Start today's trial</button>`;
  }
  const qs = checkQs(id), i = Math.min(TRIAL.solved ? marks.length - 1 : marks.length, TRIAL_QS - 1), [q, opts, ans, why, clue] = qs[i];
  const solved = TRIAL.solved, tried = TRIAL.tried, help = TRIAL.help;
  const order = checkOrder(id + ":trial:" + i, opts.length), letter = k => "ABCDEF"[order.indexOf(k)];
  const buttons = order.map(k => { const off = solved || tried.includes(k);
    return `<button class="opt${solved && k === ans ? " right" : tried.includes(k) ? " wrong" : ""}" data-trial-opt="${k}"${off ? " disabled" : ""}><span class="k">${letter(k)}</span><span>${md(opts[k])}</span></button>`; }).join("");
  const verdict = solved ? hzCoach(help === 2 ? "answer" : "right", `<div class="verdict ok">${ic("check")}<div><b>${help === 2 ? `The answer is ${letter(ans)}.` : "Right."}</b> ${md(why)}</div></div>`)
    : tried.length ? hzCoach("wrong", `<div class="verdict no">${ic("x")}<div><b>Not quite.</b> Try another one${help || !clue ? "" : ", or ask for a clue"}.</div></div>`) : "";
  const helpHtml = solved ? "" : help === 0 && clue ? `<button class="linkbtn" data-trial-help>Give me a clue</button>`
    : help === 0 ? `<button class="linkbtn" data-trial-help>Tell me the answer</button>`
    : hzCoach("clue", `<p class="clzclue">${ic("bulb")}<span>${md(clue)}</span></p>`) + `<button class="linkbtn" data-trial-help>Tell me the answer</button>`;
  const next = solved ? `<button class="btn primary chknext" data-trial-next>${marks.length >= TRIAL_QS ? "See everyone's marks" : "Next question"}${ic("arrowr")}</button>` : "";
  return `${head}<div class="shead chkhead"><span class="scount">Question ${i + 1} of ${TRIAL_QS}</span><span class="qf-dots" aria-hidden="true">${Array.from({ length: TRIAL_QS }, (_, j) => `<i class="${j < marks.length ? "d" : j === i ? "n" : ""}"></i>`).join("")}</span></div>
    <p class="q">${md(q)}</p><div class="opts">${buttons}</div><div aria-live="polite">${verdict}</div><div class="clzhelp">${helpHtml}${next}</div>`;
}
function trialMark(how) {  // the question's mark goes in at once, so a reload can't buy a second first try
  const day = today(), b = boardState(), id = trialLesson(day, trialPool());
  b.trial = b.trial || {};
  const t = b.trial[day] = b.trial[day] || { id, marks: [] };
  if (t.marks.length < TRIAL_QS) t.marks.push(how);
  TRIAL.solved = true;
  saveProgress(); boardSave();
}
function trialRedraw() { const box = $("trialBox"); if (box) box.innerHTML = trialHtml(); }
function trialClick(e) {
  const t = e.target.closest("[data-trial-start], [data-trial-opt], [data-trial-help], [data-trial-next], [data-trial-copy]");
  if (!t) return;
  const day = today(), id = trialLesson(day, trialPool());
  if (t.dataset.trialStart !== undefined) Object.assign(TRIAL, { day, started: true, tried: [], help: 0, solved: false });
  else if (t.dataset.trialOpt !== undefined) {
    const k = +t.dataset.trialOpt, i = ((myTrial(day) || {}).marks || []).length, ans = checkQs(id)[i][2];
    if (k === ans) { trialMark(TRIAL.tried.length || TRIAL.help ? "knot" : "sign"); fxOn(t, "seal", FX.seal()); }
    else TRIAL.tried.push(k);
  } else if (t.dataset.trialHelp !== undefined) {
    const clue = checkQs(id)[((myTrial(day) || {}).marks || []).length][4];
    TRIAL.help = Math.max(TRIAL.help, clue ? 0 : 1) + 1;
    if (TRIAL.help >= 2) { TRIAL.help = 2; trialMark("curtain"); }
  } else if (t.dataset.trialNext !== undefined) Object.assign(TRIAL, { tried: [], help: 0, solved: false });
  else if (t.dataset.trialCopy !== undefined) {
    const marks = (myTrial(day) || {}).marks || [];
    const text = `Daily Drill trial · ${day}\n${LESSONS[id].title}\n${marks.map(m => SHARE_MARKS[m]).join("")}`;
    navigator.clipboard.writeText(text).then(() => toast("Copied"), () => toast("Couldn't copy here"));
    return;
  }
  trialRedraw();
}

document.addEventListener("click", e => {
  const t = e.target.closest("[data-board-open], [data-board-join], [data-board-back], [data-board-leave], [data-board-pick]");
  if (t) {
    if (t.dataset.boardOpen !== undefined) openBoard();
    else if (t.dataset.boardJoin !== undefined) { boardJoin(true); if ($("board").hidden) openBoard(); }
    else if (t.dataset.boardBack !== undefined) goHome();
    else if (t.dataset.boardLeave !== undefined) boardJoin(false);
    else if (t.dataset.boardPick !== undefined && (t.dataset.boardPick === "on") !== !!boardState().on) boardJoin(t.dataset.boardPick === "on");
    return;
  }
  if (!$("board").hidden) trialClick(e);
});
