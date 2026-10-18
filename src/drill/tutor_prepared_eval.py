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
- **Traces**: one per answer. The root span (``tutor.prepared_answer``) returns the stored answer, with its
  drafting model and fingerprint as attributes, and tags for split, phase and kind. The judge's verdicts are
  assessments on that trace; the ``passes`` verdict carries the judge's model, prompt version, tokens and
  time. (The judge's call is not a trace of its own: on a local SQLite-backed MLflow server every extra write
  queues behind the others.)
- **Scorers**: ``judge`` (``passes`` and the five checks, each with the judge's reason when it fails) and
  ``rules`` (the live tutor's code checks: word limit, no maths notation, no exercise code).
- **Cost**: the judge's calls, tokens, seconds and list-price cost, in total and per answer.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from drill import mlflow_names
from drill import tutor_prepared as tp

EXPERIMENT_KIND = "tutor_prepared_eval"
JUDGE_MODEL = "databricks-claude-haiku-5-5"  # fast and cheap; agreement with the reference judge says if it is good enough
CHECKS = ("correct", "answers_it", "plain", "no_giveaway", "standalone")
KAPPA_GATE = 0.6  # "substantial" agreement: below it, the judge disagrees with the reference too often to monitor with


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


def register_prompts(mlflow, judge_version: int = 1) -> dict[str, Any]:
    """The drafting prompt and the judge prompt (the requested checklist version), registered: a version is
    added only when its text is new. ``production`` points at what is in use (the drafter and checklist 1);
    another checklist version gets ``candidate``."""
    out = {}
    client = mlflow.MlflowClient()
    wanted = (("tutor_prepared_draft", tp.DRAFT, "production", "1"),
              ("tutor_prepared_judge", tp.JUDGES[judge_version][0], "production" if judge_version == 1 else "candidate", str(judge_version)))
    for short, template, alias, checklist in wanted:
        name = _name(short)
        found = None
        try:
            versions = client.search_prompt_versions(name)
            for v in getattr(versions, "prompt_versions", versions) or []:
                if v.template == template:
                    found = v
        except Exception:  # noqa: BLE001 - not registered yet
            found = None
        out[short] = found or mlflow.genai.register_prompt(name=name, template=template, commit_message=f"checklist {checklist}, from {git_commit()[:7]}",
                                                           tags={"source": "src/drill/tutor_prepared.py", "checklist": checklist})
        try:
            mlflow.genai.set_prompt_alias(name, alias, int(out[short].version))
        except Exception:  # noqa: BLE001 - a store without aliases
            pass
    return out


# -- the judge in the prompt registry: champion and challenger -------------------------------------------
# A judge is a prompt plus a model. Each judge setup is one version of the registered prompt ``tutor_judge``
# (the judge prompt, with the model attached as its model config). Aliases say which is which:
# ``champion`` is the judge in use; ``challenger`` a candidate that passed the rule on dev. A challenger is
# promoted to champion only after its one look at test and a check against a person's grades.
JUDGE_REGISTRY = "tutor_judge"


def register_judge(mlflow, provider: str, model: str, mode: str = "inline", deployment: str = "", max_tokens: int = 2000,
                   judge_version: int = 1):
    """This judge setup (checklist version, model, provider, mode) as a version of ``tutor_judge`` (the existing
    version when nothing changed)."""
    template = tp.JUDGES[judge_version][0]
    name, key = _name(JUDGE_REGISTRY), f"{provider}:{model}:{mode}:v{judge_version}"
    client = mlflow.MlflowClient()
    try:
        found = client.search_prompt_versions(name)
        for v in getattr(found, "prompt_versions", found) or []:
            if (v.tags or {}).get("judge") == key and v.template == template:
                return v
    except Exception:  # noqa: BLE001 - not registered yet
        pass
    v = mlflow.genai.register_prompt(name=name, template=template, commit_message=f"judge {key}, from {git_commit()[:7]}",
                                     model_config={"provider": provider, "model_name": model, "max_tokens": max_tokens})
    for k, val in {"judge": key, "provider": provider, "mode": mode, "deployment": deployment or model, "checklist": str(judge_version)}.items():
        mlflow.genai.set_prompt_version_tag(name, v.version, k, val)
    return v


def ensure_champion(mlflow):
    """The judge in use holds ``champion``: the one that judged the prepared answers, until a challenger is promoted."""
    name = _name(JUDGE_REGISTRY)
    try:
        return mlflow.MlflowClient().get_prompt_version_by_alias(name, "champion")
    except Exception:  # noqa: BLE001 - no champion yet
        v = register_judge(mlflow, "databricks", tp.JUDGE_MODEL)
        mlflow.genai.set_prompt_alias(name, "champion", int(v.version))
        return v


def link_judge(mlflow, run_id: str):
    """Record on a judge run which ``tutor_judge`` version it tested (registering it if needed). Returns the version."""
    run = mlflow.get_run(run_id)
    p = run.data.params
    if "judge_version" in p:
        return mlflow.MlflowClient().get_prompt_version(_name(JUDGE_REGISTRY), p["judge_version"].rsplit("/", 1)[1])
    v = register_judge(mlflow, p.get("provider", "databricks"), p["judge_model"], p.get("mode", "inline"), p.get("deployment", ""),
                       judge_version=int(p.get("judge_version", 1)))
    client = mlflow.MlflowClient()
    client.log_param(run_id, "judge_version", f"{v.name}/{v.version}")
    try:
        client.link_prompt_version_to_run(run_id, v)
    except Exception:  # noqa: BLE001 - older stores
        pass
    return v


def set_judge_alias(mlflow, alias: str, run_id: str, reason: str = "") -> str:
    """Point ``alias`` at the judge version a run tested, and note on the run why. Returns "name/version"."""
    v = link_judge(mlflow, run_id)
    mlflow.genai.set_prompt_alias(v.name, alias, int(v.version))
    mlflow.genai.set_prompt_version_tag(v.name, v.version, f"{alias}_evidence", run_id)
    client = mlflow.MlflowClient()
    client.set_tag(run_id, f"alias_{alias}", f"{v.name}/{v.version}" + (f": {reason}" if reason else ""))
    return f"{v.name}/{v.version}"


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
                # labels to filter the dataset by in the UI; "source" follows the course's three kinds of
                # example: golden (you checked it), past failure (the reference judge failed it), or prepared
                "tags": {"split": split_of(lid) if _assigned else "", "phase": phase.get(lid, ""), "kind": kind_of(chip["key"]),
                         "source": "golden" if rec.get("status") in ("checked", "rejected") else "past_failure" if not ref.get("pass") else "prepared",
                         "human_verdict": rec.get("status") if rec.get("status") in ("checked", "rejected") else "",
                         "draft_model": rec.get("model", ""), "reference_judge": ref.get("model", ""), "fingerprint": rec.get("fingerprint", "")},
            })
    return rows


