// ---------- picture cards: a lesson's Learn step as short cards, one idea and one picture each (content/model.py card) ----------
// Each picture is data, drawn here in the app's own look, so it fits a phone and follows the theme.
// Two looks tell two kinds of thing apart by shape, never by a new colour: "solid" (a filled tile) and
// "dashed" (a ruler-edged tile). Card text goes through withTrust, so a trust mark or a sticker
// callback lands in a card just as it does in a paragraph.
const pcIc = n => n ? ic(n) : "";
const pcTile = t => `<div class="pc-tile ${t.look}">${pcIc(t.icon)}<span>${md(t.text)}</span></div>`;
const pcStruck = s => `<s><span class="pc-vh">Crossed out: </span>${esc(s)}</s>`;
const PC_PIC = {
  piles: p => `<div class="pc-piles">${p.piles.map(c => `<div class="pc-pile"><div class="pc-ph"><b>${esc(c.title)}</b>${c.sub ? `<span>${esc(c.sub)}</span>` : ""}</div>${c.items.map(pcTile).join("")}</div>`).join("")}</div>
    ${p.key.length ? `<div class="pc-key">${p.key.map(([look, label]) => `<span><i class="${look}" aria-hidden="true"></i>${esc(label)}</span>`).join("")}</div>` : ""}`,
  // the same plain question asked of each row; the answer says why it lands where it does
  sortby: p => `<p class="pc-ask">${md(p.question)}</p>` + p.rows.map(r => `<div class="pc-row"><b class="pc-thing">${esc(r.text)}</b><p class="pc-then">${ic(r.icon)}<span>${md(r.then)}</span></p><span class="pc-verdict ${r.look}">${esc(r.verdict)}</span></div>`).join(""),
  crossout: p => p.rows.map(r => `<div class="pc-row">${pcStruck(r.text)}<p class="pc-then">${ic(r.icon)}<span>${md(r.then)}</span></p><span class="pc-verdict ${r.look}">${esc(r.verdict)}</span></div>`).join(""),
  split: p => `<div class="pc-strip">${p.parts.map((s, i) => `${i ? `<span class="pc-cut" aria-label="cut here">${ic("scissors")}</span>` : ""}<span class="pc-part">${esc(s)}</span>`).join("")}</div>
    <div class="pc-into">${p.into.map(pcTile).join("")}</div>`,
  rewrite: p => `<div class="pc-rewrite">${p.pairs.map(([a, b]) => `${pcStruck(a)}${ic("arrowr")}<span>${md(b)}</span>`).join("")}</div>`,
  // the roof is the thing held up; each pillar shows its icon, whatever rests on it, and its name written
  // up the column like lettering on stone (the list underneath gives the full name). A pillar nothing answers yet is dashed, in hint colours, with a question mark
  pillars: p => `<div class="pc-temple" role="group" aria-label="${esc(p.roof)}" style="--n:${p.pillars.length}">
      <div class="pc-roofbox"><svg class="pc-roof" viewBox="0 0 100 24" preserveAspectRatio="none" aria-hidden="true"><polygon points="1,23 50,1 99,23"/></svg><b>${esc(p.roof)}</b></div>
      <i class="pc-beam" aria-hidden="true"></i>
      <div class="pc-cols">${p.pillars.map(c => `<div class="pc-col${c.open ? " open" : ""}">${ic(c.icon)}${c.chips.map(x => `<span class="pc-chip">${esc(x)}</span>`).join("")}${c.open ? `<span class="pc-q" aria-label="nothing yet">?</span>` : ""}<span class="pc-pn">${esc(c.short)}</span></div>`).join("")}</div>
      <i class="pc-beam" aria-hidden="true"></i>
    </div>
    ${(() => { const qs = p.pillars.filter(c => p.list || c.open); return qs.length ? `<ul class="pc-qs">${qs.map(c => `<li class="${c.open ? "open" : ""}">${ic(c.icon)}<span><b class="pc-qn">${esc(c.name)}${c.open && !p.list ? ": nothing yet" : ""}</b>${md(c.question)}</span></li>`).join("")}</ul>` : ""; })()}`,
  // a trade-off: one side rises, the other pays. The plank tips towards the side that pays
  seesaw: p => `<div class="pc-saw"><div class="pc-plank">${[["up", p.up], ["down", p.down]].map(([k, [t, s]]) => `<div class="pc-pan ${k}"><b>${esc(t)}</b><span>${esc(s)}</span></div>`).join("")}</div>
    <svg class="pc-pivot" viewBox="0 0 40 30" aria-hidden="true"><polygon points="20,2 38,28 2,28"/></svg></div><p class="pc-cap">${md(p.caption)}</p>`,
  steps: p => `<ol class="pc-steps${p.decide ? " decide" : ""}">${p.items.map(([icon, t, x]) => `<li><span class="pc-dot">${ic(icon)}</span><div><b>${esc(t)}</b><span>${md(x)}</span></div></li>`).join("")}</ol>`,
};
function cardsLearnPane(L) {
  closeTrust(); closeCb();
  const id = cur.id, n = L.cards.length;
  return `<ol class="pcards">${L.cards.map((c, i) => `<li class="card pcard">
      <span class="pc-step">${i + 1} of ${n}</span><h3>${esc(c.heading)}</h3>
      ${withTrust(id, c.text, h => `<p>${h}</p>`)}
      ${c.picture ? `<figure class="pc-fig" data-kind="${c.picture.kind}">${PC_PIC[c.picture.kind](c.picture)}</figure>` : ""}
      ${c.after ? withTrust(id, c.after, h => `<p class="pc-after">${h}</p>`) : ""}
      ${c.note ? `<details class="pc-note"><summary>${ic("bulb")}${esc(c.note[0])}</summary>${withTrust(id, c.note[1], h => `<p>${h}</p>`)}</details>` : ""}
    </li>`).join("")}</ol>
    ${L.walk ? walkHtml(L.walk) : ""}
    ${L.stack ? `<section class="stack"><h3>In your stack</h3><span class="meta">${esc(L.stack[0])}</span><pre class="code">${esc(L.stack[1])}</pre></section>` : ""}
    ${againHtml(id)}
    ${checkedNote(L)}
    ${askPanel()}`;
}
