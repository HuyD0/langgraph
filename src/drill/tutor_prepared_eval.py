"""The prepared answers as an MLflow evaluation: a versioned dataset, registered prompts, traced judging.

    uv run drill tutor prepared-eval --profile DEFAULT              # every prepared answer, judged by Haiku
    uv run drill tutor prepared-eval --profile DEFAULT --sample 100

What it records, in the app's local experiment (``daily-drill`` on the MLflow at ``MLFLOW_TRACKING_URI``):

- **Prompts**: the drafting prompt and the judge prompt in the prompt registry
  (``tutor_prepared_draft``, ``tutor_prepared_judge``); a new version only when the text changed.
- **Dataset** ``tutor_prepared``: one record per prepared answer. Inputs: the lesson, the question's
  key, its step and words. Expectations: the reference judge's verdict (Sonnet, from the drafting run).
  The run records the dataset's digest, so a score always points at the exact data it measured.
- **Run**: parameters (drafting model, judge, reference judge, prompt versions, git commit, how many),
  tags (``kind = tutor_prepared_eval``, environment, app version), and a pass rate per check.
- **Traces**: one per answer. The root span (``tutor.prepared_answer``) returns the stored answer, with
  its drafting model and fingerprint as attributes; the judge's call is a child span with its prompt and reply.
- **Splits**, as the Evals module teaches. Whole **lessons** are split, so all of a lesson's questions stay
  together (the leakage rule). Each phase's lessons are dealt 60/20/20 across dev (tune the judge here),
  test (report before a release) and holdout (big decisions only, ``--split holdout``), so every phase is
  in every split ("Dev, test and holdout sets": stratify). The assignment is then frozen in
  ``content/prepared_splits.json``: a lesson never moves, and a new one goes to whichever split its phase
  is short of ("Splits that don't move"). A plain hash split left Design and Ship with no holdout at all.
- **Numbers with their margin**: each pass rate with its Wilson 95% interval, and the judge's agreement
  with the reference judge as Cohen's kappa (raw agreement flatters a judge when nearly everything passes).
- **Scorers**: the judge's five checks (each its own pass/fail with the judge's reason), the live
  tutor's code checks (word limit, no maths notation, no exercise code), and ``agrees_with_reference``:
  whether this judge reached the same verdict as the reference judge, overall and per check.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import threading
from pathlib import Path
from typing import Any

from drill import mlflow_names
from drill import tutor_prepared as tp

EXPERIMENT_KIND = "tutor_prepared_eval"
JUDGE_MODEL = "databricks-claude-haiku-5-5"  # fast and cheap; agreement with the reference judge says if it is good enough
CHECKS = ("correct", "answers_it", "plain", "no_giveaway", "standalone")


SPLITS = ("dev", "test", "holdout")
SHARES = {"dev": .6, "test": .2, "holdout": .2}
SPLITS_FILE = Path(__file__).parent / "content" / "prepared_splits.json"
_assigned: dict[str, str] | None = None


def _bucket(lesson_id: str) -> int:
    return int(hashlib.sha256(lesson_id.encode()).hexdigest(), 16) % 100


def assign(data: dict, existing: dict[str, str] | None = None) -> dict[str, str]:
    """Every lesson's split. Lessons already placed keep theirs; each new one, taken in hash order, goes to
    the split its phase is furthest short of (60/20/20), so every phase reaches every split."""
    placed = dict(existing or {})
    phase = phases(data)
    by_phase: dict[str, list[str]] = {}
    for lid in data["lessons"]:
        by_phase.setdefault(phase.get(lid, ""), []).append(lid)
    for ph, lids in by_phase.items():
        counts = {sp: sum(placed.get(l) == sp for l in lids) for sp in SPLITS}
        for lid in sorted((l for l in lids if l not in placed), key=_bucket):
            total = sum(counts.values()) + 1
            short = max(SPLITS, key=lambda sp: (SHARES[sp] * total - counts[sp], -SPLITS.index(sp)))
            placed[lid] = short
            counts[short] += 1
    return dict(sorted(placed.items()))


def load_splits() -> dict[str, str]:
    return json.loads(SPLITS_FILE.read_text()) if SPLITS_FILE.exists() else {}


def save_splits(splits: dict[str, str]) -> None:
    SPLITS_FILE.write_text(json.dumps(splits, indent=1) + "\n")


def split_of(lesson_id: str) -> str:
    """A lesson's frozen split (from ``prepared_splits.json``)."""
    global _assigned
    if _assigned is None:
        _assigned = load_splits()
    return _assigned[lesson_id]


def kind_of(key: str) -> str:
    """The kind of question: term, stops, spot, check, interview or gotcha."""
    return "check" if key.startswith("check:") else key.split(":")[1]


