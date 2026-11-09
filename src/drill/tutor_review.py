"""A person reviews prepared tutor answers in an MLflow review queue, on this computer or on Databricks.

Judges disagree about some answers, and only a person can settle them. ``send`` logs one trace per answer (the
lesson, the question and the answer) and puts it in the review queue ``tutor-answers``, which asks four questions:

1. Would you serve this answer to a learner? (yes or no, with a comment for why)
2. If not, what is wrong with it? (any of the judges' checklist rules, plus "too long")
3. How sure are you? (an unsure verdict can go to a second person)
4. A better answer (optional): the next draft starts from it.

``read`` brings the answers back. A "no" marks the answer failed with the person's reasons, so ``drill tutor
prepare`` redrafts it with them; a "yes" on a failed answer serves it. The judges' votes are kept out of the queue
until the person has answered, so they can't sway the verdict; then they are logged on the trace as LLM_JUDGE
feedback beside the person's HUMAN feedback, and ``compare`` says how often each judge, and each of its rules,
agreed with the person.

On this computer the queue is in your MLflow server (the experiment, then Reviews). On Databricks it is in the
app's experiment, where review queues are the Beta preview "MLflow Review Queues". Which one is used follows the
tracking URI, like the rest of the app.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from drill import tutor_prepared as tp
from drill.config import PROJECT_ROOT

QUEUE = "tutor-answers"
SERVE = "Would you serve this answer to a learner?"
YES, NO = "Yes, serve it", "No, redraft it"
PROBLEMS = "If not, what is wrong with it?"
# What a reviewer can tick, and the judges' checklist rule each one matches. Length is a code check, not a judge rule.
PROBLEM_RULES = {
    "A fact is wrong or not in the lesson": "correct",
    "It doesn't answer the question": "answers_it",
    "It isn't plain enough for a beginner": "plain",
    "It gives away a Check or Build answer": "no_giveaway",
    "It leans on an earlier chat": "standalone",
    "It is too long": "length",
}
SURE = "How sure are you?"
SURE_OPTIONS = ("Sure", "Not sure")
BETTER = "A better answer (optional)"
INSTRUCTION = ("On the left: the question a learner tapped, the Check question it is about, the house rules and the "
               "lesson (the only source of truth); the answer is under them. Serve it only if every fact is in the lesson, it answers the "
               "question, a beginner could follow it, and it doesn't give away a Check or Build answer. If not, tick what is "
               "wrong and say why in the comment.")


@dataclass(frozen=True)
class Question:
    title: str
    kind: str  # passfail, multi, single or text
    type: str = "feedback"
    options: tuple[str, ...] = ()
    comment: bool = False


QUESTIONS = (
    Question(SERVE, "passfail", comment=True),
    Question(PROBLEMS, "multi", options=tuple(PROBLEM_RULES)),
    Question(SURE, "single", options=SURE_OPTIONS),
    Question(BETTER, "text", type="expectation"),
)


def _pages(fn, *args, **kw) -> list:
    items, token = [], None
    while True:
        page = fn(*args, page_token=token, **kw)
        items += list(page)
        token = getattr(page, "token", None)
        if not token:
            return items


class Local:
    """Your own MLflow server: label schemas and a custom review queue in the experiment."""

    where = "local"

    def questions(self, experiment_id: str) -> dict[str, str]:
        """Each question's id, made the first time: {id: title}."""
        from mlflow.genai import label_schemas as ls

        have = {s.name: s for s in _pages(ls.list_label_schemas, experiment_id)}
        out = {}
        for q in reversed(QUESTIONS):  # the review screen shows the newest question first: make them last to first
            if q.title == SERVE and q.title in have and have[q.title].instruction != INSTRUCTION:
                have[q.title] = ls.update_label_schema(have[q.title].schema_id, instruction=INSTRUCTION)
            made = have.get(q.title) or ls.create_label_schema(
                q.title, type=q.type, input=self._input(q), instruction=INSTRUCTION if q.title == SERVE else None,
                enable_comment=q.comment, experiment_id=experiment_id)
            out[made.schema_id] = q.title
        return dict(reversed(out.items()))

    @staticmethod
    def _input(q: Question):
        from mlflow.genai import label_schemas as ls

        return {"passfail": lambda: ls.InputPassFail(positive_label=YES, negative_label=NO),
                "multi": lambda: ls.InputCategorical(options=list(q.options), multi_select=True),
                "single": lambda: ls.InputCategorical(options=list(q.options)),
                "text": lambda: ls.InputText()}[q.kind]()

    cap = None  # no limit on how many items a queue holds

    def queue(self, experiment_id: str, question_ids: list[str], reviewers: list[str], name: str = QUEUE) -> str:
        from mlflow.exceptions import MlflowException
        from mlflow.genai import review_queues as rq

        try:
            return rq.get_review_queue(name=name, experiment_id=experiment_id).queue_id
        except MlflowException:
            return rq.create_review_queue(name, queue_type="custom", users=reviewers or None, schema_ids=question_ids,
                                          experiment_id=experiment_id).queue_id

    def exists(self, experiment_id: str, name: str) -> bool:
        from mlflow.exceptions import MlflowException
        from mlflow.genai import review_queues as rq

        try:
            rq.get_review_queue(name=name, experiment_id=experiment_id)
            return True
        except MlflowException:
            return False

    def add(self, experiment_id: str, queue_id: str, trace_ids: list[str]) -> None:
        from mlflow.genai import review_queues as rq

        rq.add_items_to_review_queue(queue_id, item_ids=trace_ids)

    def items(self, experiment_id: str, queue_id: str) -> list[str]:
        from mlflow.genai import review_queues as rq

        return [i.item_id for i in _pages(rq.list_review_queue_items, queue_id)]


