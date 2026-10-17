"""Prepared answers for the tutor's standard questions, so "Ask about this lesson" works with no model.

    uv run drill tutor prepare --profile DEFAULT --module use-case      # draft, judge and save one module
    uv run drill tutor prepare --profile DEFAULT                        # every lesson still missing or out of date
    uv run drill tutor prepared                                         # how many are ready, failed or stale

The page's suggested questions ("When does this stop working?", "Why not B?"...) are the same for
every learner of a lesson, so their answers can be written ahead: a strong model drafts each one
from the lesson, a second model judges it against a checklist, and only the ones that pass go into
the page. The owner spot-checks a sample (``drill tutor prepared --sample``). Each answer keeps a
fingerprint of the lesson text it was written from; when the lesson changes, the answer stops being
served until it is drafted again.

:func:`chips` must ask the same questions, in the same words, as ``askChips()`` in
``page/ask.js``: the page serves a prepared answer only when its question matches the chip exactly,
so a mismatch falls back to the live tutor rather than showing the wrong answer.
``tests/test_tutor_prepared.py`` checks they agree.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Callable

DIR = Path(__file__).parent / "content" / "prepared"
DRAFT_MODEL = "databricks-claude-opus-5-5"
JUDGE_MODEL = "databricks-claude-sonnet-5-5"  # a different model from the drafter, so it isn't grading its own work

LEARNER = ("The learner is new to coding and is learning AI engineering: Databricks for agents, LangGraph, LangChain and "
           "MLflow, plus Terraform for Azure Databricks. Explain any jargon in plain words. Never use Big-O notation; say "
           "things like \"it walks through the list once\" instead. Short sentences. Encouraging but not gushing. Wrap "
           "identifiers in backticks.")


# -- the questions: the same as askChips() in page/ask.js -------------------------------------

def _short(s: str, n: int = 90) -> str:
    return s[: n - 1] + "…" if len(s) > n else s


def _quoted(t: str) -> str:
    return "“" + _short(re.sub(r"\*\*|`", "", t), 48) + "”"


def _gotchas(data: dict) -> dict[str, dict]:
    out = {}
    for cards in (data["aiGotchas"], data["iacGotchas"], data["rules"]):
        for title, why, _bad, _good, where in cards:
            if not where.startswith("build:"):
                out[where] = {"title": title, "why": why}
    return out


def _learn_chip(lesson: dict, gloss: set[str]) -> tuple[str, str]:
    text = " ".join(lesson["learn"])
    bold = list(dict.fromkeys(m[2:-2] for m in re.findall(r"\*\*[^*]+\*\*", text)))
    bold = [t for t in bold if len(t.split()) <= 3 and len(t) <= 28 and not re.search(r"[\"“”\[\]()]", t)]
    sentences = [s for para in lesson["learn"] for s in re.split(r"(?<=[.!?])\s+", para)]
    pair = next((ts for ts in ([t for t in bold if f"**{t}**" in s] for s in sentences) if len(ts) >= 2), None)
    one = next((t for t in bold if t.lower() in gloss), None) or next((t for t in bold if len(t) >= 6 or re.search(r"\s", t)), None)
    terms = pair[:2] if pair else [one] if one else []
    if len(terms) == 2:
        return (f"How is {_quoted(terms[0])} different from {_quoted(terms[1])}?",
                f"Contrast {terms[0]} and {terms[1]} as this lesson uses them: what each one is, how they differ, and how they work together, with an everyday comparison and the lesson's example.")
    if terms:
        return (f"What does {_quoted(terms[0])} mean here?",
                f"Explain {terms[0]} as this lesson uses it: an everyday comparison first, then where it appears in the lesson's example.")
    return ("Why does this matter?", "Explain why this lesson's idea matters: what goes wrong without it, in one short, realistic example. Plain words.")


def chips(data: dict) -> dict[str, list[dict]]:
    """For each lesson, the suggested questions whose answers can be prepared: ``{key, step, q, how}``.

    Left out: Quiz me and "Give me a harder one" (a conversation, checked live), and "Is my sentence
    right?" (about the learner's own words)."""
    gloss = {term.lower() for _, terms in data["glossary"] for term, _ in terms}
    gotchas = _gotchas(data)
    out: dict[str, list[dict]] = {}
    for lid, lesson in data["lessons"].items():
        if not lesson.get("learn") or lesson.get("pack"):  # a pack lesson's Ask asks live, from its own material
            continue
        q, how = _learn_chip(lesson, gloss)
        items = [
            {"key": "learn:term", "step": "Learn", "q": q, "how": how},
            {"key": "learn:stops", "step": "Learn", "q": "When does this stop working?",
             "how": "Give 2 or 3 concrete situations where this lesson's rule or method changes, breaks, or needs extra care: for example an LLM or RAG app instead of a trained model, data that changes over time, very little data, or a much bigger system. For each, say what to do instead. Keep each to two or three sentences. No code."},
            {"key": "learn:spot", "step": "Learn", "q": "How would I spot it going wrong?",
             "how": "Describe the warning signs that this lesson's idea was skipped or done wrong: what they would see in their numbers, logs, traces or results (for example a score that looks too good and then drops in real use). Then the quickest check to confirm it. No code."},
        ]
        for qi, check in enumerate([lesson["check"], *(lesson.get("more") or [])]):
            question, options, answer = check[0], check[1], check[2]
            for k, option in enumerate(options):
                if k != answer:
                    items.append({"key": f"check:{qi}:{k}", "step": "Check", "q": f"Why not {_quoted(option)}?",
                                  "how": f"In the lesson's Check question (\"{question}\"), explain in plain words why \"{option}\" is not the best answer: what it gets right, if anything, and what it misses. Then say in one sentence what makes \"{options[answer]}\" better."})
        items.append({"key": "explain:interview", "step": "Explain", "q": f"How do I explain {_quoted(lesson['angle'][0])} in an interview?",
                      "how": "Give a 30-second spoken answer in three short parts: the problem, the idea, and one trade-off or edge case. Then one follow-up question an interviewer might ask, with a hint at a strong answer."})
        if lid in gotchas:
            g = gotchas[lid]
            items.append({"key": "explain:gotcha", "step": "Explain", "q": f"Why does {_quoted(g['title'])} matter?",
                          "how": f"This lesson's gotcha is \"{g['title']}\": {g['why']} Explain in plain words what goes wrong in real work when it is ignored, with one small example."})
        out[lid] = items
    return out


