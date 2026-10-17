// ---------- the phase banner
// A strip of original line art at the top of Home's phase room: a horizon that reshapes for each phase
// (gate, seals, barrier, curtain, opening, lanterns), a layer of blue-flame energy, and a cursed spirit
// that gets weaker as you finish the phase's lessons: eyes close, it shrinks and cracks, and the last
// lesson exorcises it. A white-haired, blindfolded hero on the left hill grows stronger as it weakens, with a new stance and technique each phase. The platform
// track gets its own banner in teal (`hzTrackScene`). Decorative only (aria-hidden); tapping it strikes the spirit for fun.
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
  if (hp <= 0) return `<ellipse cx="${HZ_AT[i][0]}" cy="${HZ_AT[i][1] + 2}" rx="18" ry="2.5" class="stain"/>`;
  const [x, y, s] = HZ_AT[i];
  return hzSpirit(x, y, s * (.75 + .25 * hp), hp) + (i === 1 ? `<path class="bind" d="M292 70 L344 84 M294 86 L342 68"/>` : "");
}
// The hero: drawn in glowing outline, a dark figure with a blue rim, spiky white hair that glows, a black
// blindfold, a smile, and a long high-collared jacket with a round button. He has three stages, which follow
// `power` (the share of the phase's lessons done):
//   0 under a third   calm, a hand at the blindfold, faint rings behind his head
//   1 from a third    two fingers raised in a sign, a blue ring and a red one round a dark sphere
//   2 from two-thirds arms open, a field of stars inside two great circles, galaxies, rings at his feet
// and, on top, a small touch for the phase (`pose`, 0..5), from the hand of his stage:
//   0 Frame a scanning ring, a thread to the spirit · 1 Design energy along a line · 2 Build a blue and a red
//   orb at the hand · 3 Evaluate measuring arcs · 4 Ship a beam · 5 Monitor a quiet halo.
// Everything he gives off grows with `power`; tapping the banner fires the flame.
const hzStage = power => power < 1 / 3 ? 0 : power < 2 / 3 ? 1 : 2;
// a few fixed points in a disc (the stars of the open stage), spread by the golden angle
const HZ_SKY = Array.from({ length: 28 }, (_, k) => { const r = Math.sqrt((k + .5) / 28), a = k * 2.39996; return [r * Math.cos(a), r * Math.sin(a), k % 4 ? .35 : .6]; });
function hzSorcerer(x, g, tx, ty, power, pose = 2, unveiled = false) {
  const S = .82, X = v => (x + v * S).toFixed(1), Y = v => (g + v * S).toFixed(1), Z = v => (v * S).toFixed(1);
  const P = pts => "M" + pts.map(([a, b]) => `${X(a)},${Y(b)}`).join(" L") + "Z";
  const stage = hzStage(power), F = [0, 0, 2.6][stage];
  const leg = s => `<path class="ol" d="${P([[s * .6, -28.4], [s * 6.4, -28], [s * (7.4 + F), -14], [s * (7.6 + F * 1.6), -2], [s * (3.8 + F * 1.6), -2], [s * (3.2 + F), -14], [s * .6, -24]])}"/>`
    + `<path class="ol" d="${P([[s * (3.4 + F * 1.6), -2.2], [s * (7.8 + F * 1.6), -2.4], [s * (9.4 + F * 1.6), 0], [s * (3.2 + F * 1.6), 0]])}"/>`;
  const coat = `<path class="ol" d="${P([[-3.2, -50.2], [-7.6, -48.2], [-7.4, -38], [-6.4, -33.4], [-7.2, -27], [7.2, -27], [6.4, -33.4], [7.4, -38], [7.6, -48.2], [3.2, -50.2]])}"/>`
    + `<path class="seam" d="M${X(0)},${Y(-49)} V${Y(-27.4)} M${X(-4.8)},${Y(-46)} Q${X(-5.6)},${Y(-38)} ${X(-4.6)},${Y(-27.4)} M${X(4.8)},${Y(-46)} Q${X(5.6)},${Y(-38)} ${X(4.6)},${Y(-27.4)} M${X(-6.6)},${Y(-33.6)} H${X(-3)} M${X(6.6)},${Y(-33.6)} H${X(3)}"/>`;
  const collar = `<path class="ol" d="${P([[-3.4, -53.2], [3.4, -53.2], [4, -48.8], [0, -47.8], [-4, -48.8]])}"/><circle class="btn" cx="${X(0)}" cy="${Y(-50)}" r="${Z(.9)}"/>`;
  const head = `<ellipse class="skin" cx="${X(0)}" cy="${Y(-56.6)}" rx="${Z(3.2)}" ry="${Z(3.9)}"/>`
    + `<path class="smile" d="M${X(-1.2)},${Y(-54.2)} q${Z(1.2)},${Z(.9)} ${Z(2.4)},${Z(-.2)}"/>`;
  const band = `<path class="band" d="${P([[-3.5, -58.8], [3.5, -58.8], [3.4, -56.2], [-3.4, -56.2]])}"/>`;
  // with the blindfold pushed up: two blue eyes (h-eye, never "eye", which is the spirit's)
  const bandUp = `<path class="band up" d="${P([[-3.9, -62.2], [3.7, -61.2], [3.7, -59.6], [-3.9, -60.6]])}"/>`;
  const eyesOpen = [-1.4, 1.5].map(a => `<circle class="h-eye-blue" cx="${X(a)}" cy="${Y(-57.4)}" r="${Z(.95)}"/><circle class="h-eye-core" cx="${X(a)}" cy="${Y(-57.4)}" r="${Z(.38)}"/>`).join("");
  const hair = `<path class="hair" d="${P([[-3.6, -58.4], [-6.6, -59.2], [-4.8, -60.6], [-6.8, -62.8], [-3.8, -62.4], [-3.8, -65.4], [-1.4, -63], [0, -66.4], [1.4, -63], [3.8, -65.4], [3.8, -62.4], [6.8, -62.8], [4.8, -60.6], [6.6, -59.2], [3.6, -58.4]])}"/>`;
  // a sleeve is a tube: a wide stroke in the rim colour, a narrower one in the jacket's
  const arm = pts => { const d = "M" + pts.map(([a, b]) => `${X(a)},${Y(b)}`).join(" L"); return `<path class="sleeve" d="${d}"/><path class="sleeve in" d="${d}"/>`; };
  const fist = (a, b, r = 1.5) => `<circle class="skin" cx="${X(a)}" cy="${Y(b)}" r="${Z(r)}"/>`;
  const sign = (a, b) => `<path class="skin" d="M${X(a)},${Y(b)} l${Z(.5)},${Z(-6.4)} l${Z(.9)},0 l${Z(.2)},${Z(4.6)} l${Z(.5)},${Z(-5)} l${Z(.9)},${Z(.2)} l${Z(-.4)},${Z(6.8)}Z"/>`;
  // an open hand hanging down and out, fingers spread (s: -1 left, 1 right)
  const palm = (a, b, s) => `<path class="skin" d="M${X(a - 1.2 * s)},${Y(b - 1)} l${Z(2.4 * s)},${Z(-.4)} l${Z(1.4 * s)},${Z(3.2)} l${Z(-.6 * s)},${Z(.4)} l${Z(-.6 * s)},${Z(-1.4)} l${Z(.2 * s)},${Z(2.4)} l${Z(-.8 * s)},${Z(.2)} l${Z(-.6 * s)},${Z(-2.2)} l${Z(-.6 * s)},${Z(1.8)} l${Z(-.7 * s)},${Z(-.3)}Z"/>`;
  // [arms behind the head, hands in front of it, where the energy leaves him]
  const STAGE = [
    [arm([[7, -47.4], [12.4, -51.6], [5.4, -57]]) + arm([[-7, -47.4], [-8.6, -38], [-8.4, -30]]), fist(4.6, -57.4, 1.6) + fist(-8.4, -29.2), [5, -58]],
    [arm([[7, -47.4], [9.4, -40], [2.4, -42.4]]) + arm([[-7, -47.4], [-8.6, -40], [-1.6, -41.4]]), fist(-1, -42.2, 1.6) + sign(.4, -42.6), [1.4, -50]],
    [arm([[7, -47.4], [12.4, -39], [16.4, -32]]) + arm([[-7, -47.4], [-12.4, -39], [-16.4, -32]]), palm(16.6, -31, 1) + palm(-16.6, -31, -1), [17.4, -28.6]],
  ][stage];
  const hx = +X(STAGE[2][0]), hy = +Y(STAGE[2][1]);
  const orb = `<circle class="h-orb${pose === 3 ? " v" : ""}" cx="${hx}" cy="${hy}" r="${(pose === 3 ? 2 + 3 * power : 1.2 + 2.4 * power).toFixed(1)}" opacity="${(.35 + .6 * power).toFixed(2)}"/>`;
  // the stage's energy, behind him
  const R = 1 + .15 * power, C = [X(0), Y(-34)];
  const ring = (k, c, rx, ry, rot, dy = 0) => `<ellipse class="swirl${c}" cx="${C[0]}" cy="${Y(-34 + dy)}" rx="${Z(rx * R)}" ry="${Z(ry * R)}" transform="rotate(${rot} ${C[0]} ${Y(-34 + dy)})" pathLength="1" style="--d:${(-k * .5).toFixed(1)}s"/>`;
  // a small spiral galaxy: two curled arms round a bright core
  const galaxy = (a, b, k) => `<g class="h-gal" style="--d:${-k * 2}s"><circle cx="${X(a)}" cy="${Y(b)}" r="${Z(.6)}"/><path d="M${X(a)},${Y(b)} m${Z(-3.4)},${Z(.6)} a${Z(3.4)},${Z(1.6)} 0 0 1 ${Z(3)},${Z(-2)} a${Z(2)},${Z(1)} 0 0 1 ${Z(1.8)},${Z(1.4)} M${X(a)},${Y(b)} m${Z(3.4)},${Z(-.6)} a${Z(3.4)},${Z(1.6)} 0 0 1 ${Z(-3)},${Z(2)} a${Z(2)},${Z(1)} 0 0 1 ${Z(-1.8)},${Z(-1.4)}"/></g>`;
  const field = [
    [12, 18, 24].map((r, k) => `<circle class="h-ring" cx="${X(0)}" cy="${Y(-56)}" r="${Z(r * R)}" style="--d:${-k * .9}s"/>`).join("")
      + [[-17, -60], [21, -48], [-11, -38]].map(([a, b]) => `<circle class="h-dot" cx="${X(a)}" cy="${Y(b)}" r="${Z(.7)}"/>`).join(""),
    `<circle class="h-sphere" cx="${C[0]}" cy="${C[1]}" r="${Z(25 * R)}"/>` + ring(0, "", 22, 7, -16, -8) + ring(1, " c", 24, 6, -10, -6) + ring(2, " r", 26, 8, 16, 6)
      + HZ_SKY.slice(0, 10).map(([a, b]) => `<circle class="h-dot" cx="${X(a * 14 + 4)}" cy="${Y(b * 8 - 40)}" r="${Z(.4)}"/>`).join(""),
    `<circle class="h-dom" cx="${C[0]}" cy="${C[1]}" r="${Z(30 * R)}"/><circle class="h-dom v" cx="${C[0]}" cy="${C[1]}" r="${Z(36 * R)}"/>`
      + HZ_SKY.map(([a, b, r]) => `<circle class="h-dot" cx="${X(a * 28)}" cy="${Y(b * 28 - 34)}" r="${Z(r)}"/>`).join("")
      + galaxy(-18, -50, 0) + galaxy(19, -46, 1) + galaxy(18, -16, 2)
      + [[11, 2, ""], [16, 3.2, " c"], [21, 4.4, " v"]].map(([rx, ry, c], k) => `<ellipse class="h-floor${c}" cx="${X(0)}" cy="${Y(-.6)}" rx="${Z(rx * R)}" ry="${Z(ry * R)}" pathLength="1" style="--d:${-k * .6}s"/>`).join("")
      + ring(0, " b", 23, 6, 14, 10),
  ][stage];
  // the phase's touch, from the hand
  const line = `M${hx},${hy} Q${((hx + tx) / 2).toFixed(1)},${(Math.min(hy, ty) - 8).toFixed(1)} ${tx},${ty}`;
  const tech = [
    `<circle class="h-scan" cx="${X(0)}" cy="${Y(-57)}" r="${Z(10)}"/><circle class="h-scan" cx="${X(0)}" cy="${Y(-57)}" r="${Z(10)}" style="--d:-1.2s"/><path class="h-thread" d="${line}"/>`,
    `<path class="h-thread on" d="${line}"/><path class="h-thread hi" d="${line}"/>`,
    `<circle class="h-orb" cx="${(hx - 3).toFixed(1)}" cy="${hy}" r="1.6"/><circle class="h-orb r" cx="${(hx + 3).toFixed(1)}" cy="${hy}" r="1.6"/>`,
    [-14, -4, 6].map((d, k) => `<path class="h-arc" d="M${hx},${hy} Q${((hx + tx) / 2).toFixed(1)},${(Math.min(hy, ty) - 22 + d).toFixed(1)} ${(tx + d * .6).toFixed(1)},${ty}" style="--d:${(-k * .4).toFixed(1)}s"/>`).join(""),
    `<path class="h-ray" d="M${hx},${hy} L${tx},${ty}" opacity="${(.2 + .6 * power).toFixed(2)}"/><path class="h-ray hi" d="M${hx},${hy} L${tx},${ty}"/>`,
    `<ellipse class="h-halo" cx="${X(0)}" cy="${Y(-33)}" rx="${Z(14)}" ry="${Z(36)}"/>`,
  ][pose];
  const SP = [[-16, -44], [17, -20], [-12, -8], [20, -46], [-19, -26], [11, -66], [-8, -66], [22, -32], [-21, -14], [15, -6]];
  const sparks = SP.slice(0, 4 + Math.round(6 * power)).map(([a, b], k) =>
    `<path class="spark${k % 3 ? "" : " v"}" d="M${X(a)},${Y(b - 1.4)} l${Z(.5)},${Z(1.4)} l${Z(-.5)},${Z(1.4)} l${Z(-.5)},${Z(-1.4)}Z" style="--d:${(k * .29).toFixed(2)}s"/>`).join("");
  const beam = `<path class="h-beam" d="M${hx},${hy} L${tx},${ty}"/>`;
  // unveiled (the learner tapped him): the aura flares to full whatever the progress
  const au = k => `class="h-aura${unveiled ? " mix" : ""}" opacity="${unveiled ? 1 : (k + (1 - k) * power).toFixed(2)}"`;
  return `<g class="hero${unveiled ? " awake" : ""}" data-pose="${pose}" data-stage="${stage}"><g ${au(.4)}>${field}</g>${orb}<g ${au(.4)}>${tech}</g>`
    + `<g class="h-body">${leg(-1)}${leg(1)}${coat}${STAGE[0]}${collar}${head}${unveiled ? eyesOpen : band}${hair}${unveiled ? bandUp : ""}${STAGE[1]}</g><g ${au(.5)}>${sparks}</g>${beam}</g>`;
}
const HZ_HERO_X = 30;
const hzGround = (i, x) => { const a = HZ[i].a, k = Math.min(7, Math.floor(x / 50)), f = (x - k * 50) / 50; return a[k] + (a[k + 1] - a[k]) * f; };
const hzTarget = i => [HZ_AT[i][0], HZ_AT[i][1] - 30 * HZ_AT[i][2]];
// Tapping the hero lifts his blindfold (and tapping again puts it back), for this visit: every banner follows.
let hzAwake = false;
const hzHero = (i, hp, awake = hzAwake) => hzSorcerer(HZ_HERO_X, hzGround(i, HZ_HERO_X), ...hzTarget(i), 1 - hp, i, awake);

