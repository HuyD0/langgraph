// ---------- lesson diagrams ----------
// One picture in the Learn step, drawn from lesson data (content/diagrams.py) in the app's own tokens, so
// it follows the look and fits a phone. Five kinds: flow (boxes and arrows), tree (rows with bars to
// scale), graph (boxes on a grid with labelled arrows), table, chart (lines, bars or dots). Blue marks
// the one thing the lesson is about, amber the callout numbers; the numbers match the list under it.
const DG_W = 340;
const dgNum = v => Number.isFinite(v) ? v.toFixed(1).replace(/\.0$/, "") : "0";
const dgDefs = '<defs><marker id="dgArrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0.5 L7,4 L0,7.5"/></marker></defs>';
const dgCallout = (x, y, n) => n ? `<g class="dg-co"><circle cx="${dgNum(x)}" cy="${dgNum(y)}" r="7"/><text x="${dgNum(x)}" y="${dgNum(y + 3.2)}">${n}</text></g>` : "";
const dgEdge = x => x > DG_W - 40 ? " dg-right" : x < 40 ? " dg-left" : "";  // axis labels near an edge lean inward
const dgText = (cls, x, y, text) => `<text class="${cls}" x="${dgNum(x)}" y="${dgNum(y)}">${esc(String(text))}</text>`;
function dgBox(x, y, w, h, node) {
  const sub = node.sub || node.word;
  return `<g class="dg-bx${node.now ? " now" : ""}"><rect x="${dgNum(x)}" y="${dgNum(y)}" width="${dgNum(w)}" height="${dgNum(h)}" rx="7"/>`
    + dgText("dg-tl", x + w / 2, y + h / 2 + (sub ? -3 : 4), node.label)
    + (sub ? dgText("dg-ts", x + w / 2, y + h / 2 + 10, sub) : "") + dgCallout(x + 2, y + 2, node.n) + "</g>";
}
function dgArrow(x1, y1, x2, y2, label, lx, ly, bend) {
  const d = bend ? `M${dgNum(x1)},${dgNum(y1)} Q${dgNum(bend[0])},${dgNum(bend[1])} ${dgNum(x2)},${dgNum(y2)}` : `M${dgNum(x1)},${dgNum(y1)} L${dgNum(x2)},${dgNum(y2)}`;
  return `<path class="dg-ar" d="${d}" marker-end="url(#dgArrow)"/>` + (label ? dgText("dg-ts", lx, ly, label) : "");
}
const dgSvg = (h, body, label) => `<svg class="dg" viewBox="0 0 ${DG_W} ${h}" role="img" aria-label="${esc(label)}">${dgDefs}${body}</svg>`;

