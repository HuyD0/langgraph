"""The coach-retrieval lab's own code: pairs, frozen splits, the honest test, embedding setups, measures and logging.

Learning material: nothing here runs in CI. Long code lives here so the notebook cells stay short.

    cd notebooks/learning/coach_retrieval && uv run python retrieval.py smoke

**What is being measured.** When a learner asks the coach a question, retrieval must find the Learn
paragraphs of the right lesson. The haystack is every Learn paragraph (``build_corpus``); the needles are
questions with a known lesson (``build_pairs``). A setup scores a hit when one of the lesson's paragraphs is
among the five closest (recall@5), and a stricter hit when the closest paragraph is the lesson's (hit@1).

**The champion, said plainly.** Today's coach does *not* retrieve with embeddings: the page tells it which
lesson the learner is on. So for the retrieval step the champion is ``bge-large`` as its makers ship it, with
its search prompt (recall@5 0.84 on 150 Check questions, PR #170). A fine-tune has to earn a place where the
lesson is *not* known: a study-list follow-up, the blueprint's coach, Claude's tools without a lesson.

**The known flaw in the easy test, and the honest one.** Check questions are written from the Learn text, so
they share its words; a word-matching rule does well on them. ``build_honest_test`` has a local model rewrite
each dev and test question the way a junior developer would type it, and records how many of its content
words still appear in the lesson, so the notebook can show the paraphrases are a harder, fairer test. Every
paraphrase is model-made and marked ``checked: 0`` until a person reads it.

Reuses the app's own ``drill.embedding_compare`` (corpus, Ollama embeddings, ranking, the paired test) and the
course's ``wilson`` and ``mcnemar`` through ``tracking``. Nothing leaves this computer: Ollama, the local
MLflow server and a model already in the Hugging Face cache.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import tracking
from drill import embedding_compare as ec
from drill.embedding_compare import BGE_QUERY, GEMMA_DOC, GEMMA_QUERY, ollama_embed, paired, rank, unit  # noqa: F401

HERE = Path(__file__).resolve().parent
DATA = tracking.DATA
OLLAMA = ec.OLLAMA
# torch prints a one-line note about output redirects when sentence-transformers loads; it names the operating system and
# means nothing here, so it is kept out of the notebooks' saved output (the logger is set before the import happens).
logging.getLogger("torch.distributed.elastic.multiprocessing.redirects").setLevel(logging.ERROR)
K = 5
SEED = 7
SPLITS = ("train", "dev", "test", "holdout")
SHARES = {"train": 0.6, "dev": 0.2, "test": 0.1, "holdout": 0.1}
LOCKED = "holdout"   # scored once, at the very end; every scorer needs yes_holdout=True to touch it
PARAPHRASE_MODEL = "qwen3:14b"
PARAPHRASE_PROMPT = ("Rewrite this quiz question as a short question a junior developer might type to a coach, "
                     "in their own everyday words, without the technical terms. Give one rewrite only, nothing else.\n\n"
                     "Quiz question: {question}\n\nRewrite:")
# Small words that carry no topic; dropped before counting which of a question's words appear in the lesson.
STOPWORDS = set("""a an the and or but if so of to in on at by for from with without into onto as is are was were be been
being am do does did done have has had having it its this that these those there here what which who whom whose when
where why how not no yes you your yours we our ours they them their i me my mine he she his her him can could should
would will shall may might must about above after again all also any because before between both each few more most
other over own same some such than then too very up down out off just only now one two first next last get got make
made use used using want wants need needs say says said ask asks asked tell tells told know knows let lets thing
things way ways kind sort like really still even ever back much many well""".split())


# -- 1. pairs: a question with its known lesson ---------------------------------------------------------------------

def build_corpus(data: dict) -> list[dict]:
    """Every Learn paragraph, one chunk each: ``{id, lesson, module, text}`` (the app's own ``embedding_compare.corpus``)."""
    return ec.corpus(data)


def build_pairs(data: dict) -> list[dict]:
    """Every question with a known right lesson: ``{id, lesson, module, question, source}``.

    ``source`` is ``check`` (the lesson's own Check question), ``more`` (its extra practice questions) or
    ``prepared`` (the coach's prepared question chips). The right answer for every pair is the lesson's Learn
    paragraphs in ``build_corpus``. Identical questions (same words, ignoring case and spacing) are kept once
    within a lesson; a question that appears under two or more *different* lessons is dropped altogether, because
    on its own it has no single right lesson. Three prepared chips are like that ("why does this matter?", "when
    does this stop working?", "how would I spot it going wrong?": they only make sense on the page that shows
    them), which is why there are far fewer prepared pairs than chips; ``ambiguous_questions`` lists them. Check
    and more questions keep the same ids as ``embedding_compare.questions`` (``lesson?0``, ``lesson?1`` ...) so the
    two harnesses can be cross-read.

    Prepared pairs also carry ``chip``: ``term`` ("what does X mean here?"), ``option`` ("why not <a wrong answer>?"),
    or the chip's own key. Finding from the smoke run (2026-11-08, 328 dev questions, bge-large): Check and more
    questions are found 0.84 to 0.88 of the time, term chips 0.81, option chips 0.45. An option chip quotes a wrong
    answer and names no topic, so it only makes sense beside the question the learner just saw; the notebooks
    should look at that group apart, or leave it out of the retrieval test and say why.
    """
    module_of = {lid: m["id"] for m in data["modules"] for lid in m["lessons"]}
    lessons_of: dict[str, set[str]] = defaultdict(set)
    raw: list[dict] = []
    for lid, lesson in data["lessons"].items():
        asks = [lesson.get("check")] + list(lesson.get("more") or [])
        for i, ask in enumerate(asks):
            if ask:
                raw.append({"id": f"{lid}?{i}", "lesson": lid, "question": ask[0], "source": "check" if i == 0 else "more"})
    for lid, chips in (data.get("prepared") or {}).items():
        for chip, qa in chips.items():
            if isinstance(qa, dict) and qa.get("q"):
                kind = "term" if chip == "learn:term" else "option" if re.fullmatch(r"check:\d+:\d+", chip) else chip
                raw.append({"id": f"{lid}?prepared:{chip}", "lesson": lid, "question": qa["q"], "source": "prepared", "chip": kind})
    for p in raw:
        p["question"] = " ".join((p["question"] or "").split())
        if p["question"]:
            lessons_of[p["question"].lower()].add(p["lesson"])
    seen: set[str] = set()
    pairs: list[dict] = []
    for p in raw:
        key = p["question"].lower()
        if not key or len(lessons_of[key]) > 1 or key in seen:
            continue
        seen.add(key)
        pairs.append({"id": p["id"], "lesson": p["lesson"], "module": module_of.get(p["lesson"], ""), "question": p["question"],
                      "source": p["source"], "chip": p.get("chip", "")})
    return pairs


def ambiguous_questions(data: dict) -> list[dict]:
    """The questions ``build_pairs`` dropped because they appear under more than one lesson: ``{question, lessons}``,
    most widespread first. Useful to show why "why does this matter?" is not a retrieval test."""
    lessons_of: dict[str, set[str]] = defaultdict(set)
    for lid, lesson in data["lessons"].items():
        for ask in [lesson.get("check")] + list(lesson.get("more") or []):
            if ask:
                lessons_of[" ".join(ask[0].split()).lower()].add(lid)
    for lid, chips in (data.get("prepared") or {}).items():
        for qa in chips.values():
            if isinstance(qa, dict) and qa.get("q"):
                lessons_of[" ".join(qa["q"].split()).lower()].add(lid)
    return sorted(({"question": q, "lessons": sorted(l)} for q, l in lessons_of.items() if len(l) > 1), key=lambda x: -len(x["lessons"]))


def content_fingerprint(corpus: list[dict], pairs: list[dict]) -> str:
    """A short code that changes when any paragraph or question changes (``embedding_compare.fingerprint``), so runs
    on different content are never compared as if they were the same test."""
    return ec.fingerprint(corpus, [{"id": p["id"], "text": p["question"]} for p in pairs])


def sample_pairs(pairs: list[dict], n: int, seed: int = SEED) -> list[dict]:
    """Exactly ``n`` pairs, each module in proportion to its size (``embedding_compare.sample``, which rounds each
    module up to at least one, then trimmed in the same seeded hash order so the count is exact)."""
    picked = ec.sample(pairs, n, seed)
    if len(picked) > n:
        key = lambda p: hashlib.sha256(f"{seed}:{p['id']}".encode()).hexdigest()
        keep = set(p["id"] for p in sorted(picked, key=key)[:n])
        picked = [p for p in picked if p["id"] in keep]
    return picked


def lesson_text(corpus: list[dict]) -> dict[str, str]:
    """Each lesson's Learn paragraphs joined into one text, for the word checks."""
    out: dict[str, list[str]] = defaultdict(list)
    for c in corpus:
        out[c["lesson"]].append(c["text"])
    return {lid: "\n".join(parts) for lid, parts in out.items()}


# -- 2. splits by whole lesson, frozen ----------------------------------------------------------------------------

def _deal(n: int) -> list[str]:
    """How many lessons of a module go to each split, as a list of labels in dealing order.

    Shares 60/20/10/10. A module with 4 or more lessons has at least one lesson in each of train, dev and test
    (a topic that is never tested is never measured); a smaller module fills train, then dev, then train again,
    because training data is what the fine-tune needs most and dev is where it is watched. Whole lessons after the
    guaranteed ones go to the split whose share is furthest behind.
    """
    if n < 4:
        return ["train", "dev", "train"][:n]
    counts = {s: int(SHARES[s] * n) for s in SPLITS}
    for s in ("train", "dev", "test"):
        counts[s] = max(1, counts[s])
    while sum(counts.values()) > n:  # only when the minimums overshoot a tiny module: take from train
        counts["train"] -= 1
    while sum(counts.values()) < n:
        behind = max(SPLITS, key=lambda s: (SHARES[s] * n - counts[s], -SPLITS.index(s)))
        counts[behind] += 1
    return [s for s in SPLITS for _ in range(counts[s])]


def split_lessons(data: dict, seed: int = SEED) -> dict[str, str]:
    """Deal every lesson to one of train / dev / test / holdout: ``{lesson_id: split}``.

    Why by whole lesson: a lesson's questions and its paragraphs must land in the *same* split, or the model is
    tested on paragraphs it was trained to match, which is leakage (the course's "Splits that don't move"). Why
    within each module: a module is a topic, and stratifying keeps every topic in every split, so the dev and
    test scores say something about the whole course and the weakest module can be read. The order is a seeded
    hash of each lesson's id, so the same seed deals the same way on every computer. It does **not** survive a
    content change: a lesson added, removed or renamed changes the order and the counts, so its neighbours move
    to other splits too (checked: one new lesson in a 7-lesson module moved three existing ones, one of them out of
    holdout). That is why ``freeze_splits`` refuses to redeal by accident, and why a redeal on purpose makes every
    earlier score non-comparable. Shares 60/20/10/10; see ``_deal`` for the small-module rule.
    """
    out: dict[str, str] = {}
    for m in data["modules"]:
        lessons = [lid for lid in m["lessons"] if lid in data["lessons"]]
        key = lambda lid: hashlib.sha256(f"{seed}:{lid}".encode()).hexdigest()
        for lid, split in zip(sorted(lessons, key=key), _deal(len(lessons))):
            out[lid] = split
    return out


def split_counts(splits: dict[str, str]) -> dict[str, int]:
    """How many lessons in each split, in the fixed order train, dev, test, holdout."""
    c = Counter(splits.values())
    return {s: c.get(s, 0) for s in SPLITS}


def freeze_splits(data: dict, seed: int = SEED, path: Path | str = DATA / "splits.json", force: bool = False) -> dict[str, str]:
    """Write the splits to ``data/splits.json`` once, and refuse to change the file afterwards.

    Frozen means frozen: if the file exists and its splits differ from what ``split_lessons`` would deal now
    (a new seed, or any content change: a lesson added, removed or renamed moves other lessons too), this raises
    instead of overwriting, because every score logged so far was on the old split. Pass ``force=True`` to redeal on
    purpose: it prints every lesson that moved (old split -> new split) so the run that follows can say so, and every
    earlier score stops being comparable. The file also keeps the seed, the time and the rule, so a reader can tell how
    it was made. Returns the frozen splits.
    """
    path = Path(path)
    fresh = split_lessons(data, seed)
    if path.exists():
        frozen = json.loads(path.read_text())
        if frozen.get("splits") == fresh:
            return frozen["splits"]
        if not force:
            raise RuntimeError(f"{path} is frozen and differs from a fresh deal (seed {seed}). Scores so far used the frozen file; "
                               f"pass force=True only to redeal on purpose, and log why.")
        old = frozen.get("splits", {})
        moved = sorted((lid, old.get(lid, "(new)"), fresh.get(lid, "(gone)")) for lid in set(old) | set(fresh) if old.get(lid) != fresh.get(lid))
        print(f"REDEAL on purpose (force=True): {len(moved)} lessons change split; every score logged before this is no longer comparable.")
        for lid, was, now in moved:
            print(f"  {lid}: {was} -> {now}")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"seed": seed, "frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                "rule": "by whole lesson, within each module, seeded hash order, 60/20/10/10; "
                                        "modules with 4+ lessons have at least one in train, dev and test; "
                                        "smaller modules fill train, dev, train",
                                "counts": split_counts(fresh), "splits": fresh}, indent=1))
    return fresh


