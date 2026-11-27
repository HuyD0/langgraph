// =====================================================================================================
// The world: Home's six phase banners (page/horizon.js) laid end to end along one horizon, in course order.
// Each banner is 400 x 120 units; banner i starts at x = 400 * i. Nothing here redraws them: hzScene draws
// the hills, sky marks and landmark, HZ_ENERGY the energy, hzCurse the spirit, hzSorcerer the hero.
// =====================================================================================================
document.documentElement.dataset.theme = "dusk";        // a film is always Dusk, whatever look the app is in
document.documentElement.lang = "en";
const PW = 400, PH = 120, N = 6;
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const film = $("film"), canvas = $("sky");
const W = { here: -1, hero: -1, power: .1, stir: -1, dim: false, loop: false, hp: 1, names: false, slips: false, spirits: false, lift: 0, liftNow: 0 };
// the film's own sky, dusk to full night: darkest under Evaluate's closed curtain, lighter as Ship opens
const NIGHT = [.3, .4, .5, .9, .55, 1];

function joinHills() {
  for (let i = 1; i < N; i++) for (const k of ["a", "b"]) { const m = (HZ[i - 1][k][8] + HZ[i][k][0]) / 2; HZ[i - 1][k][8] = m; HZ[i][k][0] = m; }
}
function buildWorld() {
  joinHills();
  const g = [];
  for (let i = 0; i < N; i++) {
    g.push(`<g class="panel" data-i="${i}" transform="translate(${PW * i},0)">
      <svg class="base" width="${PW}" height="${PH}" viewBox="0 0 ${PW} ${PH}" overflow="visible"></svg>
      <svg class="en" width="${PW}" height="${PH}" viewBox="0 0 ${PW} ${PH}" overflow="visible">${HZ_ENERGY[i]}</svg>
      <svg class="cu" width="${PW}" height="${PH}" viewBox="0 0 ${PW} ${PH}" overflow="visible">${hzCurse(i, 1)}</svg>
      <svg class="fx" width="${PW}" height="${PH}" viewBox="0 0 ${PW} ${PH}" overflow="visible"></svg>
      <g class="pshape" data-n="${COURSE.phases[i].name.length}"><g>${phShape(i, 6)}</g></g>
      <text class="pname" x="200" y="150" text-anchor="middle">${esc(COURSE.phases[i].name)}</text></g>`);
  }
  // the loop: Monitor's lanterns back to Evaluate's curtain, along the sky
  const a = [PW * 5 + 250, 56], b = [PW * 3 + 200, 40];
  const d = `M${a[0]},${a[1]} C${a[0] - 120},${a[1] - 90} ${b[0] + 160},${b[1] - 80} ${b[0]},${b[1]}`;
  const slips = [[-160, 20], [-80, -30], [40, -50], [520, -20], [-200, 70], [-120, -60], [600, 30], [-240, 10], [380, -50], [-60, 60], [700, -10], [-180, -40]].map(([x, y], k) => `<circle r="2.2" class="em slipdot"><animateMotion dur="${(3.4 + k * .5).toFixed(1)}s" begin="${(-k * .9).toFixed(1)}s" repeatCount="indefinite" path="M${x},${y} Q${(x + 254) / 2},${y - 40} 254,82"/></circle>`).join("");
  $("world").innerHTML = `<svg id="wsvg" preserveAspectRatio="none">${g.join("")}<g class="slips">${slips}</g><path class="loop" id="loop1" d="${d}"/><path class="loop hi" id="loop2" d="${d}"/><circle id="rider" r="5" class="rider"/><text id="newtest" class="newtest" x="${b[0]}" y="${b[1] - 12}" text-anchor="middle">new test</text></svg>`;
  document.querySelectorAll("#wsvg .panel").forEach((p, i) => {
    hzScene(p.querySelector("svg.base"), i, i, 1);
    p.querySelectorAll("svg.base path.fl").forEach(f => { if (f.getAttribute("d").endsWith("L400,130 L0,130Z")) f.remove(); });
  });
  // one ground for the whole road, under all six banners' hills, so no seam shows where one banner meets the next
  const hills = HZ.map((z, i) => hzSmooth(z.a).replace(/-?\d+(\.\d+)?,-?\d+(\.\d+)?/g, xy => { const [x, y] = xy.split(",").map(Number); return `${(x + PW * i).toFixed(1)},${y}`; })).map((d, i) => i ? d.replace(/^M/, "L") : d).join(" ");
  const ground = document.createElementNS("http://www.w3.org/2000/svg", "path");
  const y0 = HZ[0].a[0], y1 = HZ[N - 1].a[8], yb0 = HZ[0].b[0], yb1 = HZ[N - 1].b[8];
  ground.setAttribute("class", "fl"); ground.setAttribute("opacity", ".1"); ground.setAttribute("d", `M-1200,${y0} L0,${y0} ${hills.replace(/^M/, "L")} L${PW * N + 1200},${y1} L${PW * N + 1200},900 L-1200,900Z`);
  $("wsvg").insertBefore(ground, $("wsvg").firstChild);
  // the road runs on past both ends, so the world never visibly stops
  const edge = document.createElementNS("http://www.w3.org/2000/svg", "g");
  edge.innerHTML = `<path class="ln" d="M-1200,${y0} L0,${y0} M${PW * N},${y1} L${PW * N + 1200},${y1}"/><path class="ln" opacity=".6" d="M-1200,${yb0} L0,${yb0} M${PW * N},${yb1} L${PW * N + 1200},${yb1}"/>`;
  $("wsvg").insertBefore(edge, ground.nextSibling);
}
// what the current stop needs: its landmark lit, its spirit, the hero in that banner with that phase's move
let drawnKey = "";
function stage() {
  $("wsvg").classList.toggle("named", !!W.names); $("wsvg").classList.toggle("slipping", !!W.slips);
  const key = `${W.here}|${W.hero}|${W.power}|${W.dim}|${W.hp}|${W.spirits}`;
  if (key === drawnKey) return;
  drawnKey = key;
  document.querySelectorAll("#wsvg .panel").forEach((p, i) => {
    p.classList.toggle("here", i === W.here);
    p.classList.toggle("dim", W.dim && i !== W.here);
    const cu = p.querySelector("svg.cu");
    const stirring = cu.classList.contains("stir");
    cu.innerHTML = (W.spirits ? hzCurse(i, W.hp) : "") + (i === W.hero ? hzSorcerer(HZ_HERO_X, hzGround(i, HZ_HERO_X), ...hzTarget(i), W.power, i, false) : "");
    cu.classList.toggle("stir", stirring);
  });
}
function strike(i) {
  const cu = document.querySelector(`#wsvg .panel[data-i="${i}"] svg.cu`); if (!cu) return;
  cu.classList.remove("struck"); void cu.getBoundingClientRect(); cu.classList.add("struck");
  setTimeout(() => cu.classList.remove("struck"), 600);
}
function showShapes(k) { document.querySelectorAll("#wsvg .pshape").forEach((s, j) => s.classList.toggle("on", j <= k)); }
function flipStamp(text) {
  const st = document.querySelector("#card .stamp"); if (!st) return;
  st.classList.add("flip-out");
  setTimeout(() => { st.textContent = text; st.classList.remove("flip-out"); st.classList.add("no", "flip-in"); }, 260);
}
function rideLoop(at, t0 = 0, t1 = 1) {
  const p = $("loop1"), dot = $("rider"), tag = $("newtest"); if (!p || !dot) return;
  if (at < 0) { dot.classList.remove("on", "home"); tag.classList.remove("on"); return; }
  const k = Math.min(1, Math.max(0, (at - t0) / (t1 - t0))), e = k * k * (3 - 2 * k), q = p.getPointAtLength(p.getTotalLength() * e);
  dot.setAttribute("cx", q.x.toFixed(1)); dot.setAttribute("cy", q.y.toFixed(1));
  dot.classList.toggle("on", at >= t0); dot.classList.toggle("home", k >= 1); tag.classList.toggle("on", k >= 1);
}
function stir(i) { document.querySelectorAll("#wsvg svg.cu").forEach((c, k) => c.classList.toggle("stir", k === i || i === -2)); }

