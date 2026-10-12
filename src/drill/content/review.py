"""The use case review and challenge prompts: one source for the page, the server's checks and the eval.

The page sends these prompts from the Use case and fit lessons ("Ask the model to draft the
review", "Challenge my use case"). The server checks every review against REVIEW_CHECKS in
drill.review_checks, and ``drill review eval`` scores the same prompt on cards with planted gaps.
Change a prompt here, bump its version, and run the eval before publishing.
"""

from __future__ import annotations

REVIEW_VERSION = "review-v2"  # v2: a Gaps section first; v1 missed a blank owner in the eval
CHALLENGE_VERSION = "challenge-v1"

# The use case card, shaped like the AI Canvas: [key, label, example from the HR assistant].
CARD_FIELDS = [
    ["user", "Who uses it", "HR team"],
    ["task", "The task it helps with", "answer employee policy questions"],
    ["decision", "The decision: what the AI predicts or drafts, from what", "a draft answer from the policy pages"],
    ["action", "The action: what happens next, and who does it", "HR approves or edits it before sending"],
    ["today", "How it is done today, and the cost", "15 minutes by hand, about $8"],
    ["success", "Success, as a number", "80 in 100 drafts approved without edits"],
    ["wrong_answer", "What a wrong answer costs, and who catches it", "HR reviews each draft before sending"],
    ["data", "The data to test on", "last month's 200 questions"],
    ["feedback", "Feedback: how real outcomes improve it", "every edit goes into the eval set"],
    ["owner", "The owner who decides", "Head of HR operations"],
]

# Microsoft's five Well-Architected pillars, plus Databricks' governance pillar.
PILLARS = {
    "Reliability": ["What happens when the model endpoint is down or out of quota?", "Is there a timeout, a retry limit and a fallback?"],
    "Security": ["Who can see the inputs and answers?", "Could a prompt injection make it leak data or take an action?"],
    "Cost Optimization": ["What drives the monthly cost, and is there a budget alert?"],
    "Operational Excellence": ["Is every answer traced, and is there an eval set to test changes?", "How are new versions released and rolled back?"],
    "Performance Efficiency": ["Can it handle the busiest minute within the speed target?"],
    "Data and AI governance": ["Which data and models may it use, and who grants that access?"],
}

RULES = [
    "Rules:",
    "- Base every finding on the card, and quote the line you used.",
    "- If the card does not say, write Unknown, then the question to ask the owner.",
    "- Start with a Gaps section: every card line marked not written, each as an Unknown question naming that line.",
    "- Give each pillar a risk: low, medium or high.",
    "- Do not say whether to build it. A person decides.",
]

ANSWER_FORMAT = ("Answer with one short section per pillar, starting with the pillar's name: Risk, "
                 "Findings (each quoting the card), Unknowns (as questions for the owner). "
                 "Plain words, under 350 words.")

CHALLENGE_ASKS = [
    "- Could a simple rule, a search box or a better form solve this without AI?",
    "- What data would you need to test it, and is it likely to exist?",
    "- What happens when it is wrong, and who would notice?",
    "- Is their value or doable rating too optimistic? Why?",
    "- The one question they must answer before going further.",
]
CHALLENGE_CLOSE = "Plain words, short bullets, under 220 words. Do not say whether to build it; they decide."


def card_lines(card: dict) -> str:
    return "\n".join(f"- {key}: {(card.get(key) or '').strip() or 'not written'}" for key, _l, _e in CARD_FIELDS)


def review_template() -> str:
    """The review prompt with the card left as {{card}}: what goes in MLflow's prompt registry."""
    lines = ["Review this AI use case against the Well-Architected pillars.", "", "Use case card:", "{{card}}"]
    for pillar, questions in PILLARS.items():
        lines += ["", "## " + pillar] + ["- " + q for q in questions]
    lines += ["", *RULES, "", ANSWER_FORMAT]
    return "\n".join(lines)


def review_prompt(card: dict) -> str:
    """The review prompt for a card. The page builds exactly this text from data()."""
    return review_template().replace("{{card}}", card_lines(card))


def challenge_template() -> str:
    """The challenge prompt as the page builds it, with what it fills in left as {{placeholders}}."""
    return "\n".join([
        "You are a sceptical reviewer helping someone vet an AI use case before any money is spent. {{learner}}", "",
        "The problem: {{problem}}", "The use case: {{use_case}}", "They plan to {{mode}}.", "They rate it {{value}} value and {{doable}} to do.", "",
        "Argue against it, kindly but honestly:", *CHALLENGE_ASKS, CHALLENGE_CLOSE,
    ])


def parse_card(prompt: str) -> dict:
    """The card back out of a review prompt (as stored on a trace)."""
    part = prompt.split("Use case card:", 1)[-1].split("\n## ", 1)[0]
    card = {}
    for line in part.splitlines():
        if line.startswith("- ") and ": " in line:
            key, value = line[2:].split(": ", 1)
            card[key.strip()] = "" if value.strip() == "not written" else value.strip()
    return card


def blank_fields(card: dict) -> list[str]:
    return [key for key, _l, _e in CARD_FIELDS if not (card.get(key) or "").strip()]


def data() -> dict:
    """What the page needs to build the same prompts."""
    return {
        "reviewVersion": REVIEW_VERSION, "challengeVersion": CHALLENGE_VERSION,
        "cardFields": CARD_FIELDS, "pillars": PILLARS, "rules": RULES, "answerFormat": ANSWER_FORMAT,
        "challengeAsks": CHALLENGE_ASKS, "challengeClose": CHALLENGE_CLOSE,
    }
