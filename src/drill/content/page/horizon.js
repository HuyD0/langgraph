// ---------- the phase banner
// A strip of original line art at the top of Home's phase room: a horizon that reshapes for each phase
// (gate, seals, barrier, curtain, opening, lanterns), a layer of blue-flame energy, and a cursed spirit
// that gets weaker as you finish the phase's lessons: eyes close, it shrinks and cracks, and the last
// lesson exorcises it. Decorative only (aria-hidden); tapping it strikes the spirit for fun.
// Neutral names; every colour is a token.
const HZ = [
  { sun: [70, 74], night: 0, veil: 0, open: 0, a: [92, 84, 80, 86, 90, 84, 82, 88, 92], b: [106, 102, 100, 104, 106, 102, 100, 104, 106], mark: "gate" },
  { sun: [150, 22], night: 0, veil: 0, open: 0, a: [90, 72, 80, 70, 86, 78, 84, 80, 88], b: [104, 98, 102, 96, 104, 100, 102, 98, 104], mark: "seals" },
  { sun: [310, 26], night: 0, veil: .35, open: 0, a: [88, 80, 70, 58, 66, 76, 82, 86, 90], b: [106, 100, 96, 92, 96, 100, 104, 104, 106], mark: "ward" },
  { sun: [90, 30], night: .7, veil: 1, open: 0, a: [84, 74, 82, 92, 92, 92, 80, 72, 82], b: [102, 98, 102, 108, 108, 108, 100, 96, 102], mark: "town" },
  { sun: [330, 80], night: .3, veil: .5, open: 1, a: [80, 76, 84, 96, 100, 100, 100, 100, 100], b: [100, 98, 104, 110, 112, 112, 112, 112, 112], mark: "rays" },
  { sun: [320, 34], night: 1, veil: 0, open: 0, a: [88, 82, 86, 80, 84, 90, 76, 70, 84], b: [104, 100, 104, 100, 102, 106, 98, 96, 104], mark: "lanterns" },
];
const HZ_XS = [0, 50, 100, 150, 200, 250, 300, 350, 400];
const hzSmooth = ys => { const p = HZ_XS.map((x, i) => [x, ys[i]]); let d = `M${p[0][0]},${p[0][1]}`;
  for (let i = 0; i < p.length - 1; i++) { const p0 = p[i - 1] || p[i], p1 = p[i], p2 = p[i + 1], p3 = p[i + 2] || p2;
    d += ` C${(p1[0] + (p2[0] - p0[0]) / 6).toFixed(1)},${(p1[1] + (p2[1] - p0[1]) / 6).toFixed(1)} ${(p2[0] - (p3[0] - p1[0]) / 6).toFixed(1)},${(p2[1] - (p3[1] - p1[1]) / 6).toFixed(1)} ${p2[0]},${p2[1]}`; }
  return d; };
