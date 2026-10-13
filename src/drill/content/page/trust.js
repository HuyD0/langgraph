// ---------- trust marks ----------
// An ember right after the words in a lesson where responsible AI, privacy or governance comes up
// (content/trust.py). Tapping it opens a tooltip: why it matters for trust, and one tip. A mark you
// haven't opened gives off embers; once opened (remembered on this device) it rests.
const TRAITS = D.traits, TRAIT_KEYS = Object.keys(TRAITS);
const trustSeen = new Set((() => { try { return JSON.parse(store.get("drill-trust-seen") || "[]"); } catch { return []; } })());
const TRUST_PIN = "\uE000";  // marks the spot in the raw text; md() leaves it alone
function trustPractised() {
  const on = new Set();
  for (const [id, L] of Object.entries(LESSONS)) if (L.trust && isDoneL(id)) on.add(L.trust[0]);
  return on;
}
function trustMarkHtml(id) {
  const [trait] = LESSONS[id].trust, fresh = !trustSeen.has(id);
  const embers = fresh ? [["-5px", "0s"], ["4px", ".9s"], ["-1px", "1.7s"]].map(([x, d]) => `<i class="em" style="--x:${x};--d:${d}"></i>`).join("") : "";
  const burst = [0, 45, 90, 135, 180, 225, 270, 315].map(a => `<i class="bu" style="--a:${a}deg"></i>`).join("");
  return `<button class="trustmark ${fresh ? "arrive" : "seen"}" data-trust aria-expanded="false" aria-controls="trustPop" aria-label="Why this matters for trustworthy AI: ${esc(TRAITS[trait])}">`
    + `<svg viewBox="0 0 18 18" aria-hidden="true"><g class="turn"><circle cx="9" cy="9" r="7.6" stroke-width="1" stroke-dasharray="1.2 1.7"/></g><path d="M9 3.6 L13.7 11.7 L4.3 11.7 Z" stroke-width=".8" opacity=".75"/><circle class="core" cx="9" cy="9" r="1.7"/></svg>`
    + `<i class="ring"></i>${embers}${burst}</button>`;
}
function trustPopHtml(id) {
  const [trait, , view, tip, rmf, tevv] = LESSONS[id].trust, on = trustPractised();
  const dots = TRAIT_KEYS.map(k => `<i class="${on.has(k) ? "on" : ""}" title="${esc(TRAITS[k])}"></i>`).join("");
  return `<div class="trustpop" id="trustPop" hidden>
    <div class="tk"><span>${esc(TRAITS[trait])}${tevv ? `<abbr class="tevv" title="Test, evaluation, verification and validation: evidence that it works">TEVV</abbr>` : ""}</span><span>NIST AI RMF · ${esc(rmf)}</span></div>
    <p class="tv">${esc(view)}</p>
    <p class="tt"><b>Tip</b>${esc(tip)}</p>
    <div class="tr" aria-label="${on.size} of 7 trustworthy AI traits practised">${dots}<span>${on.size} of 7 trust traits practised</span></div></div>`;
}
// One paragraph of Learn text, with the lesson's trust mark after its phrase if this is the paragraph.
function withTrust(id, text, wrap) {
  const T = LESSONS[id].trust;
  if (!T || !text.includes(T[1])) return wrap(md(text));
  return `<div class="trusthost">${wrap(md(text.replace(T[1], T[1] + TRUST_PIN)).replace(TRUST_PIN, trustMarkHtml(id)))}${trustPopHtml(id)}</div>`;
}
let trustOpen = null;
function closeTrust() {
  const b = trustOpen; if (!b) return;
  trustOpen = null; b.setAttribute("aria-expanded", "false");
  const p = b.closest(".trusthost")?.querySelector(".trustpop"); if (p) { p.hidden = true; p.classList.remove("opening"); }
}
function openTrust(b) {
  closeTrust();
  const p = b.closest(".trusthost").querySelector(".trustpop");
  p.hidden = false;
  const a = b.getBoundingClientRect(), r = p.getBoundingClientRect();
  const ox = a.left - r.left + a.width / 2, oy = a.top - r.top + a.height / 2;  // the circle grows from the mark to the far corner
  p.style.setProperty("--ox", ox + "px"); p.style.setProperty("--oy", oy + "px");
  p.style.setProperty("--or", Math.ceil(Math.hypot(Math.max(ox, r.width - ox), Math.max(oy, r.height - oy))) + 2 + "px");
  p.classList.remove("opening"); void p.offsetWidth; p.classList.add("opening");
  b.setAttribute("aria-expanded", "true"); trustOpen = b;
  b.classList.remove("arrive", "fire"); void b.offsetWidth; b.classList.add("fire", "seen");
  b.querySelectorAll(".em").forEach(e => e.remove());
  if (cur && !trustSeen.has(cur.id)) { trustSeen.add(cur.id); store.set("drill-trust-seen", JSON.stringify([...trustSeen])); }
}
document.addEventListener("click", e => {
  const b = e.target.closest("[data-trust]");
  if (b) { b === trustOpen ? closeTrust() : openTrust(b); return; }
  if (trustOpen && !e.target.closest(".trustpop")) closeTrust();
});
document.addEventListener("keydown", e => { if (e.key === "Escape" && trustOpen) { const b = trustOpen; closeTrust(); b.focus(); } });