// flow: boxes left to right, one may be opened up with detail rows, the last may split into shares.
function dgFlow(d) {
  const nodes = d.nodes.map((node, i) => d.at == null ? node : { ...node, now: i === d.at, dim: i > d.at }), n = nodes.length, gap = 14, w = Math.min(64, (DG_W - 16 - gap * (n - 1)) / n), top = d.question ? 30 : 12;
  let body = d.question ? dgText("dg-ts dg-left", 8, 16, `Question: “${d.question}”`) : "", h = top + 60;
  const xs = nodes.map((_, i) => 8 + i * (w + gap));
  nodes.forEach((node, i) => {
    body += dgBox(xs[i], top, w, 40, { ...node, sub: null, word: null }).replace('class="dg-bx', `class="dg-bx${node.dim ? " dim" : ""}`) + (node.word ? dgText("dg-ts", xs[i] + w / 2, top + 54, node.word) : "");
    if (i < n - 1) body += dgArrow(xs[i] + w, top + 20, xs[i + 1] - 1, top + 20);
  });
  if (d.detail && (d.at == null || d.at >= d.detail.at)) {  // the lesson's own step, opened up under its box
    const x = xs[d.detail.at], cx = x + w / 2;
    body += `<path class="dg-tree" d="M${dgNum(cx)},${top + 42} L${dgNum(cx)},${top + 62}"/>`;
    const left = Math.max(8, Math.min(cx - 52, DG_W - 118));
    d.detail.rows.forEach(([a, b], k) => { body += dgText("dg-mono dg-left", left, top + 76 + k * 13, a) + (b ? dgText("dg-mono dg-right", left + 110, top + 76 + k * 13, b) : ""); });
    h = top + 76 + d.detail.rows.length * 13 + 4;
  }
  if (d.branches) {  // the last box fans out into shares
    const x0 = xs[n - 1] + w, bw = 112, bx = Math.min(x0 + 40, DG_W - bw - 8), step = 52, y0 = top + 20 - (d.branches.length - 1) * step / 2;
    d.branches.forEach((b, k) => {
      const y = y0 + k * step;
      body += dgArrow(x0, top + 20, bx - 1, y, null, 0, 0, [x0 + 20, y]) + dgText("dg-ts dg-right", bx - 4, y - 10, b.share || "") + dgBox(bx, y - 18, bw, 36, { label: b.label, now: b.now, n: b.n });
    });
    h = Math.max(h, y0 + (d.branches.length - 1) * step + 30);
  }
  return dgSvg(h, body, d.caption);
}
// tree: rows with a bar each, to scale; depth draws the tree lines; a marker is a vertical line with a label.
function dgTree(d) {
  const rows = d.rows, X0 = 112, W = DG_W - X0 - 8, rowH = 26, top = d.marker ? 18 : 8;
  const px = v => X0 + v / d.max * W;
  let body = `<line class="dg-grid" x1="${X0}" y1="${top}" x2="${X0}" y2="${top + rows.length * rowH}"/>`;
  const ticks = d.ticks || [0, d.max / 2, d.max];
  ticks.forEach(t => { body += `<line class="dg-grid" x1="${dgNum(px(t))}" y1="${top}" x2="${dgNum(px(t))}" y2="${top + rows.length * rowH}"/>` + dgText("dg-ts" + dgEdge(px(t)), px(t), top + rows.length * rowH + 12, `${dgNum(t)} ${d.unit}`); });
  rows.forEach((r, i) => {
    const y = top + 6 + i * rowH, depth = r.depth || 0;
    if (depth) body += `<path class="dg-tree" d="M${8 + (depth - 1) * 12 + 4},${y - 12} L${8 + (depth - 1) * 12 + 4},${y + 8} L${8 + depth * 12},${y + 8}"/>`;
    body += dgText(`dg-tl dg-left${(d.at == null ? r.hot : i === d.at) ? " hot" : ""}`, 8 + depth * 12, y + 11, r.name);
    const x = px(r.start || 0), w = Math.max(px(r.size) - X0, 3);
    const hot = d.at == null ? r.hot : i === d.at, grow = d.playing ? ` style="--d:${((r.start || 0) / d.max * 2.4).toFixed(2)}s"` : "";
    body += `<rect class="dg-bar${hot ? " hot" : ""}${r.cut ? " cut" : ""}${d.playing ? " grow" : ""}" x="${dgNum(x)}" y="${y}" width="${dgNum(w)}" height="14" rx="3"${grow}/>`;
    const label = `${r.size} ${d.unit}`, fits = x + w + 48 < DG_W;  // no room to the right: the number sits inside the bar's end
    const num = dgText(`dg-ms ${fits ? "dg-left" : "dg-right in" + (hot ? " on" : "")}`, fits ? x + w + 4 : x + w - 4, y + 11, label);
    body += (d.playing ? num.replace("<text ", `<text style="--d:${(((r.start || 0) + r.size) / d.max * 2.4).toFixed(2)}s" `).replace('class="dg-ms', 'class="dg-ms late') : num)
      + (d.playing ? dgCallout(x + 2, y, r.n).replace('class="dg-co"', `class="dg-co pop" style="--d:${(((r.start || 0) + r.size) / d.max * 2.4).toFixed(2)}s"`) : dgCallout(x + 2, y, r.n));
  });
  if (d.marker) body += `<line class="dg-today" x1="${dgNum(px(d.marker.at))}" y1="${top - 10}" x2="${dgNum(px(d.marker.at))}" y2="${top + rows.length * rowH}"/>` + dgText("dg-ts hot" + dgEdge(px(d.marker.at) + 40), px(d.marker.at), top - 12, d.marker.label);
  return dgSvg(top + rows.length * rowH + 18, body, d.caption);
}
// graph: boxes on a small grid (at: [column, row]) with labelled arrows between their edges.
function dgGraph(d) {
  const cols = Math.max(...d.nodes.map(n => n.at[0])) + 1, rowsN = Math.max(...d.nodes.map(n => n.at[1])) + 1;
  const bw = Math.min(96, (DG_W - 16) / cols - 10), bh = 40, colW = (DG_W - 16 - bw) / Math.max(cols - 1, 1), rowH = 78;
  const pos = {}; d.nodes.forEach(n => { pos[n.id] = { x: 8 + n.at[0] * colW, y: 14 + n.at[1] * rowH }; });
  let body = "";
  d.edges.forEach(e => {
    const a = pos[e.from], b = pos[e.to], ac = { x: a.x + bw / 2, y: a.y + bh / 2 }, bc = { x: b.x + bw / 2, y: b.y + bh / 2 };
    const dx = bc.x - ac.x, dy = bc.y - ac.y;
    // leave each box from the side facing the other box
    const out = Math.abs(dx) >= Math.abs(dy) ? { x: ac.x + Math.sign(dx) * bw / 2, y: ac.y } : { x: ac.x, y: ac.y + Math.sign(dy) * bh / 2 };
    const inn = Math.abs(dx) >= Math.abs(dy) ? { x: bc.x - Math.sign(dx) * bw / 2, y: bc.y } : { x: bc.x, y: bc.y - Math.sign(dy) * bh / 2 };
    const mx = (out.x + inn.x) / 2, my = (out.y + inn.y) / 2, bend = e.bend ? [mx + e.bend * 40, my + e.bend * 40] : null;
    body += dgArrow(out.x, out.y, inn.x, inn.y, e.label, bend ? bend[0] + e.bend * 22 : mx, (bend ? bend[1] : my) - 6, bend);
  });
  d.nodes.forEach(n => { body += dgBox(pos[n.id].x, pos[n.id].y, bw, bh, d.at == null ? n : { ...n, now: n.id === d.at }); });
  return dgSvg(14 + (rowsN - 1) * rowH + bh + 14, body, d.caption);
}
// table: columns and rows; the pill column is drawn as pills; bands shade whole rows.
function dgTable(d) {
  const cols = d.columns.length, widths = d.widths || d.columns.map((_, i) => i === 0 ? .3 : .7 / (cols - 1));
  const xs = widths.reduce((acc, w) => [...acc, acc[acc.length - 1] + w * (DG_W - 16)], [8]);
  let body = "";
  d.columns.forEach((c, i) => { body += dgText("dg-th dg-left", xs[i] + 4, 14, c); });
  body += `<line class="dg-grid" x1="8" y1="20" x2="${DG_W - 8}" y2="20"/>`;
  d.rows.forEach((r, i) => {
    const y = 38 + i * 24;
    if ((d.bands || []).includes(i)) body += `<rect class="dg-band" x="8" y="${y - 15}" width="${DG_W - 16}" height="22" rx="4"/>`;
    r.forEach((cell, j) => {
      if (j === d.pill) {
        if (cell === "") return;
        const w = Math.min(xs[j + 1] - xs[j] - 8, 64);
        body += `<rect class="dg-pill ${esc(cell)}" x="${dgNum(xs[j] + 4)}" y="${y - 12}" width="${dgNum(w)}" height="17" rx="8"/>` + dgText(`dg-pt ${esc(cell)}`, xs[j] + 4 + w / 2, y, cell);
      } else body += dgText(`dg-td dg-left${j === 0 ? " dg-mono" : ""}`, xs[j] + 4, y, cell);
    });
  });
  (d.marks || []).forEach(m => { body += dgCallout(xs[m.col] + 2, 38 + m.row * 24 - 13, m.n); });
  return dgSvg(38 + d.rows.length * 24, body, d.caption);
}
// chart: two axes; lines (dashed for a reference), bars, or dots with quadrant labels; marks carry callouts.
function dgChart(d) {
  const X0 = 44, Y0 = 16, W = DG_W - X0 - 12, H = 110, xmax = d.x.max, ymax = d.y.max, xmin = d.x.min || 0;
  const px = v => X0 + (v - xmin) / (xmax - xmin) * W, py = v => Y0 + H - v / ymax * H, unit = d.y.unit || "";
  let body = "";
  (d.y.ticks || []).forEach(t => { body += `<line class="dg-grid" x1="${X0}" y1="${dgNum(py(t))}" x2="${X0 + W}" y2="${dgNum(py(t))}"/>` + dgText("dg-ts dg-right", X0 - 6, py(t) + 3, `${t}${unit}`); });
  (d.x.ticks || []).forEach(t => { body += dgText("dg-ts" + dgEdge(px(t)), px(t), Y0 + H + 13, `${d.x.label === "day" ? "day " : ""}${t}`); });
  body += `<line class="dg-grid" x1="${X0}" y1="${Y0 + H}" x2="${X0 + W}" y2="${Y0 + H}"/><line class="dg-grid" x1="${X0}" y1="${Y0}" x2="${X0}" y2="${Y0 + H}"/>`;
  if (d.quadrants) {  // a 2 by 2 map: bottom-left, bottom-right, top-left, top-right
    body += `<line class="dg-grid" x1="${dgNum(px(xmax / 2))}" y1="${Y0}" x2="${dgNum(px(xmax / 2))}" y2="${Y0 + H}"/><line class="dg-grid" x1="${X0}" y1="${dgNum(py(ymax / 2))}" x2="${X0 + W}" y2="${dgNum(py(ymax / 2))}"/>`;
    const q = d.quadrants;
    body += dgText("dg-th", px(xmax / 4), py(ymax / 4) + 32, q[0]) + dgText("dg-th", px(3 * xmax / 4), py(ymax / 4) + 32, q[1]) + dgText("dg-th", px(xmax / 4), py(3 * ymax / 4) - 26, q[2]) + dgText("dg-th", px(3 * xmax / 4), py(3 * ymax / 4) - 26, q[3]);
  }
  if (d.bars) {
    const bw = W / d.bars.length * .5;
    d.bars.forEach((v, i) => { const x = px((d.x.ticks || [])[i] ?? i + 1); body += `<rect class="dg-bar hot" x="${dgNum(x - bw / 2)}" y="${dgNum(py(v))}" width="${dgNum(bw)}" height="${dgNum(Y0 + H - py(v))}" rx="3"/>`; });
  }
  if (d.reference) body += `<line class="dg-steady" x1="${X0}" y1="${dgNum(py(d.reference.y))}" x2="${X0 + W}" y2="${dgNum(py(d.reference.y))}"/>` + dgText("dg-ts dg-right", X0 + W, py(d.reference.y) - 4, d.reference.label);
  (d.lines || []).forEach(l => {
    const pts = l.points.map(([x, y]) => `${dgNum(px(x))},${dgNum(py(y))}`).join(" L");
    body += `<path class="${l.dashed ? "dg-steady" : "dg-line"}${l.hot ? " hot" : ""}" d="M${pts}"/>`;
    if (l.label) { const [lx, ly] = l.points[Math.floor(l.points.length / 2)], right = px(lx) > DG_W / 2; body += dgText(`dg-ts ${right ? "dg-right" : "dg-left"}${l.hot ? " hot" : ""}`, px(lx) + (right ? -6 : 6), py(ly) - 4, l.label); }
  });
  (d.points || []).forEach(p => { const right = px(p.x) > DG_W / 2; body += `<circle class="dg-dot${p.now ? " now" : ""}" cx="${dgNum(px(p.x))}" cy="${dgNum(py(p.y))}" r="4"/>` + dgText(`dg-td ${right ? "dg-right" : "dg-left"}`, px(p.x) + (right ? -7 : 7), py(p.y) + 4, p.label) + dgCallout(px(p.x) + (right ? 9 : -9), py(p.y) - 9, p.n); });
  (d.marks || []).forEach(m => { body += `<circle class="dg-dot now" cx="${dgNum(px(m.x))}" cy="${dgNum(py(m.y))}" r="3.5"/>` + dgCallout(px(m.x) + 9, py(m.y) - 9, m.n) + (m.label ? dgText("dg-ts dg-left hot", px(m.x) + 8, py(m.y) + 14, m.label) : ""); });
  body += dgText("dg-ts dg-left", X0, Y0 + H + 28, `${d.y.label} against ${d.x.label}`);
  return dgSvg(Y0 + H + 34, body, d.caption);
}
const DG_DRAW = { flow: dgFlow, tree: dgTree, graph: dgGraph, table: dgTable, chart: dgChart };
const dgPair = d => `<div class="dg-pair"><div class="dg-half"><span class="dg-lbl">${esc(d.before.label)}</span>${DG_DRAW[d.before.kind](d.before)}</div><div class="dg-half"><span class="dg-lbl">${esc(d.fixed.label)}</span>${DG_DRAW[d.fixed.kind](d.fixed)}</div></div>`;
// The picture at one step (k), or at rest (k == null). A playing tree gets its grow classes once.
function dgPicture(d, k, playing) {
  if (d.kind === "pair") return dgPair(d);
  const step = d.steps && k != null ? d.steps[k] : null;
  return DG_DRAW[d.kind]({ ...d, at: step ? step.now : d.at, playing: !!playing });
}
function diagramHtml(d) {
  const list = d.callouts.map((c, i) => `<li><i aria-hidden="true">${i + 1}</i><span>${md(c)}</span></li>`).join("");
  const steps = d.steps ? `<div class="dg-steps"><button type="button" class="btn" data-dg-step="-1">Back</button><button type="button" class="btn primary" data-dg-step="1">Next</button><span class="dg-where">step 1 of ${d.steps.length}</span></div>` : "";
  const replay = d.play ? `<div class="dg-steps"><button type="button" class="linkbtn" data-dg-replay>Replay</button></div>` : "";
  return `<figure class="dgfig" data-dg data-k="${d.steps ? 0 : ""}"><span class="eyebrow">Picture</span><div class="dg-pic">${dgPicture(d, d.steps ? 0 : null, d.play)}</div>
    <figcaption class="dg-say">${md(d.steps ? d.steps[0].say : d.caption)}</figcaption>${steps}${replay}<ol class="dg-notes">${list}</ol></figure>`;
}
function dgRedraw(fig, k, playing) {
  const d = LESSONS[cur.id].diagram; if (!d) return;
  fig.querySelector(".dg-pic").innerHTML = dgPicture(d, k, playing);
  if (d.steps) { fig.dataset.k = k; fig.querySelector(".dg-say").innerHTML = md(d.steps[k].say); fig.querySelector(".dg-where").textContent = `step ${k + 1} of ${d.steps.length}`; }
}
document.addEventListener("click", e => {
  const b = e.target.closest("[data-dg-step], [data-dg-replay]"); if (!b) return;
  const fig = b.closest("[data-dg]"), d = LESSONS[cur.id].diagram; if (!fig || !d) return;
  if (b.dataset.dgReplay != null) { dgRedraw(fig, null, true); return; }
  const k = Math.max(0, Math.min(d.steps.length - 1, Number(fig.dataset.k || 0) + Number(b.dataset.dgStep)));
  dgRedraw(fig, k, false);
});

