// =====================================================================================================
// The story, as data: "The Watch". Boxes are [left, right, top, bottom] in world units; banner i spans
// x 400i to 400i + 400. Every phase stop shows the same things in the same order, one idea said several ways:
// the phase and what it is for (one plain line), what goes wrong if you skip it (its spirit stirs), the
// landmark doing the phase's job (picture first), then the card naming that idea's real term with an "At work"
// example, then the modules with a few plain words each. Each piece stays up for its words at 3 a second plus
// a moment to look. The hero stays in his calm stage; his move lands on each picture's deciding moment.
// Our own story: The Watch suggests how many people to send, never a grade; grades stay the learner's ladder.
// =====================================================================================================
const portrait = () => innerWidth / innerHeight < .8;
// a stop's shot; on a phone it comes in a little closer (Frame keeps room for its spirit at the edge)
const P = i => () => !portrait() ? [PW * i, PW * i + PW, 0, PH] : i === 0 ? [-12, PW + 12, 0, PH] : [PW * i + 5, PW * i + PW - 35, 0, PH];
const ALL = [0, PW * N, 0, PH];
const CALM = .1;
// a wide shot on a phone held upright: the camera travels slowly along the road from a to b, a few places at a time
const ROAD = (dur, a = 300, b = 2100) => () => { if (!portrait()) return ALL; const k = Math.min(1, Math.max(0, (now - F.t0) / dur)), e = k * k * (3 - 2 * k), c = a + (b - a) * e; return [c - 330, c + 330, 0, PH]; };
const wordCount = s => String(s).replace(/<[^>]+>/g, " ").split(/\s+/).filter(Boolean).length;
const card = (who, html) => `<div class="who"><i></i>${esc(who)}</div>${html}`;
const slip = (stamp, wrong, compact) => `<div class="slip${compact ? " compact" : ""}">${compact ? "" : `<span class="k">Sighting · Old market, 23:40</span><span>“Something with too many eyes, by the well.”</span>`}<span class="stamp${wrong ? " no" : ""}">${esc(stamp)}</span></div>`;
const RIGHT = "Danger: high · Send a team of four", WRONG = "Danger: low · Send one, alone";
// a few plain words under each module's own title (checked against each module's blurb and lessons)
const PLAIN = {
  "use-case": "is this job worth giving to AI?", "foundations": "how AI works, and where it fails", "pricing": "what an AI costs, saves and needs",
  "experiments": "fair comparisons, each recorded in a tool called MLflow",
  "llm-apps": "the AI behind chat assistants", "rag": "answers from your own documents", "agents": "AI that uses tools, step by step",
  "agent-teams": "several AI agents sharing one job", "databricks-ai": "Databricks’ ready-made agents and tools", "production": "keeping an AI app running for real users",
  "security": "stopping tricks, leaks and misuse",
  "evals": "scoring answers against known right answers", "models": "picking the AI that is good, fast and cheap enough",
  "shipping": "putting new versions live, safely",
  "tracing": "seeing what a live AI did, step by step", "llmops": "running AI apps, and what they cost", "reliability": "still working when other services fail",
};
const chip = m => `<span class="chip"><b>${esc(m.title)}</b><small>${esc(PLAIN[m.id])}</small></span>`;

// Writing rules for every line below: a full sentence; name The Watch instead of "it" wherever "it" could mean
// something else; "spirit" means one thing only (a danger The Watch must stop); cause and effect in one sentence.
const lead = s => { const k = s.indexOf(",") + 1; return `<b>${esc(s.slice(0, k))}</b>${esc(s.slice(k))}`; };
const WHO = "The Watch, an AI that judges sightings";
const STOPS = [
  { purpose: "Decide if an AI is worth building, and what a good answer is.",
    skip: "Start building without agreeing, and everyone has a different idea of a good answer.",
    card: "The rules a good answer must meet are called the <b>acceptance criteria</b>. One rule for The Watch: high danger always gets a team of four.",
    work: "At work, a rule might be: every answer names the policy it came from.",
    mark: .5, says: "In the picture, the gate lights up: good answer agreed." },
  { purpose: "Compare fairly: change one thing at a time, so you know what helped.",
    skip: "Change two things at once, and you can’t tell which one helped.",
    card: "To try a new model, the part of The Watch that does the thinking, change only the model and keep everything else the same. A fair comparison like this is called an <b>experiment</b>.",
    work: "At work, each experiment uses the same questions and changes one thing.",
    mark: 2.15, says: "In the picture, four seals stay the same and one changes." },
  { purpose: "Build The Watch so it keeps a record of every step it takes, called a trace.",
    skip: "Build without traces, and when an answer is wrong, nobody can find the step that caused it.",
    card: "As The Watch works, it writes down each step. That record is called a <b>trace</b>.",
    work: "At work, Databricks can keep a trace of each answer an AI assistant gives.",
    mark: 2.9, quick: true, says: "In the picture, four steps light up in order: read, check old reports, judge, suggest a team." },
  { purpose: "Test each new version on the eval set: past sightings with known right answers.",
    skip: "Check only the overall score, and one dangerous mistake can hide among eight right answers.",
    card: slip(WRONG, true) + `<p class="later">The eval set’s most dangerous sightings must always be judged right. They form the <b>must-pass set</b>. This version gets this sighting wrong, so it is not released.</p>`,
    work: "At work, one wrong answer on the must-pass set stops a release.",
    mark: 4.3, ring: true, says: "In the picture, eight windows pass and one fails the must-pass check." },
  { purpose: "Give each new version to a few people first, then to everyone.",
    skip: "Release to everyone at once, and one mistake reaches the whole city.",
    card: "Giving a new version to one district first is called a <b>canary release</b>. If that goes well, the whole city gets the new version.",
    work: "At work, one team gets a new version first, then the whole company.",
    mark: 3.2, quick: true, says: "In the picture, one ray goes out first to one district, then the rest follow." },
  { purpose: "Keep checking The Watch’s answers once it is in use, and learn from each mistake.",
    skip: "Stop checking after release, and wrong answers keep reaching people without anyone noticing.",
    card: "Weeks later, The Watch gets a new kind of sighting wrong, and the people sent report the mistake. That report is called <b>feedback</b>. It is saved with the trace of the steps behind that answer.",
    work: "At work, a user’s thumbs-down is feedback, and it can become a new test.",
    mark: 3.3, quick: true, says: "In the picture, the lanterns light one by one and one turns red: a wrong answer." },
];

