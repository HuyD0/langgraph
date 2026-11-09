"""A jury of judges on the tutor's prepared answers (``uv run drill experiment jury ...``).

The question the business asked: does a panel of judge models, with every vote kept, grade answers better than
one judge, and do its split votes point at the answers a person should read? This runs it on the app's own
product, the tutor's prepared answers, and applies the course's own lessons: "A jury of judges", "Checking your
LLM judge", "Agreement beyond chance", "Testing the checker with planted mistakes" and "Real win or luck".

What gets judged
    A frozen, stratified sample of real prepared answers from the dev split (``SAMPLE_N``), plus planted answers
    that break one checklist rule each, by construction: another lesson's answer to this question
    (``wrong_lesson``), the lesson's Check answer given away (``giveaway``), or maths notation (``maths``).

What the labels are, and are not
    Planted answers fail by construction: real ground truth. Real answers carry the drafting judge's verdict
    (Claude Sonnet 5.5): a *reference*, not a person, even where MLflow shows it as HUMAN (an evaluation's
    expectations default to that source). A person's verdict comes from ``drill experiment jury label`` and is the
    only true label for real answers.

How a judge is asked
    Every judge gets the exact checklist-1 prompt the tutor's judge uses (``tutor_prepared.JUDGE``), one call per
    answer. Verdicts are cached by (model, prompt), so a rerun after labelling costs nothing; every vote records
    whether it came from the cache, and ``--fresh`` skips the cache to measure how much a judge changes its mind.

Everything is logged to MLflow: one parent run per panel, a nested run per judge, one trace per answer with each
judge's vote as LLM_JUDGE feedback, the jury's verdict as CODE feedback and the person's label as HUMAN feedback.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import statistics
import subprocess
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from drill import mlflow_names
from drill import tutor_prepared as tp
from drill import tutor_prepared_eval as tpe

ROOT = Path(__file__).resolve().parents[2]
CACHE_FILE = ROOT / ".drill" / "jury_cache.jsonl"
LABELS_FILE = ROOT / ".drill" / "jury_labels.json"
SAMPLE_N = 200  # real answers: enough that one judge's keep rate is known to within about plus or minus 3 points
PLANTS_PER_KIND = 20
SEED = 7
KIND = "jury"


@dataclass(frozen=True)
class Judge:
    name: str
    provider: str  # "ollama" (this computer, free) or "anthropic" (Claude API, paid)
    model: str
    effort: str = ""  # Claude only: output_config.effort
    price: tuple[float, float] = (0.0, 0.0)  # US$ per million input / output tokens


# Two panels of three. The tutor's answers were drafted by a Claude model and the reference judge is Claude too,
# so the local panel (three other families) is the one with no self-preference; comparing the panels measures it.
PANELS: dict[str, list[Judge]] = {
    "local": [Judge("gemma3-12b", "ollama", "gemma3:12b"),
              Judge("qwen3-14b", "ollama", "qwen3:14b"),
              Judge("llama3.1-8b", "ollama", "llama3.1:8b")],
    # The current generation, all at medium effort. Opus 5.5 drafted these answers and Sonnet 5.5 was the reference
    # judge, so this panel also shows whether Claude grades Claude's writing more kindly than the local panel does.
    "claude": [Judge("haiku-5.5", "anthropic", "claude-haiku-5-5", "medium", (0.10, 0.50)),
               Judge("sonnet-5.5", "anthropic", "claude-sonnet-5-5", "medium", (2.0, 10.0)),
               Judge("opus-5.5", "anthropic", "claude-opus-5-5", "medium", (4.0, 20.0))],
}

# One planted kind per way an answer can fail the checklist; new kinds go at the end, so earlier picks (and their
# cached verdicts) stay the same. Which check each one breaks:
PLANT_KINDS = ("wrong_lesson",     # answers_it, correct: another lesson's answer
               "giveaway",         # no_giveaway: names the right Check option
               "maths",            # plain: Big-O notation added
               "other_question",   # answers_it: this lesson's answer to a different question
               "wrong_number",     # correct: one number that matches the lesson changed
               "solution_leak",    # no_giveaway: the exercise's solution written out
               "not_standalone")   # standalone: leans on an earlier chat and asks for a reply
BREAKS = {"wrong_lesson": "answers_it", "giveaway": "no_giveaway", "maths": "plain", "other_question": "answers_it",
          "wrong_number": "correct", "solution_leak": "no_giveaway", "not_standalone": "standalone"}
MIN_FAILURES = 96  # known-bad answers a run needs: at a catch rate near a half, 96 gives a 95% range about 10 points each way
MATHS = "\n\nIn Big-O terms this step is O(n log n): for n items it takes about n × log₂(n) operations."


# -- the items ----------------------------------------------------------------------------------------------

def item_id(lid: str, key: str, planted: str = "") -> str:
    return f"plant:{planted}:{lid}:{key}" if planted else f"{lid}:{key}"


def _real(row: dict, answers: dict) -> dict:
    i = row["inputs"]
    rec = answers[i["lesson_id"]][i["key"]]
    return {"id": item_id(i["lesson_id"], i["key"]), "lesson_id": i["lesson_id"], "key": i["key"], "step": i["step"],
            "phase": i["phase"], "kind": i["kind"], "question": i["question"], "answer": rec["a"],
            "fingerprint": rec.get("fingerprint", ""), "planted": "", "truth": None,
            "reference_pass": bool(row["expectations"]["reference_pass"])}


_NUMBER = re.compile(r"(?<![\w.])(\d+(?:,\d{3})*(?:\.\d+)?)(?![\w.])")


def wrong_number(answer: str, lesson: str) -> str | None:
    """``answer`` with its first number that also appears in the lesson changed (multiplied by ten), or None."""
    for m in _NUMBER.finditer(answer):
        if re.search(rf"(?<![\w.]){re.escape(m.group(1))}(?![\w.])", lesson):
            n = m.group(1).replace(",", "")
            new = f"{float(n) * 10:g}" if "." in n else f"{int(n) * 10:,}"
            return answer[:m.start()] + new + answer[m.end():]
    return None


def plant(kind: str, base: dict, data: dict, donor: dict | None = None) -> dict:
    """``base`` with one checklist rule broken on purpose. ``donor`` supplies the wrong answer for wrong_lesson and
    other_question."""
    item = {**base, "id": item_id(base["lesson_id"], base["key"], kind), "planted": kind, "truth": False,
            "reference_pass": None}
    if kind == "wrong_lesson":
        assert donor is not None and donor["lesson_id"] != base["lesson_id"]
        item["answer"] = donor["answer"]
    elif kind == "giveaway":
        question, options, right = data["lessons"][base["lesson_id"]]["check"][:3]
        item["answer"] = base["answer"] + f'\n\nIn the Check question, the right option is "{options[right]}".'
    elif kind == "maths":
        item["answer"] = base["answer"] + MATHS
    elif kind == "other_question":
        assert donor is not None and donor["lesson_id"] == base["lesson_id"] and donor["key"] != base["key"]
        item["answer"] = donor["answer"]
    elif kind == "wrong_number":
        changed = wrong_number(base["answer"], tp._context(data, base["lesson_id"]))
        assert changed is not None
        item["answer"] = changed
    elif kind == "solution_leak":
        sol = next(p["solution"] for p in data["bank"] if p["id"] == base["lesson_id"])
        item["answer"] = base["answer"] + f"\n\nHere is the finished code, so you can copy it:\n\n```python\n{sol.strip()}\n```"
    elif kind == "not_standalone":
        item["answer"] = ("As I said in my last message, this follows on from your earlier question.\n\n" + base["answer"]
                          + "\n\nReply and tell me which part you want me to go through next.")
    else:
        raise ValueError(f"unknown plant {kind}")
    return item


def plants(pool: list[dict], data: dict, per_kind: int = PLANTS_PER_KIND, seed: int = SEED) -> list[dict]:
    """``per_kind`` planted answers of each kind, from ``pool`` (real answers kept out of the real sample).
    A giveaway is planted only where the rule applies: on Learn and Explain questions, not Check ones."""
    rng = random.Random(seed)
    order = sorted(pool, key=lambda r: r["id"])
    rng.shuffle(order)
    out, used = [], set()
    solved = {p["id"] for p in data["bank"] if p.get("solution")}

    def fits(kind: str, r: dict) -> bool:
        if r["id"] in used:
            return False
        if kind == "giveaway":
            return r["step"] != "Check"
        if kind == "other_question":
            return any(o["lesson_id"] == r["lesson_id"] and o["key"] != r["key"] and o["id"] not in used for o in order)
        if kind == "wrong_number":
            return wrong_number(r["answer"], tp._context(data, r["lesson_id"])) is not None
        if kind == "solution_leak":
            return r["lesson_id"] in solved
        return True

    for kind in PLANT_KINDS:
        made = 0
        for base in order:
            if made == per_kind:
                break
            if not fits(kind, base):  # checked as we go: a donor taken by an earlier pick is no longer free
                continue
            made += 1
            used.add(base["id"])
            donor = None
            if kind == "wrong_lesson":
                donor = next(r for r in order if r["phase"] != base["phase"] and r["id"] not in used)
            elif kind == "other_question":
                donor = next(r for r in order if r["lesson_id"] == base["lesson_id"] and r["key"] != base["key"] and r["id"] not in used)
            if donor is not None:
                used.add(donor["id"])
            out.append(plant(kind, base, data, donor))
    return out


def measurable(rows: list[dict], need: int = MIN_FAILURES) -> dict[str, Any]:
    """Can this set measure catching? Counts the known-bad answers (planted, or labelled bad) overall, per planted kind
    and per phase. ``ok`` is False when there are fewer than ``need``: the catch rate's range would be too wide to use."""
    bad = [r for r in rows if r["planted"] or r.get("person") is False]
    by_kind: dict[str, int] = {}
    by_phase: dict[str, int] = {}
    for r in bad:
        by_kind[r["planted"] or "labelled"] = by_kind.get(r["planted"] or "labelled", 0) + 1
        by_phase[r["phase"]] = by_phase.get(r["phase"], 0) + 1
    good = sum(1 for r in rows if not r["planted"] and r.get("person") is not False)
    return {"ok": len(bad) >= need, "known_bad": len(bad), "need": need, "good": good,
            "by_kind": dict(sorted(by_kind.items())), "by_phase": dict(sorted(by_phase.items()))}


