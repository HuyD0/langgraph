// =====================================================================================================
// What each landmark DOES at its stop, so the picture shows the phase's job, not just the place. Every action
// works on the banner's own drawing (its landmark marks and energy paths) or adds small marks in the banner's
// line language, in a layer of its own (svg.fx). `settle` puts a passed stop in its finished state at once.
// =====================================================================================================
const NS = "http://www.w3.org/2000/svg";
const panelEl = i => document.querySelector(`#wsvg .panel[data-i="${i}"]`);
const fxOf = i => panelEl(i).querySelector("svg.fx");
const later = (ms, fn) => ACT_TIMERS.push({ t: now + ms / 1000, fn });   // on the film clock: Pause freezes it
const ACT_TIMERS = [];
const label = (i, x, y, text, cls = "", anchor = "middle") => { const t = document.createElementNS(NS, "text"); t.setAttribute("class", "lbl " + cls); t.setAttribute("x", x); t.setAttribute("y", y); t.setAttribute("text-anchor", anchor); t.textContent = text; fxOf(i).appendChild(t); return t; };
const bez = (p0, p1, p2, p3, t) => { const u = 1 - t; return [0, 1].map(k => u * u * u * p0[k] + 3 * u * u * t * p1[k] + 3 * u * t * t * p2[k] + t * t * t * p3[k]); };

const ACTS = [
  // Frame: the gate lights as the criteria are agreed (the landmark's own lit state), and nothing else moves
  { start() { fxOf(0).innerHTML = ""; }, run(quick) { const go = () => label(0, 254, 108, "good answer agreed", "lock"); if (quick) go(); else later(300, go); }, settle() { this.start(); this.run(true); } },
  // Design: four seals lock still and glow; one, the thing being changed, stays free and swings
  { start() { panelEl(1).querySelectorAll("svg.base .mk path").forEach((p, k) => { if (k) p.classList.remove("lock", "free"); }); fxOf(1).innerHTML = ""; },
    run(quick) { const tags = [...panelEl(1).querySelectorAll("svg.base .mk path")].slice(1);
      tags.forEach((p, k) => { const go = () => p.classList.add(k === 2 ? "free" : "lock"); if (quick) go(); else later(250 + k * 380, go); });
      const words = () => { label(1, 147, 108, "same", "lock"); label(1, 252, 108, "same", "lock"); label(1, 200, 108, "changes", "free"); };
      if (quick) words(); else later(250 + 5 * 380, words); },
    settle() { this.run(true); } },
  // Build and trace: the steps light up one by one along a stream and stay lit, joined by a thread: the trace
  { start() { fxOf(2).innerHTML = ""; },
    run(quick) { const pts = [.22, .45, .68, .9].map(t => bez([120, 106], [140, 70], [170, 40], [200, 28], t));
      const thread = document.createElementNS(NS, "path");
      thread.setAttribute("class", "thread"); thread.setAttribute("d", "M120 106 C140 70 170 40 200 28"); thread.setAttribute("pathLength", "1");
      fxOf(2).appendChild(thread);
      const NAMES = ["1 read", "2 check old reports", "3 judge", "4 suggest a team"];
      pts.forEach(([x, y], k) => { const c = document.createElementNS(NS, "circle"); c.setAttribute("class", "knot"); c.setAttribute("cx", x.toFixed(1)); c.setAttribute("cy", y.toFixed(1)); c.setAttribute("r", "2.6");
        const go = () => { fxOf(2).appendChild(c); label(2, x - 5, y + 2.5, NAMES[k], "", "end"); }; if (quick) go(); else later(300 + k * 650, go); });
      if (quick) thread.classList.add("on"); else later(300 + 4 * 650, () => thread.classList.add("on")); },
    settle() { this.start(); this.run(true); } },
  // Evaluate: the town's windows are checked one by one under the closed curtain; nearly all pass, one fails
  { start() { fxOf(3).innerHTML = ""; },
    run(quick) { const W8 = [[152, 92], [157.5, 92], [152, 98], [157.5, 98], [164.5, 86], [164.5, 94], [230, 88], [230, 95], [233.5, 101]];
      W8.forEach(([x, y], k) => { const bad = k === W8.length - 1; let r;
        if (bad) { r = document.createElementNS(NS, "path"); r.setAttribute("d", `M${x - .5} ${y - .5} l5 5 M${x + 4.5} ${y - .5} l-5 5`); r.setAttribute("class", "win bad"); }
        else { r = document.createElementNS(NS, "rect"); r.setAttribute("x", x); r.setAttribute("y", y); r.setAttribute("width", "4"); r.setAttribute("height", "4.4"); r.setAttribute("class", "win ok"); }
        const go = () => { fxOf(3).appendChild(r); if (bad) { label(3, 236, 116, "must-pass: failed", "bad"); if (!quick) { const ring = document.createElementNS(NS, "circle"); ring.setAttribute("cx", x + 2); ring.setAttribute("cy", y + 2); ring.setAttribute("r", "6"); ring.setAttribute("class", "ring"); fxOf(3).appendChild(ring); } } };
        if (quick) go(); else later(250 + k * 340 + (bad ? 1200 : 0), go); }); },
    settle() { this.start(); this.run(true); } },
  // Ship: the opening lets one ray out first; the other four follow only after it holds
  { start() { panelEl(4).querySelectorAll("svg.en path.st").forEach((p, k) => p.classList.toggle("held", k !== 2)); fxOf(4).innerHTML = ""; },
    run(quick) { const rays = [...panelEl(4).querySelectorAll("svg.en path.st")];
      const first = () => label(4, 200, 12, "one district first", "free"), rest = () => { label(4, 390, 30, "then the whole city", "lock", "end"); W.lift = 1; };
      if (quick) first(); else later(200, first);
      rays.forEach((p, k) => { if (k === 2) return; const go = () => p.classList.remove("held"); if (quick) go(); else later(3200 + [0, 1, 0, 3, 4][k] * 380, go); });
      if (quick) rest(); else later(4800, rest); },
    settle() { this.run(true); } },
  // Monitor: the lanterns light one by one along the road; one flickers red and feedback is pinned to it
  { start() { panelEl(5).querySelectorAll("svg.en path.fl").forEach(p => { p.classList.add("held"); p.classList.remove("bad"); }); fxOf(5).innerHTML = ""; },
    run(quick) { const fl = [...panelEl(5).querySelectorAll("svg.en path.fl")];
      fl.forEach((p, k) => { const go = () => p.classList.remove("held"); if (quick) go(); else later(250 + k * 600, go); });
      const bad = () => { fl[2].classList.add("bad"); const pin = document.createElementNS(NS, "path"); pin.setAttribute("class", "pin"); pin.setAttribute("d", "M250 64 l-3 -6 h6 z M250 64 v5"); fxOf(5).appendChild(pin); label(5, 250, 52, "wrong answer", "bad"); };
      if (quick) bad(); else later(3200, bad); },
    settle() { this.run(true); } },
];
function resetActs() { ACT_TIMERS.length = 0; ACTS.forEach(a => a.start()); }
