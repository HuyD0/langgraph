// ---------- spot the gotcha: one challenge per lesson, in its Explain step ----------
// Each card in extras.py names its lesson. You see the risky code, pick the rule it breaks,
// then watch it turn into the fix. Habits about how you work show in the Build step instead.
const GOTCHAS = {}, HABITS = {};
for (const set of [D.aiGotchas, D.iacGotchas, D.rules]) set.forEach(([title, why, bad, good, where], i) => {
  if (where.startsWith("build:")) { HABITS[where.slice(6)] = { title, why }; return; }
  const others = set.filter(c => c[0] !== title).map(c => c[0]);
  const options = [others[(i * 5 + 1) % others.length], others[(i * 5 + 4) % others.length]];
  const answer = i % 3; options.splice(answer, 0, title);
  GOTCHAS[where] = { title, why, bad, good, options, answer };
});
const N_GOTCHAS = Object.keys(GOTCHAS).length;
let gotchaView = "diff";
function lineDiff(a, b) {  // the lines of a and b, marked " " kept, "-" removed or "+" added
  const A = a.split("\n"), B = b.split("\n"), n = A.length, m = B.length;
  const L = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) L[i][j] = A[i] === B[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
  const out = []; let i = 0, j = 0;
  while (i < n && j < m) {
    if (A[i] === B[j]) { out.push([" ", A[i]]); i++; j++; }
    else if (L[i + 1][j] >= L[i][j + 1]) out.push(["-", A[i++]]);
    else out.push(["+", B[j++]]);
  }
  while (i < n) out.push(["-", A[i++]]);
  while (j < m) out.push(["+", B[j++]]);
  return out;
}
function codeLines(rows) {
  let k = 0;
  return rows.map(([t, line]) => {
    const cls = t === "-" ? " del" : t === "+" ? " add" : "", sr = t === "-" ? '<span class="sr">removed: </span>' : t === "+" ? '<span class="sr">added: </span>' : "";
    return `<div class="gln${cls}" style="--i:${t === " " ? 0 : k++}"><span class="gm" aria-hidden="true">${t === "-" ? "−" : t}</span>${sr}${esc(line) || " "}</div>`;
  }).join("");
}
function gotchaCard(anim) {
  const g = cur && GOTCHAS[cur.id]; if (!g) return "";
  anim = anim || {};
  const picked = progress.gotchas[cur.id], answered = picked != null, right = picked === g.answer;
  const spotted = Object.keys(GOTCHAS).filter(id => progress.gotchas[id] === GOTCHAS[id].answer).length;
  const opts = g.options.map((o, k) => {
    let cls = "opt";
    if (answered && k === g.answer) cls += " right"; else if (answered && k === picked) cls += " wrong";
    return `<button class="${cls}" data-gotcha="${k}"${answered ? " disabled" : ""}><span class="k">${"ABC"[k]}</span><span>${esc(o)}</span></button>`;
  }).join("");
  const rows = !answered ? g.bad.split("\n").map(l => [" ", l]) : gotchaView === "after" ? g.good.split("\n").map(l => [" ", l]) : lineDiff(g.bad, g.good);
  const verdict = !answered ? "" : right
    ? `<div class="verdict ok">${ic("check")}<div><b>Spotted it.</b> ${md(g.why)}</div></div>`
    : `<div class="verdict no">${ic("x")}<div><b>Not quite: it breaks "${esc(g.title)}".</b> ${md(g.why)}</div></div>`;
  return `<section class="card gotcha-card" id="gotchaCard">
    <div class="gc-head"><h3>Spot the gotcha</h3><span class="gc-badge"><span class="gc-icon${right ? " done" : ""}${anim.squash ? " squash" : ""}" aria-hidden="true">${ic("bug", "bug")}${ic("check", "ok")}</span>${spotted} of ${N_GOTCHAS} spotted</span></div>
    <p class="q">${!answered ? "This passes the tests on your laptop. Which rule does it break?" : gotchaView === "after" ? "The fixed version:" : "What changed to fix it:"}</p>
    ${answered ? `<div class="seg" role="group" aria-label="Show"><button data-gview="diff" aria-pressed="${gotchaView !== "after"}">What changed</button><button data-gview="after" aria-pressed="${gotchaView === "after"}">Fixed code</button></div>` : ""}
    <div class="gcode${anim.reveal ? " reveal" : ""}">${codeLines(rows)}</div>
    <div class="opts">${opts}</div>
    <div aria-live="polite">${verdict}</div>
    ${answered ? `<div class="tools"><button class="linkbtn" data-gotcha-retry>Try again</button>${right ? "" : `<button class="linkbtn" data-gotcha-save>Save it to my study list</button>`}</div>` : ""}
  </section>`;
}
function renderGotcha(anim) { const el = $("gotchaCard"); if (el) el.outerHTML = gotchaCard(anim); }
function answerGotcha(k) {
  const g = GOTCHAS[cur.id]; if (!g) return;
  progress.gotchas[cur.id] = k; gotchaView = "diff"; saveProgress();
  renderGotcha({ reveal: true, squash: k === g.answer });
  if (k === g.answer) fxScreen("smoke", FX.smoke, document.querySelector("#gotchaCard .gc-icon"));
}
async function saveGotcha() {
  const g = GOTCHAS[cur.id]; if (!g) return;
  const it = await addItem(g.title, "Gotcha · " + LESSONS[cur.id].title, "text");
  if (!it.explanation) await updateItem(it.id, { explanation: g.why + "\n\nBefore:\n```\n" + g.bad + "\n```\n\nAfter:\n```\n" + g.good + "\n```" });
  toast("Saved to your study list");
}
function habitLine(kind) {  // a working habit, shown in the Build step at the moment it applies
  const h = HABITS[kind]; if (!h) return "";
  const text = kind === "pass" ? "It works. Now compare it with the target above: is there a simpler or faster way?" : h.why;
  return `<div class="habit"><b>Habit: ${esc(h.title.charAt(0).toLowerCase() + h.title.slice(1))}.</b> ${md(text)}</div>`;
}
