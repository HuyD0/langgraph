"""Batch calls on Microsoft Foundry: send many requests as one job, then follow up on the output.

A batch is a file of requests (one JSON object a line). You upload it, start a job, check on it
until it's done, then download an output file and match each line back to its request by its
``custom_id`` (the output is not in the same order). It costs about half of a normal call, and
aims to finish within 24 hours, usually much sooner. That's a target: on Foundry a late job keeps
running until it finishes or you cancel it, and cancelling returns what already finished. It suits
work nobody is waiting for, like answering or judging an eval set; it can't measure how fast a
model answers a person.

On Foundry, batch needs a deployment of type ``GlobalBatch`` (or ``DataZoneBatch``), and only
OpenAI models offer it; Claude on Foundry has no batch deployments. A batch deployment's capacity is
its **enqueued-token** limit, how many tokens may wait in its queue at once (200 means 200,000): a job
bigger than that is refused with ``token_limit_exceeded``, so split the file (:func:`chunks`) and
send the parts one after another. Raising the deployment's capacity didn't lift the limit when tried
on 2026-10-18. Sign in with ``az login``:
no keys. The endpoint and deployment names come from the environment, never from the repo:

    AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
    DRILL_BATCH_ANSWER_DEPLOYMENT=<a GlobalBatch deployment>    e.g. of gpt-5.4-mini
    DRILL_BATCH_JUDGE_DEPLOYMENT=<a GlobalBatch deployment>     e.g. of gpt-5.4

``notebooks/learning/cost_speed_quality.ipynb`` (section 11) uses these: a few inline calls, then the
same model as a batch, then a follow-up cell that checks the job and logs the results to MLflow.
"""

from __future__ import annotations

import io
import json
import os
import time
from collections.abc import Callable, Iterable
from typing import Any

API_VERSION = "2025-04-01-preview"
SCOPE = "https://cognitiveservices.azure.com/.default"
DONE = ("completed", "failed", "expired", "cancelled")

# Global deployments in East US, dollars per million tokens (input, cached input, output, cache write), from
# the Azure Retail Prices API on 2026-10-18. Batch is half of standard. Models before GPT-5.6 don't charge to
# write the cache; GPT-5.6 and later do. Claude on Foundry is billed through the Azure Marketplace, so it isn't
# in that list: drill.tutor_prepared.PRICES has Anthropic's list prices.
PRICES = {
    ("gpt-5.4", "standard"): (2.5, 0.25, 15.0, 0.0),
    ("gpt-5.4", "batch"): (1.25, 0.125, 7.5, 0.0),
    ("gpt-5.4-mini", "standard"): (0.75, 0.075, 4.5, 0.0),
    ("gpt-5.4-mini", "batch"): (0.375, 0.0375, 2.25, 0.0),
    ("gpt-5.6-luna", "standard"): (0.2, 0.02, 1.2, 0.25),
    ("gpt-6.1-sol", "standard"): (2.0, 0.1, 10.0, 2.5),
}


def cost(model: str, mode: str, usage: dict) -> float:
    """Dollars for one call from its usage block. OpenAI models cache by themselves: cached input and, on
    GPT-5.6 and later, input written to the cache are parts of ``prompt_tokens``, each at its own price."""
    pin, pcached, pout, pwrite = PRICES.get((model, mode), (0.0, 0.0, 0.0, 0.0))
    details = usage.get("prompt_tokens_details") or {}
    cached = details.get("cached_tokens", 0) or 0
    written = details.get("cache_write_tokens", 0) or 0
    return ((usage.get("prompt_tokens", 0) - cached - written) * pin + cached * pcached + written * pwrite
            + usage.get("completion_tokens", 0) * pout) / 1e6


