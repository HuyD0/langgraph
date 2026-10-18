"""Judges in the prompt registry: one tutor_judge version per judge setup, champion and challenger aliases."""

from __future__ import annotations

import pytest

mlflow = pytest.importorskip("mlflow")

from drill import tutor_prepared as tp  # noqa: E402
from drill import tutor_prepared_eval as tpe  # noqa: E402


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.delenv("MLFLOW_EXPERIMENT_NAME", raising=False)
    monkeypatch.delenv("MLFLOW_EXPERIMENT_ID", raising=False)
    mlflow.set_tracking_uri(f"sqlite:///{tmp_path}/mlflow.db")
    mlflow.set_registry_uri(f"sqlite:///{tmp_path}/mlflow.db")
    mlflow.set_experiment("judges")
    yield
    mlflow.set_tracking_uri(None)


def judge_run(model, provider="foundry", mode="batch"):
    with mlflow.start_run() as run:
        mlflow.log_params({"judge_model": model, "provider": provider, "mode": mode, "deployment": f"{model}-dep"})
    return run.info.run_id


def test_one_version_per_judge_setup_with_its_model(store):
    a = tpe.register_judge(mlflow, "foundry", "gpt-5.4", "batch", "gpt-5.4-batch")
    again = tpe.register_judge(mlflow, "foundry", "gpt-5.4", "batch", "gpt-5.4-batch")
    b = tpe.register_judge(mlflow, "foundry", "gpt-5.6-luna", "inline")
    assert a.version == again.version != b.version
    assert a.template == tp.JUDGE and a.model_config["model_name"] == "gpt-5.4"


def test_the_judge_in_use_is_champion(store):
    v = tpe.ensure_champion(mlflow)
    assert v.model_config["model_name"] == tp.JUDGE_MODEL
    assert tpe.ensure_champion(mlflow).version == v.version


def test_challenger_points_at_the_version_a_run_tested(store):
    champion = tpe.ensure_champion(mlflow)
    rid = judge_run("gpt-5.4")
    named = tpe.set_judge_alias(mlflow, "challenger", rid, "passed the rule on dev")
    challenger = mlflow.MlflowClient().get_prompt_version_by_alias(champion.name, "challenger")
    assert named == f"{challenger.name}/{challenger.version}" and challenger.version != champion.version
    run = mlflow.get_run(rid)
    assert run.data.params["judge_version"] == named and run.data.tags["alias_challenger"].startswith(named)
    assert mlflow.MlflowClient().get_prompt_version_by_alias(champion.name, "champion").version == champion.version
