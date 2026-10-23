"""Compare local embedding models on the course's own text: which one finds the right lesson?

``drill experiment embeddings`` runs this. Everything is free and stays on this computer (Ollama serves the
models), and it is logged as one MLflow run per model setup under a parent run that compares them.

- **What is searched:** every Learn paragraph in the course, one chunk each (the longest is under 200
  words, so no chunk is cut off by a model's length limit).
- **The questions:** a sample of the Check questions (150 by default), each module in proportion to its
  size, picked the same way on every run. The right answer is the question's own lesson. Only the
  questions are sampled: the search always covers every paragraph, since a smaller haystack flatters
  every model.
- **The measure:** recall@5 (the share of questions with at least one of their lesson's paragraphs in the
  five closest chunks), with its Wilson interval, recall per module (the weakest group, as in "Embedding
  models have blind spots"), MRR, and the time to embed everything.
- **Paired comparison:** every setup answers the same questions, so two setups are compared on the
  questions only one of them found, with McNemar's test (the course's "Real win or luck").

Each model is used with the prompt its makers recommend for search, and once without, because leaving
it out is a common mistake. embeddinggemma also runs with its vectors cut to 256 numbers: it was trained
so the first numbers carry the most meaning, which is the "How big should a vector be?" decision.

Caveat, said in the run too: Check questions are written from the Learn text, so they share words with
it. Real users' questions are harder, so treat the numbers as an upper bound and the ranking as the
finding.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from collections import defaultdict
from dataclasses import dataclass

from drill import mlflow_names
from drill.tutor_prepared_eval import mcnemar, wilson

OLLAMA = "http://localhost:11434"
K = 5


@dataclass(frozen=True)
class Setup:
    name: str            # shown in tables and the run name
    model: str           # the Ollama model
    query_prefix: str    # put before each question
    doc_prefix: str      # put before each chunk
    dims: int | None     # keep only the first numbers of each vector (None: all of them)


# The makers' recommended search prompts: BGE's model card (bge-large-en-v1.5) and Google's for embeddinggemma.
BGE_QUERY = "Represent this sentence for searching relevant passages: "
GEMMA_QUERY, GEMMA_DOC = "task: search result | query: ", "title: none | text: "

SETUPS = [
    Setup("bge-large · with prompt", "bge-large", BGE_QUERY, "", None),
    Setup("bge-large · no prompt", "bge-large", "", "", None),
    Setup("embeddinggemma 768 · with prompt", "embeddinggemma", GEMMA_QUERY, GEMMA_DOC, None),
    Setup("embeddinggemma 256 · with prompt", "embeddinggemma", GEMMA_QUERY, GEMMA_DOC, 256),
    Setup("embeddinggemma 768 · no prompt", "embeddinggemma", "", "", None),
]


def corpus(data: dict) -> list[dict]:
    """Every Learn paragraph, one chunk each, with its lesson and module."""
    module_of = {lid: m["id"] for m in data["modules"] for lid in m["lessons"]}
    return [{"id": f"{lid}#{i}", "lesson": lid, "module": module_of.get(lid, ""), "text": p}
            for lid, lesson in data["lessons"].items() for i, p in enumerate(lesson["learn"]) if p.strip()]


def questions(data: dict) -> list[dict]:
    """Every Check question (the lesson's own and its extra ones); the right lesson is the one it belongs to."""
    module_of = {lid: m["id"] for m in data["modules"] for lid in m["lessons"]}
    out = []
    for lid, lesson in data["lessons"].items():
        asks = [lesson["check"]] + list(lesson.get("more") or [])
        for i, ask in enumerate(asks):
            if ask:
                out.append({"id": f"{lid}?{i}", "lesson": lid, "module": module_of.get(lid, ""), "text": ask[0]})
    return out


def sample(qs: list[dict], n: int, seed: int = 7) -> list[dict]:
    """About ``n`` questions, each module's share in proportion to its size (at least one each), picked in a seeded
    hash order: the same seed picks the same questions on every run, and a new lesson never reshuffles the rest."""
    if n <= 0 or n >= len(qs):
        return qs
    groups: dict[str, list[dict]] = defaultdict(list)
    for q in qs:
        groups[q["module"]].append(q)
    key = lambda q: hashlib.sha256(f"{seed}:{q['id']}".encode()).hexdigest()
    picked = []
    for items in groups.values():
        take = max(1, round(n * len(items) / len(qs)))
        picked += sorted(items, key=key)[:take]
    order = {q["id"]: i for i, q in enumerate(qs)}
    return sorted(picked, key=lambda q: order[q["id"]])


def fingerprint(chunks: list[dict], qs: list[dict]) -> str:
    """Changes when the course's text or questions change, so runs on different content are never compared."""
    h = hashlib.sha256()
    for item in chunks + qs:
        h.update(f"{item['id']}\x00{item['text']}\x00".encode())
    return h.hexdigest()[:12]


def ollama_embed(model: str, texts: list[str], batch: int = 32) -> list[list[float]]:
    out: list[list[float]] = []
    for start in range(0, len(texts), batch):
        body = json.dumps({"model": model, "input": texts[start:start + batch], "truncate": True}).encode()
        req = urllib.request.Request(f"{OLLAMA}/api/embed", body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            out.extend(json.loads(r.read())["embeddings"])
    return out


def unit(vectors, dims: int | None):
    """Keep the first ``dims`` numbers, then scale each vector to length 1 so a dot product is cosine similarity."""
    import numpy as np

    v = np.asarray(vectors, dtype="float32")
    if dims:
        v = v[:, :dims]
    return v / np.linalg.norm(v, axis=1, keepdims=True).clip(min=1e-12)


def rank(q, d, chunks: list[dict], qs: list[dict], k: int = K) -> list[dict]:
    """For each question: its top-k chunks, whether its lesson is among them, and the rank of the first hit."""
    import numpy as np

    scores = q @ d.T
    order = np.argsort(-scores, axis=1)
    rows = []
    for i, item in enumerate(qs):
        lessons = [chunks[j]["lesson"] for j in order[i]]
        first = next((n + 1 for n, lid in enumerate(lessons) if lid == item["lesson"]), None)
        rows.append({"id": item["id"], "lesson": item["lesson"], "module": item["module"], "hit": bool(first and first <= k),
                     "first_rank": first, "top": [chunks[j]["id"] for j in order[i][:k]]})
    return rows


def summary(rows: list[dict]) -> dict:
    hits = sum(r["hit"] for r in rows)
    p, low, high = wilson(hits, len(rows))
    mrr = sum(1 / r["first_rank"] for r in rows if r["first_rank"]) / len(rows)
    return {"recall_at_5": p, "recall_ci_low": low, "recall_ci_high": high, "mrr": mrr, "questions": len(rows)}


def by_module(rows: list[dict]) -> dict[str, tuple[int, int]]:
    out: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in rows:
        out[r["module"]][0] += r["hit"]
        out[r["module"]][1] += 1
    return {m: (h, n) for m, (h, n) in out.items()}


def paired(a: list[dict], b: list[dict]) -> dict:
    """Questions only A found, only B found, and McNemar's p-value on those."""
    only_a = sum(x["hit"] and not y["hit"] for x, y in zip(a, b))
    only_b = sum(y["hit"] and not x["hit"] for x, y in zip(a, b))
    return {"only_first": only_a, "only_second": only_b, "p_value": mcnemar(only_a, only_b)}


DESCRIPTION = """**Question:** which local embedding model finds the right lesson for a question, and does its search prompt or a shorter vector change that?

**What ran:** {setups} on Ollama on this computer. Searched: {chunks} chunks (every Learn paragraph). Questions: {questions} of the course's {total} Check questions, a sample stratified by module (seed {seed}; each module in proportion to its size, the same questions on every run). Content fingerprint {fp}.

**How it is measured:** recall@{k} (a question is found when one of its lesson's paragraphs is in the {k} closest chunks), Wilson 95% interval, MRR, recall per module; setups compared pairwise on the same questions with McNemar's test. Check questions are written from the Learn text, so they share words with it: treat the numbers as an upper bound and the ranking as the finding.

**Reproduce:** `{command}` (free; needs `ollama pull bge-large` and `ollama pull embeddinggemma`)."""


def run(data: dict, setups: list[Setup] = SETUPS, embed=ollama_embed, n: int = 150, seed: int = 7,
        command: str = "uv run drill experiment embeddings") -> dict:
    """Search every paragraph (a smaller haystack would flatter every model); ask a sample of the questions."""
    import mlflow

    chunks, everything = corpus(data), questions(data)
    qs = sample(everything, n, seed)
    fp = fingerprint(chunks, qs)
    mlflow.set_experiment(mlflow_names.experiment())
    models = sorted({s.model for s in setups})
    parent_name = f"embeddings compare · {' vs '.join(models)} · {len(setups)} setups · all Learn paragraphs · {len(qs)}-question sample"
    results: dict[str, list[dict]] = {}
    numbers: dict[str, dict] = {}
    cache: dict[tuple[str, str, tuple[str, ...]], list] = {}
    with mlflow.start_run(run_name=parent_name, tags={"kind": "embedding_compare", "purpose": "exploration", "content_fingerprint": fp,
                                                      "mlflow.note.content": DESCRIPTION.format(setups=", ".join(s.name for s in setups),
                                                                                                chunks=len(chunks), questions=len(qs), total=len(everything), seed=seed, fp=fp, k=K, command=command)}):
        mlflow.log_dict({"seed": seed, "questions": [q["id"] for q in qs]}, "sample.json")
        mlflow.log_params({"k": K, "chunks": len(chunks), "questions": len(qs), "all_questions": len(everything), "seed": seed, "models": ",".join(models), "source": "ollama"})
        for s in setups:
            with mlflow.start_run(run_name=f"embeddings · {s.name} · recall@{K} · {len(qs)}-question sample", nested=True,
                                  tags={"kind": "embedding_compare", "content_fingerprint": fp,
                                        "mlflow.note.content": f"One setup of the parent run: {s.model}, "
                                                               f"{'its recommended search prompt' if s.query_prefix else 'no search prompt'}, "
                                                               f"{s.dims or 'all'} numbers per vector. Reproduce: `{command}`."}):
                t0 = time.monotonic()
                key_d = (s.model, s.doc_prefix, tuple(c["text"] for c in chunks))
                if key_d not in cache:
                    cache[key_d] = embed(s.model, [s.doc_prefix + c["text"] for c in chunks])
                key_q = (s.model, s.query_prefix, tuple(q["text"] for q in qs))
                if key_q not in cache:
                    cache[key_q] = embed(s.model, [s.query_prefix + q["text"] for q in qs])
                seconds = time.monotonic() - t0
                d, q = unit(cache[key_d], s.dims), unit(cache[key_q], s.dims)
                rows = rank(q, d, chunks, qs)
                m = summary(rows) | {"seconds": round(seconds, 1), "dims": int(d.shape[1])}
                mods = by_module(rows)
                worst = min(mods, key=lambda x: mods[x][0] / mods[x][1])
                m["weakest_module_recall"] = mods[worst][0] / mods[worst][1]
                mlflow.log_params({"model": s.model, "query_prefix": s.query_prefix or "(none)", "doc_prefix": s.doc_prefix or "(none)",
                                   "dims": int(d.shape[1])})
                mlflow.log_metrics({k: v for k, v in m.items() if isinstance(v, (int, float))})
                mlflow.set_tag("weakest_module", worst)
                mlflow.log_table({"module": list(mods), "found": [h for h, _ in mods.values()], "questions": [n for _, n in mods.values()],
                                  "recall": [round(h / n, 3) for h, n in mods.values()]}, "recall_by_module.json")
                mlflow.log_table({"question": [r["id"] for r in rows], "hit": [r["hit"] for r in rows],
                                  "first_rank": [r["first_rank"] or -1 for r in rows], "top5": [" ".join(r["top"]) for r in rows]}, "questions.json")
                results[s.name], numbers[s.name] = rows, m | {"weakest_module": worst}
        names = list(results)
        pairs = [{"first": a, "second": b, **paired(results[a], results[b])} for i, a in enumerate(names) for b in names[i + 1:]]
        best = max(names, key=lambda n: numbers[n]["recall_at_5"])
        mlflow.log_table({"setup": names, **{k: [numbers[n][k] for n in names] for k in ("recall_at_5", "recall_ci_low", "recall_ci_high",
                                                                                       "mrr", "weakest_module", "weakest_module_recall", "dims", "seconds")}},
                         "comparison.json")
        mlflow.log_table({k: [p[k] for p in pairs] for k in ("first", "second", "only_first", "only_second", "p_value")}, "paired.json")
        mlflow.log_metric("best_recall_at_5", numbers[best]["recall_at_5"])
        mlflow.set_tag("best_setup", best)
    return {"numbers": numbers, "pairs": pairs, "best": best, "fingerprint": fp, "chunks": len(chunks), "questions": len(qs)}
