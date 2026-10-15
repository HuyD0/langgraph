// ---------- your result: the card on the done screen, and the picture it shares ----------
// The first time through a lesson, each step leaves marks: "sign" on your own, "knot" with a clue
// or another go, "curtain" the answer was shown. null means the step was skipped. Later goes
// don't change them, so the result you share is the first one, like a daily puzzle's.
const MARKS = ["sign", "knot", "curtain"];
const MARK_WORDS = { sign: "on your own", knot: "with a clue or another go", curtain: "answer shown" };
// Copied text can't carry drawings, so each symbol has an emoji twin.
const SHARE_MARKS = { sign: "✌️", knot: "🪢", curtain: "🌫️", spark: "⚡", gate: "⛩️", beads: "📿" };
const firstOf = id => { const s = lp(id); return s.first || (s.first = {}); };
function firstMarks(id, step, marks) { const f = firstOf(id); if (f[step] === undefined) f[step] = marks; }
function firstGap(id, mark) { const f = firstOf(id); if (f.explain === undefined) (f.gaps = f.gaps || []).push(mark); }
// At Finish: skipped steps, the Explain gaps, the day, the streak and the module join the result.
// A step done before this existed has no marks, and then there is no card (it would be a guess).
function finishMarks(id) {
  const s = lp(id), f = firstOf(id), n = gapsOf(id).length;
  if (f.check === undefined && s.checked === null) f.check = null;
  else if (f.check === undefined && s.checks) { const m = (s.checks.marks || []).filter(Boolean); f.check = m.length ? m : null; }  // stopped part way: the ones answered
  if (f.build === undefined && !progress.solved[id]) f.build = null;
  if (f.explain === undefined) {
    const gaps = f.gaps || [];
    if (n && clozeDone(id) && gaps.length >= n) f.explain = gaps.slice(0, n);
    else if (words(s.said) >= SAY_WORDS) f.explain = ["sign"];
  }
  if (f.explain !== undefined) delete f.gaps;
  if (f.day === undefined) { f.day = progress.days.length; f.streak = streak(); f.gate = MOD[modOf[id].id].lessons.every(isDoneL); }
}
function resultOf(id) {
  const f = (progress.lessons[id] || {}).first;
  if (!f || f.check === undefined || f.build === undefined || f.explain === undefined || !f.day) return null;
  const names = packOf(id) ? ["Check", "Practice", "Explain"] : ["Check", "Build", "Explain"];
  const rows = [f.check, f.build, f.explain].map((m, i) => [names[i], m]);
  const spark = rows.every(([, m]) => m && m.length && m.every(x => x === "sign"));
  return { id, no: lessonNo(id), day: f.day, rows, spark, gate: !!f.gate, streak: f.streak || 0 };
}
function shareText(r) {
  return [`Daily Drill ${r.no} · Day ${r.day}${r.spark ? " " + SHARE_MARKS.spark : ""}${r.gate ? " " + SHARE_MARKS.gate : ""}`,
    ...r.rows.map(([n, m]) => `${n} ${m ? m.map(x => SHARE_MARKS[x]).join("") : "skipped"}`),
    r.streak > 1 ? `${SHARE_MARKS.beads} ${r.streak}-day streak` : ""].filter(Boolean).join("\n");
}
function resultWords(r) {  // what a screen reader says instead of the pictures
  const row = ([n, m]) => {
    if (!m) return `${n}: skipped.`;
    if (m.length === 1) return `${n}: ${MARK_WORDS[m[0]]}.`;
    return `${n}: ` + MARKS.map(k => [k, m.filter(x => x === k).length]).filter(([, c]) => c).map(([k, c]) => `${c} of ${m.length} ${MARK_WORDS[k]}`).join(", ") + ".";
  };
  return `Lesson ${r.no}, day ${r.day}. ` + r.rows.map(row).join(" ") + (r.spark ? " Every step on your own." : "") + (r.gate ? " Module finished." : "") + (r.streak > 1 ? ` ${r.streak}-day streak.` : "");
}
const markTile = m => `<span class="rmark ${m}">${ic(m)}</span>`;
// Cracks run out from the spark's corner on a flawless finish (the card's own box, stretched).
const RES_CRACKS = `<svg class="rescracks" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">${[
  "88,10 78,16 72,27 60,30 54,42", "88,10 96,20 97,33 100,38", "88,10 85,2", "72,27 58,22 48,25", "97,33 90,45 89,60", "54,42 42,45 36,55 22,57"]
  .map(p => `<polyline pathLength="1" points="${p}"/>`).join("")}</svg>`;