class Workspace:
    """A Databricks workspace: review questions and a custom review queue in the experiment (Beta preview)."""

    where = "databricks"

    @staticmethod
    def _rq():
        import mlflow.genai.databricks.review_queues as rq

        return rq

    def questions(self, experiment_id: str) -> dict[str, str]:
        rq = self._rq()
        have = {q.title: q for q in _pages(rq.list_review_questions, experiment_id)}
        out = {}
        for q in reversed(QUESTIONS):  # as on a laptop: the newest question shows first
            made = have.get(q.title) or rq.create_review_question(
                experiment_id, title=q.title, type=q.type.upper(), input=self._input(q),
                instruction=INSTRUCTION if q.title == SERVE else None, enable_comment=q.comment)
            out[made.question_id] = q.title
        return dict(reversed(out.items()))

    def _input(self, q: Question):
        rq = self._rq()
        return {"passfail": lambda: rq.InputPassFail(positive_label=YES, negative_label=NO),
                "multi": lambda: rq.InputCategorical(options=list(q.options), multi_select=True),
                "single": lambda: rq.InputCategorical(options=list(q.options)),
                "text": lambda: rq.InputText()}[q.kind]()

    cap = 150  # a Databricks queue holds at most 150 items; more go to tutor-answers-2, -3...

    def queue(self, experiment_id: str, question_ids: list[str], reviewers: list[str], name: str = QUEUE) -> str:
        rq = self._rq()
        queue = next((q for q in _pages(rq.list_review_queues, experiment_id) if q.display_name == name), None)
        if queue is None:
            queue = rq.create_review_queue(experiment_id, name, queue_type="CUSTOM", question_ids=question_ids)
        members = {m.user for m in _pages(rq.list_review_queue_members, experiment_id, queue.queue_id)}
        for user in reviewers:
            if user and user not in members:
                rq.add_review_queue_member(experiment_id, queue.queue_id, user)
        return queue.queue_id

    def exists(self, experiment_id: str, name: str) -> bool:
        return any(q.display_name == name for q in _pages(self._rq().list_review_queues, experiment_id))

    def add(self, experiment_id: str, queue_id: str, trace_ids: list[str]) -> None:
        self._rq().add_review_queue_items(experiment_id, queue_id, trace_ids=trace_ids)

    def items(self, experiment_id: str, queue_id: str) -> list[str]:
        return [i.trace_id for i in _pages(self._rq().list_review_queue_items, experiment_id, queue_id) if i.trace_id]