def load_splits(path: Path | str = DATA / "splits.json") -> dict[str, str]:
    """Read the frozen splits back: ``{lesson_id: split}``. Raises FileNotFoundError, with what to run, when nothing is frozen yet."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist: no split is frozen yet. freeze_splits(build_data()) deals and writes it "
                                f"(00_vet.ipynb and 01_pairs.ipynb both call it).")
    return json.loads(path.read_text())["splits"]


def pairs_in(pairs: list[dict], splits: dict[str, str], which=("dev",), yes_holdout: bool = False) -> list[dict]:
    """The pairs whose lesson is in one of ``which`` splits. Asking for holdout needs ``yes_holdout=True``:
    it is scored once, at the end, and every look before that makes it a little less honest."""
    which = (which,) if isinstance(which, str) else tuple(which)
    if LOCKED in which and not yes_holdout:
        raise PermissionError("the holdout split is locked: pass yes_holdout=True only for the final, once-only score")
    return [p for p in pairs if splits.get(p["lesson"]) in which]


def chunks_in(corpus: list[dict], splits: dict[str, str], which) -> list[dict]:
    """The paragraphs whose lesson is in one of ``which`` splits (the haystack always stays the whole course when
    scoring; this is for training pairs and the leakage checks)."""
    which = (which,) if isinstance(which, str) else tuple(which)
    return [c for c in corpus if splits.get(c["lesson"]) in which]


def _norm(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())


def leakage_checks(pairs: list[dict], corpus: list[dict], splits: dict[str, str], near: float = 0.9) -> list[dict]:
    """The checks a split must pass before anything is scored on it: ``[{check, passed, detail}, ...]``.

    1. Every lesson that has a question or a paragraph is in exactly one split (the whole-lesson rule).
    2. No question's words appear verbatim inside a paragraph of *another* split (a copied question would let the
       model memorise the answer in training and be rewarded for it in dev).
    3. Near-duplicate paragraphs across splits: two paragraphs whose TF-IDF cosine is at least ``near`` (0.9: almost
       the same words in almost the same proportions). Why 0.9: a copy of a paragraph with one word in ten deleted still
       scores about 0.97 (one with a word in ten swapped for another course word, about 0.88), while the two closest
       different paragraphs across the splits score 0.67, so the line catches copies that are nearly word for word and
       leaves alone paragraphs that only share a topic; no real pair comes near it, so any line from 0.7 to 0.9 would
       give the same answer here. Recaps repeat earlier lessons on purpose, so a
       few are expected; they are listed with their lesson pairs so the notebook can decide whether to move a lesson.
    4. The holdout split is locked: its size is reported, and any scorer needs ``yes_holdout=True`` to touch it.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    checks = []
    lessons = {p["lesson"] for p in pairs} | {c["lesson"] for c in corpus}
    missing = sorted(l for l in lessons if l not in splits)
    checks.append({"check": "every lesson is in exactly one split", "passed": not missing,
                   "detail": f"{len(lessons)} lessons with questions or paragraphs; counts {split_counts(splits)}"
                             + (f"; not in any split: {missing}" if missing else "")})

    by_split_text = defaultdict(list)
    for c in corpus:
        by_split_text[splits.get(c["lesson"])].append((_norm(c["text"]), c))
    copied = []
    for p in pairs:
        q = _norm(p["question"])
        if len(q.split()) < 4:
            continue
        for s, items in by_split_text.items():
            if s == splits.get(p["lesson"]):
                continue
            for text, c in items:
                if q in text:
                    copied.append({"question": p["id"], "in_paragraph": c["id"], "splits": [splits.get(p["lesson"]), s]})
    checks.append({"check": "no question appears verbatim in another split's paragraphs", "passed": not copied,
                   "detail": f"{len(pairs)} questions checked against {len(corpus)} paragraphs" + (f"; copies: {copied}" if copied else "")})

    texts = [c["text"] for c in corpus]
    x = TfidfVectorizer(sublinear_tf=True, stop_words="english").fit_transform(texts)
    sims = (x @ x.T).toarray()
    np.fill_diagonal(sims, 0.0)
    dupes = []
    for i, j in zip(*np.where(np.triu(sims) >= near)):
        a, b = corpus[i], corpus[j]
        if splits.get(a["lesson"]) != splits.get(b["lesson"]):
            dupes.append({"paragraphs": [a["id"], b["id"]], "lessons": [a["lesson"], b["lesson"]],
                          "splits": [splits.get(a["lesson"]), splits.get(b["lesson"])], "cosine": round(float(sims[i, j]), 3)})
    checks.append({"check": f"near-duplicate paragraphs across splits (TF-IDF cosine >= {near})", "passed": not dupes,
                   "detail": f"{len(dupes)} pairs" + (f": {dupes}" if dupes else " (none)")})

    held = [l for l, s in splits.items() if s == LOCKED]
    checks.append({"check": "holdout is locked", "passed": True,
                   "detail": f"{len(held)} lessons, {sum(splits.get(p['lesson']) == LOCKED for p in pairs)} questions; "
                             f"scoring on it needs yes_holdout=True and happens once, at the end"})
    return checks


