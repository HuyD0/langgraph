"""The milestone 9 help-center lab: a live run keeps its answers when one request fails."""

from __future__ import annotations

import pytest

from drill import rag_lab as R


@pytest.fixture
def offline_mlflow(monkeypatch):
    import mlflow

    monkeypatch.setenv("DRILL_NOTEBOOK_OFFLINE", "1")  # a fresh temporary MLflow store
    R.use_mlflow("rag-lab-test")
    yield
    mlflow.clear_active_model()
    mlflow.set_tracking_uri(None)


def test_one_failing_live_request_does_not_lose_the_others(offline_mlflow):
    lab = R.Lab(live=True)
    questions = R.QUESTIONS[:3]
    broken = questions[1]["question"]

    def llm(key, prompt, temperature):  # stands in for Ollama: one question's call fails
        if broken in prompt:
            raise TimeoutError("Ollama took too long")
        return R.DECLINE

    lab.llm = llm
    results = lab.run(questions, ["v1"], quiet=True)
    assert [r["qid"] for r in results] == [q["id"] for q in questions]  # all three kept, in order
    assert "error" not in results[0] and "error" not in results[2]
    assert results[1]["passed"] is False and "Ollama took too long" in results[1]["error"]


def test_a_recorded_run_still_stops_on_a_missing_recording(offline_mlflow):
    lab = R.Lab(live=False)
    lab.recorded = {}
    with pytest.raises(KeyError):
        lab.run(R.QUESTIONS[:1], ["v1"], quiet=True)
