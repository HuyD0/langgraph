"""Stage 3 of the coach-retrieval lab: fine-tune bge-large on the course, and see what training does.

Learning material: nothing here runs in CI. Long code lives here so the cells of ``03_train.ipynb`` stay short.

    cd notebooks/learning/coach_retrieval && uv run python training.py smoke

**What is trained.** ``bge-large`` (``BAAI/bge-large-en-v1.5``, the champion as its makers ship it) learns from
*training rows*: a question (the **anchor**), the Learn paragraph of its own lesson that answers it (the **positive**),
and a paragraph of a neighbouring lesson that the champion confuses with it (the **hard negative**). The loss is
``MultipleNegativesRankingLoss``, the usual **contrastive** loss for retrieval: in each batch, every question must pick its
own positive out of all the batch's paragraphs (its own hard negative and every other row's paragraphs, the **in-batch
negatives**). It is a multiple-choice test with one right answer per question, scored by cross-entropy.

**Leakage rules, enforced in code** (the course's "Dev, test and holdout sets" and "Splits that don't move"):

* every anchor, positive and hard negative comes from a **train-split** lesson; ``check_rows`` refuses anything else,
  by lesson id *and* by text (a paragraph or question whose words also appear under a dev, test or holdout lesson);
* extra anchors written by a local model (``paraphrase_training_questions``) are rewrites of **train** questions only;
* dev is used to watch the curves and to pick the checkpoint and the settings, nothing else; test stays closed until
  stage 4; holdout stays locked (``retrieval.score`` refuses it without ``yes_holdout=True``).

**What is logged.** One MLflow run per training run, with a readable name (``name_for``), a full description, the train
loss and learning rate at every step, dev recall@5 on the honest and the original questions every ``eval_every`` steps,
the step-0 scores (this model before any training), the best step, seconds per step, peak memory, the datasets with
their digests, the computer and the git commit. Checkpoints go under ``outputs/<run name>/`` (git-ignored); only the
best one keeps its weights, every other one keeps its scores (``checkpoint.json``) and is listed in ``trim.json``.

**What cannot be trained here.** ``embeddinggemma`` is a challenger as its makers ship it (stage 4), never a fine-tune:
its weights are gated on Hugging Face and this computer has no token, so the files cannot be fetched. That is a fact
about access, not about the model.

Nothing leaves this computer: the model is already in the Hugging Face cache (``HF_HUB_OFFLINE=1``), paraphrases come
from Ollama, the runs go to the local MLflow server.
"""

from __future__ import annotations

import contextlib
import functools
import gc
import hashlib
import json
import math
import os
import shutil
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

import retrieval as r
import tracking

HERE = Path(__file__).resolve().parent
DATA = tracking.DATA
OUTPUTS = HERE / "outputs"           # git-ignored: checkpoints and their scores
BASE = "BAAI/bge-large-en-v1.5"      # the champion's weights, as its makers ship them
SHORT_NAME = {BASE: "bge-large"}
SEED = 1101                          # the training seed (the split's seed, 7, is a different thing and never changes)
EVAL_SETS = ("honest", "originals")  # the dev sets watched while training; "honest" picks the checkpoint
PICK_BY = "honest"
SOURCES = ("check", "more", "prepared")
LORA_DEFAULT = {"r": 16, "alpha": 32, "dropout": 0.1}
P_BAR = 0.05                         # stage 2's bar: McNemar p under 0.05 AND the paired bootstrap range above zero, both

# torch prints a one-line note about output redirects on this operating system when it loads; it means nothing here.
import logging  # noqa: E402

logging.getLogger("torch.distributed.elastic.multiprocessing.redirects").setLevel(logging.ERROR)


# -- small helpers --------------------------------------------------------------------------------------------------

def fmt_lr(lr: float) -> str:
    """A learning rate the way people write it: 2e-5, 1e-4, 3e-6 (not 2e-05)."""
    mantissa, exponent = f"{lr:.0e}".split("e")
    return f"{mantissa}e{int(exponent)}"


def name_for(kind: str = "full", lr: float = 2e-5, seed: int = SEED, base: str = BASE, extra: str = "") -> str:
    """The lab's run name for a training run: ``train · bge-large · full · lr 2e-5 · seed 1101`` (``extra`` is appended
    after another ``·``, e.g. ``"3 epochs"``). ``kind`` says what was trained: ``full`` (every weight), ``lora r16``,
    ``overfit on purpose``..."""
    parts = ["train", SHORT_NAME.get(base, base.rsplit("/", 1)[-1]), kind, f"lr {fmt_lr(lr)}", f"seed {seed}"]
    return " · ".join(parts + ([extra] if extra else []))


def _norm(text: str) -> str:
    return " ".join((text or "").lower().split())


def _device() -> str:
    return r.best_device()


def _memory_gb() -> float:
    """What the GPU holds right now, in GB (on a chip with shared memory: what torch's driver has reserved)."""
    import torch

    if torch.backends.mps.is_available():
        return torch.mps.driver_allocated_memory() / 1024**3
    if torch.cuda.is_available():
        return torch.cuda.max_memory_allocated() / 1024**3
    return 0.0


def _free_memory() -> None:
    import torch

    gc.collect()
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    elif torch.cuda.is_available():
        torch.cuda.empty_cache()


def seed_everything(seed: int) -> None:
    """Seed Python's ``random``, numpy and torch in one call (``transformers.set_seed``).

    The same seed gives the same data order and the same starting numbers, but **not bit-identical results on this
    chip**: the GPU adds numbers in an order that can change from run to run, and float rounding depends on that order,
    so two runs with one seed take the same path within floating-point noise, not the same numbers (the Steam lab saw
    the same). That is why a claim about a setting is made across seeds, never from one run."""
    from transformers import set_seed

    set_seed(seed)


def fresh_model(base: str = BASE, *, seed: int = SEED, max_seq: int = 256, lora: dict | None = None):
    """A new copy of the base model for training, on this computer's GPU, in full 32-bit precision (fp32).

    Never train ``retrieval.local_model``'s copy: that one is the champion every score is compared with, kept in memory.

    ``max_seq`` (256) is the **training** length: questions and paragraphs are cut at 256 tokens while training, which
    halves the memory a step needs. The makers' own length (512 for bge-large, what the champion is scored and served at)
    is kept on the model as ``_lab_serve_seq``; ``dev_scores`` and every checkpoint save switch to it (``at_length``), so
    step 0 is exactly the champion and a saved model is served the way the champion is.
    With ``lora`` (``{"r", "alpha", "dropout"}``, optional ``target_modules``), small adapter matrices (**LoRA**, low-rank
    adaptation) are added and only they are trained; the 335 million original weights stay frozen.
    """
    os.environ.setdefault("HF_HUB_OFFLINE", "1")  # the model is in the cache already; nothing is downloaded
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    try:
        from transformers.utils import logging as hf_logging

        hf_logging.disable_progress_bar()
    except Exception:  # noqa: BLE001
        pass
    from sentence_transformers import SentenceTransformer

    seed_everything(seed)
    model = SentenceTransformer(base, device=_device())
    model._lab_serve_seq = model.max_seq_length   # the makers' length (512 for bge-large): scoring and saving use it
    model.max_seq_length = max_seq                # the training length
    if lora:
        from peft import LoraConfig, TaskType

        model.add_adapter(LoraConfig(task_type=TaskType.FEATURE_EXTRACTION, r=int(lora.get("r", 16)),
                                     lora_alpha=int(lora.get("alpha", 32)), lora_dropout=float(lora.get("dropout", 0.1)),
                                     target_modules=list(lora.get("target_modules", ["query", "value"]))))
    return model


@contextlib.contextmanager
def at_length(model, n: int | None):
    """Use ``model`` with inputs cut at ``n`` tokens for a moment (scoring, saving), then go back to the length it had.
    ``None`` changes nothing. In sentence-transformers the length lives on the tokenizer (``model_max_length``), which is
    also what a saved model carries, so a model saved inside this block is loaded back at ``n``."""
    if n is None:
        yield model
        return
    old = model.max_seq_length
    model.max_seq_length = n
    try:
        yield model
    finally:
        model.max_seq_length = old


def serve_length(model) -> int | None:
    """The length a model is scored and saved at: the makers' (``fresh_model`` keeps it), or the model's own when it was
    not made by ``fresh_model``."""
    return getattr(model, "_lab_serve_seq", None) or model.max_seq_length


def ollama_loaded_gb() -> dict[str, float]:
    """The models Ollama holds in memory right now and their sizes (GB). On a chip with shared memory they take from the
    same 24 GB the training run needs (about 11 GB at batch 16, fp32): a 12-14B model loaded by another job is enough to
    make training fail with an out-of-memory error, as the first smoke attempt did (2026-11-08)."""
    import urllib.request

    try:
        with urllib.request.urlopen(f"{r.OLLAMA}/api/ps", timeout=5) as resp:  # noqa: S310  # nosec B310 - local Ollama
            models = json.loads(resp.read()).get("models", [])
    except Exception:  # noqa: BLE001 - Ollama not running: nothing loaded
        return {}
    return {m["name"]: round(m.get("size_vram", m.get("size", 0)) / 1e9, 1) for m in models}


def release_champion() -> None:
    """Drop the champion copy that ``retrieval.local_model`` keeps in memory (1.3 GB), before training needs the room.
    It is reloaded from the cache the next time a setup is embedded (about 10 s)."""
    r._LOCAL.clear()
    _free_memory()


def parameter_counts(model) -> dict:
    """How many numbers the model has, and how many of them training changes."""
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {"params_total": total, "params_trainable": trainable, "trainable_share": trainable / total if total else 0.0,
            "trainable_mb_fp32": round(trainable * 4 / 1e6, 2)}


def folder_mb(path: Path | str) -> float:
    path = Path(path)
    return round(sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1e6, 2) if path.exists() else 0.0


# -- 1. training rows -----------------------------------------------------------------------------------------------

