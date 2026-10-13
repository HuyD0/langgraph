// ---------- the sorting board: Build as a judgement task (content/model.py sort_task) ----------
// One idea at a time: place it on the map or in the tray, and the reason shows straight away.
// Right first time counts; a wrong move teaches and the card stays. The Python version is one click away.
const SO = { p: null, placed: {}, first: {}, skip: [], note: null, code: false, again: false };
const sortKey = id => "drill-sort-" + id, codeKey = id => "drill-code-" + id;
const sorting = () => !!(SO.p && cur && cur.p === SO.p && !SO.code);
function sortLoad(p) {
  Object.assign(SO, { p: p.sort ? p : null, placed: {}, first: {}, skip: [], note: null, code: false, again: false });
  if (SO.p) try {
    const s = JSON.parse(localStorage.getItem(sortKey(p.id)) || "null");
    if (s) { SO.placed = s.placed || {}; SO.first = s.first || {}; }
    SO.code = localStorage.getItem(codeKey(p.id)) === "1";
  } catch {}
  sortMode();
}
function sortMode() {
  const on = sorting();
  $("paneBuild").classList.toggle("sorting", on);
  $("sortBox").hidden = !on;
  $("modeSwap").hidden = !SO.p || on;
  $("modeSwap").innerHTML = SO.p && !on ? `<button class="linkbtn" data-sort-mode="sort">${ic("arrowl")}Back to sorting the ideas</button>` : "";
  if (on) sortRender();
}
function sortSave() { try { localStorage.setItem(sortKey(SO.p.id), JSON.stringify({ placed: SO.placed, first: SO.first })); } catch {} }
function sortLeft() {
  const left = SO.p.sort.items.map((_, i) => i).filter(i => !(i in SO.placed));
  return [...left.filter(i => !SO.skip.includes(i)), ...SO.skip.filter(i => left.includes(i))];
}
const sortRight = () => Object.keys(SO.placed).filter(i => SO.first[i]).length;
// Done before (here or on another device) and not started again: the board says so, and agrees with the bottom bar.
const sortDoneBefore = () => !!(SO.p && progress.solved[SO.p.id] && !SO.again && !Object.keys(SO.placed).length);
const sortFinished = () => !!(SO.p && progress.solved[SO.p.id] && !SO.again);
function sortRender() {
  const t = SO.p.sort, items = t.items, left = sortLeft(), now = left[0], n = items.length;
  if (sortDoneBefore()) {
    const sv = progress.solved[SO.p.id], right = Math.max(0, n - (sv.hints || 0));
    $("sortBox").innerHTML = `<div class="shead"><h2>Sort the ideas</h2><span class="scount">done</span></div>
      <div class="sdone"><b>${ic("check")} You sorted these before: ${right} of ${n} right first time.</b><p>The pattern: <em>${md((LESSONS[SO.p.id] || {}).angle ? LESSONS[SO.p.id].angle[0] : SO.p.pattern)}</em></p></div>
      <div class="sfoot"><button class="linkbtn" data-sort-reset>${ic("reset")}Sort them again</button><button class="linkbtn" data-sort-mode="code">${ic("code")}Rather write it in Python?</button></div>`;
    return;
  }
  const binOf = id => t.bins.find(b => b.id === id);
  const chip = i => `<button class="schip ${SO.first[i] ? "ok" : "late"}" data-sort-why="${i}" title="${SO.first[i] ? "Right first time" : "Took another try"}">${esc(items[i].name)}</button>`;
  const bin = (b, cls) => `<div class="sbin${cls ? " " + cls : ""}${now == null ? " off" : ""}" data-sort-bin="${b.id}"><button class="sput"${now == null ? " disabled" : ""} aria-label="${esc(now == null ? `${b.label}: ${b.who}` : `Put “${items[now].name}” in ${b.label}: ${b.who}`)}"><b>${esc(b.label)}</b><span>${esc(b.who)}</span></button><div class="schips">${items.map((_, i) => i).filter(i => SO.placed[i] === b.id).map(chip).join("")}</div></div>`;
  const note = `<div class="snote ${SO.note ? SO.note.kind : ""}" aria-live="polite"${SO.note ? "" : " hidden"}>${SO.note ? SO.note.html : ""}</div>`;
  const top = now != null
    ? `<button class="scard" draggable="true" data-sort-item="${now}" aria-describedby="sortHelp"><b>${esc(items[now].name)}</b><span>${esc(items[now].say)}</span></button>
       <div class="shelp">${left.length > 1 ? `<button class="linkbtn" data-sort-skip>Not sure? Come back to it later</button>` : ""}<button class="linkbtn" data-sort-hint>Tell me the answer</button></div>`
    : `<div class="sdone"><b>${ic("check")} All ${n} placed. ${sortRight()} of ${n} right first time.</b><p>The pattern: <em>${md((LESSONS[SO.p.id] || {}).angle ? LESSONS[SO.p.id].angle[0] : SO.p.pattern)}</em></p><p class="meta">Tap any idea on the map to see why it goes there.</p></div>`;
  $("sortBox").innerHTML = `<div class="shead"><h2>Sort the ideas</h2><span class="scount">${n - left.length} of ${n} placed</span></div>
    <p id="sortHelp">${md(t.intro)}</p>${top}${note}
    ${t.bins[4] ? bin(t.bins[4], "tray") : ""}
    <div class="smapwrap"><span class="sy">more value →</span><div class="smap">${t.bins.slice(0, 4).map(b => bin(b)).join("")}</div><span class="sx">more doable →</span></div>
    <div class="sfoot">${Object.keys(SO.placed).length ? `<button class="linkbtn" data-sort-reset>${ic("reset")}Start over</button>` : ""}<button class="linkbtn" data-sort-mode="code">${ic("code")}Rather write it in Python?</button></div>`;
}
function sortPlace(i, binId, byHint) {
  const t = SO.p.sort, it = t.items[i], right = t.bins.find(b => b.id === it.bin);
  if (i in SO.placed) return;
  // An idea that fails a gate is shelved, as the lesson says: Shelve is right for it too.
  const viaShelf = it.bin === "gate" && binId === "shelve";
  if (binId === it.bin || viaShelf || byHint) {
    if (!(i in SO.first)) SO.first[i] = !byHint;
    SO.placed[i] = it.bin; SO.skip = SO.skip.filter(x => x !== i);
    SO.note = { kind: "ok", html: byHint ? `<b>The answer: ${esc(right.label)}.</b> ${esc(it.why)}`
      : viaShelf ? `<b>${ic("check")} Right: shelved, because it stops at a gate.</b> ${esc(it.why)}`
      : `<b>${ic("check")} Right: ${esc(right.label)}.</b> ${esc(it.why)}` };
  } else {
    SO.first[i] = false;
    const wrong = t.bins.find(b => b.id === binId);
    SO.note = { kind: "no", html: `<b>Not ${esc(wrong.label.toLowerCase())}.</b> ${esc(it.why)} Try again.` };
  }
  sortSave();
  if (!sortLeft().length) { sortSolved(); SO.again = false; }
  sortRender(); renderFoot();
}
function sortSolved() {
  const p = SO.p, n = p.sort.items.length, prev = progress.solved[p.id];
  progress.solved[p.id] = { count: (prev ? prev.count : 0) + 1, last: today(), hints: n - sortRight(), mode: "sort" };
  lastRun = { summary: `Sorted all ${n} ideas, ${sortRight()} right first time.` };
  markDay();
  if (cur.kind === "lesson") $("stepper").querySelector('[data-step="2"]').classList.add("done");
  saveProgress(); renderTop();
}
function sortHint() { const now = sortLeft()[0]; if (now != null) sortPlace(now, null, true); }
function sortReset() {  // a fresh try; the lesson stays solved, and finishing again counts again
  Object.assign(SO, { placed: {}, first: {}, skip: [], note: null, again: true }); sortSave(); sortRender(); renderFoot();
  $("sortBox").scrollIntoView({ block: "start", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
}
function sortSetCode(on) {
  SO.code = on; try { localStorage.setItem(codeKey(SO.p.id), on ? "1" : "0"); } catch {}
  sortMode(); renderFoot();
  if (on) machineLoad(SO.p);
}
$("sortBox").addEventListener("click", e => {
  const t = e.target;
  const b = t.closest("[data-sort-bin]"), why = t.closest("[data-sort-why]");
  if (why) { const it = SO.p.sort.items[+why.dataset.sortWhy], bn = SO.p.sort.bins.find(x => x.id === it.bin); SO.note = { kind: "info", html: `<b>${esc(it.name)}: ${esc(bn.label)}.</b> ${esc(it.why)}` }; sortRender(); return; }
  if (b) { const now = sortLeft()[0]; if (now != null && !b.classList.contains("off")) sortPlace(now, b.dataset.sortBin); return; }
  if (t.closest("[data-sort-hint]")) { sortHint(); return; }
  if (t.closest("[data-sort-skip]")) { const now = sortLeft()[0]; SO.skip = [...SO.skip.filter(x => x !== now), now]; SO.note = null; sortRender(); return; }
  if (t.closest("[data-sort-reset]")) { sortReset(); return; }
  if (t.closest("[data-sort-mode]")) sortSetCode(true);
});
$("modeSwap").addEventListener("click", e => { if (e.target.closest("[data-sort-mode]")) sortSetCode(false); });
$("sortBox").addEventListener("dragstart", e => { const c = e.target.closest("[data-sort-item]"); if (c) e.dataTransfer.setData("text/plain", c.dataset.sortItem); });
$("sortBox").addEventListener("dragover", e => { const b = e.target.closest("[data-sort-bin]"); if (b && !b.classList.contains("off")) { e.preventDefault(); b.classList.add("over"); } });
$("sortBox").addEventListener("dragleave", e => { const b = e.target.closest("[data-sort-bin]"); if (b && !b.contains(e.relatedTarget)) b.classList.remove("over"); });
$("sortBox").addEventListener("drop", e => { const b = e.target.closest("[data-sort-bin]"); if (!b) return; e.preventDefault(); const i = e.dataTransfer.getData("text/plain"); if (i !== "") sortPlace(+i, b.dataset.sortBin); });