// =====================================================================================================
// The camera: the beat names a box of the world [left, right, top, bottom]; it is fitted into the band of the
// screen kept for the horizon (between the words above and the card below), and the svg's viewBox follows it.
// =====================================================================================================
const cam = { cx: 200, cy: 60, s: 1 }, cam0 = { cx: 200, cy: 60, s: 1, t: 0, dur: 1.6 };
const easeIO = k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
function band() {
  const H = innerHeight, Wd = innerWidth, portrait = Wd / H < .8;
  const top = $("bar-top-h") ? 0 : document.querySelector(".bar.top").offsetHeight;
  return portrait ? { x0: 0, x1: Wd, y0: H * .24, y1: H * .24 + Wd * .42 } : { x0: 0, x1: Wd, y0: Math.max(top + 10, H * .3), y1: H * .66 };
}
function fit(box, low) {
  const B = band(), [l, r, t, b] = box;
  const s = Math.min((B.x1 - B.x0) / (r - l), (B.y1 - B.y0) / (b - t));
  const by = low ? innerHeight * (innerWidth / innerHeight < .8 ? .58 : .7) - ((b - t) / 2) * s : (B.y0 + B.y1) / 2;
  return { cx: (l + r) / 2, cy: (t + b) / 2, s, bx: (B.x0 + B.x1) / 2, by };
}
let camT = null;
function applyCam() {
  const svg = $("wsvg"); if (!svg || !camT) return;
  const Wd = innerWidth, H = innerHeight;
  const vx = cam.cx - camT.bx / cam.s, vy = cam.cy - camT.by / cam.s;
  svg.setAttribute("viewBox", `${vx.toFixed(2)} ${vy.toFixed(2)} ${(Wd / cam.s).toFixed(2)} ${(H / cam.s).toFixed(2)}`);
  const pn = Math.max(20, 12 / cam.s);
  svg.style.setProperty("--pn", pn.toFixed(1) + "px");
  if (pn !== applyCam.pn) { applyCam.pn = pn; document.querySelectorAll("#wsvg .pshape").forEach(g => { const w = +g.dataset.n * pn * .58, k = pn / 20; g.firstElementChild.setAttribute("transform", `translate(${(200 - w / 2 - 14 * k).toFixed(1)},${(150 - 6.5 * k).toFixed(1)}) scale(${k.toFixed(3)})`); }); }
}
// where the bottom of the horizon falls on screen, and how far into the night we are, for the sky
const groundPx = () => camT ? camT.by + (PH - cam.cy) * cam.s : innerHeight * .66;
function nightAt(x) { const i = Math.max(0, Math.min(N - 1, x / PW - .5)), k = Math.floor(i), f = i - k; const a = NIGHT[k], b = NIGHT[Math.min(N - 1, k + 1)]; return a + (b - a) * f; }