// a phase's own cutscene: the full stop, with The Watch's card, an At work example and the modules
function stopBeat(s, i) {
  const ph = COURSE.phases[i];
  const g = s.quick ? { look: .5, act: .9, end: .8 } : { look: .8, act: 1.2, end: 1.5 };
  const bigAt = 1.7, lineAt = 2.1;                                     // the camera arrives and stops at 1.6 s
  const capAt = lineAt + wordCount(s.purpose) / 3 + g.look;
  const actAt = capAt + 2 + g.act;                                     // the skip line is read while the picture acts                                   // the danger is read while the picture acts
  const markAt = actAt + s.mark, cardAt = markAt + .4;                 // picture first, then the card names it
  const cardHtml = typeof s.card === "string" && !s.card.startsWith("<div") ? `<p>${s.card}</p>` : s.card;
  const learnAt = cardAt + .4 + (s.laterAt || 0) + wordCount(s.card) / 3 + wordCount(s.work) / 3 + 1;
  const mods = ph.modules;
  return {
    id: ph.key, stop: i, box: P(i), camDur: 1.6, dur: learnAt + .4 + 1.5 + mods.reduce((n, m) => n + wordCount(m.title + " " + PLAIN[m.id]), 0) / 3 + g.end,
    bigAt, lineAt, capAt, cardAt, learnAt,
    big: ph.name, line: s.purpose,
    cap: lead(s.skip), capText: s.skip,
    card: card(WHO, cardHtml + `<p class="work">${esc(s.work)}</p>`),
    learn: `<span class="lead">You’ll learn</span><div class="row">${mods.map(chip).join("")}</div>`,
    says: s.says, sayCard: `${wordCount(s.card) ? String(s.card).replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim() : ""} ${s.work}`, sayLearn: "You’ll learn: " + mods.map(m => `${m.title}, ${PLAIN[m.id]}`).join("; "),
    enter(quick) { W.here = i; W.hero = i; W.power = CALM; W.dim = true; W.names = false; W.slips = false; W.spirits = true; W.lift = 0; if (!quick) ACTS[i].start(); },
    cues: [[capAt, () => stir(i)], [actAt, () => { F.acted = true; ACTS[i].run(); }], [markAt, () => strike(i)]],
    settle() { ACTS[i].settle(); },
  };
}


// the overview's stop: only the phase, what it's for, the picture doing it, and what goes wrong if you skip it
function quickStop(s, i) {
  const ph = COURSE.phases[i];
  const bigAt = 1.5, lineAt = 1.9, actAt = 2.6;
  const capAt = lineAt + wordCount(s.purpose) / 3 + .4;
  const markAt = actAt + s.mark;
  const caught = i === 3;                                            // Evaluate: the opening's wrong answer is caught here
  const cardAt = caught ? markAt + .5 : null;
  const end = Math.max(capAt + wordCount(s.skip) / 3 + 1.6, markAt + (i === 4 ? 3.6 : 1.8), caught ? cardAt + 4 : 0);
  return {
    id: ph.key, stop: i, box: P(i), camDur: 1.4, dur: end,
    bigAt, lineAt, capAt, cardAt,
    big: ph.name, line: s.purpose,
    cap: lead(s.skip), capText: s.skip,
    card: caught ? card("The Watch", slip(WRONG, true, true) + `<p>That wrong answer is caught here, before anyone is sent.</p>`) : "",
    says: s.says,
    enter(quick) { W.here = i; W.hero = i; W.power = CALM; W.dim = true; W.names = false; W.slips = false; W.spirits = true; W.lift = 0; if (!quick) ACTS[i].start(); },
    cues: [[capAt, () => stir(i)], [actAt, () => { F.acted = true; ACTS[i].run(); }], [markAt, () => strike(i)]],
    settle() { ACTS[i].settle(); },
  };
}