// The platform track's banner, in the track's teal: a blueprint ground, a stack of workspaces, a pipeline
// running right, and an octagon ward (the track's shape) that is drawn a little more with every lesson
// until it closes around the spirit.
const HZ_WARD = [320, 64, 40];
const hzOct = (cx, cy, r) => "M" + Array.from({ length: 8 }, (_, k) => { const a = Math.PI / 8 + k * Math.PI / 4; return `${(cx + r * Math.cos(a)).toFixed(1)},${(cy + r * Math.sin(a)).toFixed(1)}`; }).join(" L") + "Z";
function hzTrackScene(svg, hp) {
  const grid = [40, 80, 120, 160, 200, 240].map(x => `<path class="ln grid" d="M${x} 96 v20"/>`).join("");
  const stack = [0, 1, 2].map(k => `<rect class="ln" x="${150 + k * 4}" y="${84 - k * 13}" width="34" height="11" rx="2"/><circle class="fl" cx="${157 + k * 4}" cy="${89.5 - k * 13}" r="1.3"/>`).join("");
  const pipe = `<path class="ln" d="M190 66 H226 V88 H262 M226 66 V50 H270" stroke-dasharray="3 3"/><rect class="ln" x="262" y="82" width="12" height="12" rx="2"/>`;
  const [cx, cy, r] = HZ_WARD;
  const ward = `<path class="ln ward" d="${hzOct(cx, cy, r)}" pathLength="1" stroke-dasharray="${(1 - hp).toFixed(3)} 1"/><path class="ln" d="${hzOct(cx, cy, r)}" pathLength="1" opacity=".2"/>`;
  svg.innerHTML = `<path class="ln" d="M0 96 H400"/>${grid}${stack}<g class="mk">${pipe}</g>${ward}`;
}
const HZ_TRACK_ENERGY = `<path class="st" d="M190 66 H226 V88 H262"/><path class="st hi" d="M226 66 V50 H270"/>` + hzEmb([[170, 50], [226, 60], [268, 80]]);
const HZ_TRACK_AT = [320, 96, .5];
// The track's own spirit, the drift stack: three crooked boxes piled up, like workspaces that no longer match
// their config, with loose cables for arms. Same contract as hzSpirit: nine eyes that close as `hp` falls,
// cracks below 80% and 45%.
function hzDriftStack(cx, base, sc, hp) {
  const S = v => (v * sc).toFixed(1), X = v => (cx + v * sc).toFixed(1), Y = v => (base + v * sc).toFixed(1);
  const box = (x, y, w, h) => `<path class="body" d="M${X(x + 5)},${Y(y)} H${X(x + w - 5)} Q${X(x + w)},${Y(y)} ${X(x + w)},${Y(y + 5)} V${Y(y + h)} H${X(x)} V${Y(y + 5)} Q${X(x)},${Y(y)} ${X(x + 5)},${Y(y)}Z"/>`;
  const body = box(-34, -22, 62, 22) + box(-24, -44, 56, 23) + box(-30, -64, 46, 21);
  const arms = `<path class="limb" d="M${X(-34)},${Y(-14)} C${X(-50)},${Y(-22)} ${X(-46)},${Y(2)} ${X(-60)},${Y(-2)} M${X(32)},${Y(-36)} C${X(48)},${Y(-44)} ${X(52)},${Y(-14)} ${X(64)},${Y(-8)}"/><rect class="limb" x="${X(-66)}" y="${Y(-5)}" width="${S(6)}" height="${S(5)}"/><rect class="limb" x="${X(63)}" y="${Y(-11)}" width="${S(6)}" height="${S(5)}"/>`;
  const mouth = `<path class="mouth" d="M${X(-22)},${Y(-9)} H${X(20)} L${X(16)},${Y(-4)} H${X(-18)}Z"/><path class="teeth" d="M${X(-18)},${Y(-8)}${Array.from({ length: 7 }, () => ` l${S(3)},${S(3)} l${S(3)},${S(-3)}`).join("")}"/>`;
  const hatch = Array.from({ length: 6 }, (_, k) => `<path class="hatch" d="M${X(-20 + k * 9)},${Y(-23)} l${S(-5)},${S(-9)}"/>`).join("");
  const EYES = [[-14, -54, 5], [4, -56, 3], [-24, -57, 1.6], [14, -34, 4], [-10, -34, 2.6], [24, -30, 1.8], [-24, -16, 2.2], [20, -16, 2], [0, -16, 1.6]];
  const open = Math.max(1, Math.round(EYES.length * hp));
  const eyes = EYES.map(([x, y, r], k) => k < open
    ? `<circle class="eyew" cx="${X(x)}" cy="${Y(y)}" r="${S(r)}"/><circle class="eye" cx="${X(x + r * .2)}" cy="${Y(y)}" r="${S(r * .45)}" style="--d:${(k * .41).toFixed(2)}s"/>`
    : `<path class="limb" d="M${X(x - r)},${Y(y)} h${S(r * 2)}"/>`).join("");
  const cracks = (hp < .8 ? `<path class="crack" d="M${X(-6)},${Y(-64)} l${S(4)},${S(8)} ${S(-5)},${S(7)} ${S(5)},${S(8)}"/>` : "")
    + (hp < .45 ? `<path class="crack" d="M${X(20)},${Y(-44)} l${S(-6)},${S(8)} ${S(5)},${S(6)} ${S(-6)},${S(10)}"/><path class="crack" d="M${X(-28)},${Y(-20)} l${S(8)},${S(-4)} ${S(4)},${S(6)}"/>` : "");
  return `<g class="wob">${arms}${body}${hatch}${mouth}${eyes}${cracks}</g><circle class="hit" cx="${cx}" cy="${Y(-32)}" r="${S(36)}" style="fill:var(--fx-core)"/>`;
}
function hzTrackCurse(hp, awake = hzAwake) {
  const [x, y, sc] = HZ_TRACK_AT;
  const foe = hp <= 0 ? `<ellipse cx="${x}" cy="${y + 2}" rx="18" ry="2.5" class="stain"/>` : hzDriftStack(x, y, sc * (.75 + .25 * hp), hp);
  return foe + hzSorcerer(HZ_HERO_X, 96, x, y - 30 * sc, 1 - hp, 2, awake);
}