def stratified_sample(rows: list[dict], n: int) -> list[dict]:
    """``n`` answers for tuning the judge: every answer the reference judge failed (they are rare, and the
    point is to see whether this judge catches them), then passed answers shared out across phase and kind
    in proportion, picked in hash order so the same sample comes back every time."""
    failed = [r for r in rows if not r["expectations"]["reference_pass"]]
    passed = [r for r in rows if r["expectations"]["reference_pass"]]
    want = max(0, n - len(failed))
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in passed:
        groups.setdefault((r["inputs"]["phase"], r["inputs"]["kind"]), []).append(r)
    chosen: list[dict] = []
    for _, items in sorted(groups.items()):
        items.sort(key=lambda r: hashlib.sha256(f"{r['inputs']['lesson_id']}/{r['inputs']['key']}".encode()).hexdigest())
        chosen += items[:round(want * len(items) / max(1, len(passed)))]
    return failed + chosen


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
                         "version": f"tutor_prepared_{split}-{time.strftime('%Y-%m-%d')}-{commit[:7]}",
                         "split_rule": "lessons dealt 60/20/20 within each phase, frozen in prepared_splits.json"})
        except Exception:  # noqa: BLE001 - older stores keep no dataset tags
            pass
    return ds


def evaluate(profile: str | None, judge_model: str = JUDGE_MODEL, split: str = "dev", workers: int = 10, limit: int = 0,
             sample: int = 0, provider: str = "databricks", mode: str = "inline", deployment: str = "",
             record: Path | None = None, purpose: str = "", judge_version: int = 1) -> dict:
    """Judge one split's prepared answers again, as one MLflow evaluation run. Returns the run id and the numbers.

    ``provider="foundry"`` judges on a Microsoft Foundry deployment (``deployment``; sign in with ``az login`` and set
    ``AZURE_OPENAI_ENDPOINT``), ``mode="batch"`` as batch jobs at half price, sent inside the run before the scorers
    look the replies up. ``record`` also writes the run's verdicts to a file a notebook can replay."""
    if provider not in ("databricks", "foundry") or mode not in ("inline", "batch") or (provider == "databricks" and mode == "batch"):
        raise ValueError("provider is databricks (inline) or foundry (inline or batch)")
    if provider == "foundry" and not deployment:
        raise ValueError("a Foundry run needs --deployment")
    if judge_version not in tp.JUDGES:
        raise ValueError(f"judge_version must be one of {sorted(tp.JUDGES)}")
    template, checks, _must = tp.JUDGES[judge_version]
    import mlflow
    from mlflow.entities import AssessmentSource, Feedback, SpanType  # noqa: F401
    from mlflow.genai.scorers import scorer

    from drill.content.build import build_data
    from drill.server.observe import answer_checks, app_version

    # MLflow imports some of its modules lazily, from inside the worker threads (its usage telemetry, the
    # LLM-judge metrics). Several threads importing at once deadlock on Python's import locks, so load them
    # here first, and leave the telemetry off for this process.
    os.environ.setdefault("MLFLOW_DISABLE_TELEMETRY", "true")
    import mlflow.genai.judges  # noqa: F401
    import mlflow.metrics.genai  # noqa: F401
    import mlflow.tracking.request_header.registry  # noqa: F401

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
    population = {"failed": sum(not r["expectations"]["reference_pass"] for r in rows), "passed": sum(r["expectations"]["reference_pass"] for r in rows)}
    eval_name = f"tutor_prepared_{split}"
    if sample:  # its own registered dataset, so the next judge version is scored on exactly these answers
        rows = stratified_sample(rows, sample)
        eval_name = f"tutor_prepared_{split}_sample"
        datasets[eval_name] = dataset(mlflow, experiment.experiment_id, rows, commit, f"{split}_sample")
    seen: list[dict] = []
    lock = threading.Lock()
    prompts = register_prompts(mlflow, judge_version)
    fns = {p["id"]: p.get("fn") or "" for p in data["bank"]}
    from drill import answer_quality as aq

    glossary = aq.glossary_terms(data)
    allow_names = aq.COURSE_NAMES
    from drill import foundry_batch as fb

    judge_chat: dict[str, Any] = {"call": tp.databricks_chat(judge_model, profile) if provider == "databricks"
                                  else fb.foundry_chat(deployment, judge_model) if mode == "inline" else None}
    by_key = {(lid, c["key"]): c for lid, items in tp.chips(data).items() for c in items}

    def judge_text(lid: str, key: str, answer: str) -> str:
        """The judge prompt for one answer, exactly as the scorer sends it."""
        chip, fn = by_key[(lid, key)], fns.get(lid, "")
        giveaway = "" if chip["step"] == "Check" else ", and does not say which option of the lesson's Check questions is right"
        return template.format(context=tp._context(data, lid), q=chip["q"], how=chip["how"], answer=answer,
                               giveaway=(f" (`{fn}`)" if fn else "") + giveaway)

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

    source = AssessmentSource(source_type="LLM_JUDGE", source_id=judge_model)
    judge_prompt = f"{prompts['tutor_prepared_judge'].name}/{prompts['tutor_prepared_judge'].version}"

    # The judge's call is not a trace of its own: on a local MLflow server every extra trace and verdict is
    # another write, and a SQLite store takes one at a time. Its model, prompt version, tokens and time go
    # on the verdicts instead, which sit on the answer's trace. Agreement with the reference judge is a run
    # metric (kappa), not one verdict per answer.
    @scorer(name="judge")
    def judge(inputs, outputs, expectations):
        """The five checks, from the judge prompt, and whether it passes overall."""
        lid = inputs["lesson_id"]
        chat = judge_chat["call"]
        reply = chat(judge_text(lid, inputs["key"], outputs))
        verdict, usage = tp._verdict(reply, judge_version), chat.last()
        quality = aq.quality_checks(outputs, tp._context(data, lid), glossary, word_limit=200, allow_names=allow_names)
        with lock:
            seen.append({"lesson_id": lid, "key": inputs["key"], "phase": inputs.get("phase", ""), "kind": inputs.get("kind", ""),
                         "verdict": verdict, "reference": expectations or {}, "usage": usage,
                         "quality": {k: quality[k] for k in ("grade", "hard_to_read", "fillers", "repeated", "unexplained_terms",
                                                             "unknown_numbers", "unknown_names", "blocking")}})
        meta = {"judge_model": judge_model, "judge_prompt": judge_prompt, **{k: str(v) for k, v in usage.items() if k != "model"}}
        why = verdict["notes"] or None
        return ([Feedback(name="passes", value=verdict["pass"], rationale=why, source=source, metadata=meta)]
                + [Feedback(name=c, value=verdict[c], rationale=why if not verdict[c] else None, source=source) for c in checks])

    @scorer(name="rules")
    def rules(inputs, outputs):
        """The live tutor's own code checks (word limit, no maths notation, no exercise code), as one pass."""
        checks = answer_checks(outputs, {"exercise_fn": fns.get(inputs["lesson_id"], ""), "word_limit": 200})
        broken = [name for name in ("over_word_limit", "big_o", "solution_leak") if checks.get(name)]
        q = aq.quality_checks(outputs, tp._context(data, inputs["lesson_id"]), glossary, word_limit=200, allow_names=allow_names)
        code = AssessmentSource(source_type="CODE", source_id="drill.answer_quality")
        return [Feedback(name="rules", value=not broken, rationale=("broke: " + ", ".join(broken)) if broken else None,
                         source=AssessmentSource(source_type="CODE", source_id="drill.observe.answer_checks"),
                         metadata={"words": str(checks["words"])}),
                Feedback(name="readable", value=not q["hard_to_read"], rationale=f"grade {q['grade']}", source=code),
                Feedback(name="concise_code", value=not (q["fillers"] or q["repeated"]),
                         rationale=("fillers: " + ", ".join(q["fillers"]) if q["fillers"] else "a sentence repeats") if (q["fillers"] or q["repeated"]) else None, source=code),
                Feedback(name="terms_explained", value=not q["unexplained_terms"], rationale=", ".join(q["unexplained_terms"]) or None, source=code),
                Feedback(name="inside_lesson_code", value=not (q["unknown_numbers"] or q["unknown_names"]),
                         rationale=(f"numbers {q['unknown_numbers']} names {q['unknown_names']}" if (q["unknown_numbers"] or q["unknown_names"]) else None), source=code)]

    model = mlflow.set_active_model(name=f"daily-drill-{app_version()}")  # results show on the app version too
    model_short = judge_model.removeprefix("databricks-")
    data_name = f"{split}-sample-{len(rows)}" if sample else f"{split}-{len(rows)}"
    # readable at a glance in the runs list: what was judged, by whom, where and how, on what
    run_name = f"judge {model_short} · {provider} {mode} · prepared answers {data_name}" + (f" · checklist v{judge_version}" if judge_version != 1 else "")
    command = (f"uv run drill tutor prepared-eval --split {split}" + (f" --sample {sample}" if sample else "")
               + (f" --profile {profile or 'DEFAULT'} --judge-model {judge_model}" if provider == "databricks"
                  else f" --provider foundry --mode {mode} --judge-model {judge_model} --deployment {deployment}")
               + (f" --judge-version {judge_version}" if judge_version != 1 else ""))
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tag("mlflow.note.content", "\n\n".join([
            f"**Question:** can {model_short} stand in as the judge of the tutor's prepared answers? "
            + (purpose or "A candidate judge, compared with the reference on the same answers."),
            f"**What ran:** {len(rows)} prepared answers from the {split} split"
            + (" (a stratified sample: every reference failure, the rest spread by phase and kind)" if sample else "")
            + f", judged by {judge_model} on {'Databricks' if provider == 'databricks' else 'Microsoft Foundry'}"
            + (" as batch jobs at half price" if mode == "batch" else ", one call per answer")
            + f", with checklist version {judge_version} of the registered judge prompt"
            + (" (correct split into no_contradiction and within_lesson, plain moved to code, concise and tone added)" if judge_version == 2 else "")
            + f". Reference: {tp.JUDGE_MODEL}'s verdicts from the drafting run (checklist 1).",
            ("**How it's measured:** pass rates with Wilson 95% intervals; catch and keep rates against the reference, "
             f"re-weighted to the split's real mix; Cohen's kappa per check. Gate: kappa >= {KAPPA_GATE} to monitor with it. "
             "Splits: lessons dealt 60/20/20 within each phase, frozen in content/prepared_splits.json."),
            f"**Reproduce:** `{command}` (git commit {commit[:7]}).",
        ]))
        mlflow.set_tags({"question": "judge stand-in", "reproduce": command, "judge_model": judge_model})
        mlflow.set_tags({**mlflow_names.context_tags(app_version()), "kind": EXPERIMENT_KIND, "split": split,
                         "mlflow.source.git.commit": commit})
        draft_models = sorted({r.get("model", "") for recs in answers.values() for r in recs.values() if r.get("model")})
        mlflow.log_params({
            "draft_models": ",".join(draft_models), "judge_model": judge_model, "reference_judge": tp.JUDGE_MODEL,
            "draft_prompt": f"{prompts['tutor_prepared_draft'].name}/{prompts['tutor_prepared_draft'].version}",
            "judge_prompt": f"{prompts['tutor_prepared_judge'].name}/{prompts['tutor_prepared_judge'].version}",
            "dataset": mlflow_names.dataset_name(eval_name), "split": split, "records": len(rows), "sample": sample or "all",
            "split_rule": "lessons dealt 60/20/20 within each phase, frozen in prepared_splits.json", "git_commit": commit,
            "strata_missing": len(empty), "kappa_gate": KAPPA_GATE, "app_model": getattr(model, "name", ""),
            "price_per_mtok": ("{}/{} (list price; Databricks bills in DBUs)".format(*tp.PRICES.get(judge_model, ("?", "?")))
                               if provider == "databricks" else "{}/{} input/output, {} (Azure retail prices)".format(
                                   *[fb.PRICES.get((judge_model, "batch" if mode == "batch" else "standard"), (0, 0, 0, 0))[i] for i in (0, 2)], mode)),
            "provider": provider, "mode": mode, "deployment": deployment or judge_model, "judge_version": judge_version,
            "must_pass": ",".join(tp.JUDGES[judge_version][2]),
            **({"api_version": fb.API_VERSION, "judge_max_tokens": 2000} if provider == "foundry" else {}),
        })
        mlflow.set_tag("provider", provider)
        mlflow.log_table({"phase": [k[0] for k in table], "kind": [k[1] for k in table],
                          **{sp: [table[k][sp] for k in table] for sp in SPLITS}}, "strata.json")
        # The records are read out of the split's dataset, and the run names that dataset and its digest:
        # the exact version scored. (Handing evaluate() the dataset object itself hangs on a local MLflow
        # server after a few rows; its records as a list do not.)
        ds = datasets.get(eval_name, datasets[split])
        mlflow.log_params({"dataset_id": ds.dataset_id, "dataset_digest": ds.digest})
        data_in = [{"inputs": r["inputs"], "expectations": r["expectations"]} for r in ds.to_df()[["inputs", "expectations"]].to_dict("records")]
        if limit:
            data_in = data_in[:limit]  # a quick check of the plumbing, not a result
            mlflow.set_tag("limited", str(limit))
        if provider == "foundry" and mode == "batch":  # every verdict first, as batch jobs; the scorer then looks them up
            prompts = {f"{r['inputs']['lesson_id']}/{r['inputs']['key']}": judge_text(r["inputs"]["lesson_id"], r["inputs"]["key"],
                                                                                        answers[r["inputs"]["lesson_id"]][r["inputs"]["key"]]["a"])
                       for r in data_in}
            judge_chat["call"] = fb.batched_chat(prompts, deployment, judge_model,
                                                 on_job=lambda j: mlflow.set_tag(f"batch_part_{j['part']}", f"{j['batch_id']} {j['status']}"))
            mlflow.log_dict({"jobs": judge_chat["call"].jobs, "queue_limit_tokens_per_part": 120_000}, "batch_jobs.json")
        result = mlflow.genai.evaluate(data=data_in, predict_fn=prepared_answer, scorers=[judge, rules],
                                       model_id=getattr(model, "model_id", None))
        numbers = summary(seen, population, checks)
        for name in ("hard_to_read", "repeated"):
            numbers[f"quality_{name}_rate"] = sum(bool(x["quality"][name]) for x in seen) / max(1, len(seen))
        for name in ("unexplained_terms", "unknown_numbers", "unknown_names", "fillers"):
            numbers[f"quality_{name}_rate"] = sum(bool(x["quality"][name]) for x in seen) / max(1, len(seen))
        ensure_champion(mlflow)
        judge_version = link_judge(mlflow, run.info.run_id)
        mlflow.set_tag("judge_version", f"{judge_version.name}/{judge_version.version}")
        u = judge_chat["call"].usage  # what the judge cost (list price; the DBU charge is in system.billing.usage)
        spent = tp.cost(judge_model, u["input_tokens"], u["output_tokens"]) if provider == "databricks" else u["cost"]
        numbers.update({"judge_rate_limited": float(u["rate_limited"]), "judge_calls": float(u["calls"]), "judge_input_tokens": float(u["input_tokens"]),
                        "judge_output_tokens": float(u["output_tokens"]), "judge_seconds": float(u["seconds"]),
                        "judge_cost_usd": spent, "judge_cost_per_answer_usd": spent / max(1, u["calls"])})
        if u.get("served_model"):
            mlflow.log_param("served_model", u["served_model"])  # the exact model version that answered
        # the course's must-pass gate: is this judge close enough to the reference to monitor with?
        numbers["judge_gate_passed"] = float(numbers.get("passes_kappa", -1.0) >= KAPPA_GATE)
        mlflow.log_metrics({k: v for k, v in numbers.items() if isinstance(v, float)})
        mlflow.set_tag("judge_gate", "passed" if numbers["judge_gate_passed"] else "failed")
        mlflow.log_table(per_stratum(seen), "by_stratum.json")
        # every answer's verdict beside the reference one, so two runs can be compared answer by answer
        mlflow.log_table({"lesson_id": [x["lesson_id"] for x in seen], "key": [x["key"] for x in seen],
                          "passes": [x["verdict"]["pass"] for x in seen],
                          "reference_pass": [bool(x["reference"].get("reference_pass")) for x in seen],
                          "notes": [x["verdict"]["notes"] for x in seen]}, "answers.json")
    if record is not None:  # the run's own results, for a notebook to replay; the run stays the record
        params = mlflow.get_run(run.info.run_id).data.params
        Path(record).write_text(json.dumps({
            "about": f"Prepared answers, {split} split, judged by {judge_model} ({provider}, {mode}): written by MLflow run "
                     f"{run.info.run_id} in experiment '{experiment.name}'. Endpoint and resource names are left out on purpose.",
            "run_id": run.info.run_id, "run_name": run_name, "reproduce": command, "params": params, "metrics": numbers,
            "batch_jobs": getattr(judge_chat["call"], "jobs", []),
            "answers": [{"lesson_id": x["lesson_id"], "key": x["key"], "passes": x["verdict"]["pass"],
                         "reference_pass": bool(x["reference"].get("reference_pass")), "notes": x["verdict"]["notes"],
                         "quality": x["quality"], **{c: x["verdict"][c] for c in checks}} for x in seen],
            "judge_version": judge_version, "checks": list(checks), "must_pass": list(tp.JUDGES[judge_version][2])}, indent=1, ensure_ascii=False))
    return {"run_id": run.info.run_id, "experiment_id": experiment.experiment_id, "records": len(rows), "split": split,
            "numbers": numbers, "strata_missing": empty, "metrics": dict(result.metrics)}


