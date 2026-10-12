"""The machinery behind notebook 10: one agent or a team, on the help-center app.

Notebook 10 builds two designs on the help center from milestones 9a-9d: one agent with a
search tool, and a team (a supervisor, parallel researchers, one writer and a checker). This
module holds the parts a learner does not need to read to follow the experiment:

- the 20 questions the experiment uses,
- a chat model that either calls a local Ollama (``qwen3:14b``, which can call tools) or
  replays replies recorded from it (``recorded_m10.json``), so the notebook runs offline and
  the test suite gives the same result everywhere,
- small helpers for searching one section of the help center and reading JSON replies.

Each reply is recorded under a key made of the design, the run, the question and the agent,
plus how many calls that agent had already made in that request. Token counts and timings
are recorded with it, so cost and time are real numbers from the recording run.
"""

from __future__ import annotations

import contextvars
import json
import os
import re
import tempfile
import time
import urllib.request
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import ConfigDict

from drill import rag_lab as R

HERE = Path(__file__).resolve().parent
RECORDED = HERE / "recorded_m10.json"

MODEL = "qwen3:14b"          # gemma3:12b (the 9a-9d model) cannot call tools in Ollama
TEMPERATURE = 0.6            # above 0, so repeat runs can differ, as they do in production

# Example prices from docs/research/LLM_COST_AND_SIZING.md (GPT-6 Sol, Global Standard,
# checked 2026-10-11): dollars per million tokens. The local model is free; these turn its
# token counts into what the same runs would cost on Azure AI Foundry.
PRICE = {"input": 2.00, "output": 10.00}

SECTIONS = {
    "billing": ["kb-01", "kb-02", "kb-03", "kb-04", "kb-05", "kb-06"],
    "shipping": ["kb-07", "kb-08", "kb-09", "kb-10", "kb-11", "kb-12"],
    "returns": ["kb-13", "kb-14", "kb-15", "kb-16", "kb-17", "kb-18"],
    "security": ["kb-19", "kb-20", "kb-21", "kb-22", "kb-23", "kb-24"],
}

# 7 one-article questions from 9a, 9 two-article questions (customers often ask two things
# at once), and 4 the help center can't answer. Facts use " | " between acceptable wordings.
_ONE = ["billing-05", "billing-11", "shipping-10", "refund-05", "refund-12", "fraud-03", "fraud-07"]
_NONE = ["none-01", "none-02", "none-03", "none-06"]
_TWO = [
    ("two-01", "My lamp arrived cracked. Do I have to pay to send it back, and how long until I get my money?",
     ["kb-15", "kb-14"], ["free | no cost | don't have to pay | do not have to pay | won't have to pay | will not have to pay", "5 to 7 | 5-7 | five to seven"]),
    ("two-02", "I want to return shoes I bought. How long do I have, and what does return shipping cost me?",
     ["kb-13", "kb-15"], ["30 days | thirty days", "$6 | 6 dollars | six dollars"]),
    ("two-03", "Someone placed orders on my account and I'm also getting password reset emails I didn't ask for. What should I do?",
     ["kb-19", "kb-21"], ["lock", "two-factor | two factor | 2fa"]),
    ("two-04", "I live in Nunavut. Who delivers there, and how much longer does it take?",
     ["kb-11"], ["canada post", "3 to 7 | 3-7 | three to seven"]),
    ("two-05", "My payment failed. How many times will you retry it, and can I switch to paying by bank transfer on my monthly plan?",
     ["kb-03", "kb-02"], ["3 times | three times | 3 retries | three retries", "yearly"]),
    ("two-06", "How much is express shipping and how fast is it?",
     ["kb-08", "kb-07"], ["$15 | 15 dollars | 15$", "1 to 2 | 1-2 | one to two"]),
    ("two-07", "There's a charge on my card I don't recognise, and I got a text asking for my card number. How long do I have to dispute the charge, and where do I report the text?",
     ["kb-23", "kb-20"], ["60 days | sixty days", "phishing@example.com"]),
    ("two-08", "I'm in Canada and thinking about the Plus plan. How much is it a month, and can I pay in Canadian dollars?",
     ["kb-01", "kb-05"], ["$15 | 15 dollars | 15$", "canadian dollars | cad"]),
    ("two-09", "I need to change the address on my order and I'd like express shipping. Until when can I change the address, and what does express cost?",
     ["kb-10", "kb-08"], ["until the order ships | before it ships | until it ships | hasn't shipped | has not shipped | until your order ships | before the order ships | before your order ships",
                          "$15 | 15 dollars | 15$"]),
]