const HZ_SVG = cls => `<svg${cls ? ` class="${cls}"` : ""} viewBox="0 0 400 120" preserveAspectRatio="xMidYMid slice"></svg>`;
function horizonHtml(i, done, total) {
  const hp = total ? (total - done) / total : 0;
  return `<div class="horizon" data-strike aria-hidden="true" data-awakened="${hzAwake}" data-hz="${i}" data-hp="${hp.toFixed(3)}">${HZ_SVG("")}${HZ_SVG("cu")}${HZ_SVG("en")}</div>`;
}
// Fill the banner after the room is drawn; with `from`, the hills, sun and landmark morph from that phase.
let hzRaf = 0;
// Finishing a room: the first time you see it finished, the hero takes his finishing stance (pose 4, at full
// power), charges at his hand, and fires a blast that fills the banner; a flash where the spirit stood, the
// spirit breaks apart, then the room settles to its finished look. Once per room, remembered on this device
// (drill-hz-won). `hero` is his finishing-stance drawing for this room.
const hzWon = () => { try { return JSON.parse(store.get("drill-hz-won") || "[]"); } catch { return []; } };
function horizonFinale(band, key, [tx, ty], hero) {
  const won = hzWon(); if (won.includes(key)) return;
  store.set("drill-hz-won", JSON.stringify([...won, key]));
  const cu = band.querySelector("svg.cu"), old = cu.querySelector && cu.querySelector(".hero");
  if (old) old.remove();
  const [, hx, hy] = hero.match(/class="h-beam" d="M([\d.]+),([\d.]+)/) || [0, 30, 60];
  cu.insertAdjacentHTML("beforeend", `<g class="fin">${hero}<circle class="charge" cx="${hx}" cy="${hy}" r="9"/>`
    + `<path class="blast" d="M${hx},${hy} L${tx},${ty}"/><path class="blast hi" d="M${hx},${hy} L${tx},${ty}"/>`
    + `<circle class="burst" cx="${tx}" cy="${ty}" r="34"/><g class="shards">${hzShards(tx, ty)}</g></g>`);
  band.classList.add("finale");
  if (typeof document !== "undefined") setTimeout(() => { band.classList.remove("finale"); horizonDraw(); }, 3000);
}
function horizonDraw(from) {
  for (const t of document.querySelectorAll('.horizon[data-hz="t"]')) {
    const [base, cu, en] = t.querySelectorAll("svg"), hp = +t.dataset.hp;
    hzTrackScene(base, hp); cu.innerHTML = hzTrackCurse(hp); en.innerHTML = HZ_TRACK_ENERGY;
    if (hp <= 0) { const tg = [HZ_TRACK_AT[0], HZ_TRACK_AT[1] - 30 * HZ_TRACK_AT[2]]; horizonFinale(t, "t", tg, hzSorcerer(HZ_HERO_X, 96, ...tg, 1, 4)); }
  }
  const band = document.querySelector(".phasebox .horizon"); if (!band) return;
  const [base, cu, en] = band.querySelectorAll("svg"), i = +band.dataset.hz, hp = +band.dataset.hp;
  cancelAnimationFrame(hzRaf);
  cu.innerHTML = hzCurse(i, hp) + hzHero(i, hp); en.innerHTML = HZ_ENERGY[i];
  if (hp <= 0) horizonFinale(band, "p" + i, hzTarget(i), hzSorcerer(HZ_HERO_X, hzGround(i, HZ_HERO_X), ...hzTarget(i), 1, 4));
  if (from == null || from === i) { hzScene(base, i, i, 1); return; }
  const t0 = performance.now(), D = 650;
  fxMove(cu, [{ opacity: 0 }, { opacity: 0, offset: .5 }, { opacity: 1 }], "--dur-slide");
  fxMove(en, [{ opacity: 0 }, { opacity: 0, offset: .5 }, { opacity: 1 }], "--dur-slide");
  const step = now => { const k = Math.min(1, (now - t0) / D); hzScene(base, from, i, 1 - Math.pow(1 - k, 3)); if (k < 1) hzRaf = requestAnimationFrame(step); };
  hzScene(base, from, i, 0); hzRaf = requestAnimationFrame(step);
}
// A tap on the hero (or close to him) toggles his blindfold, with a burst of light at him; anywhere else strikes the spirit.
function horizonStrike(band, ev) {
  const cu = band.querySelector("svg.cu"), me = cu.querySelector(".h-body");
  if (ev && me) {
    const r = me.getBoundingClientRect(), pad = 16;
    if (ev.clientX > r.left - pad && ev.clientX < r.right + pad && ev.clientY > r.top - pad && ev.clientY < r.bottom + pad) {
      hzAwake = !hzAwake;
      for (const b of document.querySelectorAll(".horizon[data-hz]")) b.dataset.awakened = hzAwake;
      horizonDraw();
      if (hzAwake) fxOn(band, "bloom", FX.bloom, band.querySelector("svg.cu .h-body"));
      return;
    }
  }
  cu.classList.remove("struck"); void cu.getBoundingClientRect(); cu.classList.add("struck");
}

// ---------- the hero beside the help (outside the banner)
// His portrait sits beside the boxes that already exist: the clue (blindfolded), the verdict, and the answer
// (blindfold up, his eyes showing). He says nothing of his own: the box beside him keeps the lesson's words.
// The portrait is drawn on its own, close up: a tall dark collar over the chin with a round button, a narrow
// face, angular white hair. A blindfold for a clue or a verdict; for the answer it's gone and his eyes glow.
function hzFace(mood) {
  const P = pts => "M" + pts.map(([x, y]) => `${x},${y}`).join(" L") + "Z";
  const coat = `<path class="coat" d="M-2,60 L1,47 Q5,41 14,39 L38,39 Q47,41 51,47 L54,60Z"/>`;
  const face = `<path class="skin" d="M17,33 V16 Q17,11 22,11 H30 Q35,11 35,16 V33Z"/>`;
  const collar = `<path class="coat" d="M13,50 L15,31 L37,31 L39,50 Q26,54 13,50Z"/><path class="seam" d="M13,50 Q26,54 39,50 M26,44.6 V60"/><circle class="btn" cx="26" cy="42" r="2.6"/>`;
  const hair = `<path class="hair" d="${P([[8, 15], [12, 9], [5, 5], [18, 6], [21, 0], [27, 5], [35, -1], [37, 6], [48, 2], [44, 9], [50, 13], [36, 15], [26, 13], [16, 15]])}"/>`;
  const eyes = mood === "answer"
    ? [21.9, 30.1].map(x => `<g class="h-eyes"><circle class="h-eye" cx="${x}" cy="22" r="3"/><circle class="h-glint" cx="${x}" cy="22" r="1.25"/></g>`).join("")
    : `<path class="band" d="M15.5,19 H36.5 V25.4 H15.5Z"/>`;
  const sparks = mood === "right" ? [[45, 22], [7, 30]].map(([x, y], k) => `<path class="spark" d="M${x},${y - 3} l1,3 l-1,3 l-1,-3Z" style="--d:${k * .4}s"/>`).join("") : "";
  return `<span class="horizon hface ${mood}" aria-hidden="true"><svg class="cu" viewBox="0 0 52 60">${coat}${face}${eyes}${collar}${hair}${sparks}</svg></span>`;
}
const hzCoach = (mood, html) => `<div class="hcoach">${hzFace(mood)}${html}</div>`;
// On the done screen: the whole figure, in the phase's stance (the Build sign on the track), as strong as the phase is done.
const hzFigure = (pose, power) => `<span class="horizon hfig" aria-hidden="true"><svg class="cu" viewBox="4 40 54 64">${hzSorcerer(30, 100, 140, 70, power, pose)}</svg></span>`;