// ---------------- the overview: about two and a half minutes, every phase once, in order ----------------
const OVERVIEW = [
  { id: "far", low: true, box0: [-200, PW * N + 200, -40, PH + 10], box: ROAD(8, 2100, 300), camDur: 4, dur: 8, capAt: 1.2,
    cap: "Every night, people across the city send in sightings of spirits. There are too many for anyone to read.",
    enter() { W.slips = true; W.spirits = false; } },

  { id: "watch", box: P(0), camDur: 2.2, dur: 14, capAt: 1.2, cardAt: 6,
    cap: "An AI called The Watch reads every one. It says how dangerous each spirit is, and suggests how many people to send.",
    card: card("The Watch", slip(RIGHT)),
    enter() { W.hero = -1; W.slips = true; W.spirits = false; const st = document.querySelector("#card .stamp"); if (st) { st.textContent = RIGHT; st.classList.remove("no"); } } },

  // the same card stays; only its answer flips, so it reads as the same sighting with a different answer
  { id: "wrong", box: P(0), dur: 11.5, cardAt: 0, bigAt: 1.5, capAt: 2.7,
    card: card("The Watch", slip(RIGHT)),
    big: "One wrong answer", bigClass: "no",
    cap: "Then the builders change The Watch. The new version reads the same sighting, and suggests sending one person alone, where four were needed.",
    says: `The answer changes to: ${WRONG}.`,
    enter() { W.hero = -1; W.slips = true; W.spirits = false; },
    cues: [[.9, () => flipStamp(WRONG)]] },

  { id: "six", low: true, box: ROAD(10, 300, 1200), camDur: 2.4, dur: 10, bigAt: .8, capAt: 2.2,
    big: "Six phases stop this.",
    cap: "Building an AI like The Watch takes six phases of work, in order. Each phase stops one kind of mistake.",
    says: "In order: " + COURSE.phases.map(p => p.name).join(", ") + ".",
    enter() { W.hero = -1; W.here = -1; W.dim = false; W.slips = false; W.names = true; W.spirits = false; },
    during(at) { const k = Math.min(N - 1, Math.floor((at - 1) / .5)); if (at > 1 && k !== F.seen) { F.seen = k; phasesBar(-1, k); showShapes(k); } },
    settle() { showShapes(N - 1); } },

  { id: "rule", low: true, box: ROAD(10, 1200, 2100), dur: 10, capAt: 1,
    cap: "At each phase, a spirit is waiting. Skip that phase, and The Watch’s mistakes let that spirit get away.",
    enter(quick) { W.names = true; W.spirits = !!quick; showShapes(N - 1); },
    cues: [[.8, () => { W.spirits = true; }], [1.1, () => stir(-2)]],
    settle() { W.spirits = true; } },

  ...STOPS.map(quickStop),

  // the wrong answer from Monitor rides back to Evaluate and becomes a new test
  { id: "loop", low: true, box: [1150, 2450, 0, PH], camDur: 2.4, dur: 10, bigAt: .8, capAt: 2.2,
    big: "Mistakes become tests.",
    cap: "A sighting The Watch got wrong joins the eval set. From then on, every new version is tested on that sighting.",
    says: "In the picture, the wrong answer travels back from Monitor to Evaluate and becomes a new test.",
    enter() { W.here = -1; W.hero = -1; W.dim = false; W.loop = true; W.names = true; W.spirits = true; W.lift = 0; stir(-1); },
    during(at) { rideLoop(at, 3, 6); },
    settle() { rideLoop(99, 0, 1); } },

  { id: "start", wait: "end", box: P(0), camDur: 3, bigAt: 1.2, capAt: 2.4, endAt: 5.5,
    big: "Start at Frame.",
    cap: "The same six phases build real AI assistants at your job. Your first lesson asks if an AI is worth building at all.",
    start: COURSE.first, phases: true,
    enter() { W.loop = false; W.names = portrait(); W.here = 0; W.hero = 0; W.power = CALM; W.dim = false; W.spirits = true; rideLoop(-1); },
    cues: [[2.5, () => { W.names = false; }]] },
];

// ---------------- a phase's own cutscene: played when you open that phase's room ----------------
function phaseFilm(i) {
  const ph = COURSE.phases[i], from = Math.max(0, i - 1);
  const stop = stopBeat(STOPS[i], i);
  stop.box0 = [PW * from, PW * from + PW, 0, PH];                     // arrive from the place before it on the road
  stop.camDur = i ? 2.4 : 1.6;
  return [stop,
    { id: "start", wait: "end", box: P(i), camDur: 1.5, bigAt: .4, capAt: 1.2, endAt: 3,
      big: "Start here.",
      cap: `Every lesson you finish in ${ph.name} weakens the spirit waiting here. Finish them all, and that spirit is beaten.`,
      start: ph.first, overview: true,
      enter() { W.here = i; W.hero = i; W.power = CALM; W.dim = true; W.spirits = true; } }];
}
const BEATS = FILM === "overview" ? OVERVIEW : phaseFilm(COURSE.phases.findIndex(p => p.key === FILM));
