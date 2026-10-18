"""Does the drafter's own uncertainty predict a judge fail?

    uv run drill tutor uncertainty --provider foundry --deployment gpt-5.4-mini-batch --draft-model gpt-5.4-mini \\
        --judge-deployment gpt-5.4-batch --judge-model gpt-5.4 --sample 50 --samples 3

The idea under test: when a model writes a fact it is unsure of, two things show it. The word-level
probabilities at that spot are spread out (**confidence**), and asking the same question several
times gives answers that disagree (**self-consistency**). If either predicts the judge's verdict, it
is worth using at drafting time as a flag: send the unsure answer to a person, or write it again.

The run drafts each sampled question ``samples`` times with the prepared answers' drafting prompt,
asking for every token's log probability, then judges every draft with the prepared answers' checklist.
Four code signals per draft, none needing a model:

- ``mean_logprob``: the average log probability of the answer's tokens (higher is more confident;
  ``exp(-mean_logprob)`` is the perplexity).
- ``min_prob``: the least likely token's probability.
- ``risky_min_prob``: the least likely token among the risky ones: numbers, and capitalised words that
  are not sentence starts (names).
- ``disagreement``: how much this draft differs from the question's other drafts in content words
  (1 minus the mean Jaccard overlap), and ``numbers_differ``: whether the drafts don't all state the
  same numbers.

Everything runs as one named MLflow evaluation run: one trace per draft with the judge's verdict and
the signals as feedback, the predictive power of each signal (a rank-based AUC: the chance a passing
draft looks more confident than a failing one) as metrics, every draft as a table, and ``--record``
writes the recording a notebook replays.
"""

from __future__ import annotations

import json
import math
import random
import re
import time
from pathlib import Path

from drill import foundry_batch as fb
from drill import mlflow_names
from drill import tutor_prepared as tp
from drill import tutor_prepared_eval as tpe

SIGNALS = ("mean_logprob", "min_prob", "risky_min_prob", "disagreement", "numbers_differ")
STOP = set("the a an and or of to in on for with by is are was were be it its this that as at from not no if so "
           "you your they their we our he she his her them than then there here when what which who how why do does did "
           "can could would should will may might one two also just more most very into out up down over under".split())


# -- the signals ------------------------------------------------------------------------------------

def confidence(logprobs: list[tuple[str, float]]) -> dict[str, float]:
    """Three confidence numbers from a draft's token log probabilities."""
    if not logprobs:
        return {"mean_logprob": float("nan"), "min_prob": float("nan"), "risky_min_prob": float("nan")}
    probs = [math.exp(lp) for _, lp in logprobs]
    risky = []
    prev_end = True
    for (tok, lp) in logprobs:
        word = tok.strip()
        if word:
            if any(ch.isdigit() for ch in word) or (word[0].isupper() and not prev_end and word.isalpha()):
                risky.append(math.exp(lp))
            prev_end = word.endswith((".", "!", "?", ":"))
    return {"mean_logprob": sum(lp for _, lp in logprobs) / len(logprobs), "min_prob": min(probs),
            "risky_min_prob": min(risky) if risky else 1.0}


def content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9@.]+", text.lower()) if w not in STOP and len(w) > 2}


def numbers_in(text: str) -> set[str]:
    return set(re.findall(r"\d[\d,.]*", text))


def disagreement(texts: list[str]) -> list[dict[str, float]]:
    """For each draft: 1 minus its mean word overlap with the others, and whether the drafts' numbers differ."""
    words = [content_words(t) for t in texts]
    nums = [numbers_in(t) for t in texts]
    all_same_numbers = all(n == nums[0] for n in nums)
    out = []
    for i, w in enumerate(words):
        others = [x for j, x in enumerate(words) if j != i]
        overlaps = [len(w & o) / len(w | o) if (w | o) else 1.0 for o in others]
        out.append({"disagreement": 1 - (sum(overlaps) / len(overlaps) if overlaps else 1.0),
                    "numbers_differ": 0.0 if all_same_numbers else 1.0})
    return out