def _questions() -> list[dict]:
    out = []
    for qid in _ONE:
        q = R.BY_ID[qid]
        out.append({"id": qid, "group": "one article", "question": q["question"], "gold": [q["gold"]], "facts": q["facts"]})
    for qid, text, gold, facts in _TWO:
        out.append({"id": qid, "group": "two articles", "question": text, "gold": gold, "facts": facts})
    for qid in _NONE:
        out.append({"id": qid, "group": "can't answer", "question": R.BY_ID[qid]["question"], "gold": [], "facts": []})
    return out


QUESTIONS = _questions()
BY_ID = {q["id"]: q for q in QUESTIONS}
DECLINE = R.DECLINE
score = R.score
declined = R.declined
has_facts = R.has_facts
_KB_TEXT = " ".join(a["text"] for a in R.KB.values()).lower()


def made_up_contacts(answer: str) -> list[str]:
    """Email addresses in an answer that appear nowhere in the help center."""
    emails = re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", answer.lower())
    return sorted({e.rstrip(".") for e in emails if e.rstrip(".") not in _KB_TEXT})


# ----------------------------------------------------------------------------- search


_INDEXES = {name: R.Index({i: R.KB[i] for i in ids}) for name, ids in SECTIONS.items()}
_WHOLE = R.Index(R.KB)


def search(query: str, k: int = 3, section: str | None = None) -> str:
    """The top k articles for a query, as text, from one section or the whole help center."""
    index = _INDEXES[section] if section else _WHOLE
    return R.articles_block(R.KB, index.search(query, k))


def read_json(reply: str, key: str) -> list:
    """The list under `key` in a model's JSON reply, or [] when the reply is not readable."""
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    try:
        value = json.loads(match.group(0))[key] if match else []
    except (ValueError, KeyError, TypeError):
        return []
    return [str(v) for v in value] if isinstance(value, list) else []


# ----------------------------------------------------------------------------- the model

_REQUEST: contextvars.ContextVar[dict | None] = contextvars.ContextVar("drill_m10_request", default=None)


def ollama_is_running() -> bool:
    return R.ollama_is_running()