def backend():
    """The review queues that match the tracking URI: a Databricks workspace's, or your own MLflow server's."""
    import mlflow

    return Workspace() if mlflow.get_tracking_uri().startswith("databricks") else Local()


# -- what was sent: a file beside the project, so read can find each answer and its hidden votes -----------------

def sent_path(where: str) -> Path:
    return PROJECT_ROOT / ".drill" / "review" / f"{where}-{QUEUE}.json"


def load_sent(where: str) -> dict:
    path = sent_path(where)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"items": {}}


def save_sent(where: str, sent: dict) -> None:
    path = sent_path(where)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sent, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def read_votes(path: Path) -> dict[str, dict]:
    """A votes file: ``{"<lesson id>:<key>": {"<judge>": {"pass": bool, "notes": str, "checks": {rule: bool},
    "model": str, "prompt": str}}}``. ``prompt`` is the judge's registered setup (``tutor_judge/<version>``, from
    ``tutor_prepared_eval.register_judge``), so each vote on the trace says exactly which prompt and model made it."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


# -- send -----------------------------------------------------------------------------------------------------

def _checks(lesson: dict) -> list:
    """The lesson's Check questions: ``[question, options, index of the right one, why]`` each."""
    return [lesson["check"], *(lesson.get("more") or [])]


def _check_block(check: list) -> str:
    question, options, right, why = check[0], check[1], check[2], (check[3] if len(check) > 3 else "")
    lines = [f"- {'**' + o + '** (right)' if i == right else o}" for i, o in enumerate(options)]
    return f"{question}\n\n" + "\n".join(lines) + (f"\n\n*Why:* {why}" if why else "")


def _code(text: str) -> str:
    return f"```\n{text.strip()}\n```"


def review_request(data: dict, lid: str, chip: dict) -> str:
    """What a reviewer needs to judge the answer the way the judges were asked to: the question in its place in the
    lesson, the Check question it is about (or the ones it must not give away), the house rules, then the lesson."""
    lesson = data["lessons"][lid]
    problem = next((p for p in data["bank"] if p["id"] == lid), {})
    module = next((m for m in data["modules"] if lid in m["lessons"]), {})
    parts = [f"**On the {chip['step']} step of the lesson \"{lesson['title']}\", a learner tapped:** {chip['q']}",
             f"**How the tutor was asked to answer:** {chip['how']}"]
    if chip["key"].startswith("check:"):
        qi = int(chip["key"].split(":")[1])
        parts.append("**The Check question this is about** (the learner has answered it, so the answer may say which "
                     "option is right):\n\n" + _check_block(_checks(lesson)[qi]))
    else:
        parts.append("**The lesson's Check questions.** The learner hasn't answered them yet, so the answer must not say "
                     "or hint which option is right:\n\n" + "\n\n".join(f"{n}. " + _check_block(c) for n, c in enumerate(_checks(lesson), 1)))
    rules = ["the learner is new to coding: plain words, every piece of jargon explained, no maths notation",
             "under about 200 words", "written once for every learner who taps this question, so it can't refer to "
             "an earlier chat or ask them to reply", "it stays on this lesson's topic and inside its setting"]
    if problem.get("fn"):
        rules.append(f"it never writes the lesson's coding exercise, `{problem['fn']}`, or lists what that code would contain")
    parts.append("**House rules for every answer:**\n\n" + "\n".join(f"- {r}" for r in rules))
    body = ["\n\n".join(lesson["learn"]), f"*Its example: {lesson['example'][0]}*\n\n" + _code(lesson["example"][1])]
    if lesson.get("stack"):
        body.append(f"*In the learner's stack: {lesson['stack'][0]}*\n\n" + _code(lesson["stack"][1]))
    body.append(f"*The angle to explain it: {lesson['angle'][0]}.* {lesson['angle'][1]}")
    if problem.get("title"):
        body.append(f"*The lesson's {'coding exercise' if problem.get('fn') else 'practice'}: {problem['title']}.*")
    if module.get("setting"):
        body.append(f"*The setting every example stays in:* {module['setting']}")
    parts.append(f"---\n\n**The lesson: {lesson['title']}** (the only source of truth)\n\n" + "\n\n".join(body))
    return "\n\n".join(parts)