def auc(scores: list[float], passed: list[bool]) -> float | None:
    """Rank-based AUC: the chance a passing draft has a higher score than a failing one (0.5 = no signal)."""
    pos = [s for s, p in zip(scores, passed) if p and not math.isnan(s)]
    neg = [s for s, p in zip(scores, passed) if not p and not math.isnan(s)]
    if not pos or not neg:
        return None
    wins = sum((1.0 if a > b else 0.5 if a == b else 0.0) for a in pos for b in neg)
    return wins / (len(pos) * len(neg))


# -- the run ----------------------------------------------------------------------------------------

def sample_questions(data: dict, n: int, seed: int) -> list[dict]:
    chips = tp.chips(data)
    splits = tpe.load_splits()
    dev = [{"lesson_id": lid, "key": c["key"], "chip": c} for lid, items in chips.items() if splits.get(lid) == "dev" for c in items]
    return random.Random(seed).sample(dev, min(n, len(dev)))


def send_in_parts(api, rows: list[dict], note: str, on_job=None, every: float = 30) -> tuple[dict[str, dict], list[dict]]:
    """Batch jobs that each fit the deployment's queue, one after another; what failed is sent once more."""
    results: dict[str, dict] = {}
    jobs: list[dict] = []
    for i, part in enumerate(fb.chunks(rows, 120_000)):
        checks: list[dict] = []
        batch = fb.wait(api, fb.submit(api, part, note=f"{note}, part {i + 1}"), every=every, on_check=checks.append)
        got = fb.read_output(api, batch)
        left = fb.to_retry(part, got)
        if left:
            again = fb.wait(api, fb.submit(api, left, note=f"{note}, part {i + 1}, again"), every=every)
            got.update({k: v for k, v in fb.read_output(api, again).items() if "text" in v})
        jobs.append({"part": i + 1, "batch_id": batch.id, "requests": len(part), "status": batch.status,
                     "seconds": checks[-1]["after_s"] if checks else 0, "sent_again": len(left)})
        if on_job:
            on_job(jobs[-1])
        results.update(got)
    return results, jobs