function resultHtml(r) {
  const rows = r.rows.map(([n, m]) => `<div class="resrow"><span>${n}</span>${m ? `<span class="marks">${m.map(markTile).join("")}</span>` : `<span class="resskip">Skipped</span>`}</div>`).join("");
  return `<section class="card result" data-result>
    ${r.spark ? RES_CRACKS : ""}
    <div class="resbadges" aria-hidden="true">${r.gate ? `<span class="resgate" title="Module finished">${ic("gate")}</span>` : ""}${r.spark ? markTile("spark") : ""}</div>
    <span class="eyebrow">Your result · Day ${r.day}</span>
    <p class="sr">${esc(resultWords(r))}</p>
    <div class="resrows" aria-hidden="true">${rows}</div>
    ${r.streak > 1 ? `<p class="resweek" aria-hidden="true">${r.streak}-day streak</p>` : ""}
    <p class="reskey" aria-hidden="true">${MARKS.map(m => `<span>${markTile(m)}${MARK_WORDS[m]}</span>`).join("")}${r.spark ? `<span>${markTile("spark")}every step on your own</span>` : ""}</p>
    <div class="resshare"><button class="btn" data-share-pic>${ic("share")}<span>Share result</span></button><button class="linkbtn" data-share-text>${ic("copy")}Copy as text</button></div>
    <div class="resmore" data-res-more hidden></div>
  </section>`;
}
// The picture: the same card drawn on a canvas in the current look's colours (read from the
// tokens), so it pastes into chat looking like the app. Made as the done screen opens, so sharing
// can start straight from the tap: browsers only allow it inside the tap itself.
const RES = { id: null, png: null, blob: null, url: null };
function prepareResult(r) {
  if (RES.url) URL.revokeObjectURL(RES.url);
  Object.assign(RES, { id: r.id, png: resultPng(r), blob: null, url: null });
  RES.png.then(b => { if (RES.id === r.id) RES.blob = b; }).catch(() => {});
}
function iconImage(name, color, css) {
  const sym = document.getElementById("i-" + name);
  const inner = sym.innerHTML.replace(/var\((--[\w-]+)\)/g, (_, n) => css.getPropertyValue(n).trim());
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${sym.getAttribute("viewBox")}" width="64" height="64" fill="none" stroke="${color}" color="${color}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">${inner}</svg>`;
  const img = new Image(); img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
  return img.decode().then(() => img);
}
async function resultPng(r) {
  await document.fonts.ready;
  const css = getComputedStyle(document.documentElement), v = n => css.getPropertyValue(n).trim();
  const c = { bg: v("--bg"), card: v("--surface"), line: v("--line"), fg: v("--fg"), muted: v("--muted"), sunk: v("--sunk"),
    sign: v("--pass"), knot: v("--hint"), curtain: v("--muted"), spark: v("--fx-red"), veil: v("--fx-veil"), finish: v("--finish") || v("--pass") };
  const font = (w, size, fam) => `${w} ${size}px ${v(fam)}`;
  const icons = {};
  for (const n of ["sign", "knot", "curtain", "spark", "gate"]) icons[n] = await iconImage(n, n === "gate" ? c.finish : c[n], css);
  const S = 2, W = 360, P = 16, X = P + 18, TX = X + 76, TW = 30, TH = 36, STEP = 26;
  const per = Math.max(1, Math.floor((W - P - 18 - TX - TW) / STEP) + 1);
  const lines = r.rows.map(([, m]) => m ? Math.ceil(m.length / per) || 1 : 1);
  const H = P + 54 + lines.reduce((a, n) => a + n * (TH + 4) + 8, 0) + (r.streak > 1 ? 26 : 0) + 30 + P;
  const cv = document.createElement("canvas"); cv.width = W * S; cv.height = H * S;
  const g = cv.getContext("2d"); g.scale(S, S);
  const rgba = (col, a) => { g.fillStyle = col; const h = g.fillStyle; if (!h.startsWith("#")) return h; const n = parseInt(h.slice(1), 16); return `rgba(${n >> 16},${n >> 8 & 255},${n & 255},${a})`; };
  const round = (x, y, w, h, rad) => { g.beginPath(); if (g.roundRect) g.roundRect(x, y, w, h, rad); else g.rect(x, y, w, h); };
  g.fillStyle = c.bg; g.fillRect(0, 0, W, H);
  round(P, P, W - P * 2, H - P * 2, 16); g.fillStyle = c.card; g.fill(); g.strokeStyle = c.line; g.lineWidth = 1; g.stroke();
  g.save(); round(P, P, W - P * 2, H - P * 2, 16); g.clip();
  g.fillStyle = c.finish; g.fillRect(P + 16, P, W - P * 2 - 32, 2);
  if (r.spark) {  // the cracks, from the spark's corner
    g.strokeStyle = rgba(c.spark, .7); g.lineWidth = 1.2; g.lineCap = g.lineJoin = "round";
    const bx = P, by = P, bw = W - P * 2, bh = H - P * 2;
    for (const p of RES_CRACKS.match(/points="([^"]+)"/g).map(s => s.slice(8, -1))) {
      g.beginPath(); p.split(" ").forEach((xy, i) => { const [x, y] = xy.split(",").map(Number); g[i ? "lineTo" : "moveTo"](bx + x / 100 * bw, by + y / 100 * bh); }); g.stroke();
    }
  }
  g.restore();
  const tile = (x, y, w, h, m) => {
    const col = c[m], path = () => { g.beginPath(); g.moveTo(x + w * .18, y); g.lineTo(x + w, y); g.lineTo(x + w * .82, y + h); g.lineTo(x, y + h); g.closePath(); };
    g.save(); path(); g.clip();
    g.fillStyle = m === "spark" ? c.veil : c.sunk; g.fillRect(x, y, w, h);
    const grad = m === "spark" ? g.createRadialGradient(x + w / 2, y + h * .45, 0, x + w / 2, y + h * .45, w * .7) : g.createLinearGradient(x, y, x + w * .6, y + h);
    grad.addColorStop(0, rgba(col, m === "spark" ? .4 : .26)); grad.addColorStop(m === "spark" ? 1 : .7, rgba(col, 0));
    g.fillStyle = grad; g.fillRect(x, y, w, h);
    g.fillStyle = col; g.fillRect(x, y + h - 3, w, 3);
    g.restore();
    const s = Math.min(w, h) * .64; g.drawImage(icons[m], x + (w - s) / 2, y + (h - s) / 2 - 1, s, s);
  };
  let y = P + 30;
  g.textBaseline = "middle"; g.fillStyle = c.finish; g.font = font(600, 11, "--mono");
  if ("letterSpacing" in g) g.letterSpacing = "0.8px";
  g.fillText(`DAILY DRILL ${r.no} · DAY ${r.day}`.toUpperCase(), X, y);
  if ("letterSpacing" in g) g.letterSpacing = "0px";
  let bxr = W - P - 16;  // badges, from the right
  if (r.spark) { tile(bxr - 40, P + 12, 40, 48, "spark"); bxr -= 48; }
  if (r.gate) {
    g.save(); g.translate(bxr - 19, P + 34); g.rotate(-10 * Math.PI / 180);
    g.beginPath(); g.arc(0, 0, 19, 0, Math.PI * 2); g.strokeStyle = c.finish; g.lineWidth = 1.5; g.stroke();
    g.drawImage(icons.gate, -11, -11, 22, 22); g.restore();
  }
  y = P + 54;
  r.rows.forEach(([n, m], i) => {
    g.fillStyle = c.muted; g.font = font(400, 13, "--body"); g.fillText(n, X, y + TH / 2);
    if (!m) g.fillText("Skipped", TX, y + TH / 2);
    else m.forEach((mk, k) => tile(TX + (k % per) * STEP, y + Math.floor(k / per) * (TH + 4), TW, TH, mk));
    y += lines[i] * (TH + 4) + 8;
  });
  if (r.streak > 1) { g.fillStyle = c.muted; g.font = font(400, 13, "--body"); g.fillText(`${r.streak}-day streak`, X, y + 8); y += 26; }
  // the key, so whoever you send it to can read it
  g.font = font(400, 11, "--body"); let kx = X;
  for (const [m, w] of [["sign", "on your own"], ["knot", "a clue"], ["curtain", "answer shown"]]) {
    tile(kx, y, 14, 17, m); g.fillStyle = c.muted; g.fillText(w, kx + 19, y + 9); kx += 19 + g.measureText(w).width + 14;
  }
  return new Promise((ok, no) => cv.toBlob(b => b ? ok(b) : no(new Error("no picture")), "image/png"));
}
function resultMore(html) { const box = document.querySelector("[data-res-more]"); if (box) { box.innerHTML = html; box.hidden = false; } return box; }
const sharedOk = (msg, btn) => { toast(msg); fxOn(btn, "seal", FX.seal()); };
// Share result: on a phone, the share sheet with the picture; elsewhere, the picture on the
// clipboard. If neither is allowed (a plain-http address, a sandboxed frame), the picture shows
// below, to save or copy by hand.
function sharePicture(btn) {
  const r = resultOf(cur.id); if (!r || RES.id !== r.id) return;
  const name = `daily-drill-${r.no}.png`, fallback = () => RES.png.then(b => {
    RES.url = RES.url || URL.createObjectURL(b);
    resultMore(`<img src="${RES.url}" alt="${esc(resultWords(r))}"><p class="meta">Press and hold the picture (or right-click it) to copy or save it.</p><a class="linkbtn" href="${RES.url}" download="${name}">${ic("arrowr")}Save the picture</a>`);
  }).catch(() => toast("The picture didn't work here. Try Copy as text."));
  if (coarse.matches && RES.blob && navigator.canShare) {
    const file = new File([RES.blob], name, { type: "image/png" });
    if (navigator.canShare({ files: [file] })) {
      navigator.share({ files: [file], text: shareText(r) }).catch(e => { if (!e || e.name !== "AbortError") fallback(); });
      return;
    }
  }
  try {
    navigator.clipboard.write([new ClipboardItem({ "image/png": RES.png })]).then(() => sharedOk("Picture copied. Paste it anywhere.", btn), fallback);
  } catch { fallback(); }
}
function shareTextNow(btn) {
  const r = resultOf(cur.id); if (!r) return;
  const text = shareText(r), fallback = () => {
    const box = resultMore(`<textarea readonly rows="${text.split("\n").length}" aria-label="Your result as text">${esc(text)}</textarea><p class="meta">${coarse.matches ? "Press and hold the text to copy it." : "Press Ctrl+C (or ⌘C) to copy it."}</p>`);
    const ta = box && box.querySelector("textarea"); if (ta) { ta.focus(); ta.select(); }
  };
  try { navigator.clipboard.writeText(text).then(() => sharedOk("Copied. Paste it anywhere.", btn), fallback); } catch { fallback(); }
}