def check_rows(rows: list[dict], corpus: list[dict], splits: dict[str, str], all_pairs: list[dict] | None = None) -> dict:
    """The content check: every text in every row belongs to a **train** lesson, by id and by words. Raises AssertionError.

    By id: the row's lesson, its positive's lesson and each hard negative's lesson are train lessons. By text: a positive
    or negative whose exact words also appear as a paragraph of a non-train lesson fails (a copied paragraph would carry
    dev or test content into training), and, when ``all_pairs`` is given, an anchor whose words are a non-train question
    fails too. The text check compares strings only: it scores nothing, so it does not count as a look at the holdout.
    Returns the counts that were checked.
    """
    lesson_of_chunk = {c["id"]: c["lesson"] for c in corpus}
    lessons_of_text: dict[str, set[str]] = defaultdict(set)
    for c in corpus:
        lessons_of_text[_norm(c["text"])].add(c["lesson"])
    other_questions = {_norm(p["question"]) for p in (all_pairs or []) if splits.get(p["lesson"]) != "train"}
    bad = []
    for row in rows:
        ids = [row["positive_id"], *row["negative_ids"]]
        lessons = {row["lesson"], *(lesson_of_chunk.get(i, "?") for i in ids)}
        if any(splits.get(l) != "train" for l in lessons):
            bad.append((row["id"], "a lesson outside train", sorted(lessons)))
        for text in [row["positive"], *row["negatives"]]:
            if any(splits.get(l) != "train" for l in lessons_of_text.get(_norm(text), {"?"})):
                bad.append((row["id"], "paragraph text also under a non-train lesson (or not in the corpus)", None))
        if _norm(row["anchor"]) in other_questions:
            bad.append((row["id"], "anchor is a dev, test or holdout question", None))
    assert not bad, f"{len(bad)} training rows break the leakage rule, e.g. {bad[:3]}"
    return {"rows_checked": len(rows), "texts_checked": sum(2 + len(x["negatives"]) for x in rows),
            "non_train_questions_compared": len(other_questions), "problems": 0}


def build_training_rows(pairs: list[dict], corpus: list[dict], splits: dict[str, str], *, sources=SOURCES,
                        include_option_chips: bool = False, positive: str = "best", negatives: int = 1,
                        paraphrases: list[dict] | None = None, seed: int = 7, max_negative_ratio: float = 0.95,
                        all_pairs: list[dict] | None = None, setup: r.Setup = r.CHAMPION, stats: dict | None = None,
                        progress: bool = True) -> list[dict]:
    """The training rows, from **train-split lessons only**: ``[{id, anchor, positive, negative, negatives, positive_id,
    negative_ids, negative_lessons, negative_same_module, lesson, module, source, chip, kind, orig, positive_score,
    negative_scores}, ...]``.

    ``anchor`` is the question as written (``retrieval.BGE_QUERY`` is put in front at training time, in ``train``, the
    same prefix the champion uses when serving). ``kind`` is ``original`` (a course question) or ``paraphrase`` (a
    model-made rewrite of a train question, from ``paraphrases``). ``negative`` is the first hard negative and
    ``negatives`` all of them.

    **Which questions.** ``sources`` (default Check, practice and the coach's prepared chips). **Option chips** ("why not
    <a wrong answer>?") are left out unless ``include_option_chips=True``: they quote a wrong answer and name no topic, so
    no search can find their lesson from their words (stage 2 found them under 0.5 for every setup and left them out of
    the bar); training on them would teach the model to guess a lesson from a wrong answer.

    **The positive.** ``positive="best"``: the one paragraph of the question's own lesson that the champion (``setup``)
    ranks highest, so each question has one clear right answer. Why not every paragraph of the lesson: the loss treats
    every *other* paragraph in the batch as wrong, so a row per paragraph would put the lesson's other paragraphs in the
    same batches as wrong answers to the same question (``train``'s sampler keeps one row per lesson in a batch, which
    softens that, but the rows would still pull the question towards paragraphs that may not answer it).
    ``positive="all"`` makes one row per paragraph of the lesson, for the notebook to show the difference.

    **The hard negative.** The paragraph the champion ranks highest among the paragraphs of *other train lessons in the
    same module* (a module is a topic, and the neighbouring lesson is what the champion confuses today), or of any other
    train lesson when the module has only one train lesson. ``negatives`` > 1 takes the next ones down the same list.
    A candidate scoring at least ``max_negative_ratio`` x the positive's score is skipped (the real term is
    **positive-aware hard-negative mining**): recaps repeat earlier lessons on purpose, so a paragraph that close to the
    positive may well answer the question too, and calling it wrong would teach the model a falsehood.
    For a paraphrase, the positive is its original's and the hard negative is mined with the paraphrase's own words
    (what the champion confuses for a learner's wording).

    ``seed`` sets the order of the returned rows (a seeded hash, as everywhere in the lab). ``all_pairs`` (every pair,
    all splits) lets ``check_rows`` also refuse an anchor that is a non-train question. ``stats``, when given a dict, is
    filled with the counts and timings the notebook reports (rows by kind and source, seconds to embed and to pick,
    modules with no second train lesson, negatives skipped as maybe-right, how often the champion already ranks the
    right lesson first).

    That last share is measured the way every dev score is: against **the whole course** (all paragraphs, every split, as
    ``retrieval.score`` searches), in ``champion_already_first_share``. The share against the train paragraphs only (the
    pool the hard negatives are mined from, smaller and so easier) is ``champion_first_among_train_paragraphs_share``.
    The other splits' paragraphs are embedded only for that count: nothing from them goes into a row.
    """
    if positive not in ("best", "all"):
        raise ValueError("positive must be 'best' or 'all'")
    if negatives < 0:
        raise ValueError("negatives must be 0 or more")
    sources = (sources,) if isinstance(sources, str) else tuple(sources)
    t0 = time.monotonic()
    chosen = [p for p in pairs if splits.get(p["lesson"]) == "train" and p["source"] in sources
              and (include_option_chips or p.get("chip") != "option")]
    by_id = {p["id"]: p for p in chosen}
    paras = [x for x in (paraphrases or []) if splits.get(x["lesson"]) == "train" and x.get("orig") in by_id]
    dropped_paraphrases = len(paraphrases or []) - len(paras)
    docs = r.chunks_in(corpus, splits, "train")
    lesson_of = np.array([c["lesson"] for c in docs])
    module_of = np.array([c["module"] for c in docs])
    train_lessons_in = defaultdict(set)
    for c in docs:
        train_lessons_in[c["module"]].add(c["lesson"])
    lonely = sorted(m for m, ls in train_lessons_in.items() if len(ls) < 2)

    d = r.embed_setup(setup, [c["text"] for c in docs], "doc")
    questions = chosen + paras
    q = r.embed_setup(setup, [x["question"] for x in questions], "query")
    others = [c for c in corpus if splits.get(c["lesson"]) != "train"]   # for the whole-course share only, never for rows
    o = r.embed_setup(setup, [c["text"] for c in others], "doc") if others else None
    seconds_embed = d.seconds + q.seconds + (o.seconds if o else 0.0)
    t_pick = time.monotonic()
    sims = q.vectors @ d.vectors.T
    sims_others = q.vectors @ o.vectors.T if o is not None else None
    lesson_of_others = np.array([c["lesson"] for c in others])

    def own_order(i: int, lesson: str) -> np.ndarray:
        own = np.flatnonzero(lesson_of == lesson)
        return own[np.argsort(-sims[i, own])]

    def mine(i: int, lesson: str, module: str, pos_score: float) -> tuple[list[int], int, bool]:
        same_module = len(train_lessons_in.get(module, ())) >= 2
        pool = np.flatnonzero((lesson_of != lesson) & ((module_of == module) if same_module else True))
        order = pool[np.argsort(-sims[i, pool])]
        picked, skipped = [], 0
        for j in order:
            if len(picked) == negatives:
                break
            if sims[i, j] >= max_negative_ratio * pos_score:
                skipped += 1
                continue
            picked.append(int(j))
        return picked, skipped, same_module

    best_of: dict[str, list[int]] = {}
    rows: list[dict] = []
    skipped_total = 0
    already_first = 0          # the right lesson first, searching the whole course (how every dev score searches)
    first_among_train = 0      # the right lesson first, searching the train paragraphs only
    for i, x in enumerate(questions):
        is_para = i >= len(chosen)
        orig = by_id[x["orig"]] if is_para else x
        if is_para:
            positives = best_of[orig["id"]]
        else:
            order = own_order(i, x["lesson"])
            positives = [int(order[0])] if positive == "best" else [int(j) for j in order]
            best_of[x["id"]] = positives
            top_train = int(np.argmax(sims[i]))
            first_among_train += int(lesson_of[top_train] == x["lesson"])
            beaten = sims_others is not None and float(sims_others[i].max()) > float(sims[i, top_train])
            already_first += int(not beaten and lesson_of[top_train] == x["lesson"])
        pos_score = float(max(sims[i, j] for j in positives))
        neg, skipped, same_module = mine(i, x["lesson"], x["module"], pos_score)
        skipped_total += skipped
        for n, j in enumerate(positives):
            rows.append({"id": f"{x['id']}#{n}" if positive == "all" else x["id"], "anchor": x["question"],
                         "positive": docs[j]["text"], "negative": docs[neg[0]]["text"] if neg else None,
                         "negatives": [docs[k]["text"] for k in neg], "positive_id": docs[j]["id"],
                         "negative_ids": [docs[k]["id"] for k in neg], "negative_lessons": [docs[k]["lesson"] for k in neg],
                         "negative_same_module": same_module, "lesson": x["lesson"], "module": x["module"],
                         "source": orig["source"], "chip": orig.get("chip", ""), "kind": "paraphrase" if is_para else "original",
                         "orig": orig["id"], "positive_score": round(float(sims[i, j]), 4),
                         "negative_scores": [round(float(sims[i, k]), 4) for k in neg]})
    key = lambda row: hashlib.sha256(f"{seed}:{row['id']}".encode()).hexdigest()
    rows.sort(key=key)
    checked = check_rows(rows, corpus, splits, all_pairs)
    seconds_pick = time.monotonic() - t_pick
    info = {"rows": len(rows), "questions": len(chosen), "paraphrases": len(paras), "paraphrases_dropped_not_train": dropped_paraphrases,
            "by_kind": dict(Counter(x["kind"] for x in rows)), "by_source": dict(Counter(x["chip"] or x["source"] for x in rows)),
            "lessons": len({x["lesson"] for x in rows}), "train_paragraphs": len(docs),
            "seconds_embed": round(seconds_embed, 2), "seconds_pick": round(seconds_pick, 2),
            "seconds_all": round(time.monotonic() - t0, 2), "modules_without_second_train_lesson": lonely,
            "negatives_skipped_as_maybe_right": skipped_total, "max_negative_ratio": max_negative_ratio,
            "share_negative_same_module": round(float(np.mean([x["negative_same_module"] for x in rows])), 3) if rows else 0.0,
            "rows_without_negative": sum(not x["negatives"] for x in rows),
            "champion_already_first_share": round(already_first / max(1, len(chosen)), 3),
            "champion_first_among_train_paragraphs_share": round(first_among_train / max(1, len(chosen)), 3),
            "champion_first_searched_paragraphs": len(docs) + len(others),
            "positive": positive, "negatives": negatives, "include_option_chips": include_option_chips,
            "sources": list(sources), "setup": setup.name, "check": checked}
    if stats is not None:
        stats.update(info)
    if progress:
        print(f"training rows: {len(rows)} ({info['by_kind']}) from {len(chosen)} train questions and {len(paras)} paraphrases, "
              f"{info['lessons']} lessons; embed {seconds_embed:.1f} s, pick {seconds_pick:.1f} s; modules with no second train "
              f"lesson: {lonely}; negatives skipped as maybe-right: {skipped_total}; leakage check passed on {checked['rows_checked']} rows")
    return rows