const hzFlame = (x, y, k = 1) => `<path class="ac" d="M${x},${y} c${-5*k},${-6*k} ${-2*k},${-12*k} ${1*k},${-17*k} c${0},${6*k} ${6*k},${7*k} ${4*k},${13*k} c${-1*k},${3*k} ${-3*k},${4*k} ${-5*k},${4*k}z" opacity=".85"/>`;
const HZ_MARKS = {
  gate: `<path class="ln" d="M238 96 v-30 M270 96 v-30 M228 68 q26 -6 52 0 M232 75 h44" stroke-width="1.7"/><path class="ln" d="M310 90 l8 -10 h22 l8 10 M316 90 v8 h28 v-8" opacity=".75"/>`,
  seals: `<path class="ln" d="M90 98 v-50 M310 98 v-50 M90 52 Q200 76 310 52" stroke-width="1.6"/>` + [130, 165, 200, 235, 270].map((x, i) => { const y = 52 + 24 * (1 - Math.pow((x - 200) / 110, 2)) * .9; return `<path class="ln" d="M${x} ${y.toFixed(1)} v7 l-4 5 h8 l-4 5 v6" stroke-width="1"/>`; }).join(""),
  ward: ``,
  town: `<path class="ln" d="M150 104 v-14 h12 v-8 h10 v22 M180 104 v-18 l8 -6 8 6 v18 M204 104 v-12 h16 v12 M228 104 v-20 h10 v20" opacity=".9"/>`,
  rays: [-60, -35, -10, 15, 40].map(a => { const r = a * Math.PI / 180, x1 = 200 + 70 * Math.sin(r), y1 = 100 - 70 * Math.cos(r), x2 = 200 + 104 * Math.sin(r), y2 = 100 - 104 * Math.cos(r); return `<path class="ln" d="M${x1.toFixed(1)} ${y1.toFixed(1)} L${x2.toFixed(1)} ${y2.toFixed(1)}" stroke-dasharray="4 4"/>`; }).join("") + hzFlame(200, 30, .8),
  lanterns: [70, 150, 250, 340].map(x => `<path class="ln" d="M${x} 100 v-16 M${x - 5} 84 h10 v-10 h-10z" stroke-width="1"/>` + hzFlame(x, 80, .45)).join(""),
};
const hzEmb = (pts) => pts.map(([x, y], i) => `<circle class="em" cx="${x}" cy="${y}" r="1.6" style="--d:${(i * .37 % 2.4).toFixed(2)}s"/>`).join("");
const HZ_ENERGY = [
  // Frame: the first traces of it, rising off the gate
  `<path class="st" d="M246 96 C240 80 252 70 246 56"/><path class="st" d="M262 96 C268 82 258 72 264 58"/>` + hzEmb([[250, 60], [262, 70], [244, 74]]),
  // Design: it runs along the rope and down each seal
  `<path class="st" d="M90 52 Q200 76 310 52"/><path class="st hi" d="M90 52 Q200 76 310 52"/>` + hzEmb([[130, 70], [200, 80], [270, 70]]),
  // Build: streams gather from the ground to the top of the barrier
  `<path class="st" d="M120 106 C140 70 170 40 200 28"/><path class="st" d="M280 106 C260 70 230 40 200 28"/><path class="st" d="M200 108 V30"/><path class="st hi" d="M150 106 C160 80 185 50 200 30"/>` + hzEmb([[200, 30], [180, 44], [220, 44]]),
  // Evaluate: it circles inside the closed curtain
  `<path class="st" d="M146 98 A54 54 0 0 1 254 98"/><path class="st" d="M254 98 A54 54 0 0 0 146 98" style="animation-direction:reverse" opacity=".5"/><path class="st hi" d="M166 98 A34 34 0 0 1 234 98"/><path class="st" d="M184 98 A16 16 0 0 1 216 98" style="animation-direction:reverse"/>` + hzEmb([[190, 74], [212, 66], [200, 86]]),
  // Ship: it bursts out along the opening
  [-60, -35, -10, 15, 40].map(a => { const r = a * Math.PI / 180; return `<path class="st" d="M${(200 + 60 * Math.sin(r)).toFixed(1)} ${(100 - 60 * Math.cos(r)).toFixed(1)} L${(200 + 112 * Math.sin(r)).toFixed(1)} ${(100 - 112 * Math.cos(r)).toFixed(1)}"/>`; }).join("") + hzEmb([[150, 40], [200, 16], [250, 40], [120, 60], [282, 62]]),
  // Monitor: it settles into the lanterns' flames, a few embers drifting up
  [70, 150, 250, 340].map(x => `<path class="fl" d="M${x},80 c-3,-4 -1,-8 1,-11 c0,4 4,5 3,8 c-1,2 -2,3 -4,3z"/>`).join("") + hzEmb([[70, 66], [150, 62], [250, 66], [340, 60]]),
];
// the cursed spirit: an original grotesque in the genre's style (lopsided body, scattered mismatched eyes,
// a wide toothed grin, long thin clawed arms, ink hatching). `hp` from 1 (whole) to 0 (exorcised) shrinks it,
// closes eyes and cracks it: in the app, hp would be the share of the phase's lessons still to do.
const hzSpirit = (cx, base, sc, hp) => {
  const S = v => (v * sc).toFixed(1), X = v => (cx + v * sc).toFixed(1), Y = v => (base + v * sc).toFixed(1);
  const body = `<path class="body" d="M${X(-30)},${Y(0)} C${X(-38)},${Y(-22)} ${X(-30)},${Y(-50)} ${X(-12)},${Y(-58)} C${X(0)},${Y(-66)} ${X(18)},${Y(-62)} ${X(26)},${Y(-48)} C${X(36)},${Y(-34)} ${X(34)},${Y(-12)} ${X(28)},${Y(0)} C${X(18)},${Y(-6)} ${X(8)},${Y(3)} ${X(-2)},${Y(-3)} C${X(-12)},${Y(3)} ${X(-22)},${Y(-6)} ${X(-30)},${Y(0)}Z"/>`;
  const arms = `<path class="limb" d="M${X(-28)},${Y(-30)} C${X(-46)},${Y(-30)} ${X(-54)},${Y(-12)} ${X(-60)},${Y(0)} M${X(-60)},${Y(0)} l${S(-5)},${S(3)} M${X(-60)},${Y(0)} l${S(-2)},${S(5)} M${X(-60)},${Y(0)} l${S(3)},${S(5)} M${X(27)},${Y(-36)} C${X(46)},${Y(-44)} ${X(56)},${Y(-24)} ${X(62)},${Y(-6)} M${X(62)},${Y(-6)} l${S(5)},${S(2)} M${X(62)},${Y(-6)} l${S(2)},${S(6)} M${X(62)},${Y(-6)} l${S(-3)},${S(5)}"/>`;
  const hatch = Array.from({ length: 7 }, (_, k) => `<path class="hatch" d="M${X(-24 + k * 6)},${Y(-6)} l${S(-6)},${S(-12)}"/>`).join("");
  const mouth = `<path class="mouth" d="M${X(-16)},${Y(-22)} Q${X(0)},${Y(-10)} ${X(18)},${Y(-24)} Q${X(2)},${Y(-16)} ${X(-16)},${Y(-22)}Z"/><path class="teeth" d="M${X(-12)},${Y(-20)} l${S(2)},${S(3)} l${S(2)},${S(-3)} l${S(2)},${S(4)} l${S(2)},${S(-4)} l${S(2)},${S(4)} l${S(2)},${S(-4)} l${S(2)},${S(4)} l${S(2)},${S(-4)} l${S(2)},${S(3)} l${S(2)},${S(-3)} l${S(2)},${S(3)}"/>`;
  const EYES = [[-10, -42, 5], [8, -48, 3], [18, -36, 2.4], [-20, -32, 2.2], [0, -54, 2], [24, -50, 1.6], [-4, -34, 1.8], [12, -30, 1.4], [-26, -44, 1.5]];
  const open = Math.max(1, Math.round(EYES.length * hp));
  const eyes = EYES.map(([x, y, r], k) => k < open
    ? `<circle class="eyew" cx="${X(x)}" cy="${Y(y)}" r="${S(r)}"/><circle class="eye" cx="${X(x + r * .2)}" cy="${Y(y)}" r="${S(r * .45)}" style="--d:${(k * .41).toFixed(2)}s"/>`
    : `<path class="limb" d="M${X(x - r)},${Y(y)} h${S(r * 2)}"/>`).join("");
  const cracks = hp < .8 ? `<path class="crack" d="M${X(-6)},${Y(-60)} l${S(4)},${S(10)} ${S(-5)},${S(8)} ${S(6)},${S(10)}"/>` : "";
  const cracks2 = hp < .45 ? `<path class="crack" d="M${X(22)},${Y(-52)} l${S(-6)},${S(9)} ${S(5)},${S(6)} ${S(-7)},${S(12)}"/><path class="crack" d="M${X(-28)},${Y(-20)} l${S(8)},${S(-4)} ${S(4)},${S(6)}"/>` : "";
  return `<g class="wob">${arms}${body}${hatch}${mouth}${eyes}${cracks}${cracks2}</g><circle class="hit" cx="${cx}" cy="${Y(-30)}" r="${S(34)}" style="fill:var(--fx-core)"/>`;
};
const hzShards = (cx, cy) => Array.from({ length: 10 }, (_, i) => `<path class="bit" d="M${cx - 12 + (i % 5) * 6},${cy + Math.floor(i / 5) * 12} l5,-4 4,6 -7,3z" style="--d:${(i * .18).toFixed(2)}s;--x:${(i % 3 - 1) * 16}px"/>`).join("");
const HZ_STARS = [[40, 20], [96, 34], [150, 16], [210, 30], [262, 14], [390, 24], [120, 52]];
function hzScene(svg, from, to, t) {
  const L = (a, b) => a + (b - a) * t, A = HZ[from], B = HZ[to];
  const ya = A.a.map((y, i) => L(y, B.a[i])), yb = A.b.map((y, i) => L(y, B.b[i]));
  const [sx, sy] = [L(A.sun[0], B.sun[0]), L(A.sun[1], B.sun[1])], night = L(A.night, B.night);
  const sun = night < .5
    ? `<circle class="ln" cx="${sx}" cy="${sy}" r="16" opacity="${1 - night * 2}"/><circle class="ln" cx="${sx}" cy="${sy}" r="24" stroke-dasharray="2 5" opacity="${(1 - night * 2) * .8}"/>`
    : `<path class="fl" d="M${sx - 8},${sy - 13} a14 14 0 1 0 14 22 a11 11 0 1 1 -14 -22z" opacity="${(night - .5) * 2}"/>`;
  const stars = HZ_STARS.map(([x, y]) => `<circle class="fl" cx="${x}" cy="${y}" r="1.4" opacity="${night * .8}"/>`).join("");
  const veil = L(A.veil, B.veil), open = L(A.open, B.open), R = 74;
  const dome = veil <= 0.01 ? "" : open > .5
    ? `<path class="ln" d="M${200 - R} 100 A${R} ${R} 0 0 1 ${200 - 18} ${100 - R + 4}" opacity="${veil}"/><path class="ln" d="M${200 + 18} ${100 - R + 4} A${R} ${R} 0 0 1 ${200 + R} 100" opacity="${veil}"/>`
    : `<path d="M${200 - R} 100 A${R} ${R} 0 0 1 ${200 + R} 100 Z" style="fill:var(--fx-veil)" opacity="${Math.max(0, veil - .4) * 1.2}"/><path class="ln" d="M${200 - R} 100 A${R} ${R} 0 0 1 ${200 + R} 100" stroke-dasharray="${veil < .9 ? "5 6" : "none"}" opacity="${Math.min(1, veil * 1.6)}"/>`;
  const markA = `<g opacity="${1 - t}">${HZ_MARKS[A.mark]}</g>`, markB = `<g opacity="${t}">${HZ_MARKS[B.mark]}</g>`;
  svg.innerHTML = stars + sun + dome + `<path class="fl" d="${hzSmooth(ya)} L400,130 L0,130Z" opacity=".1"/><path class="ln" d="${hzSmooth(ya)}"/><path class="ln" d="${hzSmooth(yb)}" opacity=".6"/>` + `<g class="mk">${from === to ? HZ_MARKS[B.mark] : markA + markB}</g>`;
}
const HZ_AT = [[374, 94, .42], [318, 98, .56], [200, 102, .72], [200, 102, .78], [200, 100, .6], [300, 102, .44]];
// hp: share of the phase's lessons still to do (1 = untouched, 0 = phase finished).
function hzCurse(i, hp) {
  if (hp <= 0) return hzShards(HZ_AT[i][0], HZ_AT[i][1] - 30) + `<ellipse cx="${HZ_AT[i][0]}" cy="${HZ_AT[i][1] + 2}" rx="18" ry="2.5" class="stain"/>`;
  const [x, y, s] = HZ_AT[i];
  return hzSpirit(x, y, s * (.75 + .25 * hp), hp) + (i === 1 ? `<path class="bind" d="M292 70 L344 84 M294 86 L342 68"/>` : "");
}
const HZ_SVG = cls => `<svg${cls ? ` class="${cls}"` : ""} viewBox="0 0 400 120" preserveAspectRatio="xMidYMid slice"></svg>`;
function horizonHtml(i, done, total) {
  const hp = total ? (total - done) / total : 0;
  return `<div class="horizon" data-strike aria-hidden="true" data-hz="${i}" data-hp="${hp.toFixed(3)}">${HZ_SVG("")}${HZ_SVG("cu")}${HZ_SVG("en")}</div>`;
}
// Fill the banner after the room is drawn; with `from`, the hills, sun and landmark morph from that phase.
let hzRaf = 0;
function horizonDraw(from) {
  const band = document.querySelector(".horizon"); if (!band) return;
  const [base, cu, en] = band.querySelectorAll("svg"), i = +band.dataset.hz, hp = +band.dataset.hp;
  cancelAnimationFrame(hzRaf);
  cu.innerHTML = hzCurse(i, hp); en.innerHTML = HZ_ENERGY[i];
  if (from == null || from === i) { hzScene(base, i, i, 1); return; }
  const t0 = performance.now(), D = 650;
  fxMove(cu, [{ opacity: 0 }, { opacity: 0, offset: .5 }, { opacity: 1 }], "--dur-slide");
  fxMove(en, [{ opacity: 0 }, { opacity: 0, offset: .5 }, { opacity: 1 }], "--dur-slide");
  const step = now => { const k = Math.min(1, (now - t0) / D); hzScene(base, from, i, 1 - Math.pow(1 - k, 3)); if (k < 1) hzRaf = requestAnimationFrame(step); };
  hzScene(base, from, i, 0); hzRaf = requestAnimationFrame(step);
}
function horizonStrike(band) { const cu = band.querySelector("svg.cu"); cu.classList.remove("struck"); void cu.getBoundingClientRect(); cu.classList.add("struck"); }
