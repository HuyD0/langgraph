"""Code checks on a tutor's answer: the parts of "plain" and "concise" no judge should have to read for.

Five AI judges disagreed most on the checklist's "plain" check, because it had no definition. These
rules give it one, in code, so every judge (and every run) measures the same thing:

- ``grade``: a readability grade from sentence and word length (the Flesch-Kincaid grade: roughly the
  school year needed to read it comfortably). ``hard_to_read`` when it is over :data:`MAX_GRADE`.
- ``fillers``: openers that say nothing ("Great question", "Certainly").
- ``repeated``: sentences that appear twice.
- ``unexplained_terms``: course glossary terms the answer uses that neither the lesson's own text nor
  the answer explains (a gloss in brackets, or "that is"/"which means"/"called" in the same sentence).
- ``unknown_numbers`` and ``unknown_names``: numbers, and capitalised words that are not sentence starts,
  that the lesson's text does not contain. Made-up facts cluster there, so these are the spans to read.
- ``over_word_limit`` against the limit the question allows.

``quality_checks`` returns them all, plus ``blocking``: the rules whose failure should stop an answer
(:data:`BLOCKING`); the rest are reported for a person to read. The judge still decides whether the
answer is right; these only say whether it is readable and stays inside the lesson.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

MAX_GRADE = 10.0
FILLERS = ("great question", "good question", "excellent question", "certainly", "absolutely", "of course",
           "happy to help", "let's dive", "i hope this helps", "hope that helps", "sure thing")
BLOCKING = ("over_word_limit", "hard_to_read", "repeated")
# Product and project names the course uses, so they never count as names outside a lesson.
COURSE_NAMES = ("Databricks", "MLflow", "LangGraph", "LangChain", "Azure", "Microsoft", "Foundry", "Python", "Terraform",
                "Spacelift", "Unity", "Catalog", "Delta", "Spark", "OpenAI", "Claude", "GPT", "Lakebase", "Genie", "Postgres",
                "Entra", "GitHub", "Copilot", "Ollama")
PLAIN = {"over_word_limit": "over the word limit", "hard_to_read": "hard to read (long sentences or long words)",
         "repeated": "a sentence is repeated"}
_GLOSS = re.compile(r"\(|\bthat is\b|\bwhich means\b|\bmeans\b|\bcalled\b|\bin other words\b|: ", re.I)
_SENTENCE_END = re.compile(r"(?<=[.!?:])\s+|\n+")   # a line break or a label's colon starts a new sentence too
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def sentences(text: str) -> list[str]:
    plain = re.sub(r"```.*?```", " ", text, flags=re.S)      # code blocks are not prose
    plain = re.sub(r"`[^`]*`", " ", plain)                    # nor inline code
    plain = re.sub(r"[*_#>]+", "", plain)
    plain = re.sub(r"(?m)^\s*(?:[-*]|\d+[.)])\s+", "", plain)  # a bullet or a number starts a line, not a name
    return [s.strip() for s in _SENTENCE_END.split(plain) if s.strip()]


def syllables(word: str) -> int:
    w = word.lower().strip("'-")
    if not w:
        return 0
    groups = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not w.endswith(("le", "ee")) and groups > 1:
        groups -= 1
    return max(1, groups)


def readability_grade(text: str) -> float:
    """Flesch-Kincaid grade level: 0.39 x words per sentence + 11.8 x syllables per word - 15.59."""
    sents = sentences(text)
    words = [w for s in sents for w in _WORD.findall(s)]
    if not sents or not words:
        return 0.0
    return round(0.39 * len(words) / len(sents) + 11.8 * sum(syllables(w) for w in words) / len(words) - 15.59, 1)


def filler_openers(text: str) -> list[str]:
    """Fillers that open the answer or a sentence ("Great question! ..."), not the words inside other phrases."""
    starts = [s.lower() for s in sentences(text)]
    return [f for f in FILLERS if any(re.match(rf"{re.escape(f)}\b", s) for s in starts)]


def repeated_sentences(text: str) -> int:
    seen: dict[str, int] = {}
    for s in sentences(text):
        key = re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()
        if len(key.split()) >= 4:
            seen[key] = seen.get(key, 0) + 1
    return sum(n - 1 for n in seen.values() if n > 1)


def unexplained_terms(text: str, glossary_terms: Iterable[str], lesson_text: str) -> list[str]:
    """Glossary terms the answer uses that the lesson doesn't mention and the answer doesn't explain."""
    lesson_low, out = lesson_text.lower(), []
    for term in glossary_terms:
        t = term.lower()
        if len(t) < 3 or t in lesson_low:
            continue
        for s in sentences(text):
            if re.search(rf"\b{re.escape(t)}\b", s, re.I):
                if not _GLOSS.search(s):
                    out.append(term)
                break
    return sorted(set(out))


def _norm_number(n: str) -> str:
    return n.replace(",", "").rstrip(".")


def unknown_numbers(text: str, lesson_text: str) -> list[str]:
    """Numbers in the answer that the lesson's text doesn't contain (small counts, 1 to 10, are ignored).
    Pass the question's own wording inside ``lesson_text`` too, so a "30-second answer" isn't a stranger."""
    known = {_norm_number(n) for n in _NUMBER.findall(lesson_text)}
    out = []
    for n in _NUMBER.findall(re.sub(r"```.*?```", " ", text, flags=re.S)):
        v = _norm_number(n)
        try:
            if float(v) <= 10:
                continue
        except ValueError:
            pass  # not a plain number (like "1.2.0"): keep it and compare it as written
        if v not in known:
            out.append(n)
    return sorted(set(out))


def unknown_names(text: str, lesson_text: str, allow: Iterable[str] = ()) -> list[str]:
    """Capitalised words that are not sentence starts and are not in the lesson's text (nor allowed)."""
    known = {w.lower() for w in _WORD.findall(lesson_text)} | {a.lower() for a in allow}
    out = set()
    for s in sentences(text):
        words = _WORD.findall(s)
        for w in words[1:]:
            if w[0].isupper() and w.lower() not in known and not w.isupper() and "'" not in w:
                out.add(w)
    return sorted(out)


