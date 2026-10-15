// ---------- practice questions: Build as reading real evidence (content/model.py practice, ask) ----------
// For platform lessons the job is reading YAML, plans and logs, so the Build step can be a few
// questions instead of code: one per screen, the evidence above it. A wrong pick is crossed out
// with a plain reason; help is a clue first, then the answer. The Python version is one tap away.
const QF = { p: null, i: 0, tried: [], help: 0, first: {}, code: false, again: false, log: [] };
// One line per question for the backend: the question, wrong picks, clue or answer used, YAML checks.
function qfNote(change) {
  const a = QF.p.practice.asks[QF.i];
  const x = QF.log[QF.i] || (QF.log[QF.i] = { q: String(a.question).replace(/[`*]/g, "").slice(0, 120), wrong: [], clue: false, answer: false, first: true });
  change(x, a);
}
const flowing = () => !!(QF.p && cur && cur.p === QF.p && !QF.code);
const qfFinished = () => !!(QF.p && progress.solved[QF.p.id] && !QF.again);
const qfKey = id => "drill-flow-" + id, codeKey = id => "drill-code-" + id;
function qfLoad(p) {
  Object.assign(QF, { p: p.practice ? p : null, i: 0, tried: [], help: 0, first: {}, code: false, again: false, log: [] });
  if (QF.p) try { QF.code = localStorage.getItem(codeKey(p.id)) === "1"; } catch {}
  qfMode();
}
function qfMode() {
  if (!QF.p) { $("flowBox").hidden = true; return; }
  const on = flowing();
  $("paneBuild").classList.toggle("sorting", on);
  $("flowBox").hidden = !on;
  $("modeSwap").hidden = on;
  $("modeSwap").innerHTML = on ? "" : `<button class="linkbtn" data-qf-mode="flow">${ic("arrowl")}Back to the practice questions</button>`;
  if (on) qfRender();
}
function qfEvidence(e, a, solved) {
  if (!e) return "";
  if (e.kind === "code") return `<figure class="qf-ev">${e.title ? `<figcaption>${esc(e.title)}</figcaption>` : ""}<pre class="code">${esc(e.text)}</pre></figure>`;
  if (e.kind === "claim") return `<div class="qf-claim"><span class="eyebrow">${esc(e.who || "The AI said")}</span><p>${md(e.text)}</p></div>`;
  if (e.kind === "prompt") return `<figure class="qf-ev"><figcaption>${esc(e.title || "Your prompt")}</figcaption><pre class="code qf-prompt">${esc(e.text).replace("___", `<span class="gap now">?</span>`)}</pre></figure>`;
  if (e.kind === "chain") return `<ol class="qf-chain">${e.stops.map((st, k) => `<li class="${st.state}"><span class="qf-dot">${st.state === "ok" ? "✓" : k + 1}</span><span><b>${esc(st.label)}</b>${st.sub ? `<small>${esc(st.sub)}</small>` : ""}</span>${st.tag ? `<em>${esc(st.tag)}</em>` : ""}</li>`).join("")}</ol>${e.snippet ? `<pre class="code">${esc(e.snippet)}</pre>` : ""}`;
  if (e.kind === "plan") {
    const sum = (e.summary || []).map(([n, w, c]) => `<span class="qf-c ${c || ""}">${esc(n)} ${esc(w)}</span>`).join("");
    const row = (r, k) => {
      const cls = a && a.pick ? (solved && k === a.answer ? " right" : QF.tried.includes(k) ? " wrong" : "") : "";
      const inner = `<span class="qf-sym ${r.sym === "-/+" ? "r" : r.sym === "+" ? "a" : r.sym === "-" ? "d" : "u"}">${esc(r.sym)}</span><span class="qf-addr">${esc(r.address)}${r.note ? `<small>${esc(r.note)}</small>` : ""}</span>`;
      return a && a.pick ? `<button class="qf-row${cls}" data-qf="${k}"${solved || QF.tried.includes(k) ? " disabled" : ""}>${inner}</button>` : `<div class="qf-row">${inner}</div>`;
    };
    return `${e.title ? `<span class="eyebrow">${esc(e.title)}</span>` : ""}<div class="qf-sum">${sum}</div><div class="qf-rows">${e.changes.map(row).join("")}</div>`;
  }
  return "";
}
// Fix the YAML: a small reader for the YAML config repos use (maps, lists of maps, plain values),
// with the line of every key, and the same checks as content/yaml_rules.py.
function yamlRead(text) {
  const rows = [];
  text.split("\n").forEach((raw, k) => {
    if (/^\s*(#.*)?$/.test(raw)) return;
    const lead = raw.match(/^[ \t]*/)[0];
    if (lead.includes("\t")) throw { line: k + 1, msg: "Use spaces to indent, not tabs." };
    rows.push({ n: k + 1, ind: lead.length, text: raw.trim() });
  });
  const scalar = v => {
    v = v.replace(/\s+#.*$/, "").trim();
    if (/^".*"$|^'.*'$/.test(v)) return v.slice(1, -1);
    if (/^-?\d+$/.test(v)) return parseInt(v, 10);
    if (v === "true" || v === "false") return v === "true";
    if (v === "" || v === "null" || v === "~") return null;
    return v;
  };
  const isItem = r => r.text === "-" || r.text.startsWith("- ");
  let i = 0;
  function block(ind) { return isItem(rows[i]) ? list(ind) : map(ind); }
  function map(ind) {
    const obj = {}, lines = {};
    Object.defineProperty(obj, "__lines", { value: lines });
    Object.defineProperty(obj, "__line", { value: rows[i].n });
    while (i < rows.length && rows[i].ind === ind && !isItem(rows[i])) {
      const r = rows[i], m = r.text.match(/^([^:#"'][^:]*?|"[^"]*"):(?:\s+(.*))?$/);
      if (!m) throw { line: r.n, msg: "Expected key: value." };
      const key = m[1].replace(/^"|"$/g, "").trim(); lines[key] = r.n; i++;
      if (m[2] === undefined || m[2].replace(/\s*#.*$/, "") === "") obj[key] = i < rows.length && rows[i].ind > ind ? block(rows[i].ind) : null;
      else obj[key] = scalar(m[2]);
    }
    if (i < rows.length && rows[i].ind > ind) throw { line: rows[i].n, msg: "This line is indented too far." };
    return obj;
  }
  function list(ind) {
    const arr = [];
    while (i < rows.length && rows[i].ind === ind && isItem(rows[i])) {
      const r = rows[i], after = r.text.slice(1).trimStart();
      if (!after) { i++; arr.push(i < rows.length && rows[i].ind > ind ? block(rows[i].ind) : null); continue; }
      if (/^[^:#"'][^:]*:(\s|$)/.test(after)) { rows[i] = { n: r.n, ind: ind + (r.text.length - after.length), text: after }; arr.push(map(rows[i].ind)); }
      else { arr.push(scalar(after)); i++; }
    }
    return arr;
  }
  if (!rows.length) return null;
  const doc = block(rows[0].ind);
  if (i < rows.length) throw { line: rows[i].n, msg: "This line's indent doesn't match the lines above it." };
  return doc;
}
function yamlCheck(text, rules, goal) {
  let doc;
  try { doc = yamlRead(text); } catch (e) { return [{ line: e.line, msg: e.msg }]; }
  let node = doc;
  for (const part of rules.path.split(".")) node = node && typeof node === "object" && !Array.isArray(node) ? node[part] : undefined;
  const items = Array.isArray(node) ? node : node && typeof node === "object" ? [node] : null;
  if (!items) return [{ line: 1, msg: `Expected a list under ${rules.path}.` }];
  const out = [], forbid = rules.forbid || {};
  items.forEach(it => {
    if (!it || typeof it !== "object") { out.push({ line: 1, msg: "Each item needs key: value lines." }); return; }
    const at = f => (it.__lines || {})[f] || it.__line || 1;
    for (const [f, msg] of Object.entries(forbid)) if (f in it) out.push({ line: at(f), msg });
    if (rules.allowed) for (const f of Object.keys(it)) if (!rules.allowed.includes(f) && !(f in forbid)) out.push({ line: at(f), msg: `${f} isn't a field the check knows.` });
    for (const f of rules.required || []) if (!(f in it)) out.push({ line: it.__line || 1, msg: `${f} is missing.` });
    for (const [f, kind] of Object.entries(rules.types || {})) if (f in it && (kind === "int" ? !Number.isInteger(it[f]) : typeof it[f] !== "string")) out.push({ line: at(f), msg: `${f} must be ${kind === "int" ? "a whole number" : "text"}.` });
    for (const [f, vals] of Object.entries(rules.enum || {})) if (f in it && !vals.includes(it[f])) out.push({ line: at(f), msg: `${f} must be one of ${vals.join(", ")}.` });
    if (rules.size) { const fx = "num_workers" in it, lo = "min_workers" in it, hi = "max_workers" in it;
      if (!(fx && !lo && !hi) && !(lo && hi && !fx)) out.push({ line: at(fx ? "num_workers" : lo ? "min_workers" : hi ? "max_workers" : "name"), msg: "Use num_workers, or both min_workers and max_workers." }); }
  });
  if (out.length) return out;
  for (const g of goal || []) {
    if ("equals" in g && (!items.length || items[0][g.field] !== g.equals)) out.push({ line: null, msg: g.message });
    if ("contains" in g && !items.some(it => it[g.field] === g.contains)) out.push({ line: null, msg: g.message });
  }
  return out;
}
function qfFixHtml(a, solved) {
  const text = QF.text != null ? QF.text : a.start, probs = QF.probs;
  const rows = Math.max(5, text.split("\n").length + 1);
  const list = probs && probs.length ? `<div class="qf-probs" aria-live="polite"><b>${probs.length} problem${probs.length === 1 ? "" : "s"}</b>${probs.map(p => `<div>${p.line ? `<span class="qf-ln">Line ${p.line}</span>` : `<span class="qf-ln">Goal</span>`}${esc(p.msg)}</div>`).join("")}</div>` : "";
  const keys = ["  ", "- ", ": ", "min_workers: ", "max_workers: ", "policy_name: "].filter(k => k.trim().length < 3 || text.includes("workers") || a.rules.size);
  return `<figure class="qf-ev"><figcaption>${esc(a.file || "YAML")}</figcaption>
    <textarea class="qf-yaml" data-qf-yaml rows="${rows}" spellcheck="false" autocapitalize="off" autocomplete="off"${solved ? " readonly" : ""} aria-label="${esc(a.file || "YAML")}">${esc(text)}</textarea></figure>
    ${solved ? "" : `<div class="qf-keys" aria-label="Typing keys">${keys.map(k => `<button type="button" data-qf-key="${esc(k)}">${k === "  " ? "⇥ indent" : esc(k.trim() || k)}</button>`).join("")}</div>`}
    ${list}`;
}
function qfRender() {
  const pr = QF.p.practice, asks = pr.asks, n = asks.length, box = $("flowBox");
  const dots = k => `<span class="qf-dots" aria-hidden="true">${asks.map((_, j) => `<i class="${j < k ? "d" : j === k ? "n" : ""}"></i>`).join("")}</span>`;
  const right = Object.values(QF.first).filter(Boolean).length;
  if (qfFinished() && QF.i === 0 && !QF.tried.length) {
    const sv = progress.solved[QF.p.id];
    box.innerHTML = `<div class="shead"><h2>Practice</h2><span class="scount">done</span></div>
      <div class="sdone"><b>${ic("check")} You answered these before${sv && sv.hints != null ? `: ${Math.max(0, n - sv.hints)} of ${n} right first time` : ""}.</b></div>
      <div class="sfoot"><button class="linkbtn" data-qf-reset>${ic("reset")}Practise again</button><button class="linkbtn" data-qf-mode="code">${ic("code")}Rather write it in Python?</button></div>`;
    return;
  }
  if (QF.i >= n) {
    box.innerHTML = `<div class="shead"><h2>Practice</h2><span class="scount">done</span></div>
      <div class="sdone"><b>${ic("check")} All ${n} answered. ${right} of ${n} right first time.</b><p>The pattern: <em>${md(LESSONS[QF.p.id] ? LESSONS[QF.p.id].angle[0] : QF.p.pattern)}</em></p></div>
      <div class="sfoot"><button class="linkbtn" data-qf-reset>${ic("reset")}Practise again</button><button class="linkbtn" data-qf-mode="code">${ic("code")}Rather write it in Python?</button></div>`;
    return;
  }
  const a = asks[QF.i], solved = QF.solved === QF.i, lastWrong = QF.tried.length ? QF.tried[QF.tried.length - 1] : null;
  if (a.kind === "fix") {
    const fixHelp = solved ? `<button class="btn primary qf-next" data-qf-next>${QF.i + 1 < n ? "Next question" : "See how you did"}${ic("arrowr")}</button>`
      : `<button class="btn primary qf-next" data-qf-check>Check YAML</button>${QF.help === 0 ? `<button class="linkbtn" data-qf-help>Give me a clue</button>` : `<p class="clzclue">${ic("bulb")}<span>${md(a.clue)}</span></p><button class="linkbtn" data-qf-help>Show a fixed version</button>`}`;
    box.innerHTML = `<div class="shead"><h2>Practice</h2><span class="scount">Question ${QF.i + 1} of ${n}</span>${dots(QF.i)}</div>
      ${QF.i === 0 ? `<p class="meta">${md(pr.intro)}</p>` : ""}
      <p class="q">${md(a.question)}</p>${qfFixHtml(a, solved)}
      <div aria-live="polite">${solved ? `<div class="snote ok"><b>${ic("check")} ${QF.help === 2 ? "A fixed version." : "The check passes."}</b> ${md(a.why)}</div>` : ""}</div>
      <div class="clzhelp">${fixHelp}</div>
      <div class="sfoot"><button class="linkbtn" data-qf-mode="code">${ic("code")}Rather write it in Python?</button></div>`;
    return;
  }
  const opts = a.pick ? "" : `<div class="opts">${a.options.map((o, k) => `<button class="opt${solved && k === a.answer ? " right" : QF.tried.includes(k) ? " wrong" : ""}" data-qf="${k}"${solved || QF.tried.includes(k) ? " disabled" : ""}><span class="k">${"ABCDEF"[k]}</span><span>${md(o)}</span></button>`).join("")}</div>`;
  const note = solved ? `<div class="snote ok"><b>${ic("check")} ${QF.help === 2 ? "The answer." : "Right."}</b> ${md(a.why)}</div>`
    : lastWrong != null ? `<div class="snote no"><b>Not quite.</b> ${md((a.wrong && a.wrong[lastWrong]) || "Look at the evidence again.")}</div>` : "";
  const help = solved ? `<button class="btn primary qf-next" data-qf-next>${QF.i + 1 < n ? "Next question" : "See how you did"}${ic("arrowr")}</button>`
    : QF.help === 0 ? `<button class="linkbtn" data-qf-help>Give me a clue</button>`
    : `<p class="clzclue">${ic("bulb")}<span>${md(a.clue)}</span></p><button class="linkbtn" data-qf-help>Tell me the answer</button>`;
  box.innerHTML = `<div class="shead"><h2>Practice</h2><span class="scount">Question ${QF.i + 1} of ${n}</span>${dots(QF.i)}</div>
    ${QF.i === 0 ? `<p class="meta">${md(pr.intro)}</p>` : ""}
    ${qfEvidence(a.evidence, a, solved)}
    <p class="q">${md(a.question)}</p>${opts}
    <div aria-live="polite">${note}</div><div class="clzhelp">${help}</div>
    <div class="sfoot"><button class="linkbtn" data-qf-mode="code">${ic("code")}Rather write it in Python?</button></div>`;
}
function qfPick(k) {
  const a = QF.p.practice.asks[QF.i];
  if (QF.solved === QF.i || QF.tried.includes(k)) return;
  if (k === a.answer) { if (!(QF.i in QF.first)) QF.first[QF.i] = !QF.tried.length && QF.help < 2; QF.solved = QF.i; qfNote(x => { x.first = !!QF.first[QF.i]; }); fxOn($("flowBox"), "seal", FX.seal()); }
  else { QF.tried.push(k); QF.first[QF.i] = false; qfNote((x, a) => { x.first = false; x.wrong.push(a.pick ? a.evidence.changes[k].address : String(a.options[k]).replace(/[`*]/g, "")); }); }
  qfRender();
}
function qfHelp() {
  const a = QF.p.practice.asks[QF.i];
  QF.help = Math.min(2, QF.help + 1);
  qfNote(x => { x.first = false; if (QF.help === 1) x.clue = true; else x.answer = true; });
  if (QF.help === 2) { QF.first[QF.i] = false; QF.solved = QF.i; if (a.kind === "fix") { QF.text = a.answer; QF.probs = null; } }
  qfRender();
}
function qfCheck() {
  const a = QF.p.practice.asks[QF.i], text = QF.text != null ? QF.text : a.start;
  QF.probs = yamlCheck(text, a.rules, a.goal);
  qfNote(x => { x.checks = (x.checks || 0) + 1; if (QF.probs.length) { x.first = false; x.problems = [...new Set([...(x.problems || []), ...QF.probs.map(p => p.msg)])].slice(0, 6); } });
  if (!QF.probs.length) { if (!(QF.i in QF.first)) QF.first[QF.i] = !QF.fails && QF.help < 2; QF.solved = QF.i; fxOn($("flowBox"), "seal", FX.seal()); }
  else { QF.fails = (QF.fails || 0) + 1; QF.first[QF.i] = false; }
  qfRender();
}
function qfNext() {
  QF.i++; QF.tried = []; QF.help = 0; QF.solved = null; QF.text = null; QF.probs = null; QF.fails = 0;
  if (QF.i >= QF.p.practice.asks.length) qfSolved();
  qfRender(); renderFoot();
  $("flowBox").scrollIntoView({ block: "start", behavior: motionOn() ? "smooth" : "auto" });
}
function qfSolved() {
  const p = QF.p, n = p.practice.asks.length, right = Object.values(QF.first).filter(Boolean).length, prev = progress.solved[p.id];
  progress.solved[p.id] = { count: (prev ? prev.count : 0) + 1, last: today(), hints: n - right, mode: "practice" };
  // what a manager needs to help: every question that wasn't right first time, and how
  if (cur.kind === "lesson") lp(p.id).practice = { day: today(), right, total: n, missed: (QF.log || []).filter(x => x && !x.first).map(({ first, ...x }) => x) };
  lastRun = { summary: `Answered all ${n} practice questions, ${right} right first time.` };
  QF.again = false; markDay();
  if (cur.kind === "lesson") $("stepper").querySelector('[data-step="2"]').classList.add("done");
  saveProgress(); renderTop();
}
function qfReset() { Object.assign(QF, { i: 0, tried: [], help: 0, first: {}, solved: null, again: true, text: null, probs: null, fails: 0, log: [] }); qfRender(); renderFoot(); }
function qfSetCode(on) {
  QF.code = on; try { localStorage.setItem(codeKey(QF.p.id), on ? "1" : "0"); } catch {}
  qfMode(); renderFoot();
  if (on) machineLoad(QF.p);
}
$("flowBox").addEventListener("click", e => {
  const t = e.target;
  const o = t.closest("[data-qf]"); if (o && !o.disabled) { qfPick(+o.dataset.qf); return; }
  if (t.closest("[data-qf-help]")) { qfHelp(); return; }
  if (t.closest("[data-qf-check]")) { qfCheck(); return; }
  const key = t.closest("[data-qf-key]");
  if (key) {  // a typing key: insert at the cursor and keep typing
    const ta = $("flowBox").querySelector("[data-qf-yaml]"), k = key.dataset.qfKey, a = ta.selectionStart, b = ta.selectionEnd;
    ta.value = ta.value.slice(0, a) + k + ta.value.slice(b); ta.selectionStart = ta.selectionEnd = a + k.length; ta.focus(); QF.text = ta.value; return;
  }
  if (t.closest("[data-qf-next]")) { qfNext(); return; }
  if (t.closest("[data-qf-reset]")) { qfReset(); return; }
  if (t.closest('[data-qf-mode="code"]')) qfSetCode(true);
});
$("modeSwap").addEventListener("click", e => { if (e.target.closest('[data-qf-mode="flow"]')) qfSetCode(false); });
$("flowBox").addEventListener("input", e => { if (e.target.matches("[data-qf-yaml]")) QF.text = e.target.value; });
$("flowBox").addEventListener("keydown", e => {  // Tab indents two spaces in the YAML box, like an editor
  if (e.key !== "Tab" || !e.target.matches("[data-qf-yaml]") || e.shiftKey) return;
  e.preventDefault(); const ta = e.target, a = ta.selectionStart; ta.value = ta.value.slice(0, a) + "  " + ta.value.slice(ta.selectionEnd); ta.selectionStart = ta.selectionEnd = a + 2; QF.text = ta.value;
});
