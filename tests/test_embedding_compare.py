"""The embedding comparison, with a fake embedder: the right numbers, and a run anyone can find again."""

import mlflow

from drill import embedding_compare as ec

DATA = {
    "modules": [{"id": "rag", "lessons": ["a", "b"]}, {"id": "evals", "lessons": ["c"]}],
    "lessons": {
        "a": {"learn": ["apples are red", "apples grow on trees"], "check": ["what colour are apples?", [], 0, ""], "more": []},
        "b": {"learn": ["bananas are yellow"], "check": ["what colour are bananas?", [], 0, ""], "more": [["are bananas long?", [], 0, ""]]},
        "c": {"learn": ["cherries are small"], "check": ["how big is a cherry?", [], 0, ""], "more": []},
    },
}
WORDS = ["apple", "banana", "cherr"]


def fake(model, texts):
    """One number per fruit word, so a question lands on its own lesson; 'tiny' setups lose the cherry number."""
    return [[1.0 if w in t.lower() else 0.0 for w in WORDS] + [0.01] for t in texts]


def test_corpus_and_questions_cover_every_paragraph_and_check():
    assert [c["id"] for c in ec.corpus(DATA)] == ["a#0", "a#1", "b#0", "c#0"]
    assert [q["id"] for q in ec.questions(DATA)] == ["a?0", "b?0", "b?1", "c?0"]


def test_a_cut_vector_can_lose_what_its_last_numbers_carried(tmp_path, monkeypatch):
    monkeypatch.setenv("DRILL_MLFLOW_EXPERIMENT", "embeddings-test")
    mlflow.set_tracking_uri(f"sqlite:///{tmp_path / 'm.db'}")
    setups = [ec.Setup("full", "m", "", "", None), ec.Setup("cut", "m", "", "", 2)]
    out = ec.run(DATA, setups, embed=fake, n=0, command="test")
    full, cut = out["numbers"]["full"], out["numbers"]["cut"]
    assert full["recall_at_5"] == 1.0
    # with k=5 over 4 chunks everything is found, so check the first hit's rank instead: MRR drops for the cherry question
    assert cut["mrr"] < full["mrr"]
    assert out["best"] == "full"
    runs = mlflow.search_runs(experiment_names=["embeddings-test"])
    assert len(runs) == 3                                   # the parent and one per setup
    parent = runs[runs["tags.mlflow.parentRunId"].isna()].iloc[0]
    assert parent["tags.mlflow.runName"].startswith("embeddings compare · m · 2 setups")
    assert "**Reproduce:** `test`" in parent["tags.mlflow.note.content"]


def test_the_sample_is_stratified_and_the_same_every_time():
    qs = [{"id": f"{m}{i}", "module": m} for m, size in (("big", 60), ("mid", 30), ("small", 10)) for i in range(size)]
    one, two = ec.sample(qs, 20), ec.sample(qs, 20)
    assert one == two
    counts = {m: sum(q["module"] == m for q in one) for m in ("big", "mid", "small")}
    assert counts == {"big": 12, "mid": 6, "small": 2}
    # a new question elsewhere doesn't reshuffle a module's picks
    assert [q for q in ec.sample(qs + [{"id": "new", "module": "other"}], 20) if q["module"] == "small"] == \
           [q for q in one if q["module"] == "small"]
    assert ec.sample(qs, 0) == qs