// =====================================================================================================
// The sky behind the banners: one pass on the graphics card, colours from the page's tokens.
// =====================================================================================================
const FRAG = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
uniform vec2 r; uniform float t; uniform float night; uniform float ground; uniform float pan; uniform float fade;
uniform vec3 cVeil, cBg, cGlow, cCore, cPath;
float h(vec2 p){vec3 q=fract(vec3(p.xyx)*.1031);q+=dot(q,q.yzx+33.33);return fract((q.x+q.y)*q.z);}
float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}
float fbm(vec2 p){float a=.5,s=0.;for(int i=0;i<4;i++){s+=a*n(p);p=p*2.03+7.;a*=.5;}return s;}
void main(){
  vec2 fc=gl_FragCoord.xy; vec2 uv=(fc-.5*r)/r.y; float gy=1.-ground/r.y;     // gy: the horizon's foot, 0 at the bottom
  float y=fc.y/r.y;
  vec3 dusk=mix(cPath*.55+cBg,cBg,smoothstep(gy,gy+.55,y));
  vec3 deep=mix(cPath*.16+cVeil,cVeil*.7,smoothstep(gy,gy+.6,y));
  vec3 col=mix(dusk,deep,night);
  col+=cPath*.22*(1.-night*.6)*exp(-abs(y-gy-.05)*6.);
  vec2 sp=uv+vec2(pan*.05,0.); vec2 g=floor(sp*230.);
  col+=cCore*step(.9965,h(g))*(.55+.45*sin(t*1.5+h(g+3.)*40.))*smoothstep(gy+.05,gy+.4,y)*(.25+.75*night);
  col+=cPath*.08*fbm(vec2(sp.x*2.+t*.01,y*3.))*smoothstep(gy+.1,gy+.6,y);
  float below=1.-smoothstep(gy-.004,gy+.004,y);
  col=mix(col,mix(cPath*.12+cBg*.6,cVeil*.85,smoothstep(gy,gy-.35,y)),below);
  col+=cPath*.05*fbm(vec2(sp.x*4.+t*.03,y*14.))*below*smoothstep(gy-.25,gy,y);
  col*=1.-.32*dot(uv,uv);
  gl_FragColor=vec4(col*fade,1.);
}`;
let GL = null, now = 0, scale = Math.min(window.devicePixelRatio || 1, 1.5);
const tokRGB = name => { const el = document.createElement("i"); el.style.color = `var(${name})`; document.body.appendChild(el); const m = getComputedStyle(el).color.match(/[\d.]+/g).map(Number); el.remove(); return [m[0] / 255, m[1] / 255, m[2] / 255]; };
function initGL() {
  const gl = canvas.getContext("webgl", { antialias: false, powerPreference: "low-power", failIfMajorPerformanceCaveat: true });
  if (!gl) return false;
  const mk = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
  const pr = gl.createProgram();
  try { gl.attachShader(pr, mk(gl.VERTEX_SHADER, "attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}")); gl.attachShader(pr, mk(gl.FRAGMENT_SHADER, FRAG)); }
  catch (e) { console.error(e); return false; }
  gl.linkProgram(pr); if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) { console.error(gl.getProgramInfoLog(pr)); return false; }
  gl.useProgram(pr);
  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer()); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  const a = gl.getAttribLocation(pr, "a"); gl.enableVertexAttribArray(a); gl.vertexAttribPointer(a, 2, gl.FLOAT, false, 0, 0);
  const U = {}; for (const nm of ["r", "t", "night", "ground", "pan", "fade"]) U[nm] = gl.getUniformLocation(pr, nm);
  for (const [u, tk] of Object.entries({ cVeil: "--fx-veil", cBg: "--bg", cGlow: "--fx-glow", cCore: "--fx-core", cPath: "--path" })) gl.uniform3fv(gl.getUniformLocation(pr, u), tokRGB(tk));
  GL = { gl, U };
  canvas.addEventListener("webglcontextlost", e => { e.preventDefault(); GL = null; film.classList.add("flat"); });
  return true;
}
function drawSky(fade) {
  if (!GL) return;
  const { gl, U } = GL, w = Math.round(canvas.clientWidth * scale), h = Math.round(canvas.clientHeight * scale);
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  gl.viewport(0, 0, w, h);
  gl.uniform2f(U.r, w, h); gl.uniform1f(U.t, now % 600); gl.uniform1f(U.night, Math.max(0, nightAt(cam.cx) - .35 * W.liftNow)); gl.uniform1f(U.ground, groundPx() * scale);
  gl.uniform1f(U.pan, cam.cx / PW); gl.uniform1f(U.fade, fade);
  gl.drawArrays(gl.TRIANGLES, 0, 3);
}

// =====================================================================================================
// The words: big type and the course's line in the sky, The Watch's card and the modules under the horizon,
// the subtitle in the bottom bar. Each beat says when each one appears.
// =====================================================================================================
function swap(el, html, cls) {
  if ((el.dataset.v || "") === (html || "") && (el.dataset.c || "") === (cls || "")) return;
  el.dataset.v = html || ""; el.dataset.c = cls || "";
  el.classList.add("off");
  setTimeout(() => { if (el.dataset.v !== (html || "")) return; el.innerHTML = html || ""; el.className = el.className.replace(/\b(no)\b/g, "").trim(); if (cls) el.classList.add(cls); el.classList.toggle("off", !html); }, 380);
}
function phasesBar(i, seen) {
  $("phases").innerHTML = COURSE.phases.map((p, k) => `<span class="ph${k === i ? " here" : k <= seen ? " on" : ""}"><svg viewBox="-9 -9 18 18" aria-hidden="true">${phShape(k, 7)}</svg><span class="t">${esc(p.name)}</span></span>`).join("");
}
const F = { i: 0, t0: 0, paused: false, fade: 0, fired: new Set(), seen: -1 };
function words(B, at) {
  const show = (key, t) => t != null && at >= t;
  if (show("big", B.bigAt ?? (B.big ? 0 : null))) swap($("big"), esc(B.big), B.bigClass); else if (!B.keepBig) swap($("big"), "");
  if (show("line", B.lineAt ?? (B.line ? 0 : null))) swap($("line"), B.lineHtml ? B.line : esc(B.line)); else swap($("line"), "");
  if (show("cap", B.capAt ?? (B.cap ? 0 : null))) swap($("cap"), B.cap); else swap($("cap"), "");
  if (show("card", B.cardAt ?? (B.card ? 0 : null))) swap($("card"), B.card); else swap($("card"), "");
  if (show("learn", B.learnAt ?? (B.learn ? 0 : null))) swap($("learn"), B.learn); else swap($("learn"), "");
}
const plain = h => { const d = document.createElement("div"); d.innerHTML = h || ""; return d.textContent.replace(/\s+/g, " ").trim(); };
const end = s => /[.:!?”]$/.test(s) ? s : s + ".";
function say(B) { $("said").textContent = [B.big, plain(B.line), B.capText || plain(B.cap), B.says, B.sayCard ? plain(B.sayCard) : plain(B.card), B.sayLearn || plain(B.learn)].filter(Boolean).map(end).join(" "); }
function go(i, opts = {}) {
  i = Math.max(0, Math.min(BEATS.length - 1, i));
  setPaused(false);
  // moving forward past a stop whose picture never got to act: finish it, so the road behind stays true
  const Prev = BEATS[F.i]; if (!opts.rebuild && i > F.i && Prev && Prev.stop != null && !F.acted) { ACTS[Prev.stop].start(); ACTS[Prev.stop].settle(); }
  F.acted = false;
  if (opts.rebuild || i < F.i) rebuild(i);
  F.i = i; F.t0 = now; F.fired = new Set();
  const B = BEATS[i];
  Object.assign(cam0, { cx: cam.cx, cy: cam.cy, s: cam.s, t: now, dur: B.camDur || 2 });
  if (B.enter) B.enter(false);
  if (B.stop != null) F.seen = Math.max(F.seen, B.stop);
  phasesBar(B.stop ?? -1, B.stop != null ? B.stop - 1 : F.seen);
  words(B, 0); say(B);
  $("end").hidden = true; $("end").innerHTML = "";
}
function rebuild(i) {
  Object.assign(W, { here: -1, hero: -1, power: .1, dim: false, loop: false, hp: 1, names: false, slips: false, spirits: false, lift: 0, liftNow: 0 });
  showShapes(-1); rideLoop(-1);
  F.seen = -1; resetActs(); stir(-1);
  const fi = COURSE.phases.findIndex(p => p.key === FILM);
  if (fi >= 0) { for (let j = 0; j < fi; j++) ACTS[j].settle(); W.spirits = true; F.seen = fi - 1; }
  for (let k = 0; k < i; k++) { const b = BEATS[k]; if (b.enter) b.enter(true); if (b.settle) b.settle(); if (b.stop != null) F.seen = Math.max(F.seen, b.stop); }
}
function next() { const B = BEATS[F.i]; if (B.wait) return; if (F.i < BEATS.length - 1) go(F.i + 1); }
function back() { if (F.i > 0) go(F.i - 1); }
function setPaused(v) { F.paused = v; $("pause").textContent = v ? "Play" : "Pause"; }
$("back").onclick = e => { e.stopPropagation(); back(); };
$("pause").onclick = e => { e.stopPropagation(); setPaused(!F.paused); };
$("skip").onclick = e => { e.stopPropagation(); const end = BEATS.length - 1; if (F.i !== end) { rebuild(end); F.i = end - 1; go(end); F.t0 = now - (BEATS[end].endAt || 0); } };
film.addEventListener("click", e => { if (F.swiped) { F.swiped = false; return; } if (e.target.closest("button, a, .panel-end, .bar")) return; if (e.clientX < innerWidth * .3) back(); else next(); });
addEventListener("keydown", e => {
  if (e.target.closest && e.target.closest(".panel-end")) return;
  if (e.key === "ArrowRight") { e.preventDefault(); next(); }
  else if (e.key === "ArrowLeft") { e.preventDefault(); back(); }
  else if (e.key === " " && !(e.target.closest && e.target.closest("button, a"))) { e.preventDefault(); setPaused(!F.paused); }
});
let sx = null;
film.addEventListener("touchstart", e => { F.swiped = false; sx = e.target.closest(".panel-end, .bar") ? null : e.touches[0].clientX; }, { passive: true });
film.addEventListener("touchend", e => { if (sx == null) return; const x0 = sx, dx = e.changedTouches[0].clientX - x0; sx = null; if (x0 < 24 || x0 > innerWidth - 24) return; if (Math.abs(dx) > 60) { F.swiped = true; if (dx < 0) next(); else back(); } }, { passive: true });
function endPanel(B) {
  const el = $("end"); if (!el.hidden) return;
  el.hidden = false;
  const film = k => `the-watch-${COURSE.phases[k].key}.html`;
  const more = B.phases ? `<nav class="films" aria-label="Each phase up close"><span>Each phase up close:</span>${COURSE.phases.map((p, k) => `<a href="${film(k)}"><svg viewBox="-9 -9 18 18" aria-hidden="true">${phShape(k, 7)}</svg>${esc(p.name)}</a>`).join("")}</nav>`
    : B.overview ? `<nav class="films" aria-label="More"><a href="the-watch.html">All six phases</a></nav>` : "";
  el.innerHTML = `<div class="hcoach">${hzFace("clue")}<p>This is your guide. In every lesson, he gives you a clue first, then the answer.</p></div><a class="btn primary" href="${APP_URL}#${esc(B.start.lesson)}" id="start">Start: ${esc(B.start.title)}</a>${more}<button type="button" class="btn quiet" id="again">Play again</button>`;
  $("said").textContent = "This is your guide. In every lesson, he gives you a clue first, then the answer. Start: " + B.start.title + ".";
  $("again").onclick = () => { F.fade = 0; F.i = 0; rebuild(0); go(0); $("pause").focus({ preventScroll: true }); };
  $("start").focus({ preventScroll: true });
}

// =====================================================================================================
// The loop: draws only while the page is visible; Pause stops the clock on a timed beat.
// =====================================================================================================
let last = performance.now(), samples = [], tuned = false;
function frame(ms) {
  const dt = Math.min(.05, (ms - last) / 1000); last = ms;
  if (!document.hidden && !F.held) tick(dt);
  requestAnimationFrame(frame);
}
function tick(dt) {
  const B = BEATS[F.i];
  if (F.paused && !B.wait) { drawSky(F.fade); return; }
  now += dt;
  for (let k = ACT_TIMERS.length - 1; k >= 0; k--) if (ACT_TIMERS[k].t <= now) { const fn = ACT_TIMERS[k].fn; ACT_TIMERS.splice(k, 1); fn(); }
  const at = now - F.t0;
  if (B.during) B.during(at);
  for (const [t, fn] of B.cues || []) if (at >= t && !F.fired.has(t)) { F.fired.add(t); fn(); }
  words(B, at);
  stage();
  camT = fit(typeof B.box === "function" ? B.box() : B.box, B.low);
  const e = easeIO(Math.min(1, (now - cam0.t) / cam0.dur));
  cam.cx = cam0.cx + (camT.cx - cam0.cx) * e; cam.cy = cam0.cy + (camT.cy - cam0.cy) * e; cam.s = cam0.s * Math.pow(camT.s / cam0.s, e);
  W.liftNow += (W.lift - W.liftNow) * (1 - Math.exp(-dt * 1.2));
  applyCam();
  $("loop1").classList.toggle("on", W.loop); $("loop2").classList.toggle("on", W.loop);
  F.fade = Math.min(1, F.fade + dt / 2.2);
  drawSky(F.fade);
  if (B.wait === "end" && at >= (B.endAt || 0)) endPanel(B);
  if (!F.paused && !B.wait && at >= B.dur && !F.held) next();
  if (!tuned && GL && !F.held) { samples.push(dt * 1000); if (samples.length === 50) { tuned = true; const m = samples.slice(10).sort((x, y) => x - y)[20]; if (m > 24) scale = m > 40 ? .5 : .75; } }
}
// for review screenshots: jump to a beat and play it forward some seconds, held there
window.__film = { jump(i, secs) { F.held = true; rebuild(i); F.i = i; go(i, { rebuild: true }); const b0 = fit(typeof BEATS[i].box === "function" ? BEATS[i].box() : BEATS[i].box, BEATS[i].low); Object.assign(cam, { cx: b0.cx, cy: b0.cy, s: b0.s }); Object.assign(cam0, { cx: b0.cx, cy: b0.cy, s: b0.s, t: now }); for (let k = 0; k < secs * 30; k++) tick(1 / 30); const B = BEATS[F.i]; if (B.stop != null && secs > (B.cardAt || 0)) { ACT_TIMERS.length = 0; ACTS[B.stop].start(); ACTS[B.stop].settle(); } F.fade = 1; drawSky(1); return { beat: BEATS[F.i].id, flat: film.classList.contains("flat") }; } };
addEventListener("error", e => { if ($("oops")) return; const d = document.createElement("div"); d.id = "oops"; d.className = "panel-end"; d.innerHTML = `<p>The film couldn’t play here.</p><a class="btn primary" href="${APP_URL}#${esc(COURSE.first.lesson)}">Start: ${esc(COURSE.first.title)}</a>`; film.appendChild(d); });
function start() {
  buildWorld();
  resetActs();
  // a phase's own film: the places before it on the road are already done, the spirits already named
  const fi = COURSE.phases.findIndex(p => p.key === FILM);
  if (fi >= 0) { for (let j = 0; j < fi; j++) ACTS[j].settle(); W.spirits = true; F.seen = fi - 1; }
  if (!initGL()) film.classList.add("flat");
  const b0 = fit(BEATS[0].box0 || BEATS[0].box, BEATS[0].low); camT = b0; Object.assign(cam, { cx: b0.cx, cy: b0.cy, s: b0.s });
  go(0);
  requestAnimationFrame(frame);
}