def phases(data: dict) -> dict[str, str]:
    """Each lesson's phase (or the platform track)."""
    out = {}
    for group in [*data["lifecycle"], *data["tracks"]]:
        for mid in group["modules"]:
            m = next((m for m in data["modules"] if m["id"] == mid), None)
            for lid in (m or {}).get("lessons", []):
                out[lid] = group["name"]
    return out


def wilson(passed: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """The pass rate and its Wilson 95% interval (the course's "How sure is that pass rate?")."""
    if not n:
        return 0.0, 0.0, 0.0
    p = passed / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return p, max(0.0, centre - half), min(1.0, centre + half)


def kappa(a: list[bool], b: list[bool]) -> float | None:
    """Cohen's kappa between two judges' yes/no verdicts: agreement beyond what chance alone would give."""
    n = len(a)
    if not n:
        return None
    agree = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    chance = pa * pb + (1 - pa) * (1 - pb)
    return None if chance >= 1 else (agree - chance) / (1 - chance)


def _name(short: str) -> str:
    schema = mlflow_names.prompt_schema()
    return f"{schema}.{short}" if schema else short


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
                              cwd=os.path.dirname(__file__)).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def register_prompts(mlflow) -> dict[str, Any]:
    """The drafting and judge prompts, registered (a new version only when the text changed)."""
    out = {}
    for short, template in (("tutor_prepared_draft", tp.DRAFT), ("tutor_prepared_judge", tp.JUDGE)):
        name = _name(short)
        try:
            latest = mlflow.genai.load_prompt(f"prompts:/{name}@latest", link_to_model=False)
        except Exception:  # noqa: BLE001 - not registered yet
            latest = None
        if latest is not None and latest.template == template:
            out[short] = latest
            continue
        out[short] = mlflow.genai.register_prompt(name=name, template=template, commit_message=f"from {git_commit()[:7]}",
                                                  tags={"source": "src/drill/tutor_prepared.py"})
    return out


def records(data: dict, answers: dict, split: str | None = None) -> list[dict]:
    """One record per prepared answer that still matches its lesson, in ``split`` (or all of them)."""
    phase = phases(data)
    rows = []
    for lid, items in tp.chips(data).items():
        for chip in items:
            rec = answers.get(lid, {}).get(chip["key"])
            if not rec or rec.get("q") != chip["q"] or rec.get("fingerprint") != tp.fingerprint(data, lid, chip) or not rec.get("a"):
                continue
            if split and split_of(lid) != split:
                continue
            ref = rec.get("judge", {})
            rows.append({
                "inputs": {"lesson_id": lid, "key": chip["key"], "step": chip["step"], "question": chip["q"],
                           "phase": phase.get(lid, ""), "kind": kind_of(chip["key"])},
                "expectations": {"reference_pass": bool(ref.get("pass")), **{f"reference_{c}": bool(ref.get(c)) for c in CHECKS}},
            })
    return rows


def strata(rows: list[dict]) -> dict[tuple[str, str], dict[str, int]]:
    """How many answers of each (phase, kind) land in each split: every cell should be filled."""
    out: dict[tuple[str, str], dict[str, int]] = {}
    for r in rows:
        i = r["inputs"]
        cell = out.setdefault((i["phase"], i["kind"]), {s: 0 for s in SPLITS})
        cell[split_of(i["lesson_id"])] += 1
    return out


def dataset(mlflow, experiment_id: str, rows: list[dict], commit: str, split: str):
    """``tutor_prepared_<split>``, brought up to date with ``rows``."""
    from drill.config import is_databricks_uri

    name = mlflow_names.dataset_name(f"tutor_prepared_{split}")
    try:
        ds = mlflow.genai.get_dataset(name=name)
    except Exception:  # noqa: BLE001 - not there yet
        tags = None if is_databricks_uri(mlflow.get_tracking_uri()) else {"source": "src/drill/tutor_prepared_eval.py"}
        ds = mlflow.genai.create_dataset(name=name, experiment_id=experiment_id, tags=tags)
    ds.merge_records(rows)
    if not is_databricks_uri(mlflow.get_tracking_uri()):
        try:
            ds.set_tags({"git_commit": commit, "records": str(len(rows)), "split": split,
                         "split_rule": "lessons dealt 60/20/20 within each phase, frozen in prepared_splits.json"})
        except Exception:  # noqa: BLE001 - older stores keep no dataset tags
            pass
    return ds