def rows_table(rows: list[dict]) -> list[dict]:
    """The rows flattened for an MLflow dataset (text and number columns only, so the digest sees every word)."""
    return [{"id": x["id"], "anchor": x["anchor"], "positive": x["positive"], "negative": " || ".join(x["negatives"]),
             "positive_id": x["positive_id"], "negative_ids": " ".join(x["negative_ids"]), "lesson": x["lesson"],
             "module": x["module"], "source": x["source"], "chip": x["chip"], "kind": x["kind"],
             "positive_score": x["positive_score"]} for x in rows]


def rows_dataset(rows: list[dict], name: str | None = None):
    """The training rows as an MLflow dataset; its digest changes when any word of any row changes."""
    name = name or f"training rows · {len(rows)} · {dict(Counter(x['kind'] for x in rows))}"
    return tracking.table_dataset(rows_table(rows), name, targets="lesson")


# -- 2. synthetic training questions -----------------------------------------------------------------------------------

def paraphrase_training_questions(pairs: list[dict], splits: dict[str, str], cache: Path | str = DATA / "paraphrases_train.json",
                                  model: str = r.PARAPHRASE_MODEL, max_questions: int | None = None, *,
                                  corpus: list[dict] | None = None, all_pairs: list[dict] | None = None,
                                  progress: bool = True) -> list[dict]:
    """Learner-worded rewrites of **train** questions (Check and practice only), as extra anchors for training.

    The real term is **synthetic training data**: examples written by a model rather than collected, and Databricks'
    own guidance for fine-tuning an embedding model is to generate synthetic questions for the documents when real ones
    are few. Same prompt, same local model (``qwen3:14b`` in Ollama) and the same cache format as the honest test
    (``retrieval.build_honest_test`` with ``which=("train",)``), but a separate cache file, ``data/paraphrases_train.json``,
    so dev and test rewrites can never be mixed in. Dev, test and holdout questions are never sent here.

    Each rewrite is model-made and unread (``checked: 0``); the training rows say ``kind: paraphrase``. Cached by question
    id: a rerun only sends new questions. Budget: about 1.2 s a question once the model is loaded (all 365 train Check and
    practice questions: about 7 minutes). ``max_questions`` takes the first n in id order, for a first try. With
    ``all_pairs`` (every pair, all splits), a rewrite whose words equal a non-train question is refused.
    """
    out = r.build_honest_test(pairs, splits, which=("train",), per_question=1, cache=cache, sources=("check", "more"),
                              corpus=corpus, model=model, max_questions=max_questions, progress=progress)
    assert all(splits.get(x["lesson"]) == "train" for x in out), "a paraphrase from outside train: stop and look"
    if all_pairs:
        others = {_norm(p["question"]) for p in all_pairs if splits.get(p["lesson"]) != "train"}
        clash = [x["id"] for x in out if _norm(x["question"]) in others]
        assert not clash, f"paraphrases that equal a non-train question: {clash}"
    return out


# -- 3. the batches -------------------------------------------------------------------------------------------------

def _no_same_lesson_sampler(lessons: list[str]):
    """A batch sampler that never puts two rows of the same lesson, or two rows sharing any text, in one batch.

    The loss treats every other paragraph in a batch as a wrong answer. Two rows of the same lesson in one batch would
    make each one's positive a "wrong answer" for the other, although it is from the right lesson (a **false negative**).
    The library's ``NO_DUPLICATES`` sampler only stops rows that share a text; this one also stops rows that share a
    lesson. Rows that cannot be placed without breaking the rule are left out of that epoch (the next epoch shuffles
    again), so the number of batches matches what the learning-rate schedule was told.
    """
    from sentence_transformers.base.sampler import DefaultBatchSampler

    class NoSameLessonBatchSampler(DefaultBatchSampler):
        instances: list = []

        def __init__(self, dataset, batch_size, drop_last, valid_label_columns=None, generator=None, seed=0):
            super().__init__(dataset, batch_size=batch_size, drop_last=drop_last, valid_label_columns=valid_label_columns,
                             generator=generator, seed=seed)
            assert len(lessons) == len(dataset), "one lesson per row, in the dataset's order"
            self.texts = [set(v for v in dataset[i].values() if isinstance(v, str)) for i in range(len(dataset))]
            self.left_out: list[int] = []   # rows left out of each epoch, one number per epoch
            NoSameLessonBatchSampler.instances.append(self)

        def __iter__(self):
            import torch

            g = torch.Generator()
            g.manual_seed(int(self.seed) + int(self.epoch))
            pending = torch.randperm(len(self.texts), generator=g).tolist()
            target, batches = len(self), []
            while pending and len(batches) < target:
                batch, used_lessons, used_texts, rest = [], set(), set(), []
                for i in pending:
                    if len(batch) < self.batch_size and lessons[i] not in used_lessons and used_texts.isdisjoint(self.texts[i]):
                        batch.append(i)
                        used_lessons.add(lessons[i])
                        used_texts |= self.texts[i]
                    else:
                        rest.append(i)
                if self.drop_last and len(batch) < self.batch_size:
                    rest = batch + rest
                    break
                batches.append(batch)
                pending = rest
            self.left_out.append(len(pending))
            yield from batches

    return NoSameLessonBatchSampler