def summary(seen: list[dict], population: dict[str, int] | None = None, checks: tuple[str, ...] = CHECKS) -> dict[str, float]:
    """The pass rate with its interval, and the judge's agreement with the reference judge (kappa and raw).

    With a stratified sample, failures are over-represented on purpose, so the headline numbers are split by
    the reference verdict: ``catch_rate`` (of the answers the reference failed, the share this judge failed
    too) and ``keep_rate`` (of those it passed, the share this judge passed too), each with its interval, and
    ``weighted_agreement``, the two re-weighted to the split's real mix (``population``)."""
    out: dict[str, float] = {}
    n = len(seen)
    ref_failed = [s for s in seen if not s["reference"].get("reference_pass")]
    ref_passed = [s for s in seen if s["reference"].get("reference_pass")]
    for name, items, want in (("catch", ref_failed, False), ("keep", ref_passed, True)):
        rate, low, high = wilson(sum(s["verdict"]["pass"] == want for s in items), len(items))
        out.update({f"{name}_rate": rate, f"{name}_ci_low": low, f"{name}_ci_high": high, f"{name}_n": float(len(items))})
    if population and sum(population.values()):
        total = sum(population.values())
        out["weighted_agreement"] = (out["catch_rate"] * population["failed"] + out["keep_rate"] * population["passed"]) / total
        out["population_failed_share"] = population["failed"] / total
    for check in ("pass", *checks):
        mine = [s["verdict"][check] for s in seen]
        name = "passes" if check == "pass" else check
        rate, low, high = wilson(sum(mine), n)
        out.update({f"{name}_rate": rate, f"{name}_ci_low": low, f"{name}_ci_high": high})
        ref_key = "reference_pass" if check == "pass" else f"reference_{check}"
        if n and any(ref_key in s["reference"] for s in seen):  # the reference judged with checklist 1: compare only shared checks
            ref = [bool(s["reference"].get(ref_key)) for s in seen]
            out[f"{name}_agreement"] = sum(a == b for a, b in zip(mine, ref)) / n
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