# -- 3. the honest test: questions in a learner's own words --------------------------------------------------------

def paraphrase(question: str, model: str = PARAPHRASE_MODEL, seed: int | None = None, temperature: float = 0.7) -> str:
    """Ask a local model (Ollama) to rewrite a quiz question the way a junior developer would type it to a coach.
    One rewrite, no thinking tokens, no streaming. About 1.5 s per question with qwen3:14b on this computer."""
    options = {"temperature": temperature}
    if seed is not None:
        options["seed"] = seed
    body = json.dumps({"model": model, "prompt": PARAPHRASE_PROMPT.format(question=question), "stream": False,
                       "think": False, "options": options}).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/generate", body, {"Content-Type": "application/json"})  # noqa: S310 - local Ollama
    with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310  # nosec B310 - local Ollama
        text = json.loads(r.read())["response"]
    text = text.strip().split("\n")[0].strip().strip('"“”\'').strip()
    return re.sub(r"^(rewrite|question)\s*:\s*", "", text, flags=re.I).strip()


def content_words(text: str) -> list[str]:
    """The words that carry topic: letters only, lower case, small common words dropped."""
    return [w for w in re.findall(r"[a-z][a-z\-]+", text.lower()) if w not in STOPWORDS and len(w) > 2]


def word_overlap(text: str, lesson: str) -> float:
    """The share of ``text``'s content words that also appear in the lesson's Learn text (0 to 1). High means the
    question borrows the lesson's own words, which makes retrieval easy; a learner's words share fewer."""
    words = content_words(text)
    if not words:
        return 0.0
    have = set(content_words(lesson))
    return round(sum(w in have for w in words) / len(words), 3)


