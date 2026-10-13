// ---------- content packs: practice exercises and investigation views (src/drill/content/packs.py) ----------
// A pack lesson has the same four steps; its Build step is Practice: one exercise, checked here,
// with the why under the answer. The views draw a lesson's evidence as rows a phone can read.
const packOf = id => (LESSONS[id] || {}).pack || null;
const PX = {};  // lesson id -> this exercise's state while the page is open (also kept in the browser)
const pxKey = id => "drill-px-" + id;
function pxState(id) {
  if (!PX[id]) { let s = null; try { s = JSON.parse(localStorage.getItem(pxKey(id)) || "null"); } catch {} PX[id] = s || {}; }
  return PX[id];
}
function pxSave(id) { try { localStorage.setItem(pxKey(id), JSON.stringify(PX[id])); } catch {} }
// A fixed shuffle per lesson, so options don't move when the page redraws.
function pxShuffle(items, seed) {
  let h = 0; for (const c of seed) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  const out = items.map((v, i) => [((h ^ (i * 2654435761)) >>> 0) % 997, v]);
  out.sort((a, b) => a[0] - b[0]);
  const shuffled = out.map(x => x[1]);
  return shuffled.every((v, i) => v === items[i]) && items.length > 1 ? [...shuffled.slice(1), shuffled[0]] : shuffled;
}
function pxSolved(id, tries) {
  const prev = progress.solved[id];
  progress.solved[id] = { count: (prev ? prev.count : 0) + 1, last: today(), hints: Math.max(0, tries - 1), mode: "pack" };
  markDay(); saveProgress(); renderTop();
  if (cur && cur.kind === "lesson") { const b = $("stepper").querySelector('[data-step="2"]'); if (b) b.classList.add("done"); }
  renderFoot();
}
// Investigation views: relationships, an implementation trace, a troubleshooting walkthrough, a plan review.
const IV_STATE = { same: "same", added: "added here", changed: "changed here", unknown: "not verified" };
const IV_ACTION = { create: "create", update: "update in place", replace: "replace", destroy: "destroy", read: "read", no_op: "no change" };
// A guided tour: a screenshot with numbered stops; the current one is boxed, the rest dimmed.
const TOUR = {}, TOURV = {};  // tour key -> current stop, and the tour itself
function tourHtml(v) {
  const key = (cur ? cur.id : "") + "|" + v.image, n = v.stops.length, i = Math.min(TOUR[key] || 0, n - 1), s = v.stops[i];
  TOURV[key] = v;
  // the close-up: the stop's box, scaled to the full width, so small text is readable on a phone
  const zx = s.w >= 100 ? 0 : (s.x / (100 - s.w)) * 100, zy = s.h >= 100 ? 0 : (s.y / (100 - s.h)) * 100;
  const zoom = `background-image:url('${esc(v.image)}');background-size:${(100 / s.w) * 100}% auto;background-position:${zx}% ${zy}%;aspect-ratio:${s.w} / ${s.h * (v.ratio || 0.5333)}`;
  return `<section class="iv iv-tour" data-tour="${esc(key)}">${v.title ? `<h4>${esc(v.title)}</h4>` : "<h4>Find your way around</h4>"}
    <a class="tour-shot" href="${esc(v.image)}" target="_blank" rel="noopener" aria-label="Open the full screenshot"><img src="${esc(v.image)}" alt="${esc(v.alt || v.title || "Screenshot")}">
      <i class="tour-box" style="left:${s.x}%;top:${s.y}%;width:${s.w}%;height:${s.h}%"><b>${i + 1}</b></i></a>
    <div class="tour-zoom" role="img" aria-label="Close-up of step ${i + 1}" style="${zoom}"></div>
    <div class="tour-step" aria-live="polite"><span class="eyebrow">Step ${i + 1} of ${n}</span><b class="tour-title">${esc(s.title)}</b><p>${md(s.text)}</p></div>
    <div class="tour-nav"><button class="btn" data-tour-go="${i - 1}"${i === 0 ? " disabled" : ""} aria-label="Back">${ic("arrowl")}</button>
      ${v.stops.map((st, k) => `<button class="tour-dot${k === i ? " on" : ""}" data-tour-go="${k}" aria-label="Step ${k + 1}: ${esc(st.title)}"${k === i ? ' aria-current="step"' : ""}>${k + 1}</button>`).join("")}
      <button class="btn" data-tour-go="${i + 1}"${i === n - 1 ? " disabled" : ""} aria-label="Next">${ic("arrowr")}</button></div></section>`;
}
document.addEventListener("click", e => {
  const go = e.target.closest("[data-tour-go]"), box = go && go.closest("[data-tour]");
  if (!box || go.disabled) return;
  const key = box.dataset.tour, v = TOURV[key]; if (!v) return;
  TOUR[key] = Math.max(0, Math.min(v.stops.length - 1, +go.dataset.tourGo));
  box.outerHTML = tourHtml(v);
});
function viewHtml(v) {
  const head = v.title ? `<h4>${esc(v.title)}</h4>` : "";
  if (v.kind === "tour") return tourHtml(v);
  if (v.kind === "relationships") return `<section class="iv iv-rel">${head || "<h4>What points at what</h4>"}
    ${v.links.map(l => `<div class="iv-link"><code>${esc(l.from)}</code><span class="iv-ref">${esc(l.ref)} →</span><code>${esc(l.to)}</code></div>`).join("")}</section>`;
  if (v.kind === "trace") return `<section class="iv iv-trace">${head || `<h4>Follow <code>${esc(v.field)}</code> through each layer</h4>`}
    <ol>${v.layers.map(l => `<li class="${esc(l.state)}"><b>${esc(l.layer)}</b><code>${esc(l.value)}</code><span class="iv-tag">${esc(IV_STATE[l.state] || l.state)}</span>${l.source ? `<span class="meta">source: ${esc(l.source)}</span>` : ""}</li>`).join("")}</ol></section>`;
  if (v.kind === "walkthrough") return `<section class="iv iv-walk">${head || "<h4>From symptom to fix</h4>"}
    <div class="iv-row"><span class="eyebrow">Symptom</span><p>${md(v.symptom)}</p></div>
    <div class="iv-row"><span class="eyebrow">What we looked at</span><ol>${v.steps.map(s => `<li><b>${md(s.look)}</b> ${md(s.found)}</li>`).join("")}</ol></div>
    ${(v.suspects || []).length ? `<div class="iv-row"><span class="eyebrow">Possible causes</span><ul class="iv-sus">${v.suspects.map(s => `<li class="${/confirm/i.test(s.verdict) ? "yes" : "no"}"><b>${esc(s.cause)}</b> <span class="iv-tag">${esc(s.verdict)}</span> ${md(s.why || "")}</li>`).join("")}</ul></div>` : ""}
    <div class="iv-row"><span class="eyebrow">Root cause</span><p>${md(v.root_cause)}</p></div>
    <div class="iv-row"><span class="eyebrow">Fix</span><p>${md(v.resolution)}</p></div>
    ${v.cannot_verify ? `<div class="iv-row"><span class="eyebrow">Can't verify yet</span><p>${md(v.cannot_verify)}</p></div>` : ""}</section>`;
  if (v.kind === "plan_review") return `<section class="iv iv-plan">${head || "<h4>What the plan would change</h4>"}
    ${v.changes.map(c => `<div class="iv-change ${esc(c.risk)}"><span class="iv-act ${esc(c.action)}">${esc(IV_ACTION[c.action] || c.action)}</span><code>${esc(c.address)}</code><span class="iv-tag">${esc(c.risk)} risk</span>${c.note ? `<p>${md(c.note)}</p>` : ""}</div>`).join("")}
    ${v.decision ? `<div class="iv-row"><span class="eyebrow">Decision</span><p><b>${esc(v.decision)}.</b> ${md(v.reason || "")}</p></div>` : ""}</section>`;
  return "";
}
function artifactHtml(a) {
  if (["relationships", "trace", "walkthrough", "plan_review", "tour"].includes(a.kind)) return viewHtml({ ...a, title: a.label });
  if (a.kind === "diff") return `<figure class="ex"><figcaption>${esc(a.label)}</figcaption><div class="gcode reveal">${codeLines(lineDiff(String(a.before), String(a.after)))}</div></figure>`;
  return `<figure class="ex"><figcaption>${esc(a.label)}</figcaption><pre class="code">${esc(a.content)}</pre></figure>`;
}
function evidenceHtml(ids, all) {
  const list = (all || []).filter(e => !ids || ids.includes(e.id));
  if (!list.length) return "";
  return `<ul class="iv-src">${list.map(e => `<li><span class="iv-tag ${e.status === "verified" ? "ok" : ""}">${e.status === "verified" ? `verified${e.reviewed ? " " + esc(e.reviewed) : ""}` : esc(e.status)}</span><b>${esc(e.title)}</b> <code>${esc(e.ref)}</code>${e.revision ? ` <span class="meta">at ${esc(e.revision)}</span>` : ""}</li>`).join("")}</ul>`;
}
function packLearnPane(L, x) {
  const [first, ...rest] = L.learn;
  const ex = L.example[1] ? [{ caption: L.example[0], code: L.example[1] }, ...(x.examples || [])] : (x.examples || []);
  return `${x.status === "draft" ? `<div class="callout"><b>Draft</b><p>This lesson is still being written. Only previews show it.</p></div>` : ""}
    <p class="intro">${md(first)}</p>
    ${rest.map(p => `<div class="prose"><p>${md(p)}</p></div>`).join("")}
    <div class="keyidea">${ic("target")}<div><b>By the end</b><p>${md(x.objective)}</p></div></div>
    ${(x.concepts || []).length ? `<dl class="gloss">${x.concepts.map(c => `<dt>${esc(c.term)}</dt><dd>${md(c.meaning)}</dd>`).join("")}</dl>` : ""}
    ${ex.map(e => `<figure class="ex"><figcaption>${esc(e.caption)}</figcaption><pre class="code">${esc(e.code)}</pre></figure>`).join("")}
    ${(x.views || []).map(viewHtml).join("")}
    ${x.diagram ? `<figure class="ex"><img class="iv-img" src="${esc(x.diagram)}" alt="Diagram for ${esc(L.title)}"></figure>` : ""}
    ${(x.screenshots || []).map(s => `<figure class="ex"><a href="${esc(s.file)}" target="_blank" rel="noopener"><img class="iv-img" src="${esc(s.file)}" alt="${esc(s.caption || "")}"></a><figcaption>${esc(s.caption || "")}</figcaption></figure>`).join("")}
    ${(x.sources || []).length ? `<section class="sec"><h3>Sources</h3>${evidenceHtml(x.sources, x.evidence)}</section>` : ""}
    ${askPanel()}`;
}
const PX_SHAPE = { multiple_choice: "choice", identify_error: "choice", troubleshooting: "choice", review_decision: "choice",
  source_tracing: "choice", difference_review: "choice", ordering: "ordering", relationship_mapping: "match",
  configuration_repair: "repair", reasoning: "reasoning" };
