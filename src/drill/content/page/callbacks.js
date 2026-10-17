// ---------- sticker callbacks ----------
// Where a lesson uses an idea taught earlier (content/callbacks.py), the sticker the learner earned in
// that lesson sits right after the phrase. Tapping it opens a card under the paragraph: the idea, what
// it means here, and a way back. A sticker not yet earned is an outline, and the card offers the lesson.
// After Learn, one Look again question may use that idea: a wrong pick shows the clue, then the answer
// is one tap away. It is practice only: the result card and the Check step never read it.
const cbSeen = new Set((() => { try { return JSON.parse(store.get("drill-cb-seen") || "[]"); } catch { return []; } })());
const CB_PIN = i => String.fromCharCode(0xE010 + i);  // each callback's spot in the raw text, like TRUST_PIN
const cbOf = id => LESSONS[id].callbacks || [];
const cbRoute = to => trackOf[to] ? " tr" : "";
function cbMarkHtml(id, i) {
  const [to, , idea] = cbOf(id)[i], earned = isDoneL(to), fresh = earned && !cbSeen.has(id + ">" + to);
  return `<button class="cbmark${cbRoute(to)}${earned ? "" : " ahead"}${fresh ? " fresh" : ""}" data-cb="${i}" aria-expanded="false" aria-controls="cbPop${i}" aria-label="Seen before: ${esc(idea)}, from lesson ${esc(lessonNo(to))}">`
    + `${stickerSvg(to, earned ? "done" : "ahead", 20)}</button>`;
}
function cbPopHtml(id, i) {
  const [to, , idea, here] = cbOf(id)[i], earned = isDoneL(to), no = lessonNo(to);
  return `<div class="trustpop cbpop${cbRoute(to)}${earned ? "" : " ahead"}" id="cbPop${i}" hidden>
    <span class="cbbig">${stickerSvg(to, earned ? "done" : "ahead", 20)}</span>
    <div class="cbbody"><div class="tk"><span>${earned ? `Your ${esc(no)} sticker` : "Not yet earned"}</span><span>${esc(LESSONS[to].title)}</span></div>
    <p class="tv">${esc(idea)}</p>
    <p class="tt">${earned ? "" : `You haven't done ${esc(no)} yet, so its sticker is still an outline. `}${esc(here)}</p>
    <button class="linkbtn cbgo" data-open="${esc(to)}">${earned ? `Revisit ${esc(no)}` : `Do ${esc(no)} now`} <span aria-hidden="true">→</span></button></div></div>`;
}
let cbOpen = null;
function closeCb() {
  const b = cbOpen; if (!b) return;
  cbOpen = null; b.setAttribute("aria-expanded", "false");
  const p = document.getElementById(b.getAttribute("aria-controls")); if (p) { p.hidden = true; p.classList.remove("opening"); }
}
function openCb(b) {
  closeCb(); closeTrust();
  const p = document.getElementById(b.getAttribute("aria-controls")); if (!p) return;
  p.hidden = false; growPop(b, p);
  b.setAttribute("aria-expanded", "true"); b.classList.remove("fresh"); cbOpen = b;
  const link = cbOf(cur.id)[Number(b.dataset.cb)];
  if (link && !cbSeen.has(cur.id + ">" + link[0])) { cbSeen.add(cur.id + ">" + link[0]); store.set("drill-cb-seen", JSON.stringify([...cbSeen])); }
}

// The Look again card: one question through the earlier idea, after Learn. lp(id).again keeps the
// wrong picks, whether the clue or the answer was asked for, and whether it was answered right.
function againHtml(id) {
  const A = LESSONS[id].again; if (!A) return "";
  const [to, q, opts, ans, why, clue] = A, st = lp(id).again || {}, wrong = st.wrong || [];
  const done = !!(st.right || st.shown), own = !!st.right && !wrong.length && !st.clue && !st.shown;
  const earned = isDoneL(to), no = lessonNo(to), order = checkOrder(id + ":again", opts.length);
  const buttons = order.map((k, n) => {
    const cls = done && k === ans ? " yes" : wrong.includes(k) ? " no" : "";
    return `<button class="againopt${cls}" data-again="${k}"${done || wrong.includes(k) ? " disabled" : ""}><b aria-hidden="true">${"ABCDEF"[n]}</b>${esc(opts[k])}</button>`;
  }).join("");
  const help = done
    ? `<p class="note againwhy" tabindex="-1"><b>${own ? "On your own" : st.shown ? "The answer" : "Right"}</b>${esc(why)}</p>`
      + (own ? `<p class="againseen">Your ${esc(no)} sticker: seen again in ${esc(lessonNo(id))}</p>` : "")
    : wrong.length || st.clue
      ? `<p class="note hint againclue" tabindex="-1"><b>Clue</b>${esc(clue)}</p><button class="linkbtn" data-again-show>Show me the answer</button>`
      : `<button class="linkbtn" data-again-clue>Give me a clue</button>`;
  return `<section class="card again${cbRoute(to)}${own ? " own" : ""}" id="againCard" aria-labelledby="againQ">
    <span class="againstk${earned ? "" : " ahead"}">${stickerSvg(to, earned ? "done" : "ahead", 20)}</span>
    <span class="eyebrow">Look again · from ${esc(no)}</span>
    <p class="againq" id="againQ">${esc(q)}</p>
    <div class="againopts" role="group" aria-labelledby="againQ">${buttons}</div>
    ${help}</section>`;
}
function againStep(change) {
  const A = LESSONS[cur.id].again; if (!A) return;
  const s = lp(cur.id), st = s.again || (s.again = { wrong: [] });
  st.wrong = st.wrong || [];
  if (st.right || st.shown) return;
  change(st, A);
  saveProgress();
  const c = $("againCard"); if (!c) return;
  c.outerHTML = againHtml(cur.id);
  $("againCard").querySelector(".againwhy, .againclue")?.focus();
}
document.addEventListener("click", e => {
  const b = e.target.closest("[data-cb]");
  if (b) { b === cbOpen ? closeCb() : openCb(b); return; }
  if (cbOpen && !e.target.closest(".cbpop")) closeCb();
  const pick = e.target.closest("[data-again]");
  if (pick) {
    const k = Number(pick.dataset.again);
    againStep((st, A) => { if (!Number.isInteger(k) || k < 0 || k >= A[2].length) return; if (k === A[3]) st.right = true; else if (!st.wrong.includes(k)) st.wrong.push(k); });
    return;
  }
  if (e.target.closest("[data-again-clue]")) { againStep(st => { st.clue = true; }); return; }
  if (e.target.closest("[data-again-show]")) againStep(st => { st.shown = true; });
});
document.addEventListener("keydown", e => { if (e.key === "Escape" && cbOpen) { const b = cbOpen; closeCb(); b.focus(); } });