def items(data: dict, answers: dict, n: int = SAMPLE_N) -> tuple[list[dict], dict]:
    """The real sample (frozen in prepared_sample.json under its size) and the planted answers. Returns the items
    and a note of the sample's state."""
    tpe._assigned = tpe.assign(data, tpe.load_splits())  # new lessons get a split; the file itself is left alone
    rows = [r for r in tpe.records(data, answers) if tpe.split_of(r["inputs"]["lesson_id"]) == "dev"]
    fps = {(lid, k): rec.get("fingerprint", "") for lid, recs in answers.items() for k, rec in recs.items()}
    sample, note = tpe.frozen_sample(rows, "dev", n, fingerprints=fps)
    real = [_real(r, answers) for r in sample]
    chosen = {r["id"] for r in real}
    pool = [_real(r, answers) for r in rows if item_id(r["inputs"]["lesson_id"], r["inputs"]["key"]) not in chosen]
    return real + plants(pool, data), note


def features(answer: str) -> dict[str, Any]:
    """What code can measure about an answer's text, for the bias, drift and baseline checks."""
    from drill import answer_quality as aq

    words = len(answer.split())
    return {"words": words, "chars": len(answer), "est_tokens": round(len(answer) / 4),  # about 4 characters a token
            "sentences": len(aq.sentences(answer)), "has_list": bool(re.search(r"^\s*([-*]|\d+\.)\s", answer, re.M)),
            "has_code": "`" in answer, "grade": round(aq.readability_grade(answer), 1)}


