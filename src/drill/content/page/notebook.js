// ---------- notebook ----------
let nbTab = "gloss";
function openNotebook(tab) {
  if (tab) nbTab = tab;
  if (!$("nb-" + nbTab)) nbTab = "gloss";  // the study list lives in the pocket now
  for (const t of document.querySelectorAll("[data-nb]")) t.setAttribute("aria-selected", String(t.dataset.nb === nbTab));
  for (const t of document.querySelectorAll("[data-nb]")) $("nb-" + t.dataset.nb).hidden = t.dataset.nb !== nbTab;
  renderResults();
  $("drawer").hidden = false; $("scrim").hidden = false;
  document.body.style.overflow = "hidden";
  $("nbClose").focus();
}
function closeNotebook() { $("drawer").hidden = true; $("scrim").hidden = true; document.body.style.overflow = ""; $("nbBtn").focus(); }
const GROWTH = [
  ["The same work at any size", n => 1, "Looking up a key in a dict"],
  ["Halving each step", n => Math.max(1, Math.log2(n)), "Finding the first failing version by checking the middle"],
  ["One walk through the data", n => n, "Adding up token costs"],
  ["Sorting", n => n * Math.max(1, Math.log2(n)), "Ranking documents by score"],
  ["Checking every pair", n => n * n, "Comparing every chunk with every other chunk"],
  ["Trying every combination", n => Math.pow(2, n), "Testing every possible set of features"],
];
function fmtTime(sec) {
  if (!isFinite(sec) || sec > 4.4e17) return "longer than the universe";
  if (sec < 0.001) return "instant";
  if (sec < 1) return Math.round(sec * 1000) + " ms";
  if (sec < 60) return sec.toFixed(1) + " seconds";
  if (sec < 3600) return Math.round(sec / 60) + " minutes";
  if (sec < 86400) return (sec / 3600).toFixed(1) + " hours";
  if (sec < 86400 * 365) return Math.round(sec / 86400) + " days";
  const y = sec / (86400 * 365);
  return y < 1e6 ? Math.round(y).toLocaleString() + " years" : "millions of years";
}
function renderGrowth() {
  const n = Math.round(Math.pow(10, +$("nRange").value));
  $("nOut").textContent = n.toLocaleString() + " items";
  $("growth").innerHTML = GROWTH.map(([name, f, eg]) => {
    const steps = f(n), sec = steps / 1e7;
    const w = Math.min(100, Math.max(1.5, (Math.log10(Math.max(1, steps)) / 18) * 100));
    const cls = sec > 3600 ? "dead" : sec > 1 ? "slow" : "";
    return `<span><b>${esc(name)}</b><br><span class="meta">${esc(eg)}</span></span><span class="t ${cls === "dead" ? "dead" : ""}">${fmtTime(sec)}</span><span class="track" aria-hidden="true"><span class="fill ${cls}" style="width:${w}%;display:block"></span></span>`;
  }).join("");
}
function renderGlossary() {
  const q = $("glossSearch").value.trim().toLowerCase();
  const html = D.glossary.map(([group, terms]) => {
    const hits = terms.filter(([t, d]) => !q || t.toLowerCase().includes(q) || d.toLowerCase().includes(q));
    if (!hits.length) return "";
    return `<h3>${esc(group)}</h3><dl class="gloss">${hits.map(([t, d]) => `<div><dt>${esc(t)}</dt><dd>${md(d)}</dd>${tagButtons(t, "Glossary")}</div>`).join("")}</dl>`;
  }).join("");
  $("glossBody").innerHTML = html || `<p class="empty">No term matches "${esc(q)}". Try a shorter word.</p>`;
  markSaved();
}