def client(endpoint: str | None = None):
    """An Azure OpenAI client signed in as you (``az login``, or any azure.identity credential)."""
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    from openai import AzureOpenAI

    endpoint = endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    if not endpoint:
        raise RuntimeError("Set AZURE_OPENAI_ENDPOINT to your Foundry resource's endpoint.")
    return AzureOpenAI(azure_endpoint=endpoint, api_version=API_VERSION,
                       azure_ad_token_provider=get_bearer_token_provider(DefaultAzureCredential(), SCOPE))


# -- 1. the request file ----------------------------------------------------------------------------

def lines(requests: Iterable[tuple[str, list[dict]]], deployment: str, max_tokens: int = 4000) -> list[dict]:
    """One batch line per ``(custom_id, messages)``. ``custom_id`` must be unique: it's how each
    output line finds its request again."""
    out, seen = [], set()
    for cid, messages in requests:
        if cid in seen:
            raise ValueError(f"custom_id used twice: {cid}")
        seen.add(cid)
        out.append({"custom_id": cid, "method": "POST", "url": "/chat/completions",
                    "body": {"model": deployment, "messages": messages, "max_completion_tokens": max_tokens}})
    return out


def chunks(rows: list[dict], limit_tokens: int = 150_000) -> list[list[dict]]:
    """Split request lines into files that each stay under a deployment's enqueued-token limit
    (estimated at four characters a token), to send one after another."""
    out: list[list[dict]] = [[]]
    used = 0
    for r in rows:
        size = len(json.dumps(r["body"]["messages"])) // 4 + 1
        if out[-1] and used + size > limit_tokens:
            out.append([])
            used = 0
        out[-1].append(r)
        used += size
    return out


def jsonl(rows: list[dict]) -> bytes:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode()


# -- 2. send it, and check on it --------------------------------------------------------------------

def submit(api, rows: list[dict], note: str = "") -> str:
    """Upload the request file and start the job. Returns the batch id."""
    f = api.files.create(file=("requests.jsonl", io.BytesIO(jsonl(rows))), purpose="batch")
    batch = api.batches.create(input_file_id=f.id, endpoint="/chat/completions", completion_window="24h",
                               metadata={"note": note[:500]} if note else None)
    return batch.id


def snapshot(batch: Any) -> dict:
    """What a check on the job tells you: its status and how many requests are done or failed."""
    counts = batch.request_counts
    return {"status": batch.status, "total": getattr(counts, "total", 0) or 0,
            "completed": getattr(counts, "completed", 0) or 0, "failed": getattr(counts, "failed", 0) or 0}


def wait(api, batch_id: str, every: float = 30, timeout: float = 24 * 3600,
         on_check: Callable[[dict], None] | None = None) -> Any:
    """Check on the job every ``every`` seconds until it's done (completed, failed, expired or
    cancelled). Each check is passed to ``on_check``, so a caller can log the timeline."""
    start = time.monotonic()
    while True:
        batch = api.batches.retrieve(batch_id)
        check = {**snapshot(batch), "after_s": round(time.monotonic() - start)}
        if on_check:
            on_check(check)
        if batch.status in DONE or time.monotonic() - start > timeout:
            return batch
        time.sleep(every)


# -- 3. follow up on the output ---------------------------------------------------------------------

def read_output(api, batch: Any) -> dict[str, dict]:
    """Every request's result by ``custom_id``: ``{text, usage}`` or ``{error}``. Lines in the error
    file, and requests missing from both files, come back as errors too."""
    out: dict[str, dict] = {}
    for file_id, failed in ((batch.output_file_id, False), (getattr(batch, "error_file_id", None), True)):
        if not file_id:
            continue
        for raw in api.files.content(file_id).text.splitlines():
            if raw.strip():
                row = json.loads(raw)
                out[row["custom_id"]] = parse_line(row, failed)
    return out