# -- the prompt: the tutor's own, as page/ask.js builds it ---------------------------------------

def _context(data: dict, lid: str) -> str:
    lesson = data["lessons"][lid]
    problem = next((p for p in data["bank"] if p["id"] == lid), {})
    module = next((m for m in data["modules"] if lid in m["lessons"]), {})
    stack = lesson.get("stack")
    exercise = (f"The lesson's coding exercise: {problem.get('title')}, writing `{problem['fn']}`. {problem['prompt'].splitlines()[0]}"
                if problem.get("fn") else f"The lesson's practice: {problem.get('prompt', '')}")
    return "\n".join(filter(None, [
        f"Lesson: {lesson['title']}", "What the lesson says:", "\n".join(lesson["learn"]),
        f"Its example ({lesson['example'][0]}):", lesson["example"][1],
        f"In their stack ({stack[0]}):\n{stack[1]}" if stack else "",
        f"Interview angle: {lesson['angle'][0]}. {lesson['angle'][1]}", exercise,
        f"Setting (every example, question and harder question stays in it): {module['setting']}" if module.get("setting") else "",
    ]))


def prompt(data: dict, lid: str, chip: dict) -> str:
    fn = next((p.get("fn") for p in data["bank"] if p["id"] == lid), "") or ""
    return f"""You are a patient tutor helping with one lesson of an AI engineering course. {LEARNER}

{_context(data, lid)}

They are on the {chip['step']} step of the lesson.
Their message: {chip['q']}
How to answer: {chip['how']}
Rules:
- This answer is written ahead and shown to every learner who taps this question, so don't refer to anything they said before, and don't ask them to reply.
- Stay on this lesson's topic.
- Never write code for the lesson's coding exercise (`{fn}`), not even part of it, and don't list what its answer would contain.
- {"Before the Check step is answered, never say which option of its questions is right." if chip['step'] != "Check" else "The Check question is already answered, so you may say which option is right."}
- Only add a code example if it makes the answer clearer, and make sure it matches what you said.
- Plain words, short paragraphs, under 180 words. Explain any jargon you use. Wrap identifiers in backticks.
- Reply with the answer only."""