def log_answer(data: dict, lid: str, chip: dict, rec: dict) -> str:
    """One trace a reviewer reads, shaped as a chat so the review screen shows it as formatted text, not JSON:
    :func:`review_request` as the request, the answer as the response. (A system message would hold the lesson
    more neatly, but the review screen doesn't show system messages.)"""
    import mlflow

    from drill import mlflow_names

    module = next((m["id"] for m in data["modules"] if lid in m["lessons"]), "")
    with mlflow.start_span(name="tutor.prepared_answer", span_type="CHAT_MODEL") as span:
        span.set_inputs({"messages": [{"role": "user", "content": review_request(data, lid, chip)}]})
        span.set_outputs({"choices": [{"index": 0, "message": {"role": "assistant", "content": rec["a"]}, "finish_reason": "stop"}]})
        mlflow.update_current_trace(tags={"kind": "tutor_review", "lesson_id": lid, "key": chip["key"], "step": chip["step"],
                                          "module": module, "status": rec.get("status", ""), "layout": "2",
                                          "fingerprint": rec.get("fingerprint", ""), "environment": mlflow_names.environment()})
        return span.trace_id


def existing(experiment_id: str) -> dict[tuple[str, str, str], str]:
    """Review traces already in the experiment: (lesson id, key, fingerprint) -> trace id. A send that stopped part
    way left them there; reusing them keeps one trace per answer."""
    import mlflow

    found = mlflow.search_traces(locations=[experiment_id], filter_string="tags.kind = 'tutor_review' AND tags.layout = '2'",
                                 return_type="list", include_spans=False)
    return {(t.info.tags.get("lesson_id", ""), t.info.tags.get("key", ""), t.info.tags.get("fingerprint", "")): t.info.trace_id
            for t in found}


BATCH = 100  # the most items Databricks takes in one call to add to a queue


def bare(trace_id: str) -> str:
    """A trace id as a queue lists it: traces kept in Unity Catalog are ``trace:/<location>/<id>`` elsewhere."""
    return trace_id.rsplit("/", 1)[-1]


def queue_name(n: int) -> str:
    return QUEUE if n == 1 else f"{QUEUE}-{n}"


