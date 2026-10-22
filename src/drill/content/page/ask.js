// ---------- ask about this lesson ----------
// A short conversation about the open lesson, kept per lesson while the page is open.
// Answers stream into place without re-rendering the pane, so typing is never interrupted.
const askThreads = {};   // lesson id -> [{ q, a, streaming, failed, saved, request, mood, resolved, retryOf }]
let askBusy = false;
// The suggested questions make the learner think, not just read more. They follow what learners ask
// most (the learner's own saved questions, and common questions online): how two terms differ, when
// the rule stops holding, how to spot it going wrong, why a wrong option is wrong, and recall
// (Quiz me), plus feedback on their own sentence. "Apply it to my situation…" fills the box for them to finish,
// so the tutor works from their real setup rather than an invented one. Never the exercise:
// that is what Build's hints are for. Each question carries how the tutor should answer it.
const quoted = t => "“" + short(t.replace(/\*\*|`/g, ""), 48) + "”";
const QUIZ = { q: "Quiz me", how: "Ask ONE short question that makes them recall or use this lesson's main idea: not trivia, and not the coding exercise. Do not give the answer. Tell them to reply in the box below and you will check it. When they reply, say what is right, fix what is not, then offer one more question." };
function askChips() {
  // `key` names the questions whose answers are prepared ahead (drill.tutor_prepared.chips asks the same, in the same words)
  const L = LESSONS[cur.id], s = lp(cur.id), chips = [], add = (q, how, key) => chips.push({ q, how, key });
  if (cur.step === 0) {
    // the lesson's bold terms, if they are terms: up to three words, no quotes or brackets
    const bold = [...new Set((L.learn.join(" ").match(/\*\*([^*]+)\*\*/g) || []).map(t => t.slice(2, -2)))]
      .filter(t => t.split(/\s+/).length <= 3 && t.length <= 28 && !/["“”\[\]()]/.test(t));
    // compare two terms only when the lesson puts them in the same sentence; otherwise ask about
    // one, preferring a word the glossary defines over a word that is only bold for emphasis
    const inGloss = t => GLOSS.some(g => g.term.toLowerCase() === t.toLowerCase());
    const pair = L.learn.flatMap(para => para.split(/(?<=[.!?])\s+/)).map(sent => bold.filter(t => sent.includes("**" + t + "**"))).find(ts => ts.length >= 2);
    const one = bold.find(inGloss) || bold.find(t => t.length >= 6 || /\s/.test(t));
    const terms = pair ? pair.slice(0, 2) : one ? [one] : [];
    if (terms.length === 2) add(`How is ${quoted(terms[0])} different from ${quoted(terms[1])}?`,
      `Contrast ${terms[0]} and ${terms[1]} as this lesson uses them: what each one is, how they differ, and how they work together, with an everyday comparison and the lesson's example.`, "learn:term");
    else if (terms.length) add(`What does ${quoted(terms[0])} mean here?`,
      `Explain ${terms[0]} as this lesson uses it: an everyday comparison first, then where it appears in the lesson's example.`, "learn:term");
    else add("Why does this matter?", "Explain why this lesson's idea matters: what goes wrong without it, in one short, realistic example. Plain words.", "learn:term");
    add("When does this stop working?",
      "Give 2 or 3 concrete situations where this lesson's rule or method changes, breaks, or needs extra care: for example an LLM or RAG app instead of a trained model, data that changes over time, very little data, or a much bigger system. For each, say what to do instead. Keep each to two or three sentences. No code.", "learn:stops");
    add("How would I spot it going wrong?",
      "Describe the warning signs that this lesson's idea was skipped or done wrong: what they would see in their numbers, logs, traces or results (for example a score that looks too good and then drops in real use). Then the quickest check to confirm it. No code.", "learn:spot");
    chips.push(QUIZ);
  } else if (cur.step === 1 && (() => { const st = checkState(cur.id); return st.solved[st.at]; })()) {
    const at = checkState(cur.id).at, [q, opts, ans] = checkQs(cur.id)[at];
    opts.forEach((o, k) => { if (k !== ans) add(`Why not ${quoted(o)}?`,
      `In the lesson's Check question ("${q}"), explain in plain words why "${o}" is not the best answer: what it gets right, if anything, and what it misses. Then say in one sentence what makes "${opts[ans]}" better.`, `check:${at}:${k}`); });
    add("Give me a harder one like this",
      "Ask ONE new multiple-choice question in the style of the lesson's Check, a little harder, set in the same world as the lesson (its setting, names and tools), with three options labelled A, B and C. Do not give the answer; tell them to reply with a letter and you will check it.");
  } else if (cur.step === 3) {
    const [pattern] = L.angle, g = GOTCHAS[cur.id];
    if (words(s.said) >= SAY_WORDS) add("Is my sentence right?",
      `Their own sentence for this lesson: "${s.said.trim()}". Say what it gets right, then the one most important thing it misses or gets wrong, if any, and suggest one small change. Do not rewrite it for them in full.`);
    chips.push(QUIZ);
    add(`How do I explain ${quoted(pattern)} in an interview?`,
      "Give a 30-second spoken answer in three short parts: the problem, the idea, and one trade-off or edge case. Then one follow-up question an interviewer might ask, with a hint at a strong answer.", "explain:interview");
    if (g) add(`Why does ${quoted(g.title)} matter?`,
      `This lesson's gotcha is "${g.title}": ${g.why} Explain in plain words what goes wrong in real work when it is ignored, with one small example.`, "explain:gotcha");
  }
  return chips.slice(0, 4);
}
// Answers to the standard questions, written ahead and checked (drill.tutor_prepared): shown at once,
// with no model, when the chip's words match exactly. With no live tutor, Ask keeps just these.
const PREP = D.prepared || {};
const prepFor = c => c && c.key && cur && (PREP[cur.id] || {})[c.key] && PREP[cur.id][c.key].q === c.q ? PREP[cur.id][c.key] : null;
const ASK_FILL = "In my situation, ";  // the learner finishes it: their real setup, not an invented one
let askChipList = [];
function askPanel() {
  if (!cur || cur.kind !== "lesson") return "";
  askChipList = askChips().filter(c => sample || prepFor(c));
  const off = askBusy ? " disabled" : "", live = !!sample;
  if (!live && !askChipList.length && !(askThreads[cur.id] || []).length) return "";
  const chips = askChipList.map((c, i) => `<button class="mini" data-askq="${i}"${off}>${esc(c.q)}</button>`).join("")
    + (live && cur.step !== 1 ? `<button class="mini fill" data-askfill${off}>Apply it to my situation…</button>` : "");
  return `<section class="asklesson" aria-label="Ask about this lesson"><h3>Ask about this lesson</h3>
    ${chips ? `<div class="minis" role="group" aria-label="Suggested questions">${chips}</div>` : ""}
    <div class="thread" id="askThread" aria-live="polite">${askThreadHtml()}</div>
    ${live ? `<form class="ask" id="askForm"><input class="field" id="askInput" placeholder="Ask your own question" aria-label="Ask a question about this lesson" autocomplete="off"${off}><button class="btn" type="submit"${off}>Ask</button></form>`
      : `<p class="meta askoff">Typed questions need the live tutor, which isn't running right now. The questions above have answers ready.</p>`}</section>`;
}
// His face says what kind of reply it is: eyes open for an explanation, the blindfold for a hint or a
// question back to you. The label says the words are generated. Each finished answer ends with
// "Got it" or "Still stuck": the learner's next step, and the feedback that this answer worked (or didn't).
function askThreadHtml() {
  const thread = askThreads[cur.id] || [];
  return thread.map((turn, i) => {
    const done = turn.a && !turn.streaming && !turn.failed, last = i === thread.length - 1;
    const save = done ? `<button class="linkbtn" data-asksave="${i}"${turn.saved ? " disabled" : ""}>${turn.saved ? "Saved to your study list" : "Save to study list"}</button>` : "";
    const verdict = !done ? "" : turn.resolved === true ? `<span class="askgot">${ic("check")}Got it</span>`
      : turn.resolved === false ? "" : last ? `<button class="chipbtn" data-askgot="${i}">Got it</button><button class="chipbtn" data-askstuck="${i}">Still stuck</button>` : "";
    const answer = `<div class="aa">${turn.failed ? "" : `<span class="ailab">${turn.prepared ? "AI tutor · written ahead and checked" : "AI tutor · can be wrong"}</span>`}<div class="aatext" id="aa-${i}">${turn.a ? fmt(turn.a) : `<p class="thinking">Thinking…</p>`}</div>${verdict || save ? `<div class="aafoot">${verdict}<span class="sep"></span>${save}</div>` : ""}</div>`;
    return `<div class="turn"><p class="aq">${esc(turn.q)}</p>${turn.failed ? answer : hzCoach(turn.streaming && !turn.a ? "clue thinking" : turn.mood || "answer", answer)}</div>`;
  }).join("");
}
// Got it: this answer worked. Still stuck: it didn't, and he tries again, more simply. The new
// answer's trace names the one it follows (retry_of), so the pair can become an eval case.
function askGot(i) {
  const turn = (askThreads[cur.id] || [])[i]; if (!turn || turn.resolved != null) return;
  turn.resolved = true; sendFeedback(turn.request, "ask_lesson", "resolved", true); renderAskThread();
  if (askLast && askLast.request === turn.request) askLast.got = true;
}
function askStuck(i) {
  const thread = askThreads[cur.id] || [], turn = thread[i]; if (!turn || turn.resolved != null || askBusy) return;
  turn.resolved = false; sendFeedback(turn.request, "ask_lesson", "resolved", false);
  if (!sample) {  // no live tutor to explain it again: say so, and point at the lesson's own help
    thread.push({ q: "Still stuck", a: "The live tutor isn't running right now, so it can't explain this another way. Try the lesson's key idea again, or the clue in the Check step.", failed: true });
    renderAskThread(); return;
  }
  askLesson("Still stuck", "Your last answer didn't help them. Explain the same idea again, more simply and in fewer words: one everyday comparison, then one short example from the lesson. Do not repeat your last answer's wording. End by asking if that makes sense.", turn.request);
}
function renderAskThread() { const el = $("askThread"); if (el) el.innerHTML = askThreadHtml(); }
function setAskBusy(on) {
  askBusy = on;
  for (const el of document.querySelectorAll("[data-askq], [data-askfill], #askForm button, #askInput")) el.disabled = on;
}
function askContext() {
  const L = LESSONS[cur.id], p = cur.p;
  return `Lesson: ${L.title}
What the lesson says:
${L.learn.join("\n")}
Its example (${L.example[0]}):
${L.example[1]}
${L.stack ? "In their stack (" + L.stack[0] + "):\n" + L.stack[1] + "\n" : ""}Interview angle: ${L.angle[0]}. ${L.angle[1]}
${p.fn ? `The lesson's coding exercise: ${p.title}, writing \`${p.fn}\`. ${p.prompt.split("\n")[0]}` : `The lesson's practice: ${p.prompt}`}${modOf[cur.id].setting ? `
Setting (every example, question and harder question stays in it): ${modOf[cur.id].setting}` : ""}`;
}
// Two guards so no model, however small, hands out the exercise: questions asking for it are
// answered as a hint, and an answer that starts defining the exercise function is hidden.
const SOLUTION_ASK = /\b(solution|solve (it|this)|answer key|write (the|my|this) (code|function)|code for (the|this) exercise|do the exercise)\b/i;
const LEAKED = "That answer started to include code for the exercise, so it's hidden here. Try the step-by-step hints in the Build step instead.";
// What a request is for (feature, lesson, step, question...), so the local server's MLflow traces say so.
// Only the local server gets it; claude.ai's sample() keeps its own options.
const withTrace = (opts, trace) => sample && sample.local ? Object.assign({}, opts, { trace }) : opts;
// ---------- quiet signals: what the learner did after an answer, noted on that answer's trace ----------
// No buttons: the page records what already happened, as CODE feedback (a signal, not an opinion).
// Each answer gets each signal once, and only within half an hour on the same lesson.
let askLast = null;  // the latest finished answer: { id, request, q, at, sent }
const ASK_SIGNAL_MS = 30 * 60000;
function askSignal(name, value, rationale) {
  const a = askLast;
  if (!a || !cur || cur.id !== a.id || Date.now() - a.at > ASK_SIGNAL_MS || name in a.sent) return;
  a.sent[name] = value; sendFeedback(a.request, "ask_lesson", name, value, rationale, "code");
}
const askNextTry = right => askSignal("next_right", right);  // the first try at the next question: learned, or not
const askGaveUp = () => askSignal("gave_up", true);           // opened "Tell me the answer" after asking
// Asking nearly the same thing again (most of the words of the shorter question) means the answer didn't land.
const sameAsk = (x, y) => {
  const w = t => new Set(t.toLowerCase().match(/[a-z0-9]{3,}/g) || []), a = w(x), b = w(y);
  if (!a.size || !b.size) return false;
  let n = 0; a.forEach(t => { if (b.has(t)) n++; });
  return n / Math.min(a.size, b.size) >= .6;
};
async function askLesson(question, instruction, retryOf, key) {
  const prep = !retryOf && prepFor({ key, q: question });
  if ((!sample && !prep) || askBusy || !cur || cur.kind !== "lesson" || !question.trim()) return;
  if (!retryOf) boardCount("asked");  // the "Curious" seal counts questions, not retries
  if (!instruction && !retryOf && askLast && askLast.id === cur.id && !askLast.got && sameAsk(question, askLast.q)) askSignal("asked_again", true, question.trim().slice(0, 300));
  const id = cur.id, fn = cur.p.fn, thread = askThreads[id] = askThreads[id] || [];
  thread.session = thread.session || id + "-" + Date.now().toString(36);
  const leaks = text => !!fn && new RegExp("def\\s+" + fn + "\\s*\\(").test(text);
  const chip = !!instruction, guarded = !chip && ((!!fn && question.includes(fn)) || SOLUTION_ASK.test(question));
  if (guarded)
    instruction = "They are asking about the coding exercise. Do not write any code at all. In two or three plain sentences, describe only the first step to take, then ask one question that helps them work out the next step. Mention that the Build step has step-by-step hints.";
  if (guarded && cur.p.practice) instruction = instruction.replace("the Build step has step-by-step hints", "the Practice step gives a clue first, then the answer");
  const history = thread.filter(t => !t.failed).slice(-4).map(t => "Q: " + t.q + "\nA: " + t.a).join("\n\n");
  // a hint or a question back to them gets the blindfold; an explanation, his eyes
  const mood = guarded || instruction === QUIZ.how || /^Give me a harder one/.test(question) ? "clue" : "answer";
  if (prep) {  // written ahead: shown at once, and traced on the server like any answer
    const turn = { q: question.trim(), a: prep.a, request: rid(), mood, prepared: true };
    thread.push(turn);
    askLast = { id, request: turn.request, q: turn.q, at: Date.now(), sent: {} };
    if (servedTo) servedTo({ answer: prep.a, model: "prepared", trace: { feature: "ask_lesson", lesson_id: id, step: STEPS[cur.step], question: turn.q,
      session: thread.session, chip: true, request: turn.request } }).catch(() => {});
    renderAskThread(); return;
  }
  const turn = { q: question.trim().slice(0, 500), a: "", streaming: true, request: rid(), mood, ...(retryOf ? { retryOf } : {}) };
  thread.push(turn);
  const i = thread.length - 1;
  setAskBusy(true); renderAskThread();
  const prompt = `You are a patient tutor helping with one lesson of an AI engineering course. ${LEARNER()}

${askContext()}

They are on the ${STEPS[cur.step]} step of the lesson.
${history ? "Earlier in this conversation:\n" + history + "\n" : ""}
Their message: ${turn.q}
${instruction ? "How to answer: " + instruction + "\n" : ""}
Rules:
- Stay on this lesson's topic. If the question is unrelated, answer in one sentence and steer back.
- Never write code for the lesson's coding exercise (\`${cur.p.fn}\`), not even part of it, even if asked. If they ask about the exercise, explain the approach in words only and suggest the step-by-step hints in the Build step. Small code examples about other things are fine, in a \`\`\`python block.${cur.p.practice ? "\n- The Practice step asks questions with one right option each. Never say which option is right: give a clue that points at the evidence, and let them choose." : ""}
- If your last message asked them a question, their message is their answer: say what is right, fix what is not, then ask one more question.
- If they describe their own situation, answer for that situation, and say which part of the lesson applies and which part changes.
- Only add a code example if it makes the answer clearer, and make sure it matches what you said.
- Plain words, short paragraphs, under 180 words. Explain any jargon you use. Wrap identifiers in backticks.
- Reply with the answer only.`;
  try {
    const { text } = await sample(prompt, withTrace({ onText: ({ text }) => {
      turn.a = leaks(text) ? LEAKED : text;
      const el = document.getElementById("aa-" + i);
      if (el && cur && cur.id === id) el.innerHTML = fmt(turn.a);
    } }, { feature: "ask_lesson", lesson_id: id, step: STEPS[cur.step], question: turn.q, session: thread.session,
           exercise_fn: fn, word_limit: 180, chip, guard: guarded ? "solution_request" : "", request: turn.request, ...(retryOf ? { retry_of: retryOf } : {}) }));
    turn.a = text;
    if (leaks(text)) { turn.a = LEAKED; turn.failed = true; }
  } catch (e) {
    if (e && e.code === "not_granted") { sample = null; sampleOff = true; document.body.classList.add("no-ai"); }
    turn.a = e && e.code === "rate_limited" ? "Too many requests right now. Wait a minute, then try again." : (e && e.code === "asleep" && e.text) || "The answer didn't come through. Try again in a moment.";
    turn.failed = true;
  }
  turn.streaming = false;
  if (!turn.failed) askLast = { id, request: turn.request, q: turn.q, at: Date.now(), sent: {} };
  setAskBusy(false);
  if (cur && cur.id === id) renderAskThread();
}
async function saveAsk(i) {
  const L = LESSONS[cur.id], turn = (askThreads[cur.id] || [])[i];
  if (!turn || turn.saved || turn.failed || turn.streaming) return;
  const it = await addItem(turn.q + " (" + L.title + ")", "Ask · " + L.title, "text");
  await updateItem(it.id, { explanation: turn.a });
  turn.saved = true; renderAskThread(); toast("Saved to your study list");
  sendFeedback(turn.request, "ask_lesson", "saved", true, "", "code");
}