def same_lesson_collisions(rows: list[dict], batch: int = 16, seed: int = SEED, epochs: int = 1) -> dict:
    """How often the library's ``NO_DUPLICATES`` sampler puts two rows of the same lesson in one batch (each such pair is
    a false negative for the loss), counted over ``epochs`` shuffles of these rows. The evidence for ``train``'s default
    sampler."""
    import torch
    from datasets import Dataset
    from sentence_transformers.base.sampler import NoDuplicatesBatchSampler

    ds = Dataset.from_dict(_columns(rows, r.BGE_QUERY))
    lessons = [x["lesson"] for x in rows]
    batches = pairs_same = batches_hit = 0
    for epoch in range(epochs):
        s = NoDuplicatesBatchSampler(ds, batch_size=batch, drop_last=False, generator=torch.Generator(), seed=seed)
        s.set_epoch(epoch)
        for b in s:
            c = Counter(lessons[i] for i in b)
            same = sum(n * (n - 1) // 2 for n in c.values())
            batches += 1
            pairs_same += same
            batches_hit += same > 0
    return {"batches": batches, "batches_with_same_lesson": batches_hit, "share": round(batches_hit / max(1, batches), 3),
            "same_lesson_pairs": pairs_same, "batch": batch, "epochs": epochs}


def _columns(rows: list[dict], query_prefix: str) -> dict[str, list[str]]:
    """The columns the loss reads, in order: anchor (with the search prompt), positive, then the hard negatives."""
    n_neg = min((len(x["negatives"]) for x in rows), default=0)
    cols = {"anchor": [query_prefix + x["anchor"] for x in rows], "positive": [x["positive"] for x in rows]}
    if n_neg == 1:
        cols["negative"] = [x["negatives"][0] for x in rows]
    for k in range(n_neg if n_neg > 1 else 0):
        cols[f"negative_{k + 1}"] = [x["negatives"][k] for x in rows]
    return cols


# -- 4. watching dev while training -----------------------------------------------------------------------------------

def dev_scores(model, corpus: list[dict], dev_sets: dict[str, list[dict]], splits: dict[str, str] | None = None,
               query_prefix: str = r.BGE_QUERY, batch: int = 32, seq_length: int | None = None) -> dict:
    """Score the model under training on the dev sets, the way ``retrieval.score`` scores every setup: the whole corpus
    embedded with *this* model, each question with the search prompt, recall@5, hit@1 and MRR. The model is put in
    evaluation mode for this (dropout off) and back in training mode after.

    Inputs are cut at ``seq_length`` tokens, by default the makers' length (``serve_length``: 512 for bge-large), not the
    256 the model trains at: the champion is scored at 512, and five paragraphs of the course are longer than 256 tokens,
    so scoring at 256 would make step 0 a slightly different model from the champion (same recall@5, but hit@1 and MRR
    off by about a question) and mix the training effect with a changed cut.

    Returns ``{set: summary, "seconds": s, "_rows": {set: per-question rows}}``; the per-question rows (hit or miss for
    each question) are what a paired test between two steps needs."""
    was_training = model.training
    model.eval()
    t0 = time.monotonic()
    rows_by_set = {}
    out = {}
    try:
        with at_length(model, seq_length or serve_length(model)):
            d = model.encode([c["text"] for c in corpus], batch_size=batch, normalize_embeddings=True, convert_to_numpy=True,
                             show_progress_bar=False)
            for name, pairs in dev_sets.items():
                q = model.encode([query_prefix + p["question"] for p in pairs], batch_size=batch, normalize_embeddings=True,
                                 convert_to_numpy=True, show_progress_bar=False)
                rows, summary = r.score(q, d, corpus, pairs, r.K, splits)
                out[name] = summary
                rows_by_set[name] = rows
    finally:
        if was_training:
            model.train()
    out["seconds"] = round(time.monotonic() - t0, 2)
    out["_rows"] = rows_by_set
    return out


def _flat(scores: dict) -> dict[str, float]:
    keep = ("recall_at_5", "recall_at_5_low", "recall_at_5_high", "hit_at_1", "mrr", "weakest_module_recall")
    return {f"{name}_{k}": float(s[k]) for name, s in scores.items() if isinstance(s, dict) and not name.startswith("_")
            for k in keep if k in s}


def _make_watch(model, corpus, dev_sets, splits, query_prefix, eval_every, save_every, out: Path, max_steps_hint: int):
    from transformers import TrainerCallback

    import mlflow

    class Watch(TrainerCallback):
        """Logs train/loss and lr every step; every ``eval_every`` steps scores dev and writes a checkpoint.json; keeps the
        weights of the best checkpoint so far only (by dev honest recall@5, a tie goes to the higher originals recall@5, then to the earlier step)."""

        def __init__(self):
            self.curve: list[dict] = []
            self.losses: list[dict] = []
            self.step_seconds: list[float] = []
            self.peak_gb = 0.0
            self.best: dict | None = None
            self.checkpoints: list[dict] = []
            self.rows_by_step: dict[int, dict[str, list[dict]]] = {}   # per-question hits at every evaluation
            self._t = None

        def _evaluate(self, step: int) -> dict:
            scores = dev_scores(model, corpus, dev_sets, splits, query_prefix)
            flat = _flat(scores)
            self.rows_by_step[step] = scores["_rows"]
            entry = {"step": step, **flat, "seconds_eval": scores["seconds"],
                     "weakest_module": {n: scores[n]["weakest_module"] for n in dev_sets}}
            self.curve.append(entry)
            mlflow.log_metrics({f"held_out/{k}": v for k, v in flat.items()} | {"held_out/seconds_eval": scores["seconds"]}, step=step)
            print(f"  step {step:4d} · dev " + " · ".join(f"{n} recall@5 {scores[n]['recall_at_5']:.3f}" for n in dev_sets)
                  + f" · eval {scores['seconds']:.0f} s", flush=True)
            return entry

        def _checkpoint(self, step: int, entry: dict) -> None:
            folder = out / f"checkpoint-{step}"
            folder.mkdir(parents=True, exist_ok=True)
            key = (entry.get(f"{PICK_BY}_recall_at_5", 0.0), entry.get("originals_recall_at_5", 0.0))
            is_best = self.best is None or key > self.best["key"]
            info = {"step": step, "dev": {k: v for k, v in entry.items() if k != "step"}, "picked_by": f"dev {PICK_BY} recall@5",
                    "weights_kept": False, "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
            if is_best and step > 0:
                with at_length(model, serve_length(model)):   # saved at the makers' length, as the champion is served
                    model.save(str(folder))
                info["weights_kept"] = True
                info["weights_mb"] = folder_mb(folder)
                if self.best and self.best["step"] > 0:  # the old best gives its weights up: only its scores stay
                    _trim_folder(out / f"checkpoint-{self.best['step']}")
            if is_best:
                self.best = {"step": step, "key": key, "entry": entry}
            (folder / "checkpoint.json").write_text(json.dumps(info, indent=1))
            self.checkpoints.append(info)

        def on_train_begin(self, args, state, control, **kwargs):
            entry = self._evaluate(0)   # this model before any training: the baseline of THIS run
            self._checkpoint(0, entry)

        def on_step_begin(self, args, state, control, **kwargs):
            self._t = time.monotonic()

        def on_step_end(self, args, state, control, **kwargs):
            if self._t is not None:
                self.step_seconds.append(time.monotonic() - self._t)
            self.peak_gb = max(self.peak_gb, _memory_gb())
            step = state.global_step
            last = step >= state.max_steps
            evaluate = step % eval_every == 0 or (save_every and step % save_every == 0) or last
            if evaluate:
                entry = self._evaluate(step)
                if (save_every and step % save_every == 0) or last:
                    self._checkpoint(step, entry)

        def on_log(self, args, state, control, logs=None, **kwargs):
            if not logs or "loss" not in logs:
                return
            numbers = {"train/loss": float(logs["loss"])}
            if "learning_rate" in logs:
                numbers["lr"] = float(logs["learning_rate"])
            if "grad_norm" in logs and logs["grad_norm"] is not None:
                numbers["train/grad_norm"] = float(logs["grad_norm"])
            numbers["train/epoch"] = float(logs.get("epoch", state.epoch or 0))
            mlflow.log_metrics(numbers, step=state.global_step)
            self.losses.append({"step": state.global_step, **numbers})

    return Watch()


def _trim_folder(folder: Path) -> float:
    """Delete a checkpoint's weights, keep its checkpoint.json; returns the MB freed."""
    freed = 0.0
    if not folder.exists():
        return freed
    for f in list(folder.iterdir()):
        if f.name == "checkpoint.json":
            continue
        freed += folder_mb(f) if f.is_dir() else f.stat().st_size / 1e6
        shutil.rmtree(f) if f.is_dir() else f.unlink()
    info_path = folder / "checkpoint.json"
    if info_path.exists():
        info = json.loads(info_path.read_text())
        info["weights_kept"] = False
        info["trimmed"] = True
        info_path.write_text(json.dumps(info, indent=1))
    return round(freed, 1)


# -- 5. training ------------------------------------------------------------------------------------------------------

def _quiet_model_card_bar() -> None:
    """Silence the "Computing widget examples" bar sentence-transformers draws when training starts (it writes its model
    card). In a notebook that bar is a widget whose saved state carries a random 32-character id, which the repo's scrub
    test refuses, and it ignores ``TQDM_DISABLE``, so it is switched off here at its source."""
    import sentence_transformers.base.model_card as model_card

    if not getattr(model_card.tqdm, "_lab_quiet", False):
        quiet = functools.partial(model_card.tqdm, disable=True)
        quiet._lab_quiet = True
        model_card.tqdm = quiet


def _log_datasets(datasets) -> list[dict]:
    import mlflow

    logged = []
    for item in datasets or []:
        ds, context = item if isinstance(item, tuple) else (item, None)
        mlflow.log_input(ds, context=context)
        logged.append({"name": ds.name, "digest": ds.digest, "context": context})
    return logged


def train(rows: list[dict], *, base: str = BASE, lr: float = 2e-5, epochs: float = 3, batch: int = 16, max_seq: int = 256,
          seed: int = SEED, warmup: float = 0.1, eval_every: int = 20, save_every: int = 20, out: Path | str | None = None,
          dev_sets: dict[str, list[dict]], corpus: list[dict], run_name: str | None = None, description: str = "",
          datasets: list | None = None, lora: dict | None = None, log_model: bool = False, max_steps: int | None = None,
          query_prefix: str = r.BGE_QUERY, sampler: str = "no_same_lesson", scale: float = 20.0,
          splits: dict[str, str] | None = None, parent_run_id: str | None = None, tags: dict | None = None,
          extra_params: dict | None = None, extra_metrics: dict | None = None, extra_artifacts: dict | None = None,
          all_pairs: list[dict] | None = None, gradient_checkpointing: bool | str = False) -> dict:
    """Fine-tune ``base`` on ``rows`` and log everything as one MLflow run. Returns a dict (see the end).

    **How.** ``SentenceTransformerTrainer`` with ``MultipleNegativesRankingLoss`` (``scale`` 20: the cosines are multiplied
    by 20 before the softmax, the library's default), on (anchor, positive, hard negative) rows when the rows carry
    negatives and (anchor, positive) pairs otherwise. Anchors get ``query_prefix`` (the makers' search prompt, as when
    serving). Full 32-bit precision (fp32) on this computer's GPU. Learning rate ``lr`` with a linear warm-up over the first
    ``warmup`` share of the steps, then a straight-line decay to 0. ``epochs`` passes over the rows, or exactly
    ``max_steps`` steps when given (the smoke run). ``seed`` seeds Python, numpy and torch and the batch order; the same seed is
    *not* bit-identical on this chip (see ``seed_everything``), so a setting is judged across seeds.

    **Batches.** ``sampler="no_same_lesson"`` (default): no two rows of one lesson and no shared text in a batch, so no
    in-batch negative is from the right lesson (see ``same_lesson_collisions`` for how often the library's own sampler lets
    that happen). ``sampler="no_duplicates"``: the library's ``BatchSamplers.NO_DUPLICATES`` (no shared text only).

    **Watching dev.** Before the first step (step 0: this model untrained, the baseline of *this* run) and every
    ``eval_every`` steps, the model is scored on each of ``dev_sets`` (``{"honest": [...], "originals": [...]}``) with the
    whole ``corpus`` as the haystack, via ``retrieval.score``; logged as ``held_out/<set>_recall_at_5`` and friends at that
    step. Scoring and saving use the makers' length (512 tokens for bge-large), training uses ``max_seq`` (256): see
    ``dev_scores``. A step whose number divides by ``save_every`` (and the last step) is a **checkpoint**:
    ``<out>/checkpoint-<step>/checkpoint.json`` holds its dev scores. Weights are written only for the best checkpoint so
    far (by dev ``honest`` recall@5; a tie there goes to the higher originals recall@5, then to the earlier step); when a later one beats it, the old one's
    weights are deleted and its scores stay. The end state is the same as saving every checkpoint and trimming all but the
    best afterwards, without writing 1.3 GB per checkpoint. ``trim.json`` lists every checkpoint, kept or trimmed, and the
    run gets the tag ``checkpoints.trimmed=true``. Picking the best step on dev makes its dev score a little optimistic:
    test (stage 4) is the clean number.

    **Paired against step 0.** The per-question hits at every evaluation are kept, so the best step and the last step are
    each compared with step 0 *on the same dev questions* (``retrieval.compare``: the questions only one of the two found,
    McNemar's p on those, and the paired bootstrap range of the gap). Step 0 and a later step score the same questions,
    so two separate Wilson ranges are the wrong test for "did it change"; this is the right one. Logged as
    ``paired.<best|last>_vs_step0.<set>.*`` metrics and ``paired_vs_step0.json``; the hits are in ``dev_hits_by_step.json``.

    **LoRA.** ``lora={"r": 16, "alpha": 32, "dropout": 0.1}`` trains small adapter matrices on the attention's query and
    value layers instead of every weight; the adapter's size is logged (``adapter_mb``) beside the 1.3 GB full model.

    **Memory.** About 11 GB at batch 16 with triplets, fp32, of the 19 GB the GPU may use on this computer; a model that
    Ollama holds counts against the same 19 GB. ``gradient_checkpointing=True`` (the real term: the in-between numbers of
    the forward pass are recomputed during the backward pass instead of kept) trades time for memory; ``"auto"`` turns it
    on only when Ollama holds more than 4 GB at the start. The choice and its reason are logged as params, because it
    changes seconds per step (not the maths: the same numbers are computed).

    **The model.** With ``log_model=True`` and a full fine-tune, the best checkpoint is logged with
    ``mlflow.sentence_transformers.log_model(..., name="model")`` with a signature and an input example (once per final run,
    not per sweep point: 1.3 GB each). A LoRA run logs its adapter folder as an artifact instead. When the best step is 0
    (training never beat the untrained model on dev), nothing is logged as a model and the tag ``best_is_base=true`` says so.

    Returns ``{run_id, run_name, out, steps, step0, best_step, best, final, curve, losses, seconds_per_step,
    peak_memory_gb, best_dir, trim, params, adapter_mb, left_out_per_epoch, paired, rows_by_step}``;
    ``step0``/``best``/``final`` are flat dicts like ``honest_recall_at_5``; ``paired`` is
    ``{"best_vs_step0" | "last_vs_step0": {"step": n, <set>: retrieval.compare result}}``.
    """
    import mlflow
    from datasets import Dataset
    from sentence_transformers import SentenceTransformerTrainer, SentenceTransformerTrainingArguments
    from sentence_transformers.sentence_transformer.losses import MultipleNegativesRankingLoss
    from sentence_transformers.sentence_transformer.training_args import BatchSamplers

    if not rows:
        raise ValueError("no training rows")
    if splits is None:
        splits = r.load_splits()
    check = check_rows(rows, corpus, splits, all_pairs)   # the leakage rule, again, on exactly what is trained on
    for name, pairs in dev_sets.items():
        assert all(splits.get(p["lesson"]) == "dev" for p in pairs), f"dev set {name!r} holds a non-dev question: stop and look"
    kind = f"lora r{lora.get('r', 16)}" if lora else "full"
    run_name = run_name or name_for(kind, lr, seed, base)
    out = Path(out) if out else OUTPUTS / run_name.replace(" · ", "_").replace(" ", "-").replace("/", "-")
    if out.exists():
        shutil.rmtree(out)   # a rerun with the same name starts clean; the earlier run's record is in MLflow
    out.mkdir(parents=True)

    release_champion()
    neighbours = ollama_loaded_gb()
    if sum(neighbours.values()) > 6:
        print(f"Note: Ollama holds {neighbours} in the same memory the training run needs (about 11 GB at batch 16); "
              "if this fails with an out-of-memory error, wait for that job or lower the batch.")
    if gradient_checkpointing == "auto":
        held = sum(neighbours.values())
        gradient_checkpointing = held > 4
        checkpointing_reason = (f"auto: Ollama held {held:.1f} GB at the start ({neighbours})" if gradient_checkpointing
                                else "auto: Ollama held no large model at the start")
    else:
        checkpointing_reason = "set by the caller"
    seed_everything(seed)
    model = fresh_model(base, seed=seed, max_seq=max_seq, lora=lora)
    counts = parameter_counts(model)
    seq_scored = serve_length(model)
    cols = _columns(rows, query_prefix)
    ds = Dataset.from_dict(cols)
    lessons = [x["lesson"] for x in rows]
    if sampler == "no_same_lesson":
        batch_sampler = _no_same_lesson_sampler(lessons)
    elif sampler == "no_duplicates":
        batch_sampler = BatchSamplers.NO_DUPLICATES
    else:
        raise ValueError("sampler must be 'no_same_lesson' or 'no_duplicates'")
    steps_per_epoch = math.ceil(len(rows) / batch)
    total_steps = max_steps or math.ceil(steps_per_epoch * epochs)
    warmup_steps = int(round(warmup * total_steps))
    params = {"base": base, "kind": kind, "learning_rate": lr, "epochs": epochs, "batch": batch, "max_seq_length": max_seq,
              "max_seq_length.scored_and_saved": seq_scored, "seed": seed, "warmup_share": warmup, "warmup_steps": warmup_steps, "eval_every": eval_every,
              "save_every": save_every, "max_steps": max_steps or "(epochs)", "total_steps": total_steps,
              "steps_per_epoch": steps_per_epoch, "rows": len(rows), "columns": " | ".join(cols), "loss": "MultipleNegativesRankingLoss",
              "loss.scale": scale, "sampler": sampler, "precision": "fp32", "device": _device(), "query_prefix": query_prefix or "(none)",
              "lr_schedule": "linear warm-up then linear decay to 0", "optimizer": "AdamW (torch), weight decay 0",
              "pick_checkpoint_by": f"dev {PICK_BY} recall@5", "dev_sets": " | ".join(f"{k} {len(v)}" for k, v in dev_sets.items()),
              "corpus_paragraphs": len(corpus), "lora": json.dumps(lora) if lora else "(none)",
              "gradient_checkpointing": bool(gradient_checkpointing), "gradient_checkpointing.reason": checkpointing_reason,
              **(extra_params or {})}

    args = SentenceTransformerTrainingArguments(
        output_dir=str(out / "_trainer"), per_device_train_batch_size=batch, learning_rate=lr, num_train_epochs=epochs,
        max_steps=max_steps or -1, warmup_steps=warmup_steps, lr_scheduler_type="linear", weight_decay=0.0, seed=seed,
        data_seed=seed, logging_steps=1, save_strategy="no", eval_strategy="no", report_to="none", disable_tqdm=True,
        batch_sampler=batch_sampler, dataloader_drop_last=False, fp16=False, bf16=False,
        gradient_checkpointing=bool(gradient_checkpointing), dataloader_pin_memory=False)
    loss = MultipleNegativesRankingLoss(model, scale=scale)
    watch = _make_watch(model, corpus, dev_sets, splits, query_prefix, eval_every, save_every, out, total_steps)

    import torch

    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    all_tags = {"kind": "coach_retrieval_lab", "lab.stage": "03_train", "git_commit": tracking.git_commit(), "base_model": base,
                "train.kind": kind, "seed": str(seed), **{f"computer.{k}": str(v) for k, v in tracking.this_computer().items()},
                "ollama_loaded_at_start": json.dumps(neighbours) if neighbours else "(none)",
                "mlflow.note.content": (description or "(description written at the end of the run)"), **(tags or {})}
    t_all = time.monotonic()
    with mlflow.start_run(run_name=run_name, nested=parent_run_id is not None, parent_run_id=parent_run_id, tags=all_tags) as run:
        mlflow.log_params(params)
        mlflow.log_metrics({k: float(v) for k, v in counts.items()} | {f"rows.{k}": float(v) for k, v in Counter(x["kind"] for x in rows).items()})
        logged = _log_datasets(datasets)
        rows_ds = rows_dataset(rows)
        mlflow.log_input(rows_ds, context="training")
        logged.append({"name": rows_ds.name, "digest": rows_ds.digest, "context": "training"})
        mlflow.log_dict(rows, "training_rows.json")
        mlflow.log_dict(check, "leakage_check.json")
        for name, obj in (extra_artifacts or {}).items():
            mlflow.log_dict(obj, name)
        if extra_metrics:
            mlflow.log_metrics({k: float(v) for k, v in extra_metrics.items()})

        _quiet_model_card_bar()
        trainer = SentenceTransformerTrainer(model=model, args=args, train_dataset=ds, loss=loss, callbacks=[watch])
        from transformers.trainer_callback import PrinterCallback

        trainer.remove_callback(PrinterCallback)   # the loss goes to MLflow; no dict printed per step
        t_train = time.monotonic()
        trainer.train()
        seconds_train = time.monotonic() - t_train

        step0 = {k: v for k, v in watch.curve[0].items() if isinstance(v, float)}
        final = {k: v for k, v in watch.curve[-1].items() if isinstance(v, float)}
        best = watch.best
        best_step = best["step"]
        best_flat = {k: v for k, v in best["entry"].items() if isinstance(v, float)}
        left_out = [n for sm in getattr(batch_sampler, "instances", []) for n in sm.left_out] or None
        sps = float(np.median(watch.step_seconds)) if watch.step_seconds else float("nan")

        # Trim: every checkpoint but the best keeps its scores only (the best-so-far rule already did most of it).
        trim = {"kept": f"checkpoint-{best_step}" if best_step > 0 else "(none: the best was step 0, the untrained model)",
                "picked_by": f"dev {PICK_BY} recall@5 (a tie goes to the higher originals recall@5, then to the earlier step)", "checkpoints": []}
        for info in watch.checkpoints:
            folder = out / f"checkpoint-{info['step']}"
            freed = 0.0
            if info["step"] != best_step and info.get("weights_kept"):
                freed = _trim_folder(folder)
            trim["checkpoints"].append({"step": info["step"], "weights_kept": info["step"] == best_step and best_step > 0,
                                        "freed_mb": freed, **{k: v for k, v in info["dev"].items() if isinstance(v, float)}})
        shutil.rmtree(out / "_trainer", ignore_errors=True)
        (out / "trim.json").write_text(json.dumps(trim, indent=1))
        mlflow.log_dict(trim, "checkpoints/trim.json")
        for info in watch.checkpoints:
            mlflow.log_dict(json.loads((out / f"checkpoint-{info['step']}" / "checkpoint.json").read_text()),
                            f"checkpoints/checkpoint-{info['step']}/checkpoint.json")
        mlflow.log_dict(watch.curve, "curve.json")
        mlflow.log_dict(watch.losses, "losses.json")
        best_dir = out / f"checkpoint-{best_step}" if best_step > 0 else None
        adapter_mb = adapter_size_mb(model, out) if lora else None

        # Paired against step 0 on the same dev questions: the best step and the last step.
        last_step = watch.curve[-1]["step"]
        paired = {label: {"step": step, **{n: r.compare(watch.rows_by_step[0][n], watch.rows_by_step[step][n]) for n in dev_sets}}
                  for label, step in (("best_vs_step0", best_step), ("last_vs_step0", last_step))}
        mlflow.log_dict(paired, "paired_vs_step0.json")
        mlflow.log_dict({str(step): {n: [{"id": x["id"], "hit": bool(x["hit"]), "first_rank": x.get("first_rank")} for x in rs]
                                     for n, rs in by_set.items()} for step, by_set in watch.rows_by_step.items()},
                        "dev_hits_by_step.json")
        mlflow.log_metrics({f"paired.{label}.{n}.{k}": float(p[n][k]) for label, p in paired.items() for n in dev_sets
                            for k in ("gap_recall_at_5", "gap_low", "gap_high", "p_value", "only_first", "only_second")})

        metrics = {"best_step": best_step, "seconds_per_step": sps, "seconds_train": seconds_train, "seconds_all": time.monotonic() - t_all,
                   "peak_memory_gb": watch.peak_gb, "steps": float(watch.losses[-1]["step"]) if watch.losses else 0.0,
                   "train/loss_first": watch.losses[0]["train/loss"] if watch.losses else float("nan"),
                   "train/loss_last": watch.losses[-1]["train/loss"] if watch.losses else float("nan"),
                   **{f"step0.{k}": v for k, v in step0.items()}, **{f"best.{k}": v for k, v in best_flat.items()},
                   **{f"final.{k}": v for k, v in final.items()},
                   **{f"gain_over_step0.{n}_recall_at_5": best_flat.get(f"{n}_recall_at_5", 0) - step0.get(f"{n}_recall_at_5", 0) for n in dev_sets}}
        if adapter_mb is not None:
            metrics["adapter_mb"] = adapter_mb
        if best_dir is not None and not lora:
            metrics["best_checkpoint_mb"] = folder_mb(best_dir)
        mlflow.log_metrics({k: float(v) for k, v in metrics.items()})
        mlflow.set_tags({"checkpoints.trimmed": "true", "best_step": str(best_step), "best_is_base": str(best_step == 0).lower(),
                         "best_checkpoint_dir": str(best_dir.relative_to(HERE)) if best_dir else "(none)",
                         "best.weakest_module.honest": best["entry"]["weakest_module"].get("honest", "")
                         if isinstance(best["entry"].get("weakest_module"), dict) else ""})

        if log_model and best_dir is not None:
            if lora:
                mlflow.log_artifacts(str(best_dir), "adapter")
            else:
                _log_best_model(best_dir, query_prefix)
        elif log_model:
            print("log_model: the best step is 0 (the untrained model), so there is no trained model to log.")

        result_block = (f"\n\n**Results (written by training.train at the end of the run).** {watch.losses[-1]['step'] if watch.losses else 0} "
                        f"steps in {seconds_train:.0f} s ({sps:.2f} s per step, median; peak GPU memory {watch.peak_gb:.1f} GB). "
                        + " ".join(f"Dev {n} recall@5: step 0 {step0.get(f'{n}_recall_at_5', 0):.3f} "
                                   f"[{step0.get(f'{n}_recall_at_5_low', 0):.2f}, {step0.get(f'{n}_recall_at_5_high', 0):.2f}], "
                                   f"best (step {best_step}) {best_flat.get(f'{n}_recall_at_5', 0):.3f} "
                                   f"[{best_flat.get(f'{n}_recall_at_5_low', 0):.2f}, {best_flat.get(f'{n}_recall_at_5_high', 0):.2f}], "
                                   f"last step {final.get(f'{n}_recall_at_5', 0):.3f}." for n in dev_sets)
                        + " Paired against step 0 on the same dev questions (only step 0 found / only the later step found, McNemar p): "
                        + "; ".join(f"{label.replace('_vs_step0', '')} step {p['step']} {n} {p[n]['only_first']}/{p[n]['only_second']}, "
                                    f"p {p[n]['p_value']:.3f}, gap {p[n]['gap_recall_at_5']:+.3f} [{p[n]['gap_low']:+.3f}, {p[n]['gap_high']:+.3f}]"
                                    for label, p in paired.items() for n in dev_sets) + "."
                        + f" Train loss {metrics['train/loss_first']:.3f} at the first step, {metrics['train/loss_last']:.3f} at the last. "
                        f"Inputs cut at {max_seq} tokens while training and at {seq_scored} (the makers' length, as the champion) when "
                        "scored and saved. "
                        f"Datasets: " + "; ".join(f"{d['name']} ({d['digest']}, {d['context']})" for d in logged) + ". "
                        f"Leakage check: {check['rows_checked']} rows, {check['texts_checked']} texts, all from train lessons. "
                        f"Checkpoints: weights kept for {trim['kept']} only; the others keep their scores (trim.json). "
                        "The same seed is not bit-identical on this chip, and the best step was picked on dev, so its dev score "
                        "is a little optimistic: test (stage 4) is the clean number.")
        mlflow.set_tag("mlflow.note.content", (description or f"**{run_name}**") + result_block)
        run_id = run.info.run_id

    out_dict = {"run_id": run_id, "run_name": run_name, "out": str(out), "steps": int(metrics["steps"]), "step0": step0,
                "best_step": best_step, "best": best_flat, "final": final, "curve": watch.curve, "losses": watch.losses,
                "seconds_per_step": sps, "seconds_train": seconds_train, "peak_memory_gb": watch.peak_gb,
                "best_dir": str(best_dir) if best_dir else None, "trim": trim, "params": params, "adapter_mb": adapter_mb,
                "counts": counts, "left_out_per_epoch": left_out, "datasets": logged, "paired": paired,
                "rows_by_step": watch.rows_by_step}
    trainer.callback_handler.callbacks.clear()
    del trainer, model, loss, watch
    _free_memory()
    return out_dict


def adapter_size_mb(model, out: Path | str) -> float:
    """The LoRA adapter's size on disk (MB): saved once to a scratch folder under ``out``, measured, deleted. Measured
    whether or not a checkpoint kept its weights, so the size trade-off (a few MB against 1.3 GB) is always logged."""
    probe = Path(out) / "_adapter_size"
    model.save(str(probe))
    files = {f.name: round(f.stat().st_size / 1e6, 2) for f in probe.rglob("*") if f.is_file() and "adapter" in f.name}
    size = round(sum(files.values()), 2) if files else folder_mb(probe)
    shutil.rmtree(probe, ignore_errors=True)
    return size


def _log_best_model(best_dir: Path, query_prefix: str) -> None:
    """Log the best checkpoint as an MLflow model, with a signature and an input example (a question with its prompt)."""
    import mlflow
    from mlflow.models import infer_signature
    from sentence_transformers import SentenceTransformer

    best = SentenceTransformer(str(best_dir), device=_device())
    example = [query_prefix + "How do I stop my agent from calling the same tool forever?"]
    signature = infer_signature(example, best.encode(example, normalize_embeddings=True))
    mlflow.sentence_transformers.log_model(best, name="model", signature=signature, input_example=example)
    del best
    _free_memory()


def overfit_on_purpose(rows: list[dict], *, n: int = 16, lr: float = 1e-4, epochs: int = 40, seed: int = SEED,
                       eval_every: int = 10, **train_kwargs) -> dict:
    """Train on a tiny set on purpose, to watch **overfitting**: the loss on the rows it sees falls towards 0 while dev
    recall stops rising and falls, because the model learns those 16 questions instead of the skill.

    Picks ``n`` rows from ``n`` different lessons (seeded hash order, so one batch holds them all and every step sees the
    same batch), a high learning rate (1e-4, five times the main runs') and many passes (``epochs``; one step per pass),
    no warm-up. Everything else is ``train`` (pass ``dev_sets``, ``corpus``, ``description``, ``datasets`` through), logged
    as ``train · bge-large · overfit on purpose · 16 rows · lr 1e-4 · seed 1101`` unless ``run_name`` is given.
    """
    key = lambda x: hashlib.sha256(f"{seed}:{x['id']}".encode()).hexdigest()
    small, seen = [], set()
    for x in sorted(rows, key=key):
        if x["lesson"] not in seen and x["kind"] == "original":
            small.append(x)
            seen.add(x["lesson"])
        if len(small) == n:
            break
    train_kwargs.setdefault("run_name", name_for(f"overfit on purpose · {n} rows", lr, seed))
    train_kwargs.setdefault("save_every", eval_every)
    train_kwargs.setdefault("warmup", 0.0)
    return train(small, lr=lr, epochs=epochs, batch=n, seed=seed, eval_every=eval_every, **train_kwargs) | {"rows_used": small}


# -- 6. one step by hand ----------------------------------------------------------------------------------------------

def one_step_by_hand(model, batch_rows: list[dict], *, lr: float = 2e-5, query_prefix: str = r.BGE_QUERY, scale: float = 20.0,
                     fresh_rows: list[dict] | None = None, gradient_checkpointing: bool | str = False) -> dict:
    """One training step, number by number: the loss on one batch, one update, and what moved.

    **Changes ``model`` in place**: pass a fresh copy (``fresh_model()``), never the champion from ``retrieval.local_model``.

    1. The loss **by hand**: for each question, the cosine to every paragraph in the batch (its positive, its hard negative,
       and every other row's), times ``scale`` (20), then softmax (turn scores into shares that add up to 1), then
       -log of the share the right paragraph got; averaged over the batch. It must equal the library's loss.
    2. The gradient (how much each weight would change the loss) and one AdamW update at ``lr``. AdamW's very first step
       moves almost every weight by about ``lr``, whatever the gradient's size, which is why the first steps are taken
       gently (the warm-up).
    3. The same batch scored again: loss, and each question's cosine to its positive and to its hard negative. And, with
       ``fresh_rows``, a batch the step did not see (did it help elsewhere, or only on these rows?).

    Measurements are taken with dropout off (evaluation mode), so before and after differ only by the update. The copy of
    the weights taken before the update (to measure how far they moved) is kept in ordinary memory, not on the GPU.
    ``gradient_checkpointing`` as in ``train`` (``"auto"``: on when Ollama holds more than 4 GB). Returns
    ``{loss_before, loss_after, loss_by_hand, fresh_loss_before, fresh_loss_after, cos_pos_before, cos_pos_after,
    cos_neg_before, cos_neg_after, gap_before, gap_after, grad_norm, relative_change, max_abs_change, params_changed,
    first_row: {...}, rows, lr}``.
    """
    import torch
    from sentence_transformers.sentence_transformer.losses import MultipleNegativesRankingLoss

    loss_fn = MultipleNegativesRankingLoss(model, scale=scale)
    device = model.device

    def features(rows):
        cols = _columns(rows, query_prefix)
        out = []
        for texts in cols.values():
            f = model.preprocess(texts)
            out.append({k: (v.to(device) if hasattr(v, "to") else v) for k, v in f.items()})
        return out

    def cosines(rows):
        a = model.encode([query_prefix + x["anchor"] for x in rows], normalize_embeddings=True, convert_to_tensor=True, show_progress_bar=False)
        p = model.encode([x["positive"] for x in rows], normalize_embeddings=True, convert_to_tensor=True, show_progress_bar=False)
        n = model.encode([x["negatives"][0] for x in rows], normalize_embeddings=True, convert_to_tensor=True, show_progress_bar=False) \
            if all(x["negatives"] for x in rows) else None
        return a, p, n

    def measure(rows):
        model.eval()
        with torch.no_grad():
            lib = float(loss_fn(features(rows), None).item())
            a, p, n = cosines(rows)
            candidates = torch.cat([p, n]) if n is not None else p
            scores = scale * a @ candidates.T                    # each question against every paragraph in the batch
            shares = torch.softmax(scores, dim=1)
            right = torch.arange(len(rows), device=scores.device)
            by_hand = float((-torch.log(shares[right, right])).mean().item())
            cos_pos = (a * p).sum(1)
            cos_neg = (a * n).sum(1) if n is not None else torch.zeros_like(cos_pos)
        return {"loss": lib, "loss_by_hand": by_hand, "cos_pos": cos_pos.cpu().numpy(), "cos_neg": cos_neg.cpu().numpy(),
                "share_right_first": float(shares[0, 0].item()), "scores_first": scores[0].cpu().numpy()}

    if gradient_checkpointing == "auto":
        gradient_checkpointing = sum(ollama_loaded_gb().values()) > 4
    if gradient_checkpointing:
        model.gradient_checkpointing_enable()
    before = measure(batch_rows)
    fresh_before = measure(fresh_rows) if fresh_rows else None
    trainable = [p for p in model.parameters() if p.requires_grad]
    snapshot = [p.detach().to("cpu", copy=True) for p in trainable]

    model.train()
    optimizer = torch.optim.AdamW(trainable, lr=lr, weight_decay=0.0)
    optimizer.zero_grad()
    loss = loss_fn(features(batch_rows), None)
    loss.backward()
    grad_norm = float(torch.sqrt(sum((p.grad.detach() ** 2).sum() for p in trainable if p.grad is not None)).item())
    optimizer.step()
    optimizer.zero_grad()

    del optimizer
    _free_memory()
    delta_sq = size_sq = 0.0
    max_abs, changed = 0.0, 0
    with torch.no_grad():
        for p, s in zip(trainable, snapshot):   # one weight table at a time, on the CPU
            d = p.detach().to("cpu") - s
            delta_sq += float((d.double() ** 2).sum())
            size_sq += float((s.double() ** 2).sum())
            max_abs = max(max_abs, float(d.abs().max()))
            changed += int((d != 0).sum())
    relative = math.sqrt(delta_sq / size_sq)
    del snapshot
    after = measure(batch_rows)
    fresh_after = measure(fresh_rows) if fresh_rows else None
    model.eval()
    x0 = batch_rows[0]
    result = {"rows": len(batch_rows), "lr": lr, "scale": scale,
              "loss_before": before["loss"], "loss_after": after["loss"], "loss_by_hand": before["loss_by_hand"],
              "loss_by_hand_after": after["loss_by_hand"],
              "fresh_loss_before": fresh_before["loss"] if fresh_before else None,
              "fresh_loss_after": fresh_after["loss"] if fresh_after else None,
              "cos_pos_before": float(before["cos_pos"].mean()), "cos_pos_after": float(after["cos_pos"].mean()),
              "cos_neg_before": float(before["cos_neg"].mean()), "cos_neg_after": float(after["cos_neg"].mean()),
              "gap_before": float((before["cos_pos"] - before["cos_neg"]).mean()),
              "gap_after": float((after["cos_pos"] - after["cos_neg"]).mean()),
              "grad_norm": grad_norm, "relative_change": relative, "gradient_checkpointing": bool(gradient_checkpointing), "max_abs_change": max_abs, "params_changed": changed,
              "params_trainable": sum(p.numel() for p in trainable),
              "first_row": {"question": x0["anchor"], "lesson": x0["lesson"], "positive_id": x0["positive_id"],
                            "negative_id": x0["negative_ids"][0] if x0["negative_ids"] else None,
                            "cos_pos_before": float(before["cos_pos"][0]), "cos_pos_after": float(after["cos_pos"][0]),
                            "cos_neg_before": float(before["cos_neg"][0]), "cos_neg_after": float(after["cos_neg"][0]),
                            "share_right_before": before["share_right_first"], "share_right_after": after["share_right_first"],
                            "candidates": 2 * len(batch_rows) if x0["negatives"] else len(batch_rows)}}
    return result


def distinct_lesson_batch(rows: list[dict], n: int = 16, skip: int = 0, kind: str = "original") -> list[dict]:
    """``n`` rows of ``n`` different lessons, in the rows' own (seeded) order, after skipping the first ``skip`` such rows:
    a batch the way ``train``'s sampler builds one, for ``one_step_by_hand``."""
    out, seen, skipped = [], set(), 0
    for x in rows:
        if x["kind"] != kind or x["lesson"] in seen:
            continue
        seen.add(x["lesson"])
        if skipped < skip:
            skipped += 1
            continue
        out.append(x)
        if len(out) == n:
            break
    return out


# -- 7. reading stage 1 back -------------------------------------------------------------------------------------------

def load_stage1(require=("pairs_train.json", "pairs_dev.json", "honest_dev.json", "corpus.json")) -> dict:
    """The newest stage-1 run's rows, read back from MLflow and checked against its logged digests:
    ``{run, pairs_train, pairs_dev, honest_dev, originals_dev, corpus, datasets: {name: (dataset, context)}, digests}``.

    ``originals_dev`` is built as stage 2 builds it: the dev Check and practice questions that have a paraphrase in
    ``honest_dev`` (so the two dev sets are the same questions in two wordings)."""
    import mlflow

    stage1 = tracking.find_run(tracking.EXPERIMENT, "pairs · build and freeze", require=require)
    digests = {i.dataset.name: i.dataset.digest for i in stage1.inputs.dataset_inputs}
    out = {"run": stage1, "digests": digests, "datasets": {}}
    for name, context, targets in (("pairs_train", "training", "lesson"), ("pairs_dev", "dev", "lesson"),
                                   ("honest_dev", "dev", "lesson"), ("corpus", "corpus", None)):
        rows = json.loads(Path(mlflow.artifacts.download_artifacts(run_id=stage1.info.run_id, artifact_path=f"{name}.json")).read_text())
        ds = tracking.table_dataset(rows, name, targets=targets)
        assert ds.digest == digests[name], f"{name}: digest {ds.digest} is not stage 1's {digests[name]}: the data moved, stop and look"
        out[name] = rows
        out["datasets"][name] = (ds, context)
    originals = {h["orig"] for h in out["honest_dev"]}
    out["originals_dev"] = [p for p in out["pairs_dev"] if p["id"] in originals and p["source"] in ("check", "more")]
    return out


# -- 8. notebook helpers: curves from MLflow, picking a run, champion against candidate -------------------------------

SERIES = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6")   # the validated categorical order, never cycled
INK, INK_MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def metric_history(run_id: str, key: str) -> list[tuple[int, float]]:
    """A metric's every logged value, ``[(step, value), ...]`` by step, read back from MLflow (not from memory), so a curve
    in the notebook is exactly what the run recorded."""
    import mlflow

    hist = mlflow.MlflowClient().get_metric_history(run_id, key)
    return sorted((m.step, m.value) for m in hist)


def plot_runs(runs: dict[str, str], panels=(("train/loss", "train loss (per step, thin; 10-step mean, thick)"),
                                            ("held_out/honest_recall_at_5", "dev honest recall@5"),
                                            ("held_out/originals_recall_at_5", "dev originals recall@5")),
              lines: dict[str, tuple[str, float]] | None = None, title: str = ""):
    """One small panel per measure (never two scales on one axis), one line per run, colours in a fixed order.
    ``runs`` is ``{label: run_id}``; ``lines`` draws a dashed reference line on a panel (``{metric key: (label, value)}``,
    e.g. the champion's dev number). Every point comes from ``metric_history``."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, len(panels), figsize=(5.2 * len(panels), 3.6), constrained_layout=True)
    axes = np.atleast_1d(axes)
    for ax, (key, label) in zip(axes, panels):
        for colour, (name, run_id) in zip(SERIES, runs.items()):
            pts = metric_history(run_id, key)
            if not pts:
                continue
            steps, values = zip(*pts)
            if key == "train/loss":
                ax.plot(steps, values, color=colour, lw=0.8, alpha=0.35)
                w = max(1, min(10, len(values) // 3))
                smooth = np.convolve(values, np.ones(w) / w, mode="valid")
                ax.plot(steps[w - 1:], smooth, color=colour, lw=2, label=name)
            else:
                ax.plot(steps, values, color=colour, lw=2, marker="o", ms=4, label=name)
                best = int(np.argmax(values))
                ax.annotate(f"{values[best]:.3f}", (steps[best], values[best]), textcoords="offset points", xytext=(0, 6),
                            ha="center", fontsize=8, color=INK)
        if key in (lines or {}):
            text, value = lines[key]
            ax.axhline(value, color=INK_MUTED, lw=1, ls="--")
            ax.annotate(text, (ax.get_xlim()[0], value), textcoords="offset points", xytext=(4, -11), fontsize=8, color=INK_MUTED)
        ax.set_title(label, fontsize=10, color=INK, loc="left")
        ax.set_xlabel("training step", fontsize=9, color=INK_MUTED)
        ax.grid(True, color=GRID, lw=0.6)
        ax.tick_params(colors=INK_MUTED, labelsize=8)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].legend(fontsize=8, frameon=False)
    if title:
        fig.suptitle(title, fontsize=11, color=INK, x=0.01, ha="left")
    plt.show()
    return fig


def weakest(summary: dict, at_least: int = 5, n: int = 3) -> list[str]:
    """The ``n`` weakest modules among those with at least ``at_least`` questions, as ``"module found/n"``: a module with
    one question scores 0 or 1 by chance, so ``summarise``'s own "weakest" is not read alone (stage 2 did the same)."""
    return [f"{m['module']} {m['found']}/{m['n']}" for m in summary["by_module"] if m["n"] >= at_least][:n]


def pick_best(results: dict[str, dict]) -> str:
    """The label of the run whose best checkpoint is highest on dev honest recall@5, then dev originals recall@5, then the
    earliest run in ``results`` (a tie never goes to the run looked at last). Runs whose best step is 0 (training never
    beat its own start) cannot be picked. Returns None when none qualifies."""
    ok = [(name, res) for name, res in results.items() if res.get("best_dir")]
    if not ok:
        return None
    order = {name: i for i, name in enumerate(results)}
    return max(ok, key=lambda kv: (kv[1]["best"].get("honest_recall_at_5", 0), kv[1]["best"].get("originals_recall_at_5", 0),
                                   -order[kv[0]]))[0]


def runs_table(results: dict[str, dict]):
    """One row per training run: its step 0, its best checkpoint (with the Wilson range), its last step, speed, memory."""
    import pandas as pd

    rows = []
    for name, res in results.items():
        b, s0, f = res["best"], res["step0"], res["final"]
        rows.append({"run": name, "steps": res["steps"], "best step": res["best_step"],
                     "honest step 0": s0.get("honest_recall_at_5"), "honest best": b.get("honest_recall_at_5"),
                     "honest best range": f"[{b.get('honest_recall_at_5_low', 0):.2f}, {b.get('honest_recall_at_5_high', 0):.2f}]",
                     "honest last": f.get("honest_recall_at_5"), "originals step 0": s0.get("originals_recall_at_5"),
                     "originals best": b.get("originals_recall_at_5"), "originals last": f.get("originals_recall_at_5"),
                     "honest hit@1 best": b.get("honest_hit_at_1"), "s/step": round(res["seconds_per_step"], 2),
                     "minutes": round(res["seconds_train"] / 60, 1), "peak GB": round(res["peak_memory_gb"], 1),
                     "checkpointing": res["params"].get("gradient_checkpointing")})
    return pd.DataFrame(rows).set_index("run")


def log_candidate_model(res: dict, tags: dict | None = None) -> None:
    """Log a finished run's best checkpoint as its MLflow model (``mlflow.sentence_transformers.log_model``, with a
    signature and an input example), after the fact, into that same run, and tag it. Used for the one run picked as the
    stage-4 candidate, so the sweep's other runs do not each store 1.3 GB."""
    import mlflow

    if not res.get("best_dir"):
        raise ValueError("this run's best step is 0: there is no trained model to log")
    with mlflow.start_run(run_id=res["run_id"], nested=True):
        _log_best_model(Path(res["best_dir"]), r.BGE_QUERY)
        mlflow.set_tags({"model_logged": "true", **(tags or {})})


def versus(champion_rows: list[dict], candidate_rows: list[dict], n_boot: int = 2000, p_bar: float = P_BAR) -> dict:
    """The paired comparison on the same questions (``retrieval.compare``: candidate minus champion) with two readings.

    ``reading`` is stage 2's bar, which asks for **both** tests: "candidate better" only when the paired bootstrap range of
    the gap sits above zero *and* McNemar's p is under ``p_bar`` (0.05); "champion better" when the range sits below zero
    and p is under it; "tests disagree" when exactly one of the two says there is a difference; "not shown" when neither
    does. ``range_reading`` is the bootstrap range alone (stage 2's per-row column), kept so the two can be read side by side.
    """
    cmp = r.compare(champion_rows, candidate_rows, n_boot=n_boot)
    range_says = "candidate better" if cmp["gap_low"] > 0 else "champion better" if cmp["gap_high"] < 0 else "not shown"
    mcnemar_says = cmp["p_value"] < p_bar
    if range_says != "not shown" and mcnemar_says:
        reading = range_says
    elif range_says != "not shown" or mcnemar_says:
        reading = "tests disagree"
    else:
        reading = "not shown"
    cmp["range_reading"] = range_says
    cmp["reading"] = reading
    cmp["p_bar"] = p_bar
    return cmp


def trim_weights(res: dict) -> float:
    """Delete one run's kept best-checkpoint weights (its checkpoint.json stays), for the runs that were not picked;
    returns the MB freed. Their scores stay in MLflow and on disk."""
    return _trim_folder(Path(res["best_dir"])) if res.get("best_dir") else 0.0


# -- the smoke run: does every piece work together? -------------------------------------------------------------------

SMOKE_DESCRIPTION = """**Smoke test of training.py, not a result.** Checks that every piece of the lab's training code works together on
the real data: training rows from the {n_train_lessons} train-split lessons with champion-picked positives and hard negatives, {n_para}
synthetic questions (qwen3:14b rewrites of train questions, a first slice of the cache), {steps} training steps of bge-large at lr
{lr} and batch {batch}, dev scored every {eval_every} steps, the checkpoint rule and the trim, one step by hand, and a {lora_steps}-step
LoRA run as a child run.

**Why.** Stage 3's notebook runs the real sweeps; this proves the plumbing first, on the same rows and dev sets, so a failure costs a
minute, not an hour.

**Data.** Stage-1 run {stage1} (the newest "pairs · build and freeze", content fingerprint {fingerprint}); split frozen in
data/splits.json (train {split_train} / dev {split_dev} / test {split_test} / holdout {split_holdout} lessons, holdout locked). Training rows:
{rows} ({rows_by_kind}; sources {rows_by_source}; option chips left out, they name no topic). Positives: the own-lesson paragraph the
champion ranks highest; hard negatives: the champion's top paragraph from another train lesson of the same module (any train lesson when
the module has no second one: {lonely}); {skipped} candidates skipped as maybe-right (score at least {ratio} x the positive's).
Dev sets: honest {n_honest} (qwen3:14b paraphrases of dev Check and practice questions, read by Claude at the owner's request, not by a
person; {unread} not yet read) and originals {n_orig} (the same questions as the course wrote them). Test closed, holdout locked.

**Read nothing into the numbers.** {steps} steps is under half an epoch, the dev sets give Wilson ranges about 15 points wide, and one
seed is one draw. Reproduce: `cd notebooks/learning/coach_retrieval && uv run python training.py smoke`."""


def smoke(steps: int = 20, n_paraphrases: int = 40, lr: float = 2e-5, batch: int = 16, eval_every: int = 10, lora_steps: int = 4) -> dict:
    """Build real rows, paraphrase a few train questions, train ``steps`` steps against the real dev sets, try one step by
    hand and a short LoRA run, and log it all as the run "smoke · training.py" (no model is logged)."""
    import mlflow

    from drill.content import build_data

    t_all = time.monotonic()
    tracking.connect()
    s1 = load_stage1()
    stage1 = s1["run"]
    splits = r.load_splits()
    data = build_data()
    all_pairs, corpus_now = r.build_pairs(data), r.build_corpus(data)
    fingerprint = r.content_fingerprint(corpus_now, all_pairs)
    assert fingerprint == stage1.data.params["content_fingerprint"], \
        f"content moved since stage 1 ({fingerprint} vs {stage1.data.params['content_fingerprint']}): rerun stage 1 first"
    corpus = s1["corpus"]
    train_ids = sorted(p["id"] for p in all_pairs if splits.get(p["lesson"]) == "train")
    assert train_ids == sorted(p["id"] for p in s1["pairs_train"]), "the train pairs differ from stage 1's: stop and look"
    print(f"stage 1 run {tracking.short(stage1.info.run_id)}; split {r.split_counts(splits)}; fingerprint {fingerprint}")

    t0 = time.monotonic()
    paras = paraphrase_training_questions(s1["pairs_train"], splits, max_questions=n_paraphrases, corpus=corpus, all_pairs=all_pairs)
    seconds_para = time.monotonic() - t0
    stats: dict = {}
    rows = build_training_rows(s1["pairs_train"], corpus, splits, paraphrases=paras, all_pairs=all_pairs, stats=stats)
    collisions = same_lesson_collisions(rows, batch, SEED, epochs=3)
    print(f"library NO_DUPLICATES sampler, 3 shuffles: {collisions['batches_with_same_lesson']} of {collisions['batches']} batches "
          f"hold two rows of one lesson ({collisions['same_lesson_pairs']} such pairs)")

    dev_sets = {"honest": s1["honest_dev"], "originals": s1["originals_dev"]}
    unread = sum(1 - int(h.get("checked", 0)) for h in s1["honest_dev"])
    para_ds = tracking.table_dataset(paras, f"train paraphrases · {len(paras)} · {r.PARAPHRASE_MODEL}", targets="lesson")
    datasets = [s1["datasets"]["pairs_train"], s1["datasets"]["honest_dev"], s1["datasets"]["pairs_dev"], s1["datasets"]["corpus"],
                (para_ds, "training")]
    desc = SMOKE_DESCRIPTION.format(
        n_train_lessons=r.split_counts(splits)["train"], n_para=len(paras), steps=steps, lr=fmt_lr(lr), batch=batch, eval_every=eval_every,
        lora_steps=lora_steps, stage1=tracking.short(stage1.info.run_id), fingerprint=fingerprint,
        split_train=r.split_counts(splits)["train"], split_dev=r.split_counts(splits)["dev"], split_test=r.split_counts(splits)["test"],
        split_holdout=r.split_counts(splits)["holdout"], rows=len(rows), rows_by_kind=stats["by_kind"], rows_by_source=stats["by_source"],
        lonely=", ".join(stats["modules_without_second_train_lesson"]) or "none", skipped=stats["negatives_skipped_as_maybe_right"],
        ratio=stats["max_negative_ratio"], n_honest=len(s1["honest_dev"]), unread=unread, n_orig=len(s1["originals_dev"]))
    extra_metrics = {"build.seconds_embed": stats["seconds_embed"], "build.seconds_pick": stats["seconds_pick"],
                     "build.seconds_all": stats["seconds_all"], "build.negatives_skipped_as_maybe_right": stats["negatives_skipped_as_maybe_right"],
                     "build.modules_without_second_train_lesson": len(stats["modules_without_second_train_lesson"]),
                     "build.champion_already_first_share": stats["champion_already_first_share"],
                     "build.share_negative_same_module": stats["share_negative_same_module"],
                     "paraphrase.seconds": seconds_para, "paraphrase.n": len(paras),
                     "no_duplicates.share_batches_same_lesson": collisions["share"],
                     "dev.honest_unread": unread}
    res = train(rows, lr=lr, batch=batch, seed=SEED, eval_every=eval_every, save_every=eval_every, max_steps=steps,
                dev_sets=dev_sets, corpus=corpus, splits=splits, run_name="smoke · training.py", description=desc,
                datasets=datasets, all_pairs=all_pairs, out=OUTPUTS / "smoke-training",
                tags={"purpose": "smoke", "stage1_run": tracking.short(stage1.info.run_id)},
                extra_params={"stage1_run_id": stage1.info.run_id, "content_fingerprint": fingerprint},
                extra_metrics=extra_metrics, extra_artifacts={"build_stats.json": stats, "no_duplicates_collisions.json": collisions},
                gradient_checkpointing="auto")

    # One step by hand, on a fresh copy, logged into the same run.
    _free_memory()
    model = fresh_model(seed=SEED)
    one = one_step_by_hand(model, distinct_lesson_batch(rows, batch), lr=lr, fresh_rows=distinct_lesson_batch(rows, batch, skip=batch),
                           gradient_checkpointing="auto")
    del model
    _free_memory()
    with mlflow.start_run(run_id=res["run_id"]):
        mlflow.log_metrics({f"one_step/{k}": float(v) for k, v in one.items() if isinstance(v, (int, float)) and v is not None})
        mlflow.log_dict(one, "one_step_by_hand.json")
    print(f"one step by hand: loss {one['loss_before']:.3f} -> {one['loss_after']:.3f} (by hand {one['loss_by_hand']:.3f}); "
          f"cos to positive {one['cos_pos_before']:.3f} -> {one['cos_pos_after']:.3f}, to hard negative {one['cos_neg_before']:.3f} -> "
          f"{one['cos_neg_after']:.3f}; fresh batch {one['fresh_loss_before']:.3f} -> {one['fresh_loss_after']:.3f}; "
          f"weights moved {one['relative_change']:.2e} of their size")

    lora_res = train(rows, lr=1e-4, batch=batch, seed=SEED, eval_every=lora_steps, save_every=lora_steps, max_steps=lora_steps,
                     dev_sets=dev_sets, corpus=corpus, splits=splits, lora=LORA_DEFAULT,
                     run_name=f"smoke · training.py · LoRA r{LORA_DEFAULT['r']} plumbing · {lora_steps} steps",
                     description=(f"**Smoke child run, not a result.** Checks that LoRA adapters (r {LORA_DEFAULT['r']}, alpha "
                                  f"{LORA_DEFAULT['alpha']}, dropout {LORA_DEFAULT['dropout']}, on the query and value layers) train, "
                                  f"score and save through the same code, and measures the adapter's size against the full model. "
                                  f"{lora_steps} steps at lr 1e-4 (adapters usually want a higher rate than full fine-tuning); same rows "
                                  "and dev sets as the parent run."),
                     datasets=datasets, all_pairs=all_pairs, out=OUTPUTS / "smoke-training-lora", parent_run_id=res["run_id"],
                     tags={"purpose": "smoke"}, gradient_checkpointing="auto")
    seconds_all = time.monotonic() - t_all
    with mlflow.start_run(run_id=res["run_id"]):
        mlflow.log_metrics({"smoke.seconds_all": seconds_all, "lora.adapter_mb": lora_res["adapter_mb"] or 0.0,
                            "lora.params_trainable": lora_res["counts"]["params_trainable"],
                            "lora.seconds_per_step": lora_res["seconds_per_step"]})
    print(f"smoke done in {seconds_all:.0f} s · run {tracking.short(res['run_id'])}")
    return {"run": res, "lora": lora_res, "one_step": one, "build": stats, "collisions": collisions, "paraphrase_seconds": seconds_para,
            "n_paraphrases": len(paras), "seconds_all": seconds_all}


if __name__ == "__main__":
    if sys.argv[1:] == ["smoke"]:
        out = smoke()
        res = out["run"]
        print(json.dumps({"step0": res["step0"], "best_step": res["best_step"], "best": res["best"], "final": res["final"],
                          "seconds_per_step": res["seconds_per_step"], "peak_memory_gb": res["peak_memory_gb"],
                          "lora_adapter_mb": out["lora"]["adapter_mb"], "lora_trainable": out["lora"]["counts"]["params_trainable"],
                          "build": {k: v for k, v in out["build"].items() if k != "check"}, "collisions": out["collisions"],
                          "paraphrase_seconds": out["paraphrase_seconds"]}, indent=1, default=str))
    else:
        print(__doc__)