def send(data: dict, answers: dict, ids: list[str], votes: dict, experiment_id: str, reviewers: list[str],
         queues=None) -> dict:
    """Put each answer (``"<lesson id>:<key>"``) in the review queue, once. Safe to run again: it reuses traces
    already logged and adds to the queue whatever it holds that isn't there yet. Returns the counts and the queue id."""
    import mlflow

    queues = queues or backend()
    sent = load_sent(queues.where)
    by_key = {(lid, c["key"]): c for lid, cs in tp.chips(data).items() for c in cs}
    logged = existing(experiment_id)
    # A trace the server never saved (a failed upload) is forgotten here, so this run logs it again: a queue item
    # that names a missing trace makes Databricks hang until it times out.
    sent["items"] = {tid: v for tid, v in sent["items"].items() if tid in set(logged.values())}
    done = {(v["id"], v["fingerprint"]) for v in sent["items"].values()}
    new, skipped = {}, []
    for iid in dict.fromkeys(ids):
        lid, _, key = iid.partition(":")
        rec, chip = answers.get(lid, {}).get(key), by_key.get((lid, key))
        if not rec or not rec.get("a") or chip is None or rec.get("fingerprint") != tp.fingerprint(data, lid, chip):
            skipped.append(iid)  # no answer, or the lesson changed since: a review of it would be out of date
            continue
        if (iid, rec["fingerprint"]) in done:
            continue
        tid = logged.get((lid, key, rec["fingerprint"])) or log_answer(data, lid, chip, rec)
        new[tid] = {"id": iid, "fingerprint": rec["fingerprint"], "votes": votes.get(iid, {}), "votes_logged": False}
    mlflow.flush_trace_async_logging()  # the queue can only hold traces the server already has
    saved = set(existing(experiment_id).values()) if new else set()
    not_saved = [v["id"] for tid, v in new.items() if tid not in saved]
    sent["items"].update({tid: v for tid, v in new.items() if tid in saved})
    sent["experiment_id"] = experiment_id
    save_sent(queues.where, sent)  # before the queue, so a failure there never orphans the traces
    question_ids = list(queues.questions(experiment_id))
    queue_ids, have, n = [], set(), 1
    while True:  # every part of the queue that exists, and what it already holds
        if n > 1 and not queues.exists(experiment_id, queue_name(n)):
            break
        queue_ids.append(queues.queue(experiment_id, question_ids, reviewers, queue_name(n)))
        have |= {bare(t) for t in queues.items(experiment_id, queue_ids[-1])}
        n += 1
    missing = [t for t in sent["items"] if bare(t) not in have]
    already, todo = len(have), list(missing)
    for i, qid in enumerate(queue_ids + [None] * len(todo)):  # fill each part, opening a new one when full
        if not todo:
            break
        if qid is None:
            qid = queues.queue(experiment_id, question_ids, reviewers, queue_name(len(queue_ids) + 1))
            queue_ids.append(qid)
        room = (queues.cap - len(queues.items(experiment_id, qid))) if queues.cap else len(todo)
        take, todo = todo[:max(0, room)], todo[max(0, room):]
        for j in range(0, len(take), BATCH):
            queues.add(experiment_id, qid, take[j:j + BATCH])
    sent["queue_ids"] = queue_ids
    save_sent(queues.where, sent)
    return {"added": len(missing), "already": already, "reused": sum(t in logged.values() for t in new),
            "skipped": skipped, "not_saved": not_saved, "queues": [queue_name(k + 1) for k in range(len(queue_ids))]}


# -- read back --------------------------------------------------------------------------------------------------

@dataclass
class Review:
    serve: bool
    problems: list[str] = field(default_factory=list)
    sure: str = ""
    better: str = ""
    comment: str = ""
    by: str = ""


def as_pass(value) -> bool | None:
    """A reviewer's answer to the serve question as True, False or None (can't read it)."""
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("pass", "true", "1", "yes") or text.startswith("yes"):
        return True
    if text in ("fail", "false", "0", "no") or text.startswith("no"):
        return False
    return None


def review_of(assessments, names: dict[str, str]) -> Review | None:
    """A trace's latest HUMAN answer to each question. ``names`` maps an assessment name (a question's id or its
    title, lowercased) to the question's title. None until the serve question is answered."""
    from mlflow.entities import AssessmentSourceType

    latest: dict[str, object] = {}
    for a in assessments or []:
        title = names.get((a.name or "").lower())
        if title is None or not a.source or a.source.source_type != AssessmentSourceType.HUMAN:
            continue
        when = a.last_update_time_ms or a.create_time_ms or 0
        if title not in latest or when >= (latest[title].last_update_time_ms or latest[title].create_time_ms or 0):
            latest[title] = a

    def value(title):
        a = latest.get(title)
        if a is None:
            return None
        return a.feedback.value if getattr(a, "feedback", None) is not None else getattr(a, "expectation", None) and a.expectation.value

    serve = as_pass(value(SERVE)) if SERVE in latest else None
    if serve is None:
        return None
    problems = value(PROBLEMS) or []
    return Review(serve=serve, problems=[p for p in (problems if isinstance(problems, list) else [problems]) if p in PROBLEM_RULES],
                  sure=str(value(SURE) or ""), better=str(value(BETTER) or "").strip(),
                  comment=(latest[SERVE].rationale or "").strip(), by=latest[SERVE].source.source_id or "")


