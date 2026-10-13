// ---------- the machine: the example's rows travel through your function into bins ----------
// Only for lessons whose exercise sets `machine` (content/model.py): rows in, one list per bin out.
const M = { p: null, rows: [], exp: null, got: null, k: 0, timer: null, mode: "idle", picked: null, tokens: [], g: null };
const rowKey = r => JSON.stringify(Object.keys(r).sort().map(k => [k, r[k]]));
function matchBins(rows, lists) {  // which input row ended up in which list, by equal value, in order
  const pool = new Map();
  rows.forEach((r, i) => { const k = rowKey(r); if (!pool.has(k)) pool.set(k, []); pool.get(k).push(i); });
  const bin = rows.map(() => null), order = lists.map(() => []);
  lists.forEach((list, b) => (Array.isArray(list) ? list : []).forEach(r => {
    const q = r && typeof r === "object" && !Array.isArray(r) ? pool.get(rowKey(r)) : null;
    if (q && q.length) { const i = q.shift(); bin[i] = b; order[b].push(i); }
  }));
  return { bin, order };
}
function machineLoad(p) {
  machineStop();
  M.p = p.machine ? p : null; M.g = null; $("machine").hidden = !M.p;
  if (!M.p) return;
  const c = p.cases[sampleIndex(p)], m = p.machine, names = paramNames(p);
  M.rows = c.args[0]; M.exp = matchBins(M.rows, c.expected); M.got = null; M.k = 0; M.mode = "idle"; M.picked = null;
  M.field = m.label_field || c.args[m.label_arg];
  M.leakField = m.leak_arg != null ? c.args[m.leak_arg] : null;
  const values = [...new Set(M.rows.map(r => String(r[M.field])))];
  $("mFn").textContent = p.fn + "()";
  $("mArgs").innerHTML = c.args.slice(1).map((a, i) => `<span>${esc((names[i + 1] || "input " + (i + 2)) + " = " + short(py(a), 36))}</span>`).join("");
  $("mRowsLabel").innerHTML = `${esc(names[0] || "rows")}<small>each pill is one row · tap one</small>`;
  $("mRet").textContent = "return [" + m.bins.join(", ") + "]";
  $("mBins").innerHTML = m.bins.map((b, i) => `<div class="mbin"><span class="mlabel">${esc(b)}</span><span class="mwho">${esc(m.who[i])}</span></div>`).join("");
  $("mTokens").innerHTML = M.rows.map((r, i) => {
    const v = String(r[M.field]), col = ["var(--tok-a)", "var(--tok-b)", "var(--tok-c)", "var(--tok-d)"][values.indexOf(v) % 4];
    return `<button type="button" class="mtok" data-i="${i}" style="background:${col}" aria-label="Row ${i + 1}, ${esc(M.field)} ${esc(v)}. Show the whole row.">${esc(short(v, 5))}</button>`;
  }).join("");
  M.tokens = [...$("mTokens").children];
  M.tokens.forEach(t => t.onclick = () => { M.picked = +t.dataset.i; machinePanel(); });
  $("mScrub").max = M.rows.length; $("mReplay").hidden = true; $("mLeak").innerHTML = ""; $("mDemo").disabled = false;
  setLabel($("mDemo"), "Watch what should happen");
  machineLayout(); machineRender(false);
}
function machineLayout() {
  if (!M.p) return;
  const W = $("mStage").clientWidth; if (!W) return;
  const n = M.rows.length, nb = M.p.machine.bins.length, tw = 44, gap = 6;
  const perRow = Math.max(1, Math.floor((W + gap) / (tw + gap))), qRows = Math.ceil(n / perRow);
  const qTop = 26, fnTop = qTop + qRows * 32 + 26, argsTop = fnTop + 48, binTop = argsTop + 46;
  // Four bins make a 2 by 2 map (value up the side, doable along the bottom); fewer sit in one row.
  const grid = nb === 4, perLine = grid ? 2 : nb, lines = grid ? 2 : 1, inset = grid ? 18 : 0;
  const bw = (W - inset - (perLine - 1) * 10) / perLine, cols = Math.max(1, Math.floor((bw - 16) / (tw + 8)));
  const binH = 50 + Math.ceil(n / cols) * 32 + 4, retTop = binTop + lines * (binH + 10) + (grid ? 14 : 0);
  const bx = [...Array(nb).keys()].map(b => inset + (b % perLine) * (bw + 10)), by = [...Array(nb).keys()].map(b => binTop + Math.floor(b / perLine) * (binH + 10));
  M.g = { W, n, nb, tw, gap, perRow, qTop, fnTop, binTop, bw, cols, bx, by };
  $("mStage").style.height = (retTop + 22) + "px";
  $("mFn").style.top = fnTop + "px"; $("mArgs").style.top = argsTop + "px"; $("mRet").style.top = retTop + "px";
  [...$("mBins").children].forEach((b, i) => Object.assign(b.style, { left: bx[i] + "px", top: by[i] + "px", width: bw + "px", height: binH + "px" }));
  const c = W / 2, fb = fnTop + 40;
  const axes = grid ? `<text x="4" y="${binTop + binH + 5}" transform="rotate(-90 4 ${binTop + binH + 5})" text-anchor="middle" dominant-baseline="hanging" font-size="11" fill="var(--muted)">more value →</text><text x="${inset + (W - inset) / 2}" y="${binTop + 2 * (binH + 10) + 6}" text-anchor="middle" font-size="11" fill="var(--muted)">more doable →</text>` : "";
  $("mWires").innerHTML = `<path d="M${c} ${qTop + qRows * 32 + 2} V ${fnTop - 4}" stroke="var(--fg)" stroke-width="2" fill="none"/><path d="M${c - 6} ${fnTop - 10} L${c} ${fnTop - 2} L${c + 6} ${fnTop - 10}" stroke="var(--fg)" stroke-width="2" fill="none"/>` + axes +
    (grid ? `<path d="M${c} ${fb} V ${binTop - 2}" stroke="var(--fg)" stroke-width="2" fill="none"/>`
      : [...Array(nb).keys()].map(i => { const x = bx[i] + bw / 2; return `<path d="M${c} ${fb} C ${c} ${fb + 30}, ${x} ${binTop - 30}, ${x} ${binTop - 2}" stroke="var(--fg)" stroke-width="2" fill="none"/>`; }).join(""));
}
function machineData() {
  return M.mode === "demo" ? M.exp : M.mode === "run" ? M.got : null;
}
function machineRender(fly) {
  if (M.p && (!M.g || M.g.W !== $("mStage").clientWidth)) machineLayout();  // measure on demand: the card may have just appeared
  if (!M.p || !M.g) return;
  const g = M.g, res = machineData(), bins = M.p.machine.bins;
  const leak = new Set();
  if (M.mode === "run" && M.leakField && res) {
    const seen = new Map();
    res.order.forEach((ids, b) => ids.filter(i => i < M.k).forEach(i => { const v = String(M.rows[i][M.leakField]); if (!seen.has(v)) seen.set(v, new Set()); seen.get(v).add(b); }));
    seen.forEach((bs, v) => { if (bs.size > 1) leak.add(v); });
  }
  M.tokens.forEach((t, i) => {
    let x, y; const b = res ? res.bin[i] : null;
    if (res && i < M.k && b != null) { const slot = res.order[b].filter(id => id < M.k).indexOf(i); x = g.bx[b] + 10 + (slot % g.cols) * (g.tw + 8); y = g.by[b] + 50 + Math.floor(slot / g.cols) * 32; }
    else if (res && i < M.k) { x = g.W / 2 - g.tw / 2; y = g.fnTop + 7; }
    else { x = (i % g.perRow) * (g.tw + g.gap); y = g.qTop + Math.floor(i / g.perRow) * 32; }
    if (fly === i) { x = g.W / 2 - g.tw / 2; y = g.fnTop + 7; }
    t.style.transform = `translate(${x}px, ${y}px)`;
    const isLeak = M.leakField && i < M.k && leak.has(String(M.rows[i][M.leakField]));
    t.classList.toggle("cur", !!res && i === M.k - 1 && fly !== i && !isLeak);
    t.classList.toggle("fly", fly === i);
    t.classList.toggle("leak", !!isLeak);
    t.classList.toggle("lost", !!res && i < M.k && b == null);
  });
  $("mFn").classList.toggle("busy", fly != null && fly !== false);
  $("mTag").hidden = M.mode !== "demo";
  $("mStep").textContent = `Row ${M.k} of ${M.rows.length}`;
  $("mLeak").innerHTML = leak.size ? `<div class="result fail"><div><b>Leak found.</b> ${esc(M.leakField)} ${[...leak].map(v => `"${esc(v)}"`).join(" and ")} ${leak.size > 1 ? "are" : "is"} in more than one bin. Rows that share a ${esc(M.leakField)} must stay together, or the test includes data the model already trained on and its score looks better than it really is.</div></div>` : "";
  // what each bin holds so far, as tables
  $("mOuts").innerHTML = res ? bins.map((name, b) => {
    const ids = res.order[b].filter(i => i < M.k);
    const wrong = ids.filter(i => M.exp.bin[i] !== b).length;
    const cap = `${esc(name)} <small class="${wrong ? "bad" : ""}">${wrong ? wrong + " on the wrong side" : M.mode === "demo" ? "expected" : "your result"}</small>`;
    return `<div class="dtwrap">${rowsTable(ids.map(i => M.rows[i]), { caption: cap, numbered: true, ids, wrong: j => M.exp.bin[ids[j]] !== b, empty: "No rows yet." })}</div>`;
  }).join("") : "";
  machinePanel();
}
function machinePanel() {
  const res = machineData(), show = M.picked != null ? M.picked : (res && M.k > 0 ? M.k - 1 : null);
  if (show == null) { $("mPanel").innerHTML = `<div class="mkv wide"><span>Tap a pill to see the whole row</span>${esc(py(M.rows[0]))}</div>`; codeBar(0); return; }
  const r = M.rows[show], bins = M.p.machine.bins, should = M.exp.bin[show];
  let html = `<div class="mkv wide"><span>Row ${show + 1}</span>${esc(py(r))}</div><div class="mkv"><span>${esc(M.field)}</span>${esc(py(r[M.field]))}</div><div class="mkv"><span>Should go to</span>${should != null ? esc(bins[should]) : "?"}</div>`;
  const went = res && show < M.k ? res.bin[show] : undefined;
  if (M.mode === "run" && went !== undefined) html += `<div class="mkv wide"><span>Your code sent it to</span><b class="${went === should ? "ok" : "no"}">${went != null ? esc(bins[went]) : "nowhere: it went missing"}</b></div>`;
  $("mPanel").innerHTML = html;
  if (M.mode === "run" && went != null && M.picked == null) {
    const lines = $("code").value.split("\n"), re = new RegExp("\\b" + bins[went] + "\\.append");
    let n = lines.findIndex(l => re.test(l)) + 1; if (!n) n = lines.findIndex(l => /\.append/.test(l)) + 1;
    codeBar(n);
  } else codeBar(0);
}
function codeBar(n) {  // the yellow line behind the code that sent this row to its bin
  const bar = $("codeBar"), line = n ? $("codeHl").children[n - 1] : null;
  if (!line) { bar.hidden = true; return; }
  bar.hidden = false; bar.style.top = line.offsetTop + "px"; bar.style.height = parseFloat(getComputedStyle($("code")).lineHeight) + "px";
}
function machineSet(v, fly) {
  M.k = Math.max(0, Math.min(M.rows.length, v)); $("mScrub").value = M.k;
  if (fly && motionOn()) { machineRender(M.k - 1); setTimeout(() => machineRender(false), 320); } else machineRender(false);
}
function machineStop() { clearInterval(M.timer); M.timer = null; $("mPlay").innerHTML = ic("play"); $("mPlay").setAttribute("aria-label", "Replay"); }
function machinePlay(from, done) {
  machineStop(); M.picked = null; machineSet(from, false);
  $("mPlay").innerHTML = '<svg class="ic" aria-hidden="true" viewBox="0 0 24 24"><path d="M8 5v14M16 5v14"/></svg>'; $("mPlay").setAttribute("aria-label", "Pause");
  M.timer = setInterval(() => { if (M.k >= M.rows.length) { machineStop(); if (done) done(); return; } machineSet(M.k + 1, true); }, 800);
}
function machineRun(got) {
  if (!M.p) return;
  const lists = Array.isArray(got) ? got : [];
  M.got = matchBins(M.rows, M.p.machine.bins.map((_, b) => lists[b]));
  M.mode = "run"; $("mReplay").hidden = false;
  machinePlay(0);
}
$("mPlay").onclick = () => { if (M.timer) machineStop(); else machinePlay(M.k >= M.rows.length ? 0 : M.k); };
$("mScrub").oninput = e => { machineStop(); M.picked = null; machineSet(+e.target.value, false); };
$("mDemo").onclick = () => {
  M.mode = "demo"; $("mReplay").hidden = true; $("mDemo").disabled = true;
  machinePlay(0, () => setTimeout(() => { $("mDemo").disabled = false; setLabel($("mDemo"), "Watch it again"); if (M.mode === "demo") { M.mode = M.got ? "run" : "idle"; machineSet(M.got ? M.rows.length : 0, false); } }, 1600));
};
{ let w = 0; new ResizeObserver(() => { const nw = $("mStage").clientWidth; if (nw && nw !== w) { w = nw; machineLayout(); machineRender(false); } }).observe($("mStage")); }