def quality_checks(text: str, lesson_text: str = "", glossary_terms: Iterable[str] = (), word_limit: int = 200,
                   allow_names: Iterable[str] = COURSE_NAMES) -> dict:
    """Every code check at once. ``True`` on a rule means it was broken; lists hold what to read."""
    words = len(text.split())
    grade = readability_grade(text)
    checks = {
        "words": words, "word_limit": word_limit, "over_word_limit": words > word_limit, "grade": grade, "hard_to_read": grade > MAX_GRADE,
        "fillers": filler_openers(text), "repeated": repeated_sentences(text) > 0,
        "unexplained_terms": unexplained_terms(text, glossary_terms, lesson_text) if lesson_text else [],
        "unknown_numbers": unknown_numbers(text, lesson_text) if lesson_text else [],
        "unknown_names": unknown_names(text, lesson_text, allow_names) if lesson_text else [],
    }
    checks["blocking"] = [name for name in BLOCKING if checks[name]]
    return checks


def why_blocked(checks: dict) -> str:
    """The blocking rules an answer broke, in plain words, for the drafter's second try."""
    parts = []
    for name in checks.get("blocking", []):
        extra = f" ({checks['words']} words, limit {checks.get('word_limit', 200)})" if name == "over_word_limit" else \
                f" (grade {checks['grade']}, keep it under {MAX_GRADE:.0f})" if name == "hard_to_read" else ""
        parts.append(PLAIN[name] + extra)
    return "; ".join(parts)


def glossary_terms(data: dict) -> list[str]:
    """Every term in the course's glossary (``build_data()['glossary']``)."""
    return [term for _, terms in data.get("glossary", []) for term, _ in terms]