def evaluate(profile: str | None, judge_model: str = JUDGE_MODEL, split: str = "dev", workers: int = 10, limit: int = 0) -> dict:
    """Judge one split's prepared answers again, as one MLflow evaluation run. Returns the run id and the numbers."""
    import mlflow
    from mlflow.entities import AssessmentSource, Feedback, SpanType
    from mlflow.genai.scorers import scorer

    from drill.content.build import build_data
    from drill.server.observe import answer_checks, app_version

    data, answers = build_data(), tp.load()
    experiment = mlflow.set_experiment(mlflow_names.experiment())
    commit = git_commit()
    if split not in SPLITS:
        raise ValueError(f"split must be one of {SPLITS}")
    global _assigned
    current = load_splits()
    _assigned = assign(data, current)
    if _assigned != current:
        save_splits(_assigned)  # new lessons placed; old ones never move
    every = records(data, answers)
    table = strata(every)
    empty = [f"{ph}/{kind}: {sp}" for (ph, kind), cell in table.items() for sp, n in cell.items() if n == 0]
    datasets = {sp: dataset(mlflow, experiment.experiment_id, [r for r in every if split_of(r["inputs"]["lesson_id"]) == sp], commit, sp)
                for sp in SPLITS}  # all three kept up to date; only ``split`` is judged
    rows = [r for r in every if split_of(r["inputs"]["lesson_id"]) == split]
    seen: list[dict] = []
    lock = threading.Lock()
    prompts = register_prompts(mlflow)
    fns = {p["id"]: p.get("fn") or "" for p in data["bank"]}
    chat = tp.databricks_chat(judge_model, profile)
    by_key = {(lid, c["key"]): c for lid, items in tp.chips(data).items() for c in items}

    @mlflow.trace(name="tutor.prepared_answer", span_type=SpanType.CHAIN)
    def prepared_answer(lesson_id: str, key: str, step: str, question: str, phase: str = "", kind: str = "") -> str:
        """The stored answer: what a learner sees when they tap the question (no model is asked)."""
        rec = answers[lesson_id][key]
        span = mlflow.get_current_active_span()
        if span is not None:
            span.set_attributes({"draft_model": rec.get("model", ""), "fingerprint": rec.get("fingerprint", ""),
                                 "status": rec.get("status", "")})
        mlflow.update_current_trace(tags={"kind": EXPERIMENT_KIND, "lesson_id": lesson_id, "key": key, "step": step,
                                          "feature": "ask_lesson", "route": "prepared", "split": split, "phase": phase,
                                          "question_kind": kind})
        return rec["a"]

    # The judge's own call is a trace of its own (scorers run after the answer's trace is closed),
    # tagged with the trace it judged; each verdict carries this trace's id, so either leads to the other.
    @mlflow.trace(name="judge", span_type=SpanType.LLM)
    def judge_call(text: str, judged: str) -> tuple[str, str]:
        span = mlflow.get_current_active_span()
        if span is not None:
            span.set_attributes({"model": judge_model})
        mlflow.update_current_trace(tags={"kind": "judge", "judged_trace": judged, "judge_model": judge_model})
        return chat(text), mlflow.get_active_trace_id() or ""

    source = AssessmentSource(source_type="LLM_JUDGE", source_id=judge_model)

    @scorer(name="judge")
    def judge(inputs, outputs, expectations, trace):
        """The five checks, from the judge prompt, plus whether this judge agrees with the reference one."""
        lid, chip = inputs["lesson_id"], by_key[(inputs["lesson_id"], inputs["key"])]
        fn = fns.get(lid, "")
        giveaway = "" if chip["step"] == "Check" else ", and does not say which option of the lesson's Check questions is right"
        reply, judge_trace = judge_call(tp.JUDGE.format(context=tp._context(data, lid), q=chip["q"], how=chip["how"], answer=outputs,
                                                         giveaway=(f" (`{fn}`)" if fn else "") + giveaway), trace.info.trace_id if trace else "")
        verdict = tp._verdict(reply)
        with lock:
            seen.append({"phase": inputs.get("phase", ""), "kind": inputs.get("kind", ""), "verdict": verdict, "reference": expectations or {}})
        meta = {"judge_trace_id": judge_trace}
        out = [Feedback(name=c, value=verdict[c], rationale=verdict["notes"] or None, source=source, metadata=meta) for c in CHECKS]
        out.append(Feedback(name="passes", value=verdict["pass"], rationale=verdict["notes"] or None, source=source, metadata=meta))
        if expectations:
            out.append(Feedback(name="agrees_with_reference", value=verdict["pass"] == expectations.get("reference_pass"), source=source, metadata=meta))
            out += [Feedback(name=f"agrees_on_{c}", value=verdict[c] == expectations.get(f"reference_{c}"), source=source, metadata=meta) for c in CHECKS]
        return out

    @scorer(name="rules")
    def rules(inputs, outputs):
        """The live tutor's own code checks, as passes."""
        checks = answer_checks(outputs, {"exercise_fn": fns.get(inputs["lesson_id"], ""), "word_limit": 200})
        code = AssessmentSource(source_type="CODE", source_id="drill.observe.answer_checks")
        return [Feedback(name="within_word_limit", value=not checks.get("over_word_limit", False), source=code),
                Feedback(name="plain_language", value=not checks["big_o"], source=code),
                Feedback(name="no_solution_leak", value=not checks.get("solution_leak", False), source=code)]

    with mlflow.start_run(run_name=f"tutor-prepared-{split}-{judge_model.removeprefix('databricks-')}-{commit[:7]}") as run:
        mlflow.set_tags({**mlflow_names.context_tags(app_version()), "kind": EXPERIMENT_KIND, "split": split,
                         "mlflow.source.git.commit": commit})
        draft_models = sorted({r.get("model", "") for recs in answers.values() for r in recs.values() if r.get("model")})
        mlflow.log_params({
            "draft_models": ",".join(draft_models), "judge_model": judge_model, "reference_judge": tp.JUDGE_MODEL,
            "draft_prompt": f"{prompts['tutor_prepared_draft'].name}/{prompts['tutor_prepared_draft'].version}",
            "judge_prompt": f"{prompts['tutor_prepared_judge'].name}/{prompts['tutor_prepared_judge'].version}",
            "dataset": mlflow_names.dataset_name(f"tutor_prepared_{split}"), "split": split, "records": len(rows),
            "split_rule": "lessons dealt 60/20/20 within each phase, frozen in prepared_splits.json", "git_commit": commit,
            "strata_missing": len(empty),
        })
        mlflow.log_table({"phase": [k[0] for k in table], "kind": [k[1] for k in table],
                          **{sp: [table[k][sp] for k in table] for sp in SPLITS}}, "strata.json")
        # The records are read out of the split's dataset, and the run names that dataset and its digest:
        # the exact version scored. (Handing evaluate() the dataset object itself hangs on a local MLflow
        # server after a few rows; its records as a list do not.)
        ds = datasets[split]
        mlflow.log_params({"dataset_id": ds.dataset_id, "dataset_digest": ds.digest})
        data_in = [{"inputs": r["inputs"], "expectations": r["expectations"]} for r in ds.to_df()[["inputs", "expectations"]].to_dict("records")]
        if limit:
            data_in = data_in[:limit]  # a quick check of the plumbing, not a result
            mlflow.set_tag("limited", str(limit))
        result = mlflow.genai.evaluate(data=data_in, predict_fn=prepared_answer, scorers=[judge, rules])
        numbers = summary(seen)
        mlflow.log_metrics({k: v for k, v in numbers.items() if isinstance(v, float)})
        mlflow.log_table(per_stratum(seen), "by_stratum.json")
    return {"run_id": run.info.run_id, "experiment_id": experiment.experiment_id, "records": len(rows), "split": split,
            "numbers": numbers, "strata_missing": empty, "metrics": dict(result.metrics)}