def parse_line(row: dict, failed: bool = False) -> dict:
    """One output line as ``{text, usage}``, or ``{error}`` if the request didn't succeed."""
    resp = row.get("response") or {}
    if failed or row.get("error") or resp.get("status_code", 200) != 200:
        err = row.get("error") or (resp.get("body") or {}).get("error") or {"message": f"status {resp.get('status_code')}"}
        return {"error": err.get("message", str(err)) if isinstance(err, dict) else str(err)}
    body = resp.get("body") or {}
    choice = (body.get("choices") or [{}])[0]
    return {"text": (choice.get("message") or {}).get("content") or "", "finish": choice.get("finish_reason"),
            "usage": body.get("usage") or {}}


def to_retry(rows: list[dict], results: dict[str, dict]) -> list[dict]:
    """The request lines to send again: those that failed, or never came back."""
    return [r for r in rows if "text" not in results.get(r["custom_id"], {})]


# -- the tutor's requests --------------------------------------------------------------------------

def cid(q: dict) -> str:
    """A question's ``custom_id``: its lesson and key."""
    return f"{q['lesson_id']}/{q['key']}"


def answer_requests(data: dict, questions: list[dict]) -> list[tuple[str, list[dict]]]:
    """The tutor's prompt for each question, as the page sends it today."""
    from drill import tradeoff as t

    return [(cid(q), t.today_messages(data, q["lesson_id"], q["chip"])) for q in questions]


# The prepared answers' judge checks "standalone" strictly: a prepared answer is shown to everyone who taps
# the question, so it must not ask anything back. The live tutor's rules let it end with one question back
# to the learner, so judging live answers with that check fails them for doing their job.
STRICT_STANDALONE = '5. standalone: it makes sense to anyone who taps the question (no "as you said", no request to reply).'
LIVE_STANDALONE = ('5. standalone: it makes sense on its own (no "as you said"). Ending with one question back to the '
                   'learner is fine: the live tutor is meant to.')


def judge_prompt(live: bool = True) -> str:
    """The judge's prompt: the prepared answers' own, or the same with the standalone check fitted to live answers."""
    from drill import tutor_prepared as tp

    assert STRICT_STANDALONE in tp.JUDGE, "the prepared answers' judge changed: update the live version too"
    return tp.JUDGE.replace(STRICT_STANDALONE, LIVE_STANDALONE) if live else tp.JUDGE


def judge_requests(data: dict, questions: list[dict], answers: dict[str, str], live: bool = True) -> list[tuple[str, list[dict]]]:
    """A judge request for each answered question. ``live`` fits the standalone check to the live tutor."""
    from drill import tutor_prepared as tp

    template = judge_prompt(live)
    out = []
    for q in questions:
        if answers.get(cid(q)):
            fn = next((p.get("fn") for p in data["bank"] if p["id"] == q["lesson_id"]), "") or ""
            prompt = template.format(context=tp._context(data, q["lesson_id"]), q=q["chip"]["q"], how=q["chip"]["how"],
                                     answer=answers[cid(q)], giveaway=f" (`{fn}`)" if fn else "")
            out.append((cid(q), [{"role": "user", "content": prompt}]))
    return out


def verdict(text: str) -> dict:
    """The judge's JSON reply as checks plus ``pass`` (every check true)."""
    from drill import tutor_prepared as tp

    return tp._verdict(text)


# -- one call, inline: what a learner waits for -------------------------------------------------------

def ask_inline(api, deployment: str, messages: list[dict], max_tokens: int = 4000) -> dict:
    """One streamed call, timed: seconds to the first words, seconds in all, the text and its usage."""
    t0 = time.monotonic()
    first, parts, usage = None, [], {}
    stream = api.chat.completions.create(model=deployment, messages=messages, max_completion_tokens=max_tokens,
                                         stream=True, stream_options={"include_usage": True})
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            first = first if first is not None else time.monotonic() - t0
            parts.append(chunk.choices[0].delta.content)
        if getattr(chunk, "usage", None):
            usage = chunk.usage.model_dump()
    return {"text": "".join(parts), "first_words_s": round(first if first is not None else time.monotonic() - t0, 3),
            "total_s": round(time.monotonic() - t0, 3), "usage": usage}