JUDGE = """You check a tutor's answer before it is shown to beginners. Be strict.

{context}

The question the learner tapped: {q}
How it should be answered: {how}

The tutor's answer:
---
{answer}
---

Check each, using only the lesson above as the truth:
1. correct: nothing in it is wrong or contradicts the lesson.
2. answers_it: it answers the question as asked.
3. plain: plain words, jargon explained, no Big-O or maths notation, under about 200 words.
4. no_giveaway: it does not write or list the coding exercise's solution{giveaway}.
5. standalone: it makes sense to anyone who taps the question (no "as you said", no request to reply).

Reply with JSON only: {{"correct": true|false, "answers_it": true|false, "plain": true|false, "no_giveaway": true|false, "standalone": true|false, "notes": "one sentence on the biggest problem, or empty"}}"""


def fingerprint(data: dict, lid: str, chip: dict) -> str:
    """What the answer was written from: the lesson's text and the question. A change means draft it again."""
    lesson = data["lessons"][lid]
    basis = json.dumps([lesson.get(k) for k in ("title", "learn", "example", "angle", "check", "more", "stack")] + [chip["q"], chip["how"]],
                       ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(basis.encode()).hexdigest()[:16]


# -- storage: one file per module ------------------------------------------------------------------

def _module_of(data: dict) -> dict[str, str]:
    return {lid: m["id"] for m in data["modules"] for lid in m["lessons"]}


def load(directory: Path = DIR) -> dict[str, dict[str, dict]]:
    """Every prepared answer: ``{lesson_id: {key: record}}``."""
    out: dict[str, dict] = {}
    for path in sorted(directory.glob("*.json")):
        out.update(json.loads(path.read_text()))
    return out


def save(data: dict, answers: dict[str, dict[str, dict]], directory: Path = DIR) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    by_module: dict[str, dict] = {}
    for lid, records in answers.items():
        by_module.setdefault(_module_of(data).get(lid, "other"), {})[lid] = dict(sorted(records.items()))
    for mid, lessons in by_module.items():
        (directory / f"{mid}.json").write_text(json.dumps(dict(sorted(lessons.items())), ensure_ascii=False, indent=1) + "\n")


def served(data: dict, answers: dict | None = None) -> dict[str, dict[str, dict]]:
    """What the page carries: answers that passed, weren't rejected, and still match their lesson."""
    answers = load() if answers is None else answers
    out: dict[str, dict] = {}
    for lid, items in chips(data).items():
        for chip in items:
            rec = answers.get(lid, {}).get(chip["key"])
            if rec and rec.get("status") in ("passed", "checked") and rec.get("q") == chip["q"] and rec.get("fingerprint") == fingerprint(data, lid, chip):
                out.setdefault(lid, {})[chip["key"]] = {"q": rec["q"], "a": rec["a"]}
    return out


def status(data: dict, answers: dict | None = None) -> dict[str, int]:
    answers = load() if answers is None else answers
    counts = {"questions": 0, "ready": 0, "missing": 0, "stale": 0, "failed": 0, "rejected": 0, "checked": 0}
    for lid, items in chips(data).items():
        for chip in items:
            counts["questions"] += 1
            rec = answers.get(lid, {}).get(chip["key"])
            if not rec:
                counts["missing"] += 1
            elif rec.get("q") != chip["q"] or rec.get("fingerprint") != fingerprint(data, lid, chip):
                counts["stale"] += 1
            elif rec.get("status") in ("passed", "checked"):
                counts["ready"] += 1
                counts["checked"] += rec["status"] == "checked"
            else:
                counts[rec.get("status", "failed") if rec.get("status") in ("failed", "rejected") else "failed"] += 1
    return counts


# -- drafting and judging --------------------------------------------------------------------------

def _verdict(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    try:
        v = json.loads(m.group(0)) if m else {}
    except ValueError:
        v = {}
    checks = {k: bool(v.get(k)) for k in ("correct", "answers_it", "plain", "no_giveaway", "standalone")}
    return {**checks, "pass": all(checks.values()), "notes": str(v.get("notes", ""))[:300]}


def prepare_one(data: dict, lid: str, chip: dict, draft: Callable[[str], str], judge: Callable[[str], str],
                draft_model: str = DRAFT_MODEL, judge_model: str = JUDGE_MODEL) -> dict:
    """Draft one answer and judge it; one redraft with the judge's note if it fails."""
    fn = next((p.get("fn") for p in data["bank"] if p["id"] == lid), "") or ""
    giveaway = "" if chip["step"] == "Check" else ", and does not say which option of the lesson's Check questions is right"
    ask = prompt(data, lid, chip)
    verdict: dict = {}
    answer = ""
    for attempt in range(2):
        note = f"\n\nA reviewer rejected your last draft: {verdict['notes']} Fix that." if attempt and verdict.get("notes") else ""
        answer = draft(ask + note).strip()
        verdict = _verdict(judge(JUDGE.format(context=_context(data, lid), q=chip["q"], how=chip["how"], answer=answer,
                                              giveaway=f" (`{fn}`)" + giveaway if fn else giveaway)))
        if verdict["pass"]:
            break
    return {"q": chip["q"], "a": answer, "step": chip["step"], "fingerprint": fingerprint(data, lid, chip),
            "status": "passed" if verdict["pass"] else "failed", "model": draft_model, "judge": {"model": judge_model, **verdict}}


def databricks_chat(model: str, profile: str | None) -> Callable[[str], str]:
    """A plain prompt-in, text-out call to a Databricks serving endpoint, signed with the CLI login."""
    import httpx
    from databricks.sdk.config import Config
    from openai import OpenAI

    from drill.server.router import DatabricksAuth, gateway_base_url

    config = Config(profile=profile) if profile else Config()
    client = OpenAI(base_url=gateway_base_url(config.host, model), api_key="databricks",
                    http_client=httpx.Client(auth=DatabricksAuth(config), timeout=180), max_retries=3)

    def call(text: str) -> str:
        reply = client.chat.completions.create(model=model, messages=[{"role": "user", "content": text}], max_tokens=8000)  # room to reason first: the newest models do
        content = reply.choices[0].message.content or ""
        if isinstance(content, list):  # newer Claude endpoints answer in blocks: keep the text ones
            content = "".join(b.get("text", "") if isinstance(b, dict) else getattr(b, "text", "") or "" for b in content
                              if (b.get("type") if isinstance(b, dict) else getattr(b, "type", "text")) == "text")
        return content
    return call


def todo(data: dict, answers: dict, module: str | None = None, lesson: str | None = None, redo: bool = False) -> list[tuple[str, dict]]:
    """The questions with no usable answer yet (missing, out of date, or failed), in path order."""
    mods = _module_of(data)
    out = []
    for lid, items in chips(data).items():
        if (module and mods.get(lid) != module) or (lesson and lid != lesson):
            continue
        for chip in items:
            rec = answers.get(lid, {}).get(chip["key"])
            fresh = bool(rec) and rec.get("q") == chip["q"] and rec.get("fingerprint") == fingerprint(data, lid, chip)
            if redo or not fresh or rec.get("status") == "failed":  # a rejected answer stays rejected until --redo
                out.append((lid, chip))
    return out


def run(data: dict, work: list[tuple[str, dict]], draft: Callable, judge: Callable, answers: dict,
        workers: int = 6, on_done: Callable[[str, dict, dict], None] | None = None, **models: str) -> dict:
    """Prepare ``work`` a few at a time, saving after each module's worth so a stop loses little."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(prepare_one, data, lid, chip, draft, judge, **models): (lid, chip) for lid, chip in work}
        for n, fut in enumerate(as_completed(futures), 1):
            lid, chip = futures[fut]
            try:
                rec = fut.result()
            except Exception as exc:  # noqa: BLE001 - one bad call shouldn't stop the run
                rec = {"q": chip["q"], "a": "", "step": chip["step"], "fingerprint": fingerprint(data, lid, chip),
                       "status": "failed", "judge": {"pass": False, "notes": f"error: {str(exc)[:200]}"}}
            answers.setdefault(lid, {})[chip["key"]] = rec
            if on_done:
                on_done(lid, chip, rec)
            if n % 25 == 0:
                save(data, answers)
    save(data, answers)
    return answers


def sample(answers: dict, n: int = 50, seed: int = 7) -> list[tuple[str, str, dict]]:
    """For the owner's spot check: every failure, plus ``n`` random passed answers not checked yet."""
    import random

    passed = [(lid, k, r) for lid, recs in answers.items() for k, r in recs.items() if r.get("status") == "passed"]
    failed = [(lid, k, r) for lid, recs in answers.items() for k, r in recs.items() if r.get("status") == "failed"]
    random.Random(seed).shuffle(passed)
    return failed + passed[:n]


def mark(answers: dict, lid: str, key: str, verdict: str) -> None:
    """The owner's call on one answer: ``checked`` (fine) or ``rejected`` (never served)."""
    answers[lid][key]["status"] = verdict
