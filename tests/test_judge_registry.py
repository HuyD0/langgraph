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


def judge_run(model, provider="foundry", mode="batch", checklist=1, kind=tpe.EXPERIMENT_KIND, legacy_number=None):
    with mlflow.start_run() as run:
        mlflow.set_tag("kind", kind)
        params = {"judge_model": model, "provider": provider, "mode": mode, "deployment": f"{model}-dep"}
        if legacy_number is None:
            params["checklist"] = checklist
        else:
            params["judge_version"] = legacy_number   # how runs before 00a6067 logged the checklist number
        mlflow.log_params(params)
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


def test_checklist_two_is_its_own_prompt_version_and_judge_version(store):
    one = tpe.register_prompts(mlflow, judge_version=1)["tutor_prepared_judge"]
    two = tpe.register_prompts(mlflow, judge_version=2)["tutor_prepared_judge"]
    again = tpe.register_prompts(mlflow, judge_version=1)["tutor_prepared_judge"]
    assert one.version == again.version != two.version and two.template == tp.JUDGE2
    client = mlflow.MlflowClient()
    assert client.get_prompt_version_by_alias(one.name, "production").version == one.version
    assert client.get_prompt_version_by_alias(one.name, "candidate").version == two.version
    a = tpe.register_judge(mlflow, "foundry", "gpt-5.4-mini", "batch", judge_version=1)
    b = tpe.register_judge(mlflow, "foundry", "gpt-5.4-mini", "batch", judge_version=2)
    assert a.version != b.version and b.template == tp.JUDGE2


def test_summary_compares_only_the_checks_the_reference_has():
    seen = [{"verdict": {"pass": True, "no_contradiction": True, "within_lesson": False, "answers_it": True, "no_giveaway": True,
                         "standalone": True, "concise": True, "tone": True},
             "reference": {"reference_pass": True, "reference_correct": True, "reference_answers_it": True, "reference_plain": True,
                           "reference_no_giveaway": True, "reference_standalone": True}}] * 4
    out = tpe.summary(seen, None, tp.CHECKS2)
    assert out["within_lesson_rate"] == 0.0 and "within_lesson_agreement" not in out
    assert out["answers_it_agreement"] == 1.0 and out["passes_agreement"] == 1.0


def test_a_checklist_two_run_links_to_a_checklist_two_judge_version(store):
    tpe.ensure_champion(mlflow)
    rid = judge_run("gpt-5.6-luna", mode="inline", checklist=2)
    v = tpe.link_judge(mlflow, rid)
    fresh = mlflow.MlflowClient().get_prompt_version(v.name, v.version)   # tags are set after registering, so re-read
    assert v.template == tp.JUDGE2 and (fresh.tags or {}).get("checklist") == "2"
    assert mlflow.get_run(rid).data.params["judge_version"] == f"{v.name}/{v.version}"   # the link, not the checklist number
    assert tpe.link_judge(mlflow, rid).version == v.version                               # a second call reads the link back


def test_only_judge_eval_runs_can_be_linked_and_legacy_numbers_are_read(store):
    tpe.ensure_champion(mlflow)
    with pytest.raises(ValueError):
        tpe.link_judge(mlflow, judge_run("gpt-5.4", kind="draft_uncertainty"))
    v = tpe.link_judge(mlflow, judge_run("gpt-5.4-mini", mode="inline", legacy_number="2"))
    assert v.template == tp.JUDGE2


def test_a_store_that_is_down_does_not_get_a_new_champion(store, monkeypatch):
    champion = tpe.ensure_champion(mlflow)

    class Down:
        def get_prompt_version_by_alias(self, *a):
            raise RuntimeError("connection refused")

    monkeypatch.setattr(mlflow, "MlflowClient", lambda: Down())
    with pytest.raises(RuntimeError):
        tpe.ensure_champion(mlflow)
    monkeypatch.undo()
    assert mlflow.MlflowClient().get_prompt_version_by_alias(champion.name, "champion").version == champion.version


def test_a_judge_run_can_be_named_instead_of_its_id(tmp_path, monkeypatch):
    """Recordings in the public repo keep a run's name, not its id, so judge-alias must find it by name."""
    import mlflow

    from drill import tutor_prepared_eval as tpe

    monkeypatch.setenv("DRILL_MLFLOW_EXPERIMENT", "judge-names")
    mlflow.set_tracking_uri(f"sqlite:///{tmp_path / 'm.db'}")
    mlflow.set_experiment("judge-names")
    with mlflow.start_run(run_name="judge x · foundry batch · prepared answers dev-sample-3", tags={"kind": tpe.EXPERIMENT_KIND}) as run:
        pass
    with mlflow.start_run(run_name="not a judge run"):
        pass
    assert tpe.find_judge_run(mlflow, "judge x · foundry batch · prepared answers dev-sample-3") == run.info.run_id
    assert tpe.find_judge_run(mlflow, run.info.run_id) == run.info.run_id
    with pytest.raises(ValueError, match="0 judge eval runs"):
        tpe.find_judge_run(mlflow, "not a judge run")
