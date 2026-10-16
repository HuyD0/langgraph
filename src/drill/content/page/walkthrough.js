// ---------- walkthrough: a tool's screens, redrawn with numbered callouts (content/model.py screen) ----------
// Each screen is data, drawn here in the app's own look so it fits a phone and follows the theme.
// A part with "n" gets a numbered badge and a hint-coloured outline; the steps below explain them in order.
const slT = o => o == null ? "" : typeof o === "string" ? o : o.text;
let SL_ACT = 0;  // the step being explained: only its part gets the badge and the outline
const slN = n => n && n === SL_ACT ? `<i class="sl-n" aria-hidden="true">${n}</i>` : "";
const slMark = (o, inner) => !(o && typeof o === "object" && o.n) ? inner
  : o.n === SL_ACT ? `<span class="sl-mark" data-walk-n="${o.n}">${slN(o.n)}${inner}</span>` : `<span class="sl-tgt" data-walk-n="${o.n}">${inner}</span>`;
function slLog(lines, runId) {
  let lastN = null;
  return lines.map(l => {
    const hit = l.n && l.n === SL_ACT, badge = hit && l.n !== lastN ? slN(l.n) : ""; lastN = hit ? l.n : null;
    const text = l.code ? `<span class="sl-code">${esc(l.text)}</span>` : `${runId ? `<span class="sl-id">[${esc(runId.slice(0, 6))}…]</span> ` : ""}<span${l.warn ? ' class="sl-warn"' : ""}>${esc(l.text)}</span>`;
    return `<div class="sl-line${hit ? " sl-hit" : ""}"${l.n ? ` data-walk-n="${l.n}"` : ""}>${badge}${text}</div>`;
  }).join("");
}
const SL_VIEW = {
  flow: d => `<ol class="sl-flow">${d.boxes.map((b, i) => `<li class="${b.n && b.n === SL_ACT ? "sl-hitbox" : ""}">${slN(b.n)}<span class="sl-step">${i + 1}</span><b>${esc(b.title)}</b><span>${esc(b.sub)}</span></li>`).join("")}</ol><p class="sl-note">${esc(d.note)}</p>`,
  header: d => `<div class="sl-h1">${slMark(d.title, `<b>${esc(slT(d.title))}</b>`)}${slMark(d.state, `<span class="sl-pill">✓ ${esc(slT(d.state))}</span>`)}</div>
    <div class="sl-meta">${slMark(d.path, `<span class="sl-link">${esc(slT(d.path))}</span>`)}${(d.meta || []).map(m => `<span>${esc(m)}</span>`).join("")}${slMark(d.commit, `<span class="sl-link sl-mono">⊸ ${esc(slT(d.commit))}</span>`)}</div>
    <div class="sl-meta"><span>${esc(d.started)}</span></div>
    <div class="sl-meta">${(d.line2 || []).map(m => `<span>${esc(m)}</span>`).join("")}${slMark(d.run_type, `<span>ⓘ ${esc(slT(d.run_type))}</span>`)}</div>
    <div class="sl-tabs">${d.tabs.map((t, i) => slMark(t, `<span class="sl-tab${i === 0 ? " on" : ""}">${esc(t.text)}${t.count ? ` <em>${esc(t.count)}</em>` : ""}</span>`)).join("")}</div>`,
  changes: d => `<div class="sl-cols"><aside class="sl-side">${slMark(d.filters, `<div class="sl-filt"><div class="sl-ftabs"><b>Filters</b><span>Views</span></div><div class="sl-frow"><span>Default view</span><span class="sl-btn">New view</span></div><div class="sl-frow sl-muted">⤢ Expand all</div>${d.filters.items.map(f => `<div class="sl-fitem">› ${esc(f)}</div>`).join("")}</div>`)}</aside>
    <div class="sl-mainc"><div class="sl-bar sl-top"><span class="sl-toggle"><i></i> New diff view</span>${slMark(d.count, `<span class="sl-showing">${esc(slT(d.count))}</span>`)}<span class="sl-search">⌕ ${esc(d.search)}</span></div>
    <div class="sl-bar sl-sub">${slMark(d.expand, `<span>⤢ ${esc(slT(d.expand))}</span>`)}<span class="sl-sort">Sort by: <b>Address ↓</b></span></div>
    <div class="sl-rows">${d.rows.map(r => `<div class="sl-row${r.n && r.n === SL_ACT ? " sl-hitbox" : ""}"${r.n ? ` data-walk-n="${r.n}"` : ""}>${slN(r.n)}<span class="sl-chev">›</span><span class="sl-sym">${esc(r.sym)}</span><span class="sl-mono sl-addr">${esc(r.address)}</span><span class="sl-pill sl-planned">${esc(r.status)}</span></div>`).join("")}${d.more ? `<div class="sl-muted sl-more">${esc(d.more)}</div>` : ""}</div></div></div>`,
  log: d => `<div class="sl-bar"><span><b>▾ ${esc(d.phase)}</b> <span class="sl-muted">• ${esc(d.duration)} • ${esc(d.at)}</span></span>${slMark(d.tools, `<span class="sl-chips">${d.tools.items.map(t => `<span>${esc(t)}</span>`).join("")}</span>`)}</div>
    <div class="sl-log"><div class="sl-code">${(d.tail || []).map(l => esc(l)).join("\n")}</div>
    <div class="sl-line${d.summary.n === SL_ACT ? " sl-hit" : ""}" data-walk-n="${d.summary.n}">${slN(d.summary.n)}<b>${esc(slT(d.summary))}</b></div>${slLog(d.lines, d.run_id)}</div>`,
  diff: d => `<div class="sl-log sl-code">${d.blocks.map(b => `<div class="sl-block${b.n && b.n === SL_ACT ? " sl-hitbox" : ""}"${b.n ? ` data-walk-n="${b.n}"` : ""}>${slN(b.n)}<span class="sl-add">+ access_control {
    + group_name       = "${esc(b.group)}"
    + permission_level = "${esc(b.level)}"${b.hidden ? `\n      <span class="sl-muted">${esc(b.hidden)}</span>` : ""}
  }</span></div>`).join("")}<div class="sl-block${d.hidden.n === SL_ACT ? " sl-hitbox" : ""}" data-walk-n="${d.hidden.n}">${slN(d.hidden.n)}<span class="sl-muted">${esc(slT(d.hidden))}</span></div></div>`,
  history: d => `<div class="sl-h1">${slMark(d.title, `<b>${esc(slT(d.title))}</b>`)}<span class="sl-pill">✓ ${esc(d.state)}</span></div>
    <div class="sl-meta">${slMark(d.path, `<span class="sl-link">${esc(slT(d.path))}</span>`)}${slMark(d.context, `<span>☰ ${esc(slT(d.context))}</span>`)}<span>ⓘ ${esc(d.run_type)}</span></div>
    <div class="sl-tabs"><span class="sl-tab on">History</span><span class="sl-tab">Changes <em>${esc(d.changes)}</em></span></div>
    <div class="sl-hist">${d.events.map(e => `<div class="sl-ev${e.n && e.n === SL_ACT ? " sl-hitbox" : ""}"${e.n ? ` data-walk-n="${e.n}"` : ""}>${slN(e.n)}<span class="sl-dot">✓</span><b>${esc(e.state)}</b><span class="sl-muted">${esc(e.at)}</span>${e.buttons.map(b => `<span class="sl-btn">${esc(b)}</span>`).join("")}</div>`).join("")}
    <div class="sl-bar"><span><b>▾ ${esc(d.phase)}</b> <span class="sl-muted">· ${esc(d.duration)} · ${esc(d.at)}</span></span></div>
    <div class="sl-log">${slLog(d.lines, "01M464E91G7W09T58V7GQFYN0D")}</div></div>`,
};
// One step at a time: the screen with only the current part outlined, the step's words right
// under it, and Back and Next. All the steps, and the good habits, fold away below.
const WALK = {};
function walkFig(w, k) {
  const n = w.steps.length, at = WALK[k] || 1;
  SL_ACT = at;
  const view = SL_VIEW[w.kind](w.data).replace(/data-walk-n="(\d+)"/g, (m, n) => `${m} title="${esc(String(w.steps[n - 1] || "").replace(/[*`]/g, ""))}"`);
  SL_ACT = 0;
  return `<figure class="sl" data-walk="${k}">
    <figcaption>${esc(w.caption)}</figcaption>
    <div class="sl-view sl-${w.kind}" role="img" aria-label="${esc(w.caption)}: step ${at} of ${n} highlighted">${w.kind === "flow" ? "" : `<div class="sl-chrome"><i aria-hidden="true"></i><i aria-hidden="true"></i><i aria-hidden="true"></i><span>Spacelift · example screen</span></div>`}<div class="sl-body">${view}</div></div>
    <div class="sl-now" aria-live="polite"><span class="sl-count">Step ${at} of ${n}</span><p>${slNfixed(at)}<span>${md(w.steps[at - 1])}</span></p>
      <div class="sl-nav"><button class="btn quiet" data-walk-go="-1"${at === 1 ? " disabled" : ""}>${ic("arrowl")}Back</button><button class="btn" data-walk-go="1"${at === n ? " disabled" : ""}>Next${ic("arrowr")}</button></div></div>
    <details class="sl-more"><summary>All ${n} steps</summary><ol class="sl-steps">${w.steps.map((t, i) => `<li>${slNfixed(i + 1)}<span>${md(t)}</span></li>`).join("")}</ol></details>
    ${w.tips && w.tips.length ? `<details class="sl-more sl-tips"><summary>${ic("bulb")}Good habits (${w.tips.length})</summary><ul>${w.tips.map(t => `<li>${md(t)}</li>`).join("")}</ul></details>` : ""}
  </figure>`;
}
const slNfixed = n => `<i class="sl-n" aria-hidden="true">${n}</i>`;
function walkHtml(walk) {
  return `<section class="walk"><h3>Walkthrough</h3>${walk.map((w, k) => walkFig(w, k)).join("")}</section>`;
}
function walkTo(fig, n) {
  const k = +fig.dataset.walk, w = LESSONS[cur.id].walk[k];
  WALK[k] = Math.min(w.steps.length, Math.max(1, n));
  fig.outerHTML = walkFig(w, k);
  // the new part's outline draws in and its number pops; the step's words follow. Motion is for everyone (the owner's choice, 2026-10-15).
  const now = document.querySelector(`[data-walk="${k}"]`);
  now.querySelectorAll(".sl-view .sl-mark, .sl-view .sl-hitbox, .sl-view .sl-hit").forEach(el => fxMove(el, [{ transform: "scale(1.04)", opacity: .3 }, { transform: "none", opacity: 1 }], "--dur-step"));
  now.querySelectorAll(".sl-view .sl-n").forEach(el => fxMove(el, [{ transform: "scale(0)" }, { transform: "scale(1.2)" }, { transform: "none" }], "--dur-step"));
  const words = now.querySelector(".sl-now p"); if (words) fxMove(words, [{ opacity: 0, transform: "translateY(6px)" }, { opacity: 1, transform: "none" }], "--dur-step");
}
document.addEventListener("click", e => {
  const b = e.target.closest("[data-walk-go]");
  if (b && !b.disabled) { const fig = b.closest("[data-walk]"); walkTo(fig, (WALK[+fig.dataset.walk] || 1) + +b.dataset.walkGo); return; }
  const t = e.target.closest(".sl-view [data-walk-n]");
  if (t) walkTo(t.closest("[data-walk]"), +t.dataset.walkN);
});