def build_honest_test(pairs: list[dict], splits: dict[str, str], which=("dev", "test"), per_question: int = 1,
                      cache: Path | str = DATA / "paraphrases.json", *, sources=("check", "more"), corpus: list[dict] | None = None,
                      model: str = PARAPHRASE_MODEL, max_questions: int | None = None, yes_holdout: bool = False,
                      progress: bool = True) -> list[dict]:
    """Learner-worded versions of the dev and test questions: pairs with ``source: "paraphrase"``.

    Each new pair carries the original's id (``orig``) and question (``orig_question``), the paraphrase, and two
    numbers: ``word_overlap`` (the share of the paraphrase's content words found in its lesson's Learn text) and
    ``orig_word_overlap`` (the same for the original), so the notebook can show that paraphrases share fewer
    words. Every paraphrase is model-made (``model``) and ``checked: 0`` until a person reads it (``1`` once read and
    kept; a rewrite a person rejected is dropped by the notebook). ``checked`` is a number, not True/False, on purpose:
    MLflow's dataset digest ignores True/False columns, and a person's verdicts must change the digest. Results are
    cached by question id in ``cache``, so a rerun costs nothing and only new questions are sent to the model;
    questions go in a stable order (sorted by id) with a progress print. Holdout is locked here too.
    Budget: about 1.2 s a question after the model loads. Only Check and more questions are rewritten by default
    (``sources``): they are the ones written from the Learn text; the prepared chips were already written the way a
    learner asks, and adding them (about 350 more in dev and test) would triple the time. ``max_questions`` caps a
    first try.
    """
    if corpus is None:
        from drill.content import build_data

        corpus = build_corpus(build_data())
    text_of = lesson_text(corpus)
    sources = (sources,) if isinstance(sources, str) else tuple(sources)
    chosen = sorted((p for p in pairs_in(pairs, splits, which, yes_holdout=yes_holdout) if p["source"] in sources), key=lambda p: p["id"])
    if max_questions:
        chosen = chosen[:max_questions]
    cache = Path(cache)
    store: dict[str, list[dict]] = json.loads(cache.read_text()) if cache.exists() else {}
    todo = [p for p in chosen if len([e for e in store.get(p["id"], []) if e.get("model") == model]) < per_question]
    if progress:
        print(f"honest test: {len(chosen)} questions in {which}; {len(chosen) - len(todo)} cached, {len(todo)} to paraphrase with {model}")
    t0 = time.monotonic()
    for n, p in enumerate(todo, 1):
        entries = store.setdefault(p["id"], [])
        have = len([e for e in entries if e.get("model") == model])
        for i in range(have, per_question):
            entries.append({"text": paraphrase(p["question"], model=model, seed=SEED + i), "model": model, "seed": SEED + i,
                            "made_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "checked": False})
        cache.parent.mkdir(exist_ok=True)
        cache.write_text(json.dumps(store, indent=1, ensure_ascii=False))
        if progress and (n % 10 == 0 or n == len(todo)):
            print(f"  {n}/{len(todo)} · {time.monotonic() - t0:.0f} s")
    out = []
    for p in chosen:
        entries = [e for e in store.get(p["id"], []) if e.get("model") == model][:per_question]
        for i, e in enumerate(entries):
            out.append({"id": f"{p['id']}~{i}", "lesson": p["lesson"], "module": p["module"], "question": e["text"],
                        "source": "paraphrase", "orig": p["id"], "orig_source": p["source"], "orig_question": p["question"],
                        "word_overlap": word_overlap(e["text"], text_of.get(p["lesson"], "")),
                        "orig_word_overlap": word_overlap(p["question"], text_of.get(p["lesson"], "")),
                        "model": model, "checked": int(bool(e.get("checked", False)))})
    return out


def record_checks(verdicts: dict[str, bool | None], cache: Path | str = DATA / "paraphrases.json", model: str = PARAPHRASE_MODEL,
                  by: str = "a person") -> dict:
    """Write verdicts on paraphrases into the cache and report the state of every check so far.

    ``by`` names who judged (``"a person"``, or ``"Claude"`` when the owner asked the assistant to do it): it is kept
    on each entry as ``checked_by`` and counted in the returned ``by``, so a report can say honestly who read them.

    ``verdicts`` maps an honest-test id (``orig~i``) to True (the rewrite keeps the question's meaning), False (it
    does not) or None (not looked at yet; nothing is written). A marked entry gets ``checked: True`` and ``ok``.
    Returns ``{checked, agreed, not_ok, unmarked, not_ok_ids}`` over the whole cache for ``model``, so a notebook
    can say how much of the honest test a person has read, and drop the rewrites that failed. Until ``checked``
    equals the test's size, the honest test is model-made and must be described that way.
    """
    cache = Path(cache)
    store: dict[str, list[dict]] = json.loads(cache.read_text()) if cache.exists() else {}
    for hid, verdict in verdicts.items():
        if verdict is None or "~" not in hid:
            continue
        orig, i = hid.rsplit("~", 1)
        entries = [e for e in store.get(orig, []) if e.get("model") == model]
        if int(i) < len(entries):
            entries[int(i)]["checked"] = True
            entries[int(i)]["ok"] = bool(verdict)
            entries[int(i)]["checked_by"] = by
    cache.parent.mkdir(exist_ok=True)
    cache.write_text(json.dumps(store, indent=1, ensure_ascii=False))
    checked = agreed = unmarked = 0
    not_ok_ids = []
    by_whom: dict[str, int] = {}
    for orig, entries in store.items():
        for i, e in enumerate(e for e in entries if e.get("model") == model):
            if e.get("checked"):
                checked += 1
                who = e.get("checked_by", "a person")
                by_whom[who] = by_whom.get(who, 0) + 1
                if e.get("ok"):
                    agreed += 1
                else:
                    not_ok_ids.append(f"{orig}~{i}")
            else:
                unmarked += 1
    return {"checked": checked, "agreed": agreed, "not_ok": len(not_ok_ids), "unmarked": unmarked, "not_ok_ids": not_ok_ids,
            "by": by_whom, "checked_by_person": sum(n for who, n in by_whom.items() if who == "a person")}


# -- 4. embedding setups --------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Setup:
    """One way of turning text into vectors.

    ``how``: ``local`` (sentence-transformers on this computer's GPU, the way training will run), ``ollama`` (the
    app's own path), or ``tfidf`` (a word-count table: the "could a fixed rule do it" baseline). ``query_prefix``
    goes before each question (the makers' search prompt); ``doc_prefix`` before each paragraph. ``dims`` keeps only
    the first numbers of each vector (None: all of them).
    """
    name: str
    how: str
    model: str
    query_prefix: str = ""
    dims: int | None = None
    doc_prefix: str = ""


TFIDF = Setup("tf-idf words · fixed rule", "tfidf", "tfidf word 1-2 grams")
CHAMPION = Setup("bge-large · local · with prompt", "local", "BAAI/bge-large-en-v1.5", BGE_QUERY)
CHAMPION_OLLAMA = Setup("bge-large · ollama · with prompt", "ollama", "bge-large", BGE_QUERY)
GEMMA = Setup("embeddinggemma 768 · ollama · with prompt", "ollama", "embeddinggemma", GEMMA_QUERY, None, GEMMA_DOC)


@dataclass
class Embedded:
    """Unit vectors (one row per text) and how long they took, so speed is logged beside quality."""
    vectors: np.ndarray
    seconds: float
    setup: Setup
    kind: str

    def __len__(self) -> int:
        return len(self.vectors)


_LOCAL: dict[str, object] = {}
_TFIDF: dict[str, object] = {}


def best_device() -> str:
    """The fastest place to run a model on this computer: the GPU when there is one."""
    import torch

    return "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"


def local_model(name: str):
    """Load a sentence-transformers model once and keep it (loading is the slow part)."""
    if name not in _LOCAL:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")  # the model is already in the cache; nothing leaves this computer
        os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
        try:  # the "Loading weights" bar is a notebook widget whose random id looks like an application id
            from transformers.utils import logging as hf_logging
            hf_logging.disable_progress_bar()
        except Exception:  # noqa: BLE001
            pass
        from sentence_transformers import SentenceTransformer

        _LOCAL[name] = SentenceTransformer(name, device=best_device())
    return _LOCAL[name]


def embed_setup(setup: Setup, texts: list[str], kind: str, batch: int = 32) -> Embedded:
    """Turn texts into unit vectors with one setup; ``kind`` is ``doc`` (paragraphs) or ``query`` (questions).

    The prefix for that kind is added here, so callers pass bare text. For ``tfidf`` the word table is fitted on
    the documents, so embed the corpus (``kind="doc"``) before the queries. Time taken is returned alongside.
    """
    if kind not in ("doc", "query"):
        raise ValueError("kind must be 'doc' or 'query'")
    prefix = setup.query_prefix if kind == "query" else setup.doc_prefix
    full = [prefix + t for t in texts]
    model = local_model(setup.model) if setup.how == "local" else None  # loading is not embedding: keep it off the clock
    t0 = time.monotonic()
    if setup.how == "ollama":
        vectors = ollama_embed(setup.model, full, batch)
    elif setup.how == "local":
        vectors = model.encode(full, batch_size=batch, normalize_embeddings=True, convert_to_numpy=True)
    elif setup.how == "tfidf":
        from sklearn.feature_extraction.text import TfidfVectorizer

        if kind == "doc":
            _TFIDF[setup.name] = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit(texts)
        elif setup.name not in _TFIDF:
            raise RuntimeError("tfidf: embed the corpus (kind='doc') first; the word table is fitted on it")
        vectors = _TFIDF[setup.name].transform(texts).toarray()
    else:
        raise ValueError(f"unknown how: {setup.how!r}")
    seconds = time.monotonic() - t0
    return Embedded(unit(vectors, setup.dims), round(seconds, 3), setup, kind)


# -- 5. measures ----------------------------------------------------------------------------------------------------

def score(q_vecs, d_vecs, corpus: list[dict], pairs: list[dict], k: int = K, splits: dict[str, str] | None = None,
          yes_holdout: bool = False) -> tuple[list[dict], dict]:
    """Rank every paragraph for every question and read off the measures: ``(rows, summary)``.

    ``rows`` has one line per question (hit, first rank, top-k chunk ids, source). ``summary`` has ``hit_at_1``
    and ``recall_at_k`` with their Wilson 95% ranges (the course's "How many examples do you need?" and "Margins near
    0% and 100%"), ``mrr`` (how high the first right paragraph sits, averaged), ``by_module`` weakest first, the weakest
    module and its recall, and ``n``.

    The holdout lock is not opt-in: when ``splits`` is not given, the frozen ``data/splits.json`` is read, and scoring
    a holdout question without ``yes_holdout=True`` is refused either way. When holdout *is* scored on purpose, the active
    MLflow run (if any) gets the tag ``holdout_scored=true``, so the once-only use is visible in the record.
    """
    q_vecs = q_vecs.vectors if isinstance(q_vecs, Embedded) else q_vecs
    d_vecs = d_vecs.vectors if isinstance(d_vecs, Embedded) else d_vecs
    if splits is None and (DATA / "splits.json").exists():
        splits = load_splits()
    touches_holdout = splits is not None and any(splits.get(p["lesson"]) == LOCKED for p in pairs)
    if touches_holdout and not yes_holdout:
        raise PermissionError("the holdout split is locked: pass yes_holdout=True only for the final, once-only score")
    if touches_holdout:
        import mlflow

        if mlflow.active_run():
            mlflow.set_tag("holdout_scored", "true")
    rows = rank(q_vecs, d_vecs, corpus, pairs, k)
    for r, p in zip(rows, pairs):
        r["source"] = p.get("source", "")
        r["chip"] = p.get("chip", "")
        r["question"] = p.get("question", "")
    return rows, summarise(rows, k)


def summarise(rows: list[dict], k: int = K) -> dict:
    """The numbers from a set of ranked rows (see ``score``)."""
    n = len(rows)
    hits = sum(r["hit"] for r in rows)
    firsts = sum(r["first_rank"] == 1 for r in rows)
    p5, low5, high5 = tracking.wilson(hits, n)
    p1, low1, high1 = tracking.wilson(firsts, n)
    mods = ec.by_module(rows)
    table = sorted(({"module": m, "found": h, "n": c, "recall": round(h / c, 3)} for m, (h, c) in mods.items()),
                   key=lambda x: (x["recall"], -x["n"]))
    return {"n": n, "hit_at_1": p1, "hit_at_1_low": low1, "hit_at_1_high": high1,
            f"recall_at_{k}": p5, f"recall_at_{k}_low": low5, f"recall_at_{k}_high": high5,
            "mrr": sum(1 / r["first_rank"] for r in rows if r["first_rank"]) / n if n else 0.0,
            "by_module": table, "weakest_module": table[0]["module"] if table else "",
            "weakest_module_recall": table[0]["recall"] if table else 0.0}


def compare(rows_a: list[dict], rows_b: list[dict], n_boot: int = 2000, seed: int = SEED, k: int = K) -> dict:
    """Two setups on the same questions: the paired counts and McNemar's p (the course's "Comparing on the same
    examples"), plus the gap in recall@k (second minus first) with a bootstrap 95% range made by redrawing the questions
    with replacement ``n_boot`` times. The range says how much the gap could move with a different draw of
    questions; if it straddles zero, the win could be luck.
    """
    if [r["id"] for r in rows_a] != [r["id"] for r in rows_b]:
        by_id = {r["id"]: r for r in rows_b}
        rows_b = [by_id[r["id"]] for r in rows_a]
    a = np.array([r["hit"] for r in rows_a], dtype=float)
    b = np.array([r["hit"] for r in rows_b], dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(a), size=(n_boot, len(a)))
    gaps = (b[idx] - a[idx]).mean(axis=1)
    return paired(rows_a, rows_b) | {"n": len(a), f"gap_recall_at_{k}": float(b.mean() - a.mean()),
                                     f"gap_low": float(np.percentile(gaps, 2.5)), f"gap_high": float(np.percentile(gaps, 97.5)),
                                     "n_boot": n_boot}


def model_size_mb(setup: Setup) -> float | None:
    """The size of a local model's weights file in the Hugging Face cache (MB), or None when it is not a local file
    (Ollama keeps its own copy: ``ollama show <model>`` says; a TF-IDF table is a few MB and has no file)."""
    if setup.how != "local":
        return None
    try:
        from huggingface_hub import try_to_load_from_cache

        total = 0
        for name in ("model.safetensors", "pytorch_model.bin"):
            path = try_to_load_from_cache(setup.model, name)
            if isinstance(path, str) and os.path.exists(path):
                total += os.path.getsize(os.path.realpath(path))
        return round(total / 1e6, 1) if total else None
    except Exception:  # noqa: BLE001 - a missing size is reported as None, never a crash
        return None


def cost_and_speed(setup: Setup, seconds_corpus: float, seconds_queries: float, n_queries: int, model_size_mb: float | None = None) -> dict:
    """Speed and cost beside quality, so the trade-off reads from one table (the course's "How big should a vector be?";
    the README calls the habit "Cost, speed, quality").

    ``ms_per_question`` is the time to embed one question (what a learner waits for), from the one pass that scored the
    set, so it moves by a few ms from pass to pass; ``speed_passes`` is the careful measurement for the bar.
    ``seconds_to_embed_course`` is the one-off cost of indexing every paragraph. ``model_size_mb`` is looked up for local models when not given.
    The ``usd_*`` numbers are placeholders at 0.0: Databricks prices (DBU for the GPU, tokens for a hosted model)
    are filled in at stage 8, when the same run goes to the workspace.
    """
    size = model_size_mb if model_size_mb is not None else globals()["model_size_mb"](setup)
    return {"ms_per_question": round(1000 * seconds_queries / max(1, n_queries), 2),
            "seconds_to_embed_course": round(seconds_corpus, 2), "seconds_queries": round(seconds_queries, 2),
            "n_queries": n_queries, "model_size_mb": size,
            "usd_per_1k_questions": 0.0, "usd_to_embed_course": 0.0,
            "cost_note": "usd placeholders: Databricks prices are filled in at stage 8"
                         + ("" if size is not None else f"; model_size_mb is None for how={setup.how!r} (no local weights file to measure)")}


# -- 6. logging ---------------------------------------------------------------------------------------------------

def _numbers(d: dict, prefix: str = "") -> dict[str, float]:
    return {prefix + k: float(v) for k, v in d.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}


def log_setup_run(setup: Setup, summary: dict, speed_cost: dict, datasets: list, description: str, parent_run_id: str | None = None,
                  tags: dict | None = None, rows: list[dict] | None = None, run_name: str | None = None, k: int = K) -> str:
    """One MLflow run per setup, in the style of ``embedding_compare.run``: params are the setup's fields, metrics are every
    number in ``summary`` and ``speed_cost`` plus ``recall_at_k.<module>`` for each module, the ranked rows go in as a
    JSON artifact, the datasets through ``mlflow.log_input``, and the tags say which computer and commit produced it.
    Nested under ``parent_run_id`` when given. Returns the run id.
    """
    import mlflow

    name = run_name or f"{setup.name} · recall@{k} · {summary.get('n', '?')} questions"
    all_tags = {"kind": "coach_retrieval_lab", "git_commit": tracking.git_commit(), "mlflow.note.content": description,
                "weakest_module": summary.get("weakest_module", ""),
                **{f"computer.{k_}": str(v) for k_, v in tracking.this_computer().items()}, **(tags or {})}
    with mlflow.start_run(run_name=name, nested=parent_run_id is not None, parent_run_id=parent_run_id, tags=all_tags) as run:
        mlflow.log_params({k_: (v if v not in ("", None) else "(none)") for k_, v in asdict(setup).items()})
        metrics = _numbers(summary) | _numbers(speed_cost)
        metrics.update({f"recall_at_{k}.{m['module']}": float(m["recall"]) for m in summary.get("by_module", [])})
        mlflow.log_metrics(metrics)
        mlflow.log_dict({"summary": summary, "speed_cost": speed_cost}, "summary.json")
        if summary.get("by_module"):
            mlflow.log_table({key: [m[key] for m in summary["by_module"]] for key in ("module", "found", "n", "recall")}, "recall_by_module.json")
        if rows is not None:
            mlflow.log_dict(rows, "rows.json")
        for ds in datasets:
            mlflow.log_input(ds)
        return run.info.run_id


# -- 7. baselines: several setups on several question sets, one table ---------------------------------------------

NO_PROMPT = Setup("bge-large · local · no prompt", "local", "BAAI/bge-large-en-v1.5")   # the common mistake: the makers' search prompt left out
BASELINE_SETUPS = (TFIDF, CHAMPION, CHAMPION_OLLAMA, NO_PROMPT, GEMMA)


def ollama_model_size_mb(model: str) -> float | None:
    """The size of an Ollama model's file on this computer (MB), from Ollama's own list; None when it is not there."""
    try:
        with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=10) as r:  # noqa: S310  # nosec B310 - local Ollama
            models = json.loads(r.read())["models"]
    except Exception:  # noqa: BLE001 - a missing size is reported as None, never a crash
        return None
    want = model if ":" in model else f"{model}:latest"
    for m in models:
        if m.get("name") in (model, want):
            return round(m["size"] / 1e6, 1)
    return None


def size_mb(setup: Setup) -> float | None:
    """Model size for any setup: the local weights file, Ollama's copy, or None for a TF-IDF table (a few MB, no file)."""
    return ollama_model_size_mb(setup.model) if setup.how == "ollama" else model_size_mb(setup)


def evaluate_setup(setup: Setup, corpus: list[dict], question_sets: dict[str, list[dict]], splits: dict[str, str] | None = None,
                   k: int = K, progress: bool = True) -> dict:
    """One setup on several question sets, the corpus embedded once.

    Returns ``{"doc": Embedded, "sets": {name: {"query": Embedded, "rows", "summary", "speed_cost"}}}``. The corpus is
    embedded first (TF-IDF fits its word table on it), then each set's questions; every set gets its own ``speed_cost``
    because milliseconds per question is measured on that set's questions.
    """
    t0 = time.monotonic()
    doc = embed_setup(setup, [c["text"] for c in corpus], "doc")
    size = size_mb(setup)
    out = {"doc": doc, "sets": {}}
    for name, pairs in question_sets.items():
        q = embed_setup(setup, [p["question"] for p in pairs], "query")
        rows, summary = score(q, doc, corpus, pairs, k, splits)
        out["sets"][name] = {"query": q, "rows": rows, "summary": summary,
                             "speed_cost": cost_and_speed(setup, doc.seconds, q.seconds, len(pairs), size)}
    if progress:
        parts = " · ".join(f"{name} recall@{k} {s['summary'][f'recall_at_{k}']:.2f}" for name, s in out["sets"].items())
        print(f"{setup.name:40} corpus {doc.seconds:6.1f} s · {parts} · {time.monotonic() - t0:.0f} s in all")
    return out


def results_table(results: dict[str, dict], set_name: str, k: int = K):
    """The headline table for one question set: a row per setup with quality, the weakest module, speed and size."""
    import pandas as pd

    rows = []
    for name, res in results.items():
        s, c = res["sets"][set_name]["summary"], res["sets"][set_name]["speed_cost"]
        weakest = s["by_module"][0] if s["by_module"] else {"module": "", "found": 0, "n": 0}
        rows.append({"setup": name, "n": s["n"],
                     f"recall@{k}": s[f"recall_at_{k}"], "low": s[f"recall_at_{k}_low"], "high": s[f"recall_at_{k}_high"],
                     "hit@1": s["hit_at_1"], "hit@1 low": s["hit_at_1_low"], "hit@1 high": s["hit_at_1_high"], "mrr": s["mrr"],
                     "weakest module": f"{weakest['module']} ({weakest['found']}/{weakest['n']})",
                     "ms/question": c["ms_per_question"], "s to embed course": c["seconds_to_embed_course"], "model MB": c["model_size_mb"]})
    return pd.DataFrame(rows).set_index("setup")


def by_group_table(results: dict[str, dict], set_name: str, group=lambda r: r["chip"] or r["source"], k: int = K, ranges: bool = True):
    """Recall@k per setup and per group of question (by default: check, more, term, option, ...), with the group sizes.

    With ``ranges`` (the default) each cell reads ``0.81 [0.62, 0.91]``: the share and its Wilson 95% range, because a
    group of 26 questions says much less than a group of 174 and the point alone hides that. ``ranges=False`` gives the
    bare numbers for plotting.
    """
    import pandas as pd

    table = {}
    sizes = Counter()
    for name, res in results.items():
        groups: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for r in res["sets"][set_name]["rows"]:
            g = group(r)
            groups[g][0] += r["hit"]
            groups[g][1] += 1
        if ranges:
            table[name] = {g: "{:.2f} [{:.2f}, {:.2f}]".format(*tracking.wilson(h, n)) for g, (h, n) in groups.items()}
        else:
            table[name] = {g: round(h / n, 3) for g, (h, n) in groups.items()}
        sizes = Counter({g: n for g, (h, n) in groups.items()})
    df = pd.DataFrame(table).T
    df.columns = [f"{g} (n={sizes[g]})" for g in df.columns]
    return df


def versus_champion(results: dict[str, dict], champion: str, set_name: str, k: int = K, n_boot: int = 2000, seed: int = SEED):
    """Every other setup paired against the champion on one question set: the questions only one found, McNemar's p, the gap
    (other minus champion) with its bootstrap range, and a plain reading of the range.

    The reading is per row, at the 5% level, with no allowance for how many rows there are. That matters: with several
    challengers on several sets, one "shown" result among them is what luck alone produces fairly often (the chance of at
    least one fluke, the family-wise error rate: ``family_wise_error_rate``), so a reading here is a lead to confirm on
    test, and only the one pre-registered challenger-against-champion test at stage 4 is held to 0.05 on its own.
    ``df.attrs["comparisons"]`` counts the rows that are real comparisons (a row with no disagreements, such as the same
    model served two ways, is an identity check).
    """
    import pandas as pd

    rows = []
    for name, res in results.items():
        if name == champion:
            continue
        cmp = compare(results[champion]["sets"][set_name]["rows"], res["sets"][set_name]["rows"], n_boot, seed, k)
        shown = ("other better" if cmp["gap_low"] > 0 else "champion better" if cmp["gap_high"] < 0 else "not shown")
        rows.append({"setup": name, "only champion found": cmp["only_first"], "only this found": cmp["only_second"],
                     "McNemar p": cmp["p_value"], f"gap recall@{k}": cmp[f"gap_recall_at_{k}"], "gap low": cmp["gap_low"],
                     "gap high": cmp["gap_high"], "reading": shown})
    df = pd.DataFrame(rows).set_index("setup")
    df.attrs["comparisons"] = int(sum((r["only champion found"] + r["only this found"]) > 0 for r in rows))
    return df


def family_wise_error_rate(comparisons: int, level: float = 0.05) -> float:
    """The chance of at least one fluke (the family-wise error rate): how often at least one of ``comparisons`` tests
    comes out under ``level`` when nothing really differs. In words: the chance that one test does *not* fluke is one
    minus ``level``; the chance that none of them do is that number multiplied together once for each comparison (six
    copies of 0.95 for six looks); one minus that is the chance that at least one does. Six looks at the 5% level give
    about 0.26. This treats the tests as independent; looks that share the same questions overlap, so the real chance is
    somewhat lower, and 0.26 is the cautious figure. Say this beside any "shown"
    that was one of several looks (the course's "Testing many variants" and "Telling real gains from noise")."""
    return round(1 - (1 - level) ** comparisons, 3)


def speed_passes(setup: Setup, texts: list[str], kind: str = "query", passes: int = 5, batch: int = 32) -> dict:
    """Milliseconds per text over several repeated passes on the same texts, for the speed line of the bar.

    One pass moves by a few ms with the GPU's warm-up and how Ollama batches, so a single number cannot be compared to
    another single number. This embeds the same ``texts`` ``passes`` times (same batch size, model load off the clock)
    and reports the median, the fastest and the slowest pass, and the spread (slowest minus fastest), which is the
    smallest difference that can be told from noise on this computer. Everything needed to repeat it is in the result:
    ``n_texts``, ``passes``, ``batch``, ``kind``.
    """
    ms = []
    for _ in range(passes):
        e = embed_setup(setup, texts, kind, batch)
        ms.append(1000 * e.seconds / max(1, len(texts)))
    ms_sorted = sorted(ms)
    return {"ms_per_question_median": round(float(np.median(ms)), 2), "ms_per_question_min": round(ms_sorted[0], 2),
            "ms_per_question_max": round(ms_sorted[-1], 2), "ms_spread": round(ms_sorted[-1] - ms_sorted[0], 2),
            "ms_each_pass": [round(m, 2) for m in ms], "passes": passes, "n_texts": len(texts), "batch": batch, "kind": kind,
            "setup": setup.name}


def vector_agreement(a, b) -> dict:
    """How alike two sets of unit vectors for the same texts are: the cosine between each matching pair, its mean and its
    lowest value (1.0 means identical direction). Used to show the served model and the local one are the same model."""
    a = a.vectors if isinstance(a, Embedded) else np.asarray(a)
    b = b.vectors if isinstance(b, Embedded) else np.asarray(b)
    cos = (a * b).sum(axis=1)
    return {"n": int(len(cos)), "mean_cosine": round(float(cos.mean()), 4), "min_cosine": round(float(cos.min()), 4)}


def log_extra_set(run_id: str, prefix: str, summary: dict, speed_cost: dict, rows: list[dict] | None = None, k: int = K) -> None:
    """Add a second question set's numbers to an existing setup run under ``prefix`` (e.g. ``honest.recall_at_5``), with its
    rows and per-module table as artifacts, so one child run per setup holds both the easy and the honest numbers."""
    import mlflow

    with mlflow.start_run(run_id=run_id, nested=True):
        metrics = _numbers(summary, f"{prefix}.") | _numbers(speed_cost, f"{prefix}.")
        metrics.update({f"{prefix}.recall_at_{k}.{m['module']}": float(m["recall"]) for m in summary.get("by_module", [])})
        mlflow.log_metrics(metrics)
        mlflow.set_tag(f"{prefix}.weakest_module", summary.get("weakest_module", ""))
        mlflow.log_dict({"summary": summary, "speed_cost": speed_cost}, f"{prefix}_summary.json")
        if rows is not None:
            mlflow.log_dict(rows, f"{prefix}_rows.json")


# -- the smoke run: does every piece work together? ---------------------------------------------------------------

SMOKE_DESCRIPTION = """**Smoke test of retrieval.py, not a result.** Checks that every piece of the lab's code module works together: pairs
from the course, the frozen lesson splits (seed {seed}, written to data/splits.json), the leakage checks, two embedding setups
(a TF-IDF word table as the fixed-rule baseline, and the champion bge-large loaded locally on {device} with its search prompt),
the measures and the paired comparison, each logged as a child run.

**Data:** {chunks} Learn paragraphs searched (the whole course, always); {n} dev questions, a module-stratified sample (seed {seed})
of the {dev} dev-split questions (so not every module is in it; the per-module metrics here are from one or two questions each). {pairs} pairs in all ({sources}); splits by lesson {counts}. Leakage checks: {checks}.

**Read nothing into the numbers:** 20 questions give a Wilson range about 30 points wide, and Check questions share words
with the Learn text, so the word-table baseline looks better here than it would on learner-worded questions (the honest test
in 02_baselines). Reproduce: `cd notebooks/learning/coach_retrieval && uv run python retrieval.py smoke`."""


def smoke(n: int = 20) -> dict:
    """Build everything once on a few dev questions and log it as the run "smoke · retrieval.py"."""
    import mlflow

    from drill.content import build_data

    t_all = time.monotonic()
    data = build_data()
    pairs, corpus = build_pairs(data), build_corpus(data)
    splits = freeze_splits(data, SEED)
    checks = leakage_checks(pairs, corpus, splits)
    for c in checks:
        print(("ok  " if c["passed"] else "LOOK") + f" {c['check']}: {c['detail'][:160]}")
    dev = pairs_in(pairs, splits, "dev")
    qs = sample_pairs(dev, n, SEED)
    sources = Counter(p["source"] for p in pairs)
    print(f"{len(pairs)} pairs {dict(sources)}; {len(corpus)} paragraphs; splits {split_counts(splits)}; {len(dev)} dev questions, {len(qs)} sampled")

    tracking.connect()
    desc = SMOKE_DESCRIPTION.format(seed=SEED, device=best_device(), chunks=len(corpus), n=len(qs), dev=len(dev), pairs=len(pairs),
                                    sources=", ".join(f"{k} {v}" for k, v in sources.items()), counts=split_counts(splits),
                                    checks="; ".join(f"{c['check']}: {'ok' if c['passed'] else 'look'}" for c in checks))
    ds_q = tracking.table_dataset(qs, f"dev questions · {len(qs)} smoke sample · seed {SEED}", targets="lesson")
    ds_c = tracking.table_dataset(corpus, f"learn paragraphs · {len(corpus)} · fingerprint {content_fingerprint(corpus, pairs)}")
    results = {}
    with mlflow.start_run(run_name="smoke · retrieval.py", tags={"kind": "coach_retrieval_lab", "purpose": "smoke",
                                                                "git_commit": tracking.git_commit(), "mlflow.note.content": desc}) as parent:
        mlflow.log_params({"k": K, "seed": SEED, "n_questions": len(qs), "chunks": len(corpus), "pairs": len(pairs), "split": "dev",
                           "content_fingerprint": content_fingerprint(corpus, pairs)})
        mlflow.log_dict(checks, "leakage_checks.json")
        mlflow.log_artifact(str(DATA / "splits.json"))
        mlflow.log_dict({"pairs_by_source": dict(sources), "lessons_by_split": split_counts(splits),
                         "pairs_by_split": dict(Counter(splits.get(p["lesson"]) for p in pairs))}, "counts.json")
        for setup in (TFIDF, CHAMPION):
            d = embed_setup(setup, [c["text"] for c in corpus], "doc")
            q = embed_setup(setup, [p["question"] for p in qs], "query")
            rows, summary = score(q, d, corpus, qs, K, splits)
            sc = cost_and_speed(setup, d.seconds, q.seconds, len(qs))
            run_id = log_setup_run(setup, summary, sc, [ds_q, ds_c],
                                   f"Smoke child run: {setup.name} on {len(qs)} dev questions (part of the parent smoke run; not a result). "
                                   f"Corpus embedded in {d.seconds} s, questions in {q.seconds} s.", parent.info.run_id, rows=rows)
            results[setup.name] = {"rows": rows, "summary": summary, "speed_cost": sc, "run_id": run_id}
            print(f"{setup.name}: recall@{K} {summary[f'recall_at_{K}']:.2f} [{summary[f'recall_at_{K}_low']:.2f}, {summary[f'recall_at_{K}_high']:.2f}] "
                  f"hit@1 {summary['hit_at_1']:.2f} mrr {summary['mrr']:.2f} · corpus {d.seconds}s · {sc['ms_per_question']} ms/question "
                  f"· weakest {summary['weakest_module']} {summary['weakest_module_recall']:.2f} · size {sc['model_size_mb']} MB")
        cmp = compare(results[TFIDF.name]["rows"], results[CHAMPION.name]["rows"])
        mlflow.log_dict(cmp, "comparison.json")
        mlflow.log_metrics({"gap_recall_at_5": cmp[f"gap_recall_at_{K}"], "gap_low": cmp["gap_low"], "gap_high": cmp["gap_high"],
                            "mcnemar_p": cmp["p_value"], "seconds_total": round(time.monotonic() - t_all, 1)})
        print(f"compare tfidf -> bge: {cmp}")
    print(f"smoke done in {time.monotonic() - t_all:.0f} s")
    return {"pairs": len(pairs), "splits": split_counts(splits), "checks": checks, "compare": cmp,
            "summaries": {k_: v["summary"] for k_, v in results.items()}, "speed_cost": {k_: v["speed_cost"] for k_, v in results.items()}}


if __name__ == "__main__":
    if sys.argv[1:] == ["smoke"]:
        smoke()
    else:
        print(__doc__)