def read(trace_ids: list[str], question_ids: dict[str, str]) -> dict[str, Review]:
    """Every answered trace's review."""
    import mlflow

    names = {qid.lower(): title for qid, title in question_ids.items()} | {q.title.lower(): q.title for q in QUESTIONS}
    out = {}
    for tid in trace_ids:
        try:
            trace = mlflow.get_trace(tid)
        except Exception:  # noqa: BLE001 - a trace that's gone has no review
            continue
        found = review_of(trace.info.assessments if trace else [], names)
        if found:
            out[tid] = found
    return out


def apply(answers: dict, sent: dict, reviews: dict[str, Review]) -> dict[str, int]:
    """Write each review into its prepared answer. A "no" fails it with the reasons (the next draft reads them); a
    "yes" on a failed answer serves it. An answer that changed since it was sent is left alone."""
    counts = {"served": 0, "rescued": 0, "failed": 0, "changed_since": 0}
    for tid, r in reviews.items():
        item = sent["items"].get(tid)
        if not item:
            continue
        lid, _, key = item["id"].partition(":")
        rec = answers.get(lid, {}).get(key)
        if not rec or rec.get("fingerprint") != item["fingerprint"]:
            counts["changed_since"] += 1
            continue
        rec["review"] = {"serve": r.serve, "problems": [PROBLEM_RULES[p] for p in r.problems], "sure": r.sure,
                         "comment": r.comment, "by": r.by, "trace_id": tid}
        if r.serve:
            counts["rescued" if rec.get("status") == "failed" else "served"] += 1
            if rec.get("status") == "failed":
                rec.update(status="passed", kept="a person said serve it")
            continue
        why = "A person rejected it" + (": " + "; ".join(r.problems).lower() if r.problems else "") + "."
        why += f" {r.comment}" if r.comment else ""
        why += f" Their better answer, to start from: {r.better}" if r.better else ""
        rec["status"] = "failed"
        rec["judge"] = {**rec.get("judge", {}), "pass": False, "notes": why}
        counts["failed"] += 1
    return counts


def log_votes(sent: dict, reviews: dict[str, Review]) -> int:
    """Now that a person has answered, put each judge's hidden vote on the trace as LLM_JUDGE feedback."""
    import mlflow
    from mlflow.entities import AssessmentSource, AssessmentSourceType

    logged = 0
    for tid in reviews:
        item = sent["items"].get(tid)
        if not item or item.get("votes_logged"):
            continue
        for judge, v in item["votes"].items():
            about = {k: str(v[k]) for k in ("model", "prompt") if v.get(k)}  # which judge setup, e.g. prompt tutor_judge/7
            mlflow.log_feedback(trace_id=tid, name=SERVE, value=bool(v.get("pass")), rationale=v.get("notes") or None,
                                source=AssessmentSource(AssessmentSourceType.LLM_JUDGE, judge),
                                metadata=about | {f"rule.{k}": str(c) for k, c in (v.get("checks") or {}).items()})
            logged += 1
        item["votes_logged"] = True
    return logged


def compare(sent: dict, reviews: dict[str, Review]) -> dict[str, dict]:
    """How each judge did against the person: verdicts that matched, and for each rule, how often the judge
    flagged it and how often the person ticked the same problem on those answers."""
    rule_of = {rule: label for label, rule in PROBLEM_RULES.items()}
    out: dict[str, dict] = {}
    for tid, r in reviews.items():
        ticked = {PROBLEM_RULES[p] for p in r.problems}
        for judge, v in sent["items"].get(tid, {}).get("votes", {}).items():
            s = out.setdefault(judge, {"answers": 0, "agreed": 0, "rules": {}})
            s["answers"] += 1
            s["agreed"] += bool(v.get("pass")) == r.serve
            for rule, ok in (v.get("checks") or {}).items():
                if ok is False and rule in rule_of:
                    flag = s["rules"].setdefault(rule, {"flagged": 0, "person_agreed": 0})
                    flag["flagged"] += 1
                    flag["person_agreed"] += (not r.serve) and rule in ticked
    return out
