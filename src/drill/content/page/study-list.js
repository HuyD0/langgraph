// ---------- study list: tag anything, then get it explained ----------
let studyItems = [], studyCol = null, studyQuery = "", gotOpen = false, renderPending = false;
const streaming = {}, revealed = new Set(), busyItems = new Set(), openItems = new Set();
// Spaced review: a "Got it" item comes back after 3 days, then 10, 30 and 90 while you keep
// remembering it. Keep these in step with drill/server/study.py.
const REVIEW_DAYS = [3, 10, 30, 90], DAY_MS = 86400000;
const isDue = it => it.status === "got" && (it.reviewAt || 0) <= Date.now();
function loadStudyLocal() { try { studyItems = JSON.parse(localStorage.getItem("drill-study") || "[]"); } catch { studyItems = []; } }
function saveStudyLocal() { if (studyCol) return; try { localStorage.setItem("drill-study", JSON.stringify(studyItems)); } catch {} }
// Once connected, the account holds the list and this device keeps only what couldn't reach it
// yet ("drill-study"), which is sent again at the next connect. A change is never just dropped.
const studyUnsent = new Set(), studyGone = new Set();  // ids not yet in the account; ids removed while connecting
function keepUnsent(it) {
  studyUnsent.add(it.id);
  try { const list = JSON.parse(localStorage.getItem("drill-study") || "[]").filter(x => x.id !== it.id); list.unshift(it); localStorage.setItem("drill-study", JSON.stringify(list)); } catch {}
}
function dropUnsent(id) {
  if (!studyUnsent.delete(id)) return;
  try { const list = JSON.parse(localStorage.getItem("drill-study") || "[]").filter(x => x.id !== id); if (list.length) localStorage.setItem("drill-study", JSON.stringify(list)); else localStorage.removeItem("drill-study"); } catch {}
}
const studyVersion = it => it.updatedAt || it.createdAt || 0;
const newId = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
// Saving works by selecting text (see the selection toolbar); no per-item buttons, to keep pages quiet.
function tagButtons() { return ""; }
function markSaved() {
  const saved = new Set(studyItems.map(i => i.text));
  for (const b of document.querySelectorAll("[data-tag]")) { const on = saved.has(b.dataset.text); b.classList.toggle("on", on); b.textContent = on ? "Saved" : "Save"; }
  const open = studyItems.filter(i => i.status !== "got" || isDue(i)).length;
  void open;
}
async function addItem(text, source, kind) {
  text = text.trim();
  const existing = studyItems.find(i => i.text === text);
  if (existing) return existing;
  const item = { id: newId(), text: text.slice(0, 2000), kind: kind || "text", source, problemId: cur ? cur.p.id : "", note: "", status: "open", createdAt: Date.now(), updatedAt: Date.now(), explanation: "", quiz: null, thread: [] };
  studyItems.unshift(item); saveStudyLocal(); renderStudy();
  if (studyCol) { try { await studyCol.doc(item.id).set(item); } catch { keepUnsent(item); flashStudy("Couldn't save to your account yet. It's kept on this device and sent next time."); } }
  return item;
}
async function updateItem(id, patch) {
  const it = studyItems.find(i => i.id === id); if (!it) return;
  patch = Object.assign({}, patch, { updatedAt: Date.now() });  // the newer copy wins when two lists are merged
  Object.assign(it, patch); saveStudyLocal(); renderStudy();
  if (!studyCol) return;
  try {
    // An item the account doesn't have yet is sent whole: a patch alone would save a half item.
    if (studyUnsent.has(id)) { await studyCol.doc(id).set(it); dropUnsent(id); }
    else await studyCol.doc(id).update(patch);
  } catch { keepUnsent(it); flashStudy("Couldn't save that change to your account yet. It's kept on this device and sent next time."); }
}
async function removeItem(id) {
  studyItems = studyItems.filter(i => i.id !== id); saveStudyLocal(); renderStudy();
  if (!studyCol) { studyGone.add(id); return; }  // still connecting: removed from the account once connected
  dropUnsent(id);
  try { await studyCol.doc(id).delete(); } catch { flashStudy("Couldn't remove it from your account. It may come back; try again later."); }
}
function flashStudy(msg) { toast(msg); }
// Model replies: code blocks, paragraphs, bullet and numbered lists, headings, **bold**, *italics*, `code`.
const emph = s => md(s).replace(/(^|[\s(])\*(?!\s)([^*\n]+?)\*(?=[\s.,;:!?)]|$)/g, "$1<i>$2</i>");
// The worked example, one sentence per line: as a paragraph, "add up to 0.6. 0.6 divided by 2"
// reads like a broken number. Decimals have no space after their dot, so ". " always ends a
// sentence; a very short one ("No.") stays on the line before.
function byhandSteps(text) {
  const steps = [];
  for (const s of text.trim().split(/(?<=[.!?])\s+(?=\S)/)) {
    if (steps.length && s.length < 6) steps[steps.length - 1] += " " + s; else steps.push(s);
  }
  return `<ol class="steps">${steps.map(s => `<li>${md(s)}</li>`).join("")}</ol>`;
}
function blockHtml(block) {
  const out = []; let list = null, para = [];
  const flushPara = () => { if (para.length) { out.push("<p>" + para.map(emph).join("<br>") + "</p>"); para = []; } };
  const flushList = () => { if (list) { out.push(`<${list.tag}>` + list.items.map(x => "<li>" + emph(x) + "</li>").join("") + `</${list.tag}>`); list = null; } };
  for (const raw of block.split("\n")) {
    const line = raw.trim(); if (!line) continue;
    let m;
    if ((m = line.match(/^[-*•]\s+(.*)/)) || (m = line.match(/^\d+[.)]\s+(.*)/))) {
      const tag = /^\d/.test(line) ? "ol" : "ul";
      flushPara(); if (!list || list.tag !== tag) { flushList(); list = { tag, items: [] }; }
      list.items.push(m[1]);
    } else if ((m = line.match(/^#{1,4}\s+(.*)/))) { flushList(); flushPara(); out.push("<p><b>" + emph(m[1]) + "</b></p>"); }
    else { flushList(); para.push(line); }
  }
  flushList(); flushPara();
  return out.join("");
}
function fmt(text) {
  return String(text).split(/```[a-z]*\n?/i).map((part, i) => i % 2
    ? `<pre>${esc(part.replace(/\n$/, ""))}</pre>`
    : part.split(/\n{2,}/).filter(x => x.trim()).map(blockHtml).join("")
  ).join("");
}
function gotIt(it) { openItems.delete(it.id); return updateItem(it.id, { status: "got", stage: 0, reviewAt: Date.now() + REVIEW_DAYS[0] * DAY_MS }); }
function backToLearning(it) { return updateItem(it.id, { status: "open", stage: 0, reviewAt: null }); }
async function reviewed(it, remembered, quiet) {
  revealed.delete(it.id); openItems.delete(it.id);
  if (!remembered) { await backToLearning(it); if (!quiet) toast("Back on your To learn list"); return; }
  const stage = Math.min((it.stage || 0) + 1, REVIEW_DAYS.length - 1);
  await updateItem(it.id, { stage, reviewAt: Date.now() + REVIEW_DAYS[stage] * DAY_MS });
  if (!quiet) toast("Next review in " + REVIEW_DAYS[stage] + " days");
}
let lessonOrder = null;
function studyGroup(it) {  // the lesson an item came from, in path order
  if (!lessonOrder) { lessonOrder = {}; let n = 0; for (const m of D.modules) for (const id of m.lessons) lessonOrder[id] = n++; }
  const id = it.problemId || "";
  if (id in lessonOrder && LESSONS[id]) return { key: id, title: LESSONS[id].title, order: lessonOrder[id] };
  if (byId[id]) return { key: id, title: "Practice: " + byId[id].title, order: 1e5 };
  return { key: "", title: "Other", order: 2e5 };
}
const studyMatches = (it, q) => !q || [it.text, it.note, it.explanation, it.source, studyGroup(it).title].some(t => (t || "").toLowerCase().includes(q));
function whenText(ms) { const d = Math.ceil(((ms || 0) - Date.now()) / DAY_MS); return d <= 0 ? "today" : d === 1 ? "tomorrow" : "in " + d + " days"; }
function itemMarks(it) {
  const marks = [];
  if (isDue(it)) marks.push(`<b class="due">Review now</b>`);
  else if (it.status === "got") marks.push("next review " + whenText(it.reviewAt));
  if (it.explanation) marks.push("explained");
  if (it.quiz) marks.push("quiz");
  const n = (it.thread || []).length; if (n) marks.push(n + (n === 1 ? " follow-up" : " follow-ups"));
  if (it.note) marks.push("your note");
  return marks.join(" · ") || esc(it.source || "");
}
function quizBlock(it) {
  if (!it.quiz) return "";
  return `<div class="ai"><h4>Quiz</h4><p>${md(it.quiz.question)}</p>${revealed.has(it.id) ? `<div>${fmt(it.quiz.answer)}</div>` : `<p><button class="mini" data-act="reveal" data-id="${it.id}">Think first, then show the answer</button></p>`}</div>`;
}
function threadBlock(it) {
  const s = streaming[it.id] || {};
  const thread = (it.thread || []).map(t => `<div class="ai"><h4>You asked</h4><p>${esc(t.q)}</p>${fmt(t.a)}</div>`).join("");
  const live = s.field === "thread" ? `<div class="ai"><h4>You asked</h4><p>${esc(s.q)}</p>${fmt(s.text || "Thinking…")}</div>` : "";
  return thread + live;
}
// ---------- the pocket: the study list as a tray, and review as a focus field ----------
// On the path the tray waits at the bottom; on other pages the header chip opens it as a sheet.
// Three tabs: Due (reviews), Learning, Got it. One item at a time opens inside the tray.
let pkOpen = false, pkTab = null, pkItem = null, pkSearch = false, pkNote = null, pkAsk = null;
const dueList = () => studyItems.filter(isDue).sort((a, b) => (a.reviewAt || 0) - (b.reviewAt || 0));
const learnList = () => studyItems.filter(it => it.status !== "got");
const gotList = () => studyItems.filter(it => it.status === "got" && !isDue(it)).sort((a, b) => (a.reviewAt || 0) - (b.reviewAt || 0));
const tabOf = it => isDue(it) ? "due" : it.status === "got" ? "got" : "learn";
const pkLabel = { due: "To review", learn: "Still learning", got: "Got it" };
function pkShape(it) {
  const id = it.problemId && modOf[it.problemId] ? it.problemId : null;
  return id ? `<svg class="pk-shape" viewBox="-12 -12 24 24" aria-hidden="true">${phShape(shapeOf(id), 9)}</svg>` : `<svg class="pk-shape" viewBox="-12 -12 24 24" aria-hidden="true"><circle class="sh" r="9" stroke-dasharray="3 3"/></svg>`;
}
function pkSeals(it) {  // passed reviews filled, the one it's waiting for ringed
  const stage = it.status === "got" ? (it.stage || 0) : -1;
  const say = stage < 0 ? "Not reviewed yet" : `Review ${stage + 1} of 4`;
  return `<span class="seals" role="img" aria-label="${say}">${REVIEW_DAYS.map((_, k) => `<i class="${k < stage ? "on" : k === stage ? "now" : ""}"></i>`).join("")}</span>`;
}
function pkRow(it) {
  const code = it.kind === "code", line = code ? (it.text.split("\n").find(l => l.trim()) || it.text).trim() : it.text;
  return `<button class="pk-row${isDue(it) ? " due" : it.status === "got" ? " got" : ""}" data-act="open" data-id="${it.id}">${pkShape(it)}<span class="tx${code ? " code" : ""}">${esc(line)}</span>${pkSeals(it)}</button>`;
}
function pkNext(it) {  // one main step, depending on where the item is
  const dis = busyItems.has(it.id) ? " disabled" : "";
  if (isDue(it)) return `<button class="btn primary" data-act="review1" data-id="${it.id}">Review it now</button>`;
  if (it.status === "got") return `<span class="meta">Next review ${whenText(it.reviewAt)}</span>`;
  if (sample && !it.explanation) return `<button class="btn primary" data-act="explain" data-id="${it.id}"${dis}>Explain it to me</button><button class="btn" data-act="got" data-id="${it.id}">Got it</button>`;
  if (sample && !it.quiz) return `<button class="btn primary" data-act="quiz" data-id="${it.id}"${dis}>Quiz me</button><button class="btn" data-act="got" data-id="${it.id}">Got it</button>`;
  return `<button class="btn primary" data-act="got" data-id="${it.id}">Got it</button>`;
}
function pkDetail(it) {
  const s = streaming[it.id] || {}, got = it.status === "got", stage = got ? (it.stage || 0) : -1;
  const expl = s.field === "explanation" ? s.text : it.explanation;
  const dis = busyItems.has(it.id) ? " disabled" : "";
  const g = studyGroup(it);
  const status = isDue(it) ? "<b>Due for review</b>" : got ? "Next review " + whenText(it.reviewAt) : "Learning";
  const links = [
    `<button class="linkbtn" data-act="note" data-id="${it.id}">${it.note ? "Edit your note" : "+ Add a note"}</button>`,
    sample ? `<button class="linkbtn" data-act="askshow" data-id="${it.id}">Ask a question</button>` : "",
    sample && it.explanation ? `<button class="linkbtn" data-act="explain" data-id="${it.id}"${dis}>Explain again, simpler</button>` : "",
    sample && it.quiz ? `<button class="linkbtn" data-act="quiz" data-id="${it.id}"${dis}>A different quiz question</button>` : "",
  ].join("");
  const menu = `<details class="pk-menu"><summary class="btn" aria-label="More">⋯</summary><div>${got ? `<button data-act="unlearn" data-id="${it.id}">Back to learning</button>` : ""}<button class="danger" data-act="remove" data-id="${it.id}">Remove from the list</button></div></details>`;
  const showNote = it.note || pkNote === it.id;
  return `<div class="pk-item">
    <button class="linkbtn pk-back" data-act="back">${ic("arrowl")}${pkLabel[pkTab] || "Back"}</button>
    ${it.kind === "code" ? `<pre class="pk-paper code">${esc(it.text)}</pre>` : `<p class="pk-paper">${esc(it.text)}</p>`}
    <div class="pk-meta"><span>${it.problemId && modOf[it.problemId] ? lessonNo(it.problemId) + " " : ""}${esc(g.title)}</span>${it.source ? `<span>from ${esc(it.source.split(" · ")[0])}</span>` : ""}${got ? `<span>${status}</span>` : ""}</div>
    <div class="pk-ladder" role="img" aria-label="Reviews after 3, 10, 30 and 90 days">${REVIEW_DAYS.map((d, k) => `<span class="${k < stage ? "on" : k === stage ? "now" : ""}">${d} days</span>`).join("")}</div>
    <div class="pk-next">${pkNext(it)}${menu}</div>
    ${showNote ? `<input class="field" data-note="${it.id}" id="note-${it.id}" value="${esc(it.note || "")}" placeholder="Your note: what's confusing about it?" aria-label="Your note">` : ""}
    ${expl ? `<div class="ai"><h4>Explanation</h4>${fmt(expl)}</div>` : ""}
    ${quizBlock(it)}${threadBlock(it)}
    ${sample && (pkAsk === it.id || s.field === "thread") ? `<form class="ask" data-ask="${it.id}"><input class="field" id="ask-${it.id}" placeholder="Ask a follow-up question" aria-label="Ask a follow-up question"${dis}><button class="btn" type="submit"${dis}>Ask</button></form>` : ""}
    <div class="pk-links">${links}</div>
  </div>`;
}
function renderPocket() {
  const due = dueList(), learn = learnList(), got = gotList(), total = studyItems.length;
  const onHome = !$("home").hidden;
  // It opens as a sheet when asked for, and otherwise stays out of the way: no bar over the page, no
  // aura. Home shows it as one quiet row in the page; other pages show a small header chip.
  const show = pkOpen && $("focus").hidden;
  document.body.classList.remove("pk-on");
  $("pocket").hidden = !show; $("pocket").classList.toggle("open", pkOpen); $("pocket").classList.remove("burn");
  $("pkScrim").hidden = !(pkOpen && show);
  $("pkToggle").setAttribute("aria-expanded", String(pkOpen));
  $("pkNum").textContent = due.length || learn.length || got.length;
  $("pkRing").style.setProperty("--p", total ? Math.round(100 * got.length / total) : 0);
  // Say what this is in words: "Study list", and what the numbers count.
  const things = n => `${n} ${n === 1 ? "thing" : "things"}`;
  $("pkTitle").textContent = due.length ? `Study list · ${due.length} to review` : "Study list";
  $("studySub").textContent = due.length ? `${things(due.length)} you saved to look at again · about ${Math.max(1, Math.round(due.length * .7))} min`
    : learn.length ? `${things(learn.length)} you saved and are still learning`
    : got.length ? `All learned · next review ${whenText(got[0].reviewAt)}` : "Select text in a lesson to save it here";
  $("pkStart").hidden = !due.length;
  const row = $("studyRow"); if (row) row.outerHTML = studyRowHtml();
  // the header chip, on pages other than Home (Home has its row)
  const chip = $("dueChip");
  chip.hidden = !total || onHome;
  document.body.classList.toggle("chip-on", !chip.hidden);
  chip.classList.toggle("due", due.length > 0);
  chip.innerHTML = due.length ? `<span class="dot"></span>${due.length} to review` : `Study list <b class="n">${learn.length || total}</b>`;
  chip.setAttribute("aria-label", due.length ? `${due.length} due for review: open your study list` : "Open your study list");
}
// Home's study list: one row in the page, under Today. Nothing when nothing is saved.
function studyRowHtml() {
  const total = studyItems.length; if (!total) return `<span id="studyRow" hidden></span>`;
  const due = dueList().length, learn = learnList().length, got = gotList().length;
  const bits = [learn ? `${learn} learning` : "", due ? `${due} to review` : "", got && !learn && !due ? `all ${got} learned` : ""].filter(Boolean).join(" · ");
  return `<button class="studyrow${due ? " due" : ""}" id="studyRow" data-study-open><span class="pk-ring" style="--p:${Math.round(100 * got / total)}"><span>${due || learn || got}</span></span><span class="sr-t"><b>Study list</b><span>${bits}</span></span>${ic("chevron", "chev")}</button>`;
}
function renderStudy() {
  markSaved();
  const box = $("items");
  if (box.contains(document.activeElement) && document.activeElement.tagName === "INPUT") { renderPending = true; return; }
  renderPending = false;
  renderPocket();
  $("pkBody").hidden = !pkOpen;
  if (!pkOpen) return;
  const open = pkItem && studyItems.find(i => i.id === pkItem);
  const lists = { due: dueList(), learn: learnList(), got: gotList() };
  if (!pkTab || (!lists[pkTab].length && !open)) pkTab = lists.due.length ? "due" : lists.learn.length ? "learn" : "got";
  $("pkTabs").hidden = !!open;
  $("pkTabs").innerHTML = ["due", "learn", "got"].map(k => `<button class="pk-tab" role="tab" data-ptab="${k}" aria-selected="${k === pkTab && !studyQuery}">${pkLabel[k]} ${lists[k].length}</button>`).join("")
    + `<button class="pk-tab srch" data-ptab="search" aria-label="Search your study list" aria-pressed="${pkSearch}">${ic("search")}</button>`;
  $("studySearch").hidden = !pkSearch || !!open;
  if (open) { box.innerHTML = pkDetail(open); return; }
  if (!studyItems.length) { box.innerHTML = `<p class="pk-empty">Nothing saved yet. Select any text in a lesson, or a line of your code, and choose <b>Save to study list</b>.</p>`; return; }
  const q = studyQuery.trim().toLowerCase();
  const list = q ? studyItems.filter(it => studyMatches(it, q)) : lists[pkTab];
  if (!list.length) { box.innerHTML = `<p class="pk-empty">${q ? `Nothing matches "${esc(studyQuery.trim())}".` : pkTab === "due" ? "Nothing due. Items you've got come back after 3, 10, 30 and 90 days." : "Nothing here yet."}</p>`; return; }
  box.innerHTML = list.map(pkRow).join("");
}
function openPocket(id) {
  pkOpen = true;
  if (id) { const it = studyItems.find(i => i.id === id); if (it) { pkItem = id; pkTab = tabOf(it); } }
  renderStudy();
  const target = id ? $("items").querySelector(".pk-back") : $("pkTabs").querySelector('[aria-selected="true"]');
  if (target) target.focus({ preventScroll: true });
}
function closePocket() { pkOpen = false; pkItem = null; pkNote = null; pkAsk = null; renderStudy(); }

// Review in the focus field: recall first, then check what you saved, then say how it went.
let rv = null;
function startReview(ids, from) {
  ids = ids || dueList().map(it => it.id);
  if (!ids.length) return;
  rv = { ids, i: 0, shown: false, kept: 0, lost: 0 };
  pkOpen = false; pkItem = null;
  $("focus").hidden = false; document.body.style.overflow = "hidden";
  renderStudy(); renderFocus();
  fxScreen("space", FX.space, from || $("pkStart"));
  const b = $("focusBody").querySelector(".fc-acts .btn"); if (b) b.focus({ preventScroll: true });
}
function endReview() { rv = null; $("focus").hidden = true; document.body.style.overflow = ""; renderStudy(); }
function renderFocus() {
  if (!rv) return;
  const dots = `<div class="fc-dots">${rv.ids.map((_, k) => `<i class="${k < rv.i ? "done" : k === rv.i ? "cur" : ""}"></i>`).join("")}</div>`;
  const top = `<div class="fc-top"><span>Review</span>${dots}<button class="linkbtn fc-close" data-rv="close">Close</button></div>`;
  if (rv.i >= rv.ids.length) {
    $("focusBody").innerHTML = `${top}<div class="fc-card fc-done"><b>${rv.kept ? `${rv.kept} sealed` : "Done"}</b><p class="fc-ask">${rv.kept ? `You remembered ${rv.kept} of ${rv.ids.length}. They come back later, further apart each time.` : ""}${rv.lost ? ` ${rv.lost} went back to Learning, to look at again.` : ""}</p><div class="fc-acts"><button class="btn primary" data-rv="close">Done</button></div></div>`;
    return;
  }
  const it = studyItems.find(i => i.id === rv.ids[rv.i]);
  if (!it) { rv.i++; renderFocus(); return; }
  const g = studyGroup(it), code = it.kind === "code";
  const ask = it.quiz ? `<p class="fc-ask"><b>${md(it.quiz.question)}</b></p>` : `<p class="fc-ask">Say it in your own words first: what is it, and where would you use it?</p>`;
  const saved = [it.quiz ? `<div class="ai"><h4>Answer</h4>${fmt(it.quiz.answer)}</div>` : "", it.explanation ? `<div class="ai"><h4>What you saved</h4>${fmt(it.explanation)}</div>` : "",
    it.note ? `<p><b>Your note:</b> ${esc(it.note)}</p>` : ""].join("") || `<p class="fc-ask">You saved this without an explanation. Open it in your study list and ask for one.</p>`;
  $("focusBody").innerHTML = `${top}<div class="fc-card" id="fcCard">
    <span class="fc-from">From ${esc(g.title)}${it.source ? " · " + esc(it.source.split(" · ")[0]) : ""}</span>
    ${code ? `<p class="quote code">${esc(it.text)}</p>` : `<h3>${esc(it.text)}</h3>`}
    ${ask}
    ${rv.shown ? `<div class="fc-answer">${saved}</div>` : ""}
    <div class="fc-acts">${rv.shown ? `<button class="btn" data-rv="no">I'd forgotten</button><button class="btn primary" data-rv="yes">I remembered</button>` : `<button class="btn primary" data-rv="show">Show what I saved</button>`}</div>
  </div>`;
}
async function rate(remembered, btn) {
  const it = studyItems.find(i => i.id === rv.ids[rv.i]); if (!it) return;
  if (remembered) { rv.kept++; fxScreen("spark", FX.spark, btn); fxOn($("fcCard"), "seal", FX.seal()); } else rv.lost++;
  await reviewed(it, remembered, true);
  setTimeout(() => { if (!rv) return; rv.i++; rv.shown = false; renderFocus(); const b = $("focusBody").querySelector(".fc-acts .btn"); if (b) b.focus({ preventScroll: true }); }, remembered && motionOn() ? 650 : 0);
}
$("focus").addEventListener("click", e => {
  const b = e.target.closest("[data-rv]"); if (!b || !rv) return;
  const act = b.dataset.rv;
  if (act === "close") endReview();
  else if (act === "show") { rv.shown = true; renderFocus(); const y = $("focusBody").querySelector('[data-rv="yes"]'); if (y) y.focus({ preventScroll: true }); }
  else if (act === "yes" || act === "no") { b.disabled = true; rate(act === "yes", b); }
});
$("pkToggle").onclick = () => { if (pkOpen) closePocket(); else openPocket(); };
$("pkScrim").onclick = closePocket;
$("pkStart").onclick = e => startReview(null, e.currentTarget);
$("dueChip").onclick = () => openPocket();
$("pkTabs").addEventListener("click", e => {
  const b = e.target.closest("[data-ptab]"); if (!b) return;
  if (b.dataset.ptab === "search") { pkSearch = !pkSearch; if (!pkSearch) studyQuery = $("studySearch").value = ""; renderStudy(); if (pkSearch) $("studySearch").focus(); return; }
  pkTab = b.dataset.ptab; studyQuery = $("studySearch").value = ""; renderStudy();
});
function tutorFrame(it) {
  const prob = byId[it.problemId];
  return `${LEARNER}
They saved this to understand better (from: ${it.source || "the page"}):
"""
${it.text}
"""
${it.note ? "Their note about what confuses them: " + it.note + "\n" : ""}${prob ? "They were working on: " + prob.title + " - " + prob.prompt.split("\n")[0] + "\n" : ""}`;
}
const studyTrace = (it, feature, more) => Object.assign({ feature, lesson_id: it.problemId || "",
  exercise_fn: (byId[it.problemId] || {}).fn || "", session: "study-" + it.id }, more);
async function streamInto(it, field, prompt, extra, trace) {
  busyItems.add(it.id); streaming[it.id] = Object.assign({ field, text: "" }, extra || {}); renderStudy();
  try {
    const { text } = await sample(prompt, withTrace({ onText: ({ text }) => { streaming[it.id].text = text; renderStudy(); } }, trace));
    return text;
  } catch (e) {
    if (e && e.code === "not_granted") { sample = null; sampleOff = true; document.body.classList.add("no-ai"); }
    flashStudy(e && e.code === "rate_limited" ? "Too many requests right now. Wait a minute, then try again." : "The answer didn't come through. Try again in a moment.");
    return null;
  } finally { busyItems.delete(it.id); delete streaming[it.id]; }
}
async function explainItem(id) {
  const it = studyItems.find(i => i.id === id); if (!it || !sample || busyItems.has(id)) return;
  const again = !!it.explanation;
  const text = await streamInto(it, "explanation", `${tutorFrame(it)}
Explain it to them${again ? " again, more simply than before, using an everyday comparison" : ""}.
- Say what it is in one plain sentence first.
- Then show a tiny Python example in a \`\`\`python block, with a comment on each line. Keep the example about something else, and never solve the exercise they're working on.
- Then one or two sentences on why it matters or where they'll meet it at work.
- Explain any other jargon you use. Under 180 words.${again ? "\nYour previous explanation, which didn't land: " + it.explanation.slice(0, 600) : ""}`,
    null, studyTrace(it, "explain", { question: it.text.slice(0, 300), word_limit: 180 }));
  if (text) await updateItem(id, { explanation: text }); else renderStudy();
}
async function quizItem(id) {
  const it = studyItems.find(i => i.id === id); if (!it || !sample || busyItems.has(id)) return;
  busyItems.add(id); renderStudy();
  try {
    const q = await sample.json(`${tutorFrame(it)}
Write one short quiz question that checks whether they really understand it, ideally "what does this code print?" or "what would happen if…". It must be answerable in your head without running code.${it.quiz ? " Make it different from: " + it.quiz.question : ""}
Return JSON: {"question": string, "answer": string}. The answer is 1-3 sentences explaining why. Use backticks for code.`,
      withTrace({ modelTier: "quick" }, studyTrace(it, "quiz")));
    if (q && q.question) { revealed.delete(id); await updateItem(id, { quiz: { question: String(q.question), answer: String(q.answer || "") } }); }
  } catch (e) {
    if (e && e.code === "not_granted") { sample = null; sampleOff = true; document.body.classList.add("no-ai"); }
    flashStudy("The quiz question didn't come through. Try again in a moment.");
  } finally { busyItems.delete(id); renderStudy(); }
}
async function askItem(id, question) {
  const it = studyItems.find(i => i.id === id); if (!it || !sample || busyItems.has(id) || !question.trim()) return;
  const history = (it.thread || []).slice(-4).map(t => "Q: " + t.q + "\nA: " + t.a).join("\n\n");
  const text = await streamInto(it, "thread", `${tutorFrame(it)}
${it.explanation ? "You already explained:\n" + it.explanation.slice(0, 1200) + "\n" : ""}${history ? "Earlier questions:\n" + history + "\n" : ""}
Their new question: ${question}

Answer it plainly for a beginner, under 150 words. Small code examples are fine in a \`\`\`python block, but never solve the exercise they're working on.`, { q: question },
    studyTrace(it, "ask_study_item", { question, word_limit: 150 }));
  if (text) await updateItem(id, { thread: [...(it.thread || []), { q: question, a: text, at: Date.now() }] }); else renderStudy();
}
async function connectStudy(db) {
  try {
    const col = db.collection("study"), since = Date.now();
    // Send up what was saved on this device. Only items that made it leave the local copy:
    // any that failed stay saved here, stay on screen, and are sent again next visit.
    // Sending waits on the network, so saves, edits and removals can happen meanwhile: each pass
    // sends whatever changed since the last one, so nothing done while connecting is dropped.
    const sent = new Map(), failed = new Set();
    for (let pass = 0; pass < 3; pass++) {
      const todo = studyItems.filter(it => !failed.has(it.id) && sent.get(it.id) !== studyVersion(it));
      const gone = [...studyGone].filter(id => sent.has(id));
      if (!todo.length && !gone.length) break;
      for (const it of todo) { const v = studyVersion(it); try { await col.doc(it.id).set(it); sent.set(it.id, v); } catch { failed.add(it.id); } }
      for (const id of gone) { studyGone.delete(id); sent.delete(id); try { await col.doc(id).delete(); } catch {} }
    }
    studyCol = col;  // from here on, every change goes straight to the account
    studyGone.clear();
    const unsent = studyItems.filter(it => failed.has(it.id) || sent.get(it.id) !== studyVersion(it));
    for (const it of unsent) studyUnsent.add(it.id);
    try { if (unsent.length) localStorage.setItem("drill-study", JSON.stringify(unsent)); else localStorage.removeItem("drill-study"); } catch {}
    if (unsent.length) flashStudy("Some saved items couldn't reach your account yet. They're kept on this device and will be sent next time.");
    col.orderBy("createdAt", "desc").onSnapshot(snap => {
      const items = snap.docs.map(d => Object.assign({}, d.data(), { id: d.id }));
      // Merge, don't replace: a copy changed here after the read began is newer and wins, and an
      // item saved here this visit that the read hasn't caught up with yet stays on screen.
      const mine = new Map(studyItems.map(it => [it.id, it])), have = new Set(items.map(it => it.id));
      const merged = items.map(it => { const m = mine.get(it.id); return m && studyVersion(m) > studyVersion(it) ? m : it; });
      const extra = studyItems.filter(it => !have.has(it.id) && (studyUnsent.has(it.id) || (it.createdAt || 0) >= since));
      studyItems = merged.concat(extra).sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0));
      renderStudy();
    }, () => flashStudy("Your study list couldn't load from your account. Reload to try again."));
  } catch {}
}