def run(deployment: str, draft_model: str, judge_deployment: str, judge_model: str, sample: int = 50, samples: int = 3,
        seed: int = 7, record: Path | None = None, purpose: str = "") -> dict:
    import os

    os.environ.setdefault("MLFLOW_DISABLE_TELEMETRY", "true")
    import mlflow
    import mlflow.genai.judges
    import mlflow.metrics.genai
    from mlflow.entities import AssessmentSource, Feedback, SpanType
    from mlflow.genai.scorers import scorer

    from drill.content.build import build_data

    data = build_data()
    questions = sample_questions(data, sample, seed)
    by_cid = {fb.cid(q): q for q in questions}
    fns = {p["id"]: p.get("fn") or "" for p in data["bank"]}
    api = fb.client()
    experiment = mlflow.set_experiment(mlflow_names.experiment())
    commit = tpe.git_commit()
    prompts = tpe.register_prompts(mlflow)
    command = (f"uv run drill tutor uncertainty --provider foundry --deployment {deployment} --draft-model {draft_model} "
               f"--judge-deployment {judge_deployment} --judge-model {judge_model} --sample {sample} --samples {samples} --seed {seed}")
    run_name = f"draft uncertainty · {draft_model} x{samples} · foundry batch · judge {judge_model} · dev-{len(questions)}"

    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tag("mlflow.note.content", "\n\n".join([
            "**Question:** does the drafter's own uncertainty predict a judge fail? "
            + (purpose or "If it does, it becomes a drafting-time flag: send the unsure answer to a person or write it again."),
            f"**What ran:** {len(questions)} dev questions, each drafted {samples} times by {draft_model} on Microsoft Foundry "
            f"(batch, with every token's log probability), the {len(questions) * samples} drafts judged by {judge_model} with the "
            "prepared answers' checklist (batch).",
            "**How it's measured:** four code signals per draft (mean log probability, least likely token, least likely risky "
            "token (numbers and names), disagreement with the question's other drafts in content words, whether the drafts' "
            "numbers differ), each scored by a rank-based AUC against the judge's pass/fail: 0.5 is no signal, 1 is perfect.",
            f"**Reproduce:** `{command}` (git commit {commit[:7]}).",
        ]))
        mlflow.set_tags({**mlflow_names.context_tags(""), "kind": "draft_uncertainty", "split": "dev", "provider": "foundry",
                         "mode": "batch", "question": "drafter uncertainty as a hallucination flag", "reproduce": command,
                         "mlflow.source.git.commit": commit})
        mlflow.log_params({"draft_model": draft_model, "draft_deployment": deployment, "judge_model": judge_model,
                           "judge_deployment": judge_deployment, "questions": len(questions), "samples": samples, "seed": seed,
                           "draft_prompt": f"{prompts['tutor_prepared_draft'].name}/{prompts['tutor_prepared_draft'].version}",
                           "judge_prompt": f"{prompts['tutor_prepared_judge'].name}/{prompts['tutor_prepared_judge'].version}",
                           "api_version": fb.API_VERSION, "git_commit": commit})

        # 1. drafts, with token log probabilities
        draft_rows = fb.lines([(f"{fb.cid(q)}#{k}", [{"role": "user", "content": tp.prompt(data, q["lesson_id"], q["chip"])}])
                               for q in questions for k in range(samples)], deployment, max_tokens=4000, extra={"logprobs": True})
        drafts, draft_jobs = send_in_parts(api, draft_rows, f"draft uncertainty {draft_model}",
                                           on_job=lambda j: mlflow.set_tag(f"draft_part_{j['part']}", f"{j['batch_id']} {j['status']}"))
        texts = {k: v.get("text", "") for k, v in drafts.items()}

        # 2. the judge, on every draft
        template = fb.judge_prompt(live=False)
        judge_rows = []
        for did, text in texts.items():
            if not text:
                continue
            q = by_cid[did.rsplit("#", 1)[0]]
            fn = fns.get(q["lesson_id"], "")
            prompt = template.format(context=tp._context(data, q["lesson_id"]), q=q["chip"]["q"], how=q["chip"]["how"], answer=text,
                                     giveaway=f" (`{fn}`)" if fn else "")
            judge_rows.append((did, [{"role": "user", "content": prompt}]))
        verdicts, judge_jobs = send_in_parts(api, fb.lines(judge_rows, judge_deployment, max_tokens=2000), f"draft uncertainty judge {judge_model}",
                                             on_job=lambda j: mlflow.set_tag(f"judge_part_{j['part']}", f"{j['batch_id']} {j['status']}"))
        mlflow.log_dict({"draft_jobs": draft_jobs, "judge_jobs": judge_jobs}, "batch_jobs.json")

        # 3. the signals
        rows: list[dict] = []
        for cid, q in by_cid.items():
            dids = [f"{cid}#{k}" for k in range(samples)]
            dis = disagreement([texts.get(d, "") for d in dids])
            for d, dd in zip(dids, dis):
                r = drafts.get(d, {})
                v = verdicts.get(d, {})
                verdict = tp._verdict(v["text"]) if "text" in v else {}
                rows.append({"draft_id": d, "lesson_id": q["lesson_id"], "key": q["key"], "sample": int(d.rsplit("#", 1)[1]),
                             "text": r.get("text", ""), "error": r.get("error"), **confidence(r.get("logprobs", [])), **dd,
                             "judge": verdict, "passes": bool(verdict.get("pass")) if verdict else None,
                             "draft_cost": fb.cost(draft_model, "batch", r.get("usage", {})), "judge_cost": fb.cost(judge_model, "batch", v.get("usage", {}))})
        by_id = {r["draft_id"]: r for r in rows}

        # 4. one trace per draft, with the verdict and the signals as feedback
        @mlflow.trace(name="tutor.draft", span_type=SpanType.CHAIN)
        def draft_for(lesson_id: str, key: str, sample: int) -> str:
            r = by_id[f"{lesson_id}/{key}#{sample}"]
            mlflow.update_current_trace(tags={"kind": "draft_uncertainty", "lesson_id": lesson_id, "key": key, "sample": str(sample),
                                              "draft_model": draft_model, "split": "dev"})
            return r["text"]

        source_j = AssessmentSource(source_type="LLM_JUDGE", source_id=judge_model)
        source_c = AssessmentSource(source_type="CODE", source_id="drill.draft_uncertainty")

        @scorer(name="judge")
        def judge(inputs):
            r = by_id[f"{inputs['lesson_id']}/{inputs['key']}#{inputs['sample']}"]
            if r["passes"] is None:
                return Feedback(name="passes", value=None, error=None, source=source_j, rationale="no verdict came back")
            return Feedback(name="passes", value=r["passes"], rationale=r["judge"].get("notes") or None, source=source_j)

        @scorer(name="signals")
        def signals(inputs):
            r = by_id[f"{inputs['lesson_id']}/{inputs['key']}#{inputs['sample']}"]
            return [Feedback(name=s, value=None if (isinstance(r[s], float) and math.isnan(r[s])) else float(r[s]), source=source_c) for s in SIGNALS]

        records = [{"inputs": {"lesson_id": r["lesson_id"], "key": r["key"], "sample": r["sample"]}} for r in rows if r["text"]]
        mlflow.genai.evaluate(data=records, predict_fn=draft_for, scorers=[judge, signals])

        # 5. does any signal predict the verdict?
        judged = [r for r in rows if r["passes"] is not None]
        passed = [r["passes"] for r in judged]
        metrics: dict[str, float] = {"drafts": float(len(rows)), "judged": float(len(judged)),
                                     "pass_rate": sum(passed) / max(1, len(passed)),
                                     "draft_cost_usd": sum(r["draft_cost"] for r in rows), "judge_cost_usd": sum(r["judge_cost"] for r in rows)}
        for s in SIGNALS:
            # higher confidence should mean pass, so flip the two "worse when higher" signals
            sign = -1.0 if s in ("disagreement", "numbers_differ") else 1.0
            a = auc([sign * r[s] for r in judged], passed)
            if a is not None:
                metrics[f"auc_{s}"] = a
        # the question-level view: does the majority verdict agree with the majority draft?
        by_q: dict[str, list[dict]] = {}
        for r in judged:
            by_q.setdefault(f"{r['lesson_id']}/{r['key']}", []).append(r)
        unanimous = sum(1 for rs in by_q.values() if len({r["passes"] for r in rs}) == 1)
        metrics["questions_with_unanimous_verdicts"] = unanimous / max(1, len(by_q))
        mlflow.log_metrics(metrics)
        mlflow.log_table({k: [r[k] for r in rows] for k in ("draft_id", "lesson_id", "key", "sample", *SIGNALS, "passes")}, "drafts.json")
        mlflow.log_dict({"signals": SIGNALS, "auc": {s: metrics.get(f"auc_{s}") for s in SIGNALS},
                         "reading": "AUC is the chance a passing draft scores more confident than a failing one; 0.5 means the signal is useless"},
                        "predictive_power.json")

    if record is not None:
        Path(record).write_text(json.dumps({
            "about": f"Drafter uncertainty vs the judge: {len(questions)} dev questions x {samples} drafts by {draft_model} on Microsoft "
                     f"Foundry (batch, with token log probabilities), judged by {judge_model}. Written by MLflow run {run.info.run_id} in "
                     f"experiment '{experiment.name}'. Endpoint and resource names are left out on purpose.",
            "recorded": time.strftime("%Y-%m-%d"), "run_id": run.info.run_id, "run_name": run_name, "reproduce": command,
            "params": {"draft_model": draft_model, "judge_model": judge_model, "questions": len(questions), "samples": samples, "seed": seed},
            "metrics": metrics, "jobs": {"draft": draft_jobs, "judge": judge_jobs},
            "drafts": [{k: v for k, v in r.items() if k not in ("judge",)} | {"notes": r["judge"].get("notes", "")} for r in rows],
        }, indent=1, ensure_ascii=False))
    return {"run_id": run.info.run_id, "metrics": metrics, "questions": len(questions), "drafts": len(rows)}