function practicePane() {
  const id = cur.id, x = packOf(id), p = x.practice, st = pxState(id), shape = PX_SHAPE[p.kind];
  const done = !!progress.solved[id];
  const arts = (p.artifacts || []).map(artifactHtml).join("");
  let body = "";
  if (shape === "choice") {
    const answered = st.picked != null, right = st.picked === p.answer;
    body = `<div class="opts">${p.options.map((o, k) => {
      let cls = "opt"; if (answered && k === p.answer && right) cls += " right"; else if (answered && k === st.picked) cls += " wrong";
      return `<button class="${cls}" data-px-pick="${k}"${answered ? " disabled" : ""}><span class="k">${"ABCDEF"[k]}</span><span>${md(o)}</span></button>`; }).join("")}</div>
      ${answered ? (right ? `<div class="verdict ok">${ic("check")}<div><b>Right.</b> ${md(p.why)}</div></div>`
        : `<div class="verdict no">${ic("x")}<div><b>Not quite.</b> Look again at the evidence above.</div></div><button class="linkbtn" data-px-retry>Try again</button>`) : ""}
      ${answered && right && (p.next_check || p.handoff) ? `<section class="card px-next">${p.next_check ? `<div><span class="eyebrow">Next safe check</span><p>${md(p.next_check)}</p></div>` : ""}${p.handoff ? `<div><span class="eyebrow">What to send to the owner</span><p>${md(p.handoff)}</p></div>` : ""}</section>` : ""}`;
  } else if (shape === "ordering") {
    const pool = pxShuffle(p.steps.map((_, i) => i), id), seq = st.seq || [];
    const left = pool.filter(i => !seq.includes(i)), full = seq.length === p.steps.length;
    const ok = full && seq.every((v, i) => v === i);
    body = `<ol class="px-seq">${seq.map((v, i) => `<li class="${full ? (v === i ? "ok" : "bad") : ""}">${md(p.steps[v])}</li>`).join("") || `<li class="meta">Tap the first step below.</li>`}</ol>
      ${left.length ? `<div class="minis">${left.map(i => `<button class="mini" data-px-step="${i}">${esc(p.steps[i])}</button>`).join("")}</div>` : ""}
      ${full ? (ok ? `<div class="verdict ok">${ic("check")}<div><b>Right order.</b> ${md(p.why)}</div></div>` : `<div class="verdict no">${ic("x")}<div><b>Not quite.</b> The steps marked in red are out of place.</div></div>`) : ""}
      ${seq.length && !ok ? `<button class="linkbtn" data-px-retry>Start again</button>` : ""}`;
  } else if (shape === "match") {
    const targets = pxShuffle([...new Set(p.pairs.map(q => q.to))], id), picks = st.picks || {}, checked = st.checked;
    const ok = checked && p.pairs.every((q, i) => picks[i] === q.to);
    body = `<div class="px-match">${p.pairs.map((q, i) => `<label><code>${esc(q.from)}</code><span>points at</span>
      <select data-px-match="${i}"${ok ? " disabled" : ""}><option value="">Choose…</option>${targets.map(t => `<option${picks[i] === t ? " selected" : ""}>${esc(t)}</option>`).join("")}</select>
      ${checked ? `<span class="iv-tag ${picks[i] === q.to ? "ok" : "bad"}">${picks[i] === q.to ? "right" : "not this one"}</span>` : ""}</label>`).join("")}</div>
      ${ok ? `<div class="verdict ok">${ic("check")}<div><b>All matched.</b> ${md(p.why)}</div></div>` : `<button class="btn" data-px-check>Check my answer</button>`}`;
  } else if (shape === "repair") {
    const text = st.text != null ? st.text : p.broken, results = st.results;
    const ok = results && results.every(r => r.ok);
    body = `<textarea class="px-edit" data-px-text rows="${Math.max(4, String(p.broken).split("\n").length + 1)}" spellcheck="false" aria-label="The configuration to fix">${esc(text)}</textarea>
      ${results ? `<ul class="px-rules">${results.map(r => `<li class="${r.ok ? "ok" : "bad"}">${ic(r.ok ? "check" : "x")}<span>${md(r.why)}</span></li>`).join("")}</ul>` : ""}
      ${ok ? `<div class="verdict ok">${ic("check")}<div><b>Fixed.</b> ${md(p.why)}</div></div>` : `<div class="tools"><button class="btn" data-px-check>Check my fix</button><button class="linkbtn" data-px-reset>Start from the broken version</button></div>`}
      ${st.showFixed || ok ? `<figure class="ex"><figcaption>A fixed version</figcaption><pre class="code">${esc(p.fixed)}</pre></figure>` : `<button class="linkbtn" data-px-show>Show a fixed version</button>`}`;
  } else if (shape === "reasoning") {
    const ans = st.answers || {}, shown = st.shown || {};
    body = p.questions.map((q, i) => `<section class="card px-q"><label for="pxq${i}"><b>${md(q.ask)}</b></label>
      <textarea id="pxq${i}" data-px-answer="${i}" rows="2" placeholder="Your answer">${esc(ans[i] || "")}</textarea>
      ${shown[i] ? `<div class="px-expected"><span class="eyebrow">Expected</span><p>${md(q.expected)}</p><span class="eyebrow">Why</span><p>${md(q.why)}</p></div>`
        : `<button class="linkbtn" data-px-compare="${i}"${words(ans[i]) < 3 ? " disabled" : ""}>Compare with the expected answer</button>`}</section>`).join("")
      + (p.success ? `<div class="keyidea">${ic("target")}<div><b>You're there when</b><p>${md(p.success)}</p></div></div>` : "");
  }
  return `<section class="card px">${done ? `<span class="eyebrow">${ic("check")}Done</span>` : `<span class="eyebrow">Practice</span>`}
    <p class="q">${md(p.prompt)}</p>${arts}${body}</section>`;
}
function pxRedraw() { if (cur && cur.kind === "lesson" && cur.step === 2 && packOf(cur.id)) $("paneText").innerHTML = practicePane(); }
document.addEventListener("click", e => {
  if (!cur || cur.kind !== "lesson" || cur.step !== 2 || !packOf(cur.id)) return;
  const t = e.target, id = cur.id, p = packOf(id).practice, st = pxState(id);
  const pick = t.closest("[data-px-pick]"), step = t.closest("[data-px-step]"), cmp = t.closest("[data-px-compare]");
  if (pick && !pick.disabled) {
    st.picked = +pick.dataset.pxPick; st.tries = (st.tries || 0) + 1; pxSave(id);
    const right = st.picked === p.answer; if (right) pxSolved(id, st.tries);
    pxRedraw(); if (right) fxOn($("paneText").querySelector(".opt.right"), "seal", FX.seal()); return;
  }
  if (step) {
    st.seq = [...(st.seq || []), +step.dataset.pxStep]; pxSave(id);
    if (st.seq.length === p.steps.length) {
      st.tries = (st.tries || 0) + 1; pxSave(id);
      if (st.seq.every((v, i) => v === i)) { pxSolved(id, st.tries); pxRedraw(); fxOn($("paneText").querySelector(".px"), "heal", FX.heal); return; }
    }
    pxRedraw(); return;
  }
  if (t.closest("[data-px-retry]")) { delete st.picked; st.seq = []; pxSave(id); pxRedraw(); return; }
  if (t.closest("[data-px-reset]")) { st.text = p.broken; st.results = null; pxSave(id); pxRedraw(); return; }
  if (t.closest("[data-px-show]")) { st.showFixed = true; pxSave(id); pxRedraw(); return; }
  if (t.closest("[data-px-check]")) {
    st.tries = (st.tries || 0) + 1;
    if (PX_SHAPE[p.kind] === "match") {
      st.checked = true;
      if (p.pairs.every((q, i) => (st.picks || {})[i] === q.to)) pxSolved(id, st.tries);
    } else {
      const text = st.text != null ? st.text : p.broken;
      st.results = p.rules.map(r => ({ ok: "must_contain" in r ? text.includes(r.must_contain) : !text.includes(r.must_not_contain), why: r.why }));
      if (st.results.every(r => r.ok)) pxSolved(id, st.tries);
    }
    pxSave(id); pxRedraw();
    if (progress.solved[id]) fxOn($("paneText").querySelector(".px"), "heal", FX.heal);
    return;
  }
  if (cmp && !cmp.disabled) {
    st.shown = { ...(st.shown || {}), [cmp.dataset.pxCompare]: true }; pxSave(id);
    if (p.questions.every((_, i) => st.shown[i])) pxSolved(id, 1);
    pxRedraw(); fxOn($("paneText").querySelectorAll(".px-q")[+cmp.dataset.pxCompare], "unveil", FX.unveil); return;
  }
});
document.addEventListener("input", e => {
  if (!cur || cur.kind !== "lesson" || !packOf(cur.id)) return;
  const st = pxState(cur.id), t = e.target;
  if (t.matches("[data-px-text]")) { st.text = t.value; st.results = null; pxSave(cur.id); }
  if (t.matches("[data-px-answer]")) {
    st.answers = { ...(st.answers || {}), [t.dataset.pxAnswer]: t.value }; pxSave(cur.id);
    const b = $("paneText").querySelector(`[data-px-compare="${t.dataset.pxAnswer}"]`); if (b) b.disabled = words(t.value) < 3;
  }
});
document.addEventListener("change", e => {
  if (!cur || cur.kind !== "lesson" || !packOf(cur.id) || !e.target.matches("[data-px-match]")) return;
  const st = pxState(cur.id); st.picks = { ...(st.picks || {}), [e.target.dataset.pxMatch]: e.target.value }; st.checked = false; pxSave(cur.id);
});
// A renamed lesson keeps its old id in `aliases`, so progress saved under it carries over.
function migrateAliases() {
  for (const [id, L] of Object.entries(LESSONS)) for (const old of (L.pack && L.pack.aliases) || []) {
    if (progress.lessons[old] && !progress.lessons[id]) progress.lessons[id] = progress.lessons[old];
    if (progress.solved[old] && !progress.solved[id]) progress.solved[id] = progress.solved[old];
  }
}