def judge_prompt(data: dict, item: dict, by_key: dict, fns: dict) -> str:
    """The checklist-1 judge prompt for one answer, exactly as ``tutor_prepared_eval`` sends it."""
    chip, fn = by_key[(item["lesson_id"], item["key"])], fns.get(item["lesson_id"], "")
    giveaway = "" if chip["step"] == "Check" else ", and does not say which option of the lesson's Check questions is right"
    return tp.JUDGES[1][0].format(context=tp._context(data, item["lesson_id"]), q=chip["q"], how=chip["how"],
                                  answer=item["answer"], giveaway=(f" (`{fn}`)" if fn else "") + giveaway)


# -- asking a judge -------------------------------------------------------------------------------------------

def ollama_chat(model: str, base: str = "") -> Callable[[str], tuple[str, dict]]:
    import httpx

    url = (base or os.getenv("OLLAMA_HOST_URL", "http://localhost:11434")).rstrip("/") + "/api/chat"

    def call(prompt: str) -> tuple[str, dict]:
        t0 = time.monotonic()
        r = httpx.post(url, timeout=600, json={
            "model": model, "stream": False, "think": False, "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0, "num_ctx": 8192}})
        r.raise_for_status()
        body = r.json()
        return body["message"]["content"], {"input_tokens": body.get("prompt_eval_count", 0),
                                            "output_tokens": body.get("eval_count", 0), "seconds": round(time.monotonic() - t0, 2)}
    return call


def api_key() -> str | None:
    """The Claude API key: ANTHROPIC_API_KEY, or CLAUDE_KEY (the name this project's .env uses)."""
    return os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_KEY") or None


def anthropic_chat(model: str, effort: str) -> Callable[[str], tuple[str, dict]]:
    """One judge call on the Claude API. No server-side fallback on purpose: a declined call stays unread, so every
    vote comes from the model named on it."""
    import anthropic

    workspace = os.getenv("ANTHROPIC_WORKSPACE_ID") or os.getenv("CLAUDE_WORKSPACE_ID")  # needed by an org-wide key
    client = anthropic.Anthropic(api_key=api_key(), max_retries=6,
                                 default_headers={"anthropic-workspace-id": workspace} if workspace else None)

    def call(prompt: str) -> tuple[str, dict]:
        t0 = time.monotonic()
        resp = client.messages.create(model=model, max_tokens=8000, output_config={"effort": effort},
                                      messages=[{"role": "user", "content": prompt}])
        text = "" if resp.stop_reason == "refusal" else "".join(b.text for b in resp.content if b.type == "text")
        u = resp.usage
        return text, {"input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
                      "cache_read_tokens": getattr(u, "cache_read_input_tokens", 0) or 0,
                      "stop_reason": resp.stop_reason, "seconds": round(time.monotonic() - t0, 2)}
    return call


def chat_for(judge: Judge) -> Callable[[str], tuple[str, dict]]:
    return ollama_chat(judge.model) if judge.provider == "ollama" else anthropic_chat(judge.model, judge.effort)


class VerdictCache:
    """Judge replies keyed by (model, prompt), one JSON line each in ``.drill/jury_cache.jsonl`` (git-ignored)."""

    def __init__(self, path: Path = CACHE_FILE):
        self.path, self.lock, self.rows = path, threading.Lock(), {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    self.rows[row["key"]] = row

    @staticmethod
    def key(judge: Judge, prompt: str) -> str:
        settings = f"{judge.provider}|{judge.model}|{judge.effort}"
        return hashlib.sha256(f"{settings}\n{prompt}".encode()).hexdigest()

    def get(self, key: str) -> dict | None:
        return self.rows.get(key)

    def put(self, key: str, reply: str, usage: dict) -> None:
        row = {"key": key, "reply": reply, "usage": usage, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        with self.lock:
            self.rows[key] = row
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")


def ask(judge: Judge, prompts: dict[str, str], cache: VerdictCache, fresh: bool = False, workers: int = 2,
        chat: Callable | None = None, progress: Callable[[int, int], None] | None = None) -> dict[str, dict]:
    """Every item's vote from one judge: {item id: {"pass", "parsed", "checks", "notes", "cached", "usage"}}.
    A reply with no JSON verdict is kept as unparsed, never counted as a fail."""
    chat = chat or chat_for(judge)
    out: dict[str, dict] = {}
    done = [0]
    lock = threading.Lock()

    def one(iid: str) -> None:
        prompt = prompts[iid]
        k = VerdictCache.key(judge, prompt)
        hit = None if fresh else cache.get(k)
        if hit:
            reply, usage = hit["reply"], hit["usage"]
        else:
            try:
                reply, usage = chat(prompt)
            except Exception as exc:  # noqa: BLE001 - one failed call is counted, not fatal
                reply, usage = "", {"error": str(exc)[:200]}
            if reply:
                cache.put(k, reply, usage)
        v = tp._verdict(reply, 1)
        with lock:
            out[iid] = {"pass": v["pass"], "parsed": v["parsed"], "checks": {c: v[c] for c in tp.CHECKS1},
                        "notes": v["notes"], "cached": bool(hit), "usage": usage}
            done[0] += 1
            if progress:
                progress(done[0], len(prompts))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, prompts))
    return out


# -- reading the votes ----------------------------------------------------------------------------------------

def consensus(votes: list[bool | None]) -> tuple[bool | None, bool]:
    """The jury's verdict and whether it split. Votes that could not be read (None) don't count. A pass needs more
    than half of the counted votes, so a tie is not a pass; a tie is a split."""
    counted = [v for v in votes if v is not None]
    if not counted:
        return None, False
    passes = sum(counted)
    return passes * 2 > len(counted), 0 < passes < len(counted)


def bootstrap_kappa(a: list[bool], b: list[bool], n: int = 2000, seed: int = SEED) -> tuple[float, float] | None:
    """A 95% range for Cohen's kappa by resampling the answers. None when there is too little to resample."""
    if len(a) < 10:
        return None
    rng = random.Random(seed)
    idx = range(len(a))
    ks = []
    for _ in range(n):
        pick = [rng.choice(idx) for _ in idx]
        k = tpe.kappa([a[i] for i in pick], [b[i] for i in pick])
        if k is not None:
            ks.append(k)
    if len(ks) < n // 2:
        return None
    ks.sort()
    return ks[int(0.025 * len(ks))], ks[int(0.975 * len(ks)) - 1]


def rate(hits: int, n: int) -> dict[str, float]:
    r, lo, hi = tpe.wilson(hits, n)
    return {"rate": round(r, 3), "low": round(lo, 3), "high": round(hi, 3), "n": n}


def agreement(verdicts: list[bool], labels: list[bool]) -> dict[str, Any]:
    """Raw agreement, kappa and its range, and the share of label-failures caught and label-passes kept."""
    pairs = list(zip(verdicts, labels))
    out: dict[str, Any] = {"n": len(pairs)}
    if not pairs:
        return out
    out["agreement"] = round(sum(v == lab for v, lab in pairs) / len(pairs), 3)
    out["catch"] = rate(sum(not v for v, lab in pairs if not lab), sum(not lab for _, lab in pairs))
    out["keep"] = rate(sum(v for v, lab in pairs if lab), sum(lab for _, lab in pairs))
    k = tpe.kappa(verdicts, labels)
    out["kappa"] = None if k is None else round(k, 3)
    ci = bootstrap_kappa(verdicts, labels)
    out["kappa_range"] = None if ci is None else [round(ci[0], 3), round(ci[1], 3)]
    return out


def length_bias(rows: list[dict], judge: str) -> dict[str, Any] | None:
    """Does the judge pass long answers more often than short ones that are just as good? Among real answers the
    reference passed, compare the judge's pass rate on the shorter and the longer half (split at the median)."""
    good = [r for r in rows if not r["planted"] and r["reference_pass"] and r["votes"].get(judge) is not None]
    if len(good) < 20:
        return None
    mid = statistics.median(r["features"]["words"] for r in good)
    short = [r["votes"][judge] for r in good if r["features"]["words"] <= mid]
    long = [r["votes"][judge] for r in good if r["features"]["words"] > mid]
    return {"median_words": mid, "short": rate(sum(short), len(short)), "long": rate(sum(long), len(long))}


def analyse(rows: list[dict], judges: list[str]) -> dict[str, Any]:
    """The numbers for one panel. ``rows``: one per item, with ``votes`` {judge: bool|None}, ``jury`` and ``split``,
    ``truth`` (planted: False), ``person`` (a person's label or None), ``reference_pass`` and ``features``."""
    planted = [r for r in rows if r["planted"]]
    real = [r for r in rows if not r["planted"]]
    labelled = [r for r in real if r.get("person") is not None]

    def per(name: str, get: Callable[[dict], bool | None]) -> dict[str, Any]:
        p = [get(r) for r in planted if get(r) is not None]
        kinds = {k: rate(sum(not get(r) for r in planted if r["planted"] == k and get(r) is not None),
                         sum(1 for r in planted if r["planted"] == k and get(r) is not None)) for k in PLANT_KINDS}
        ref = [get(r) for r in real if r["reference_pass"] and get(r) is not None]
        lab = [(get(r), r["person"]) for r in labelled if get(r) is not None]
        return {"name": name,
                "unread": sum(get(r) is None for r in rows),
                "catch_planted": rate(sum(not v for v in p), len(p)), "catch_by_kind": kinds,
                "keep_reference_passed": rate(sum(ref), len(ref)),
                "vs_labels": agreement([a for a, _ in lab], [b for _, b in lab])}

    out: dict[str, Any] = {"judges": [per(j, lambda r, j=j: r["votes"].get(j)) for j in judges],
                           "jury": per("jury", lambda r: r["jury"])}
    out["bias"] = {j: length_bias(rows, j) for j in judges}
    # Do splits point at the answers worth a person's time? Wrong = the jury disagrees with ground truth.
    truthful = [r for r in rows if r["jury"] is not None and (r["planted"] or r.get("person") is not None)]
    truth = {id(r): (False if r["planted"] else r["person"]) for r in truthful}
    split = [r for r in truthful if r["split"]]
    whole = [r for r in truthful if not r["split"]]
    out["split_rate"] = rate(sum(r["split"] for r in rows if r["jury"] is not None), sum(r["jury"] is not None for r in rows))
    out["wrong_when_split"] = rate(sum(r["jury"] != truth[id(r)] for r in split), len(split))
    out["wrong_when_unanimous"] = rate(sum(r["jury"] != truth[id(r)] for r in whole), len(whole))
    # Jury against its best member on the same items with ground truth ("Real win or luck"): McNemar on the
    # items where exactly one of the two is right.
    scored = [j for j in out["judges"] if j["catch_planted"]["n"]]
    if scored and truthful:
        # The best member is the one right most often on bad and good answers, weighted equally (balanced
        # accuracy): picking by catches alone would crown a judge that simply fails everything.
        best = max(scored, key=lambda j: (j["catch_planted"]["rate"] + j["keep_reference_passed"]["rate"]) / 2)["name"]
        both = [r for r in truthful if r["votes"].get(best) is not None]
        right = lambda v, r: v == truth[id(r)]  # noqa: E731
        only_jury = sum(right(r["jury"], r) and not right(r["votes"][best], r) for r in both)
        only_best = sum(right(r["votes"][best], r) and not right(r["jury"], r) for r in both)
        out["jury_vs_best"] = {"best": best, "items": len(both), "only_jury_right": only_jury,
                               "only_best_right": only_best, "p_value": round(tpe.mcnemar(only_jury, only_best), 4)}
    return out


# -- a person's labels ----------------------------------------------------------------------------------------

def load_labels(path: Path = LABELS_FILE) -> dict[str, dict]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_label(iid: str, fingerprint: str, passed: bool, note: str, who: str, path: Path = LABELS_FILE,
               source: str = "human", extra: dict | None = None) -> None:
    """One label. ``source`` is "human" (a person) or "ai" (an AI labeller); an AI label is never logged as human."""
    assert source in ("human", "ai")
    labels = load_labels(path)
    labels[iid] = {"pass": passed, "note": note, "by": who, "source": source, "fingerprint": fingerprint,
                   "at": time.strftime("%Y-%m-%dT%H:%M:%S"), **(extra or {})}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(labels, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def person_label(item: dict, labels: dict) -> bool | None:
    """A person's label counts only for the answer text they saw (a re-drafted answer needs a new label)."""
    lab = labels.get(item["id"])
    return lab["pass"] if lab and lab.get("fingerprint") == item["fingerprint"] else None


def export_queue(all_items: list[dict], data: dict, labels: dict, parts: int, folder: Path) -> list[Path]:
    """Every real answer not labelled yet, written as ``parts`` JSONL files for labellers to read. Each line holds what
    a careful reader needs and nothing that would anchor them: no judge's vote, no reference verdict, no model name."""
    by_key = {(lid, c["key"]): c for lid, cs in tp.chips(data).items() for c in cs}
    fns = {p["id"]: p.get("fn") or "" for p in data["bank"]}
    todo = to_label(all_items, labels)
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for n in range(parts):
        path = folder / f"part-{n + 1}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for i in todo[n::parts]:
                chip = by_key[(i["lesson_id"], i["key"])]
                f.write(json.dumps({"id": i["id"], "fingerprint": i["fingerprint"], "step": i["step"],
                                    "lesson": tp._context(data, i["lesson_id"]), "question": chip["q"],
                                    "how_it_should_be_answered": chip["how"], "exercise_function": fns.get(i["lesson_id"], ""),
                                    "answer": i["answer"]}, ensure_ascii=False) + "\n")
        paths.append(path)
    return paths


def import_labels(files: dict[str, Path], all_items: list[dict], path: Path = LABELS_FILE,
                  settled: dict[str, dict] | None = None) -> dict[str, Any]:
    """Labels from AI labellers ({labeller name: JSONL of {"id", "fingerprint", "pass", "failed_checks", "note"}}).
    Where the labellers agree, that is the label; where they disagree, ``settled`` decides ({id: {"pass", "note",
    "by"}}) or the answer stays unlabelled. Returns how often the labellers agreed (the ceiling for any judge)."""
    known = {i["id"]: i for i in all_items if not i["planted"]}
    got: dict[str, dict[str, dict]] = {}
    for name, f in files.items():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if row["id"] in known and row.get("fingerprint") == known[row["id"]]["fingerprint"]:
                    got.setdefault(row["id"], {})[name] = row
    names = sorted(files)
    both = {iid: v for iid, v in got.items() if len(v) == len(names)}
    a = [bool(v[names[0]]["pass"]) for v in both.values()] if len(names) >= 2 else []
    b = [bool(v[names[1]]["pass"]) for v in both.values()] if len(names) >= 2 else []
    disagree = sorted(iid for iid, v in both.items() if len({bool(x["pass"]) for x in v.values()}) > 1)
    saved = 0
    for iid, v in both.items():
        votes = {n: {"pass": bool(x["pass"]), "failed_checks": x.get("failed_checks", []), "note": x.get("note", "")} for n, x in v.items()}
        if iid in disagree:
            s = (settled or {}).get(iid)
            if s is None:
                continue
            passed, note, who = bool(s["pass"]), s.get("note", ""), s.get("by", "adjudicator")
        else:
            passed = votes[names[0]]["pass"]
            note = " | ".join(x["note"] for x in votes.values() if x["note"] and not passed)
            who = " + ".join(names)
        save_label(iid, known[iid]["fingerprint"], passed, note, who, path, source="ai",
                   extra={"labellers": votes, "agreed": iid not in disagree})
        saved += 1
    out = {"labelled_by_all": len(both), "disagree": disagree, "saved": saved}
    if a:
        out["labeller_agreement"] = round(sum(x == y for x, y in zip(a, b)) / len(a), 3)
        k = tpe.kappa(a, b)
        out["labeller_kappa"] = None if k is None else round(k, 3)
        out["labeller_fail_rates"] = {names[0]: round(1 - sum(a) / len(a), 3), names[1]: round(1 - sum(b) / len(b), 3)}
    return out


def to_label(all_items: list[dict], labels: dict, seed: int = SEED) -> list[dict]:
    """Real answers not labelled yet, in a fixed shuffled order (so two sessions label different answers)."""
    real = sorted((i for i in all_items if not i["planted"]), key=lambda i: i["id"])
    random.Random(seed).shuffle(real)
    return [i for i in real if person_label(i, labels) is None]


# -- the run ----------------------------------------------------------------------------------------------------

def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


class NotMeasurable(RuntimeError):
    """The set has too few known-bad answers to measure whether a judge catches them."""


def run(panel: str = "local", limit: int = 0, fresh: bool = False, workers: int = 0,
        progress: Callable[[str, int, int], None] | None = None, allow_short: bool = False) -> dict[str, Any]:
    """Judge every item with every judge in ``panel`` and log it all as one MLflow run. Returns the numbers."""
    import mlflow
    from mlflow.entities import AssessmentSource, SpanType

    from drill.content.build import build_data

    judges = PANELS[panel]
    data, answers = build_data(), tp.load()
    all_items, note = items(data, answers)
    if limit:
        real = [i for i in all_items if not i["planted"]][:limit]
        all_items = real + [i for i in all_items if i["planted"]][:limit]
    by_key = {(lid, c["key"]): c for lid, cs in tp.chips(data).items() for c in cs}
    fns = {p["id"]: p.get("fn") or "" for p in data["bank"]}
    prompts = {i["id"]: judge_prompt(data, i, by_key, fns) for i in all_items}
    cache = VerdictCache()
    labels = load_labels()
    # Check the set can fail before paying for a single judge call ("Check the set can fail").
    gate = measurable([{**i, "person": person_label(i, labels)} for i in all_items])
    if not gate["ok"] and not allow_short:
        raise NotMeasurable(f"only {gate['known_bad']} known-bad answers (need {gate['need']}): {gate['by_kind']}")
    workers = workers or (1 if panel == "local" else 8)

    votes: dict[str, dict[str, dict]] = {}
    for j in judges:  # one judge at a time: on one computer, loading a model is the slow part
        votes[j.name] = ask(j, prompts, cache, fresh=fresh, workers=workers,
                            progress=(lambda d, n, j=j: progress(j.name, d, n)) if progress else None)

    rows = []
    for i in all_items:
        vs = {j.name: (votes[j.name][i["id"]]["pass"] if votes[j.name][i["id"]]["parsed"] else None) for j in judges}
        jury, split = consensus(list(vs.values()))
        rows.append({**i, "votes": vs, "jury": jury, "split": split, "person": person_label(i, labels),
                     "features": features(i["answer"])})
    numbers = analyse(rows, [j.name for j in judges])
    cost = {j.name: round(sum(v["usage"].get("input_tokens", 0) for v in votes[j.name].values() if not v["cached"]) * j.price[0] / 1e6
                          + sum(v["usage"].get("output_tokens", 0) for v in votes[j.name].values() if not v["cached"]) * j.price[1] / 1e6, 4)
            for j in judges}

    commit = git_commit()
    n_real = sum(not i["planted"] for i in all_items)
    n_planted = len(all_items) - n_real
    names = ", ".join(j.model for j in judges)
    data_name = f"dev-sample-{n_real} + {n_planted} planted"
    run_name = f"jury {panel} panel ({names}) · {'ollama on this computer' if panel == 'local' else 'Claude API'} · prepared answers {data_name}"
    command = f"uv run drill experiment jury run --panel {panel}" + (f" --limit {limit}" if limit else "") + (" --fresh" if fresh else "")
    n_labelled = sum(r["person"] is not None for r in rows)
    sources = {s: sum(1 for r in rows if r["person"] is not None and labels[r["id"]].get("source", "human") == s) for s in ("human", "ai")}
    agreed = [labels[r["id"]] for r in rows if r["person"] is not None and "labellers" in labels[r["id"]]]
    label_note = (f"{sources['human']} labelled by a person and {sources['ai']} by AI labellers"
                  + ((" (two Claude Code subagents reading blind, with the full lesson; their disagreements settled by a third read). "
                      "AI labels are not a person's: a Claude labeller shares a family with the drafting model") if sources["ai"] else ""))
    mlflow.set_experiment(mlflow_names.experiment())
    with mlflow.start_run(run_name=run_name) as parent:
        # Each part is built in brackets first, so no two list items can run together by a missing comma.
        question = ("**Question:** does a jury of three judge models, with every vote kept, grade the tutor's prepared "
                    "answers better than its best single judge, and do its split votes point at the answers a person should read?")
        hunches = ("**Hunches, and what would prove them wrong (written before the run):** (1) the jury catches more planted "
                   "failures than its best member: wrong if the best member catches as many or more. (2) Split votes are where "
                   "the jury is wrong: wrong if the jury is wrong as often on unanimous answers as on split ones. (3) Judges "
                   "pass long answers more readily: wrong if the long half of good answers passes no more often than the short half.")
        what_ran = (f"**What ran:** {n_real} real prepared answers from the dev split (frozen stratified sample) and {n_planted} "
                    f"planted answers that each break one rule ({', '.join(PLANT_KINDS)}), judged by {names} with the tutor's "
                    "checklist-1 judge prompt, one call per answer"
                    + (", temperature 0 on this computer" if panel == "local" else ", effort medium, no temperature (the API no longer takes one)")
                    + f". Labels: planted answers fail by construction; real answers carry the drafting judge's verdict "
                    f"({tp.JUDGE_MODEL}, a reference, not a person); {label_note}.")
        measured = ("**How it's measured:** catch rate on planted answers and keep rate on reference-passed answers, each with a "
                    "Wilson 95% range; agreement with the labels as Cohen's kappa with a bootstrap 95% range; the jury against "
                    "its best member (by balanced accuracy) with McNemar on the same answers. **Decision rule:** a jury costs "
                    "three judges' calls, so it is worth it only if it is right where its best member is wrong more often than "
                    "the reverse (McNemar p below 0.05) without keeping fewer good answers (keep ranges overlap). The 0.05 is the "
                    "course's usual bar for \"real win or luck\"; when labels come from two labellers, their own agreement is "
                    "logged as labeller_agreement, the ceiling no judge can be expected to beat.")
        reproduce = (f"**Reproduce:** `{command}` (git commit {commit[:7]}). Verdicts come from `.drill/jury_cache.jsonl` "
                     "when the same model saw the same prompt; each vote says whether it was cached.")
        mlflow.set_tag("mlflow.note.content", "\n\n".join([question, hunches, what_ran, measured, reproduce]))
        mlflow.set_tags({"kind": KIND, "panel": panel, "reproduce": command, "mlflow.source.git.commit": commit})
        mlflow.log_params({"panel": panel, "judges": names, "judge_prompt": "tutor_prepared.JUDGE (checklist 1)",
                           "reference_judge": tp.JUDGE_MODEL, "real_answers": n_real, "planted_answers": n_planted,
                           "plant_kinds": ",".join(PLANT_KINDS), "sample_rule": "frozen stratified dev sample, prepared_sample.json",
                           "seed": SEED, "fresh": fresh, "known_bad": gate["known_bad"], "min_failures": gate["need"],
                           "gate_passed": gate["ok"], "labels": n_labelled, "labels_human": sources["human"], "labels_ai": sources["ai"], "git_commit": commit,
                           **{f"sample_{k}": v for k, v in note.items()}})
        for j, m in zip(judges, numbers["judges"]):
            v = votes[j.name]
            with mlflow.start_run(run_name=f"jury judge {j.model} · {data_name}", nested=True):
                mlflow.set_tags({"kind": KIND, "panel": panel, "judge": j.name})
                mlflow.log_params({"model": j.model, "provider": j.provider, "effort": j.effort or "n/a",
                                   "price_per_mtok": f"{j.price[0]}/{j.price[1]}"})
                mlflow.log_metrics(_flat(m) | {"cost_usd": cost[j.name], "calls_cached": sum(x["cached"] for x in v.values()),
                                               "calls_fresh": sum(not x["cached"] for x in v.values()),
                                               "seconds_fresh": round(sum(x["usage"].get("seconds", 0) for x in v.values() if not x["cached"]), 1)})
        mlflow.log_metrics(_flat(numbers["jury"], "jury_") | _flat({k: numbers[k] for k in ("split_rate", "wrong_when_split", "wrong_when_unanimous")})
                           | ({f"jury_vs_best_{k}": v for k, v in numbers["jury_vs_best"].items() if isinstance(v, (int, float))} if "jury_vs_best" in numbers else {})
                           | {"cost_usd": round(sum(cost.values()), 4)}
                           | ({"labeller_agreement": sum(x["agreed"] for x in agreed) / len(agreed)} if agreed else {}))
        mlflow.log_dict(numbers, "numbers.json")
        mlflow.log_dict(gate, "can_it_fail.json")
        mlflow.log_table({"item": [r["id"] for r in rows], "planted": [r["planted"] for r in rows], "phase": [r["phase"] for r in rows],
                          "step": [r["step"] for r in rows], "reference_pass": [r["reference_pass"] for r in rows],
                          "label": [r["person"] for r in rows],
                          **{j.name: [r["votes"][j.name] for r in rows] for j in judges},
                          "jury": [r["jury"] for r in rows], "split": [r["split"] for r in rows]}, "votes.json")
        mlflow.log_table({"item": [r["id"] for r in rows], **{k: [r["features"][k] for r in rows] for k in rows[0]["features"]}},
                         "features.json")

        # One trace per answer: the answer, its features, each judge's vote and the jury's verdict on it.
        # Traces are written in the background, so all of them are created and flushed before any vote is attached.
        trace_ids = {}
        for r in rows:
            with mlflow.start_span(name="jury.prepared_answer", span_type=SpanType.CHAIN) as span:
                span.set_inputs({"lesson_id": r["lesson_id"], "key": r["key"], "question": r["question"]})
                span.set_outputs(r["answer"])
                span.set_attributes({f"feature.{k}": v for k, v in r["features"].items()})
                mlflow.update_current_trace(tags={"kind": KIND, "panel": panel, "jury_item": r["id"], "planted": r["planted"] or "no",
                                                  "phase": r["phase"], "step": r["step"], "split": "dev"})
                trace_ids[r["id"]] = span.trace_id
        mlflow.flush_trace_async_logging()
        for r in rows:
            trace_id = trace_ids[r["id"]]
            for j in judges:
                v = votes[j.name][r["id"]]
                if v["parsed"]:
                    mlflow.log_feedback(trace_id=trace_id, name="jury", value=v["pass"], rationale=v["notes"] or None,
                                        source=AssessmentSource(source_type="LLM_JUDGE", source_id=j.model),
                                        metadata={"cached": str(v["cached"]), **{k: str(x) for k, x in v["usage"].items()},
                                                  **{f"check_{c}": str(x) for c, x in v["checks"].items()}})
            if r["jury"] is not None:
                mlflow.log_feedback(trace_id=trace_id, name="jury_pass", value=r["jury"],
                                    source=AssessmentSource(source_type="CODE", source_id="drill.jury.consensus"),
                                    metadata={"split": str(r["split"]), "votes": json.dumps(r["votes"])})
            if r["planted"]:
                mlflow.log_expectation(trace_id=trace_id, name="should_pass", value=False,
                                       source=AssessmentSource(source_type="CODE", source_id=f"drill.jury.plant.{r['planted']}"))
            if r["person"] is not None:
                lab = labels[r["id"]]
                human = lab.get("source", "human") == "human"
                mlflow.log_feedback(trace_id=trace_id, name="label_pass", value=r["person"], rationale=lab.get("note") or None,
                                    source=AssessmentSource(source_type="HUMAN" if human else "LLM_JUDGE", source_id=lab.get("by", "person")),
                                    metadata={"label_source": lab.get("source", "human"), "agreed": str(lab.get("agreed", ""))})
        return {"run_id": parent.info.run_id, "numbers": numbers, "cost": cost, "items": len(rows), "note": note, "gate": gate}


def _flat(d: dict, prefix: str = "") -> dict[str, float]:
    """Numbers from a nested result, as MLflow metric names (``catch_planted_rate``, ``vs_labels_kappa``...)."""
    out: dict[str, float] = {}
    for k, v in d.items():
        name = f"{prefix}{k}"
        if isinstance(v, bool) or v is None:
            continue
        if isinstance(v, (int, float)):
            out[name] = float(v)
        elif isinstance(v, dict):
            out.update(_flat(v, f"{name}_"))
    return out