// ---------- the live picture in Build ----------
// For lessons whose diagram says live, the same kind of picture is drawn from what the learner's function
// returned on the example (the sample case's arguments and the value it gave back), so a wrong answer is
// something you can see, not just a line of red. One drawing per lesson id: (args, returned) -> data.
const dgPills = (cells, cls) => cells;
const LIVE = {
  retrieve: ([query, docs, k], got) => {
    const picks = Array.isArray(got) ? got : [];
    return { kind: "table", columns: ["doc", "your pick"], pill: 1, widths: [.7, .3], rows: docs.map((doc, i) => { const r = picks.indexOf(i); return [doc, r >= 0 ? `${r + 1}${["st", "nd", "rd"][r] || "th"}` : ""]; }),
      say: `For “${query}” with k = ${k}, your function kept ${picks.length} of ${docs.length} documents, in this order.` };
  },
  backoff_delays: ([n, start, cap], got) => ({ kind: "chart", x: { label: "attempt", max: n, ticks: Array.from({ length: n }, (_, i) => i + 1) }, y: { label: "seconds", max: Math.max(cap + 1, ...(Array.isArray(got) ? got : [0])), ticks: [0, cap] },
    bars: Array.isArray(got) ? got : [], reference: { y: cap, label: `the cap of ${cap} seconds` }, say: `Your waits: ${Array.isArray(got) ? got.join(", ") : got} seconds, with a cap of ${cap}.` }),
  assign_splits: ([rows], got) => ({ kind: "table", columns: ["id", "group", "your split"], pill: 2, widths: [.25, .4, .35], rows: rows.map(r => [r.id, r.group, got && typeof got === "object" ? String(got[r.id] ?? "") : ""]),
    say: "Where your function dealt each question." }),
  gather_results: ([workers, timeout], got) => {
    const out = got && typeof got === "object" ? got : {}, timedOut = out.timed_out || [], waited = Number(out.waited) || timeout;
    return { kind: "tree", unit: "s", max: Math.max(timeout + 2, waited + 2), ticks: [0, timeout], rows: [...workers.map(w => ({ name: w.name, start: 0, size: Math.min(w.seconds, timeout), cut: timedOut.includes(w.name) })), { name: "gather", start: waited, size: 1, hot: true }],
      marker: { at: timeout, label: `the ${timeout} second timeout` }, say: `Your gather ran after ${waited} seconds with ${(out.results || []).length} results; timed out: ${timedOut.join(", ") || "none"}.` };
  },
  circuit_breaker: ([calls, threshold, cooldown], got) => ({ kind: "table", columns: ["second", "the call", "your breaker said"], pill: 2, widths: [.25, .3, .45],
    rows: calls.map(([t, ok], i) => [String(t), ok ? "works" : "fails", Array.isArray(got) ? String(got[i] ?? "") : ""]), say: `Limit ${threshold} failures in a row, cooldown ${cooldown} seconds.` }),
  token_bucket: ([times, rate, size], got) => ({ kind: "table", columns: ["request at", "your answer"], pill: 1, widths: [.5, .5],
    rows: times.map((t, i) => [`${t} s`, Array.isArray(got) ? (got[i] ? "allowed" : "wait") : ""]), say: `Refill ${rate} a second, bucket of ${size}.` }),
  skew_report: ([rows, factor], got) => ({ kind: "tree", unit: "rows", max: Math.max(...rows.map(r => r[1])), ticks: [0, Math.max(...rows.map(r => r[1]))],
    rows: rows.map(([key, count]) => ({ name: key, start: 0, size: count, hot: Array.isArray(got) && got.includes(key) })), say: `Keys your function called hot (more than ${factor} times the average) are filled in.` }),
  chunk_text: ([text, size, overlap], got) => {
    const chunks = Array.isArray(got) ? got.map(String) : [], len = Math.max(text.length, 1);
    return { kind: "tree", unit: "characters", max: len * 1.05, ticks: [0, len], rows: [{ name: text, depth: 0, start: 0, size: text.length },
      ...chunks.slice(0, 7).map((c, i) => { const at = text.indexOf(c, i * (size - overlap)); return { name: c, depth: 1, start: at < 0 ? 0 : at, size: c.length, cut: at < 0 }; })],
      say: `Your chunks: ${chunks.join(", ") || "none"}. Each bar sits under the characters it covers; a dashed bar is text that is not in the document.` };
  },
  plan_calls: ([deadline, steps], got) => {
    const ran = Array.isArray(got) ? got : []; let t = 0;
    const rows = steps.map(([name, ms]) => { const runs = ran.includes(name), row = { name, start: t, size: ms, cut: !runs, hot: runs }; if (runs) t += ms; return row; });
    return { kind: "tree", unit: "ms", max: Math.max(deadline, ...rows.map(r => r.start + r.size)) * 1.1, ticks: [0, deadline], rows,
      marker: { at: deadline, label: "deadline" }, say: `Your function ran ${ran.join(", ") || "nothing"}, ${t} ms of the ${deadline} ms deadline. Dashed bars are steps it skipped.` };
  },
};
function livePic(p, got, passed) {
  const draw = LIVE[p.id]; if (!draw) return;
  const c = p.cases[sampleIndex(p)];
  let d; try { d = draw(c.args, got); } catch { return; }
  $("livepic").hidden = false;
  $("livepic").innerHTML = `<h3>What your function did</h3><div class="dg-pic">${DG_DRAW[d.kind](d)}</div>
    <p class="dg-say">${esc(d.say)} ${passed ? "That matches the expected answer." : "Compare it with the expected answer above."}</p>`;
}