def summary(seen: list[dict]) -> dict[str, float]:
    """The pass rate with its interval, and the judge's agreement with the reference judge (kappa and raw)."""
    out: dict[str, float] = {}
    n = len(seen)
    for check in ("pass", *CHECKS):
        mine = [s["verdict"][check] for s in seen]
        ref = [bool(s["reference"].get("reference_pass" if check == "pass" else f"reference_{check}")) for s in seen]
        name = "passes" if check == "pass" else check
        rate, low, high = wilson(sum(mine), n)
        out.update({f"{name}_rate": rate, f"{name}_ci_low": low, f"{name}_ci_high": high,
                    f"{name}_agreement": (sum(a == b for a, b in zip(mine, ref)) / n) if n else 0.0})
        k = kappa(mine, ref)
        if k is not None:
            out[f"{name}_kappa"] = k
    out["answers"] = float(n)
    return out


def per_stratum(seen: list[dict]) -> dict[str, list]:
    """Pass rate and agreement for each phase and each kind of question, so a weak corner can't hide in the average."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for s in seen:
        groups.setdefault(("phase", s["phase"]), []).append(s)
        groups.setdefault(("kind", s["kind"]), []).append(s)
    rows: dict[str, list] = {"by": [], "group": [], "n": [], "pass_rate": [], "ci_low": [], "ci_high": [], "agreement": []}
    for (by, group), items in sorted(groups.items()):
        rate, low, high = wilson(sum(i["verdict"]["pass"] for i in items), len(items))
        rows["by"].append(by)
        rows["group"].append(group)
        rows["n"].append(len(items))
        rows["pass_rate"].append(round(rate, 3))
        rows["ci_low"].append(round(low, 3))
        rows["ci_high"].append(round(high, 3))
        rows["agreement"].append(round(sum(i["verdict"]["pass"] == bool(i["reference"].get("reference_pass")) for i in items) / len(items), 3))
    return rows