def mcnemar(b: int, c: int) -> float:
    """The exact two-sided McNemar p-value from the disagreements alone (the course's "Real win or luck"):
    ``b`` answers only the first run got right, ``c`` only the second. Small p: the difference is real."""
    n = b + c
    if not n:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def compare(run_a: str, run_b: str) -> dict:
    """Two judge runs on the same answers: which one agrees with the reference more often, and is it luck?"""
    import mlflow

    mlflow.set_experiment(mlflow_names.experiment())  # load_table reads from the active experiment

    def table(run_id: str) -> dict[tuple[str, str], tuple[bool, bool]]:
        df = mlflow.load_table("answers.json", run_ids=[run_id])
        return {(r.lesson_id, r.key): (bool(r.passes), bool(r.reference_pass)) for r in df.itertuples()}

    a, b = table(run_a), table(run_b)
    both = sorted(set(a) & set(b))
    a_right = [a[k][0] == a[k][1] for k in both]
    b_right = [b[k][0] == b[k][1] for k in both]
    only_a = sum(x and not y for x, y in zip(a_right, b_right))
    only_b = sum(y and not x for x, y in zip(a_right, b_right))
    return {"answers": len(both), "agreement_a": sum(a_right) / max(1, len(both)), "agreement_b": sum(b_right) / max(1, len(both)),
            "only_a_agrees": only_a, "only_b_agrees": only_b, "p_value": mcnemar(only_a, only_b)}