class Lab:
    """Recorded or live model replies for one notebook session."""

    def __init__(self, live: bool = False):
        self.live = live and ollama_is_running()
        self.recorded = json.loads(RECORDED.read_text(encoding="utf-8")) if RECORDED.exists() else {}
        self.new: dict[str, dict] = {}
        self.run = 0                                # which repeat run is going on
        self.session = uuid.uuid4().hex[:8]         # tags every trace from this session
        self.seconds: dict[tuple, float] = {}       # (design, run, qid) -> model seconds

    def model(self, agent: str) -> LabChatModel:
        """A chat model for one named agent. Every call it makes is recorded under that name."""
        return LabChatModel(lab=self, agent=agent)

    @contextmanager
    def request(self, design: str, qid: str):
        """Everything inside belongs to one question, in one run, of one design."""
        token = _REQUEST.set({"design": design, "run": self.run, "qid": qid, "calls": {}})
        try:
            yield
        finally:
            _REQUEST.reset(token)

    def reply(self, agent: str, messages: list[BaseMessage], tools: list[dict] | None) -> AIMessage:
        req = _REQUEST.get()
        if req is None:
            raise RuntimeError("Model calls must happen inside lab.request(design, qid).")
        n = req["calls"].get(agent, 0)
        req["calls"][agent] = n + 1
        key = f"{req['design']}|{req['run']}|{req['qid']}|{agent}|{n}"
        if self.live:
            rec = self._ollama(messages, tools)
            self.new[key] = rec
        elif key in self.recorded:
            rec = self.recorded[key]
        else:
            raise KeyError(f"No recorded reply for {key!r}. Start Ollama with {MODEL} and set LIVE = True to run it live.")
        where = (req["design"], req["run"], req["qid"])
        self.seconds[where] = self.seconds.get(where, 0.0) + rec["ms"] / 1000
        calls = [{"name": c["name"], "args": c["args"], "id": f"call_{agent}_{n}_{i}", "type": "tool_call"}
                 for i, c in enumerate(rec["tool_calls"])]
        return AIMessage(content=rec["content"], tool_calls=calls,
                         usage_metadata={"input_tokens": rec["in"], "output_tokens": rec["out"],
                                         "total_tokens": rec["in"] + rec["out"]})

    def _ollama(self, messages: list[BaseMessage], tools: list[dict] | None) -> dict:
        body: dict[str, Any] = {"model": MODEL, "stream": False, "think": False,
                                "options": {"temperature": TEMPERATURE, "num_predict": 400},
                                "messages": [_to_ollama(m) for m in messages]}
        if tools:
            body["tools"] = tools
        started = time.perf_counter()
        request = urllib.request.Request(R.OLLAMA + "/api/chat", json.dumps(body).encode(),
                                         {"content-type": "application/json"})
        data = json.load(urllib.request.urlopen(request, timeout=600))
        msg = data["message"]
        calls = [{"name": c["function"]["name"], "args": c["function"].get("arguments") or {}}
                 for c in msg.get("tool_calls") or []]
        return {"content": (msg.get("content") or "").strip(), "tool_calls": calls,
                "in": data.get("prompt_eval_count", 0), "out": data.get("eval_count", 0),
                "ms": round((time.perf_counter() - started) * 1000)}

    def save(self) -> int:
        """Merge this live session's replies into recorded_m10.json (used to refresh the recording)."""
        current = json.loads(RECORDED.read_text(encoding="utf-8")) if RECORDED.exists() else {}
        current.update(self.new)
        RECORDED.write_text(json.dumps(current, indent=0, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return len(current)


def _to_ollama(m: BaseMessage) -> dict:
    if isinstance(m, ToolMessage):
        return {"role": "tool", "content": str(m.content), "tool_name": m.name or ""}
    if isinstance(m, AIMessage):
        out: dict[str, Any] = {"role": "assistant", "content": str(m.content)}
        if m.tool_calls:
            out["tool_calls"] = [{"function": {"name": c["name"], "arguments": c["args"]}} for c in m.tool_calls]
        return out
    role = {"system": "system", "human": "user"}.get(m.type, "user")
    return {"role": role, "content": str(m.content)}


class LabChatModel(BaseChatModel):
    """A LangChain chat model that can call tools, backed by the Lab (live Ollama or recorded).

    LangChain's own GenericFakeChatModel cannot be used with create_agent: it has no
    bind_tools. This one formats the tools for Ollama, and replays tool calls from the recording.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    lab: Any
    agent: str

    @property
    def _llm_type(self) -> str:
        return "drill-lab"

    @property
    def _identifying_params(self) -> dict:
        return {"model": MODEL, "agent": self.agent}

    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        return self.bind(tools=[convert_to_openai_tool(t) for t in tools], **kwargs)

    def _generate(self, messages, stop=None, run_manager=None, tools=None, **kwargs) -> ChatResult:
        message = self.lab.reply(self.agent, messages, tools)
        return ChatResult(generations=[ChatGeneration(message=message)])


# ----------------------------------------------------------------------------- notebook helpers


def use_mlflow(name: str) -> str:
    """Point MLflow at a local store for notebook 10 and return its URI.

    Under the test suite (DRILL_NOTEBOOK_OFFLINE=1) it uses a fresh temporary folder;
    otherwise ``.drill/m10/mlflow.db`` in the repo (git ignores .drill), which you can
    browse with ``mlflow ui``.
    """
    import mlflow

    if os.getenv("DRILL_NOTEBOOK_OFFLINE") == "1":
        folder = Path(tempfile.mkdtemp(prefix="drill-m10-"))
    else:
        from drill.config import PROJECT_ROOT

        folder = PROJECT_ROOT / ".drill" / "m10"
        folder.mkdir(parents=True, exist_ok=True)
    uri = f"sqlite:///{folder / 'mlflow.db'}"
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(name)
    os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
    return uri


def dollars(usage: dict | None) -> float:
    """What a trace's tokens would cost at the example prices."""
    usage = usage or {}
    return (usage.get("input_tokens", 0) * PRICE["input"] + usage.get("output_tokens", 0) * PRICE["output"]) / 1_000_000
