---
name: vet-ai-use-case
description: Vets a proposed AI use case before anything is built. Turns a problem into a one-line use case, checks three gates (a fixed rule could do it, no examples to test on, unchecked harm), places it on a value-by-doable map, finds gaps in its use case card, reviews it against the Well-Architected pillars, works out its total cost of ownership with a script, and sets fit-for-purpose acceptance criteria. Use when someone asks whether an AI idea is worth doing, wants a use case assessed, reviewed or costed, or is preparing a business case or pilot.
---

# Vet an AI use case

Work through the steps in order, asking for anything the person has not said. Never invent a
fact about their use case: write **Unknown**, then the question to ask the owner. Do not decide
whether to build it; set out the evidence and let a person decide.

## Steps

1. **Problem.** Where do results miss expectations, or people repeat the same work? How often?
2. **One line.** Write: "Help [who] [do what] so [a number] improves." If the last part has no
   number, ask for one.
3. **Gates.** Shelve it if any is true: a fixed rule could do it; there are no past examples with
   right answers; a wrong answer causes harm and nobody checks. Say automate or augment
   (most first projects augment: AI drafts, a person decides).
4. **Map.** Rate value (what the problem costs, how much the business cares) and doable (data
   ready, AI suits the task, the team can change how it works) as high or low. Corner:
   accelerate (both high), research (value only), incubate (doable only), shelve (neither).
5. **Card.** Fill the ten fields in [reference/card.md](reference/card.md); list blank ones.
6. **Requirements.** Split what it must do from how well (speed, uptime, cost, privacy, security,
   scale, audit); every how-well line needs a number.
7. **Review.** For each pillar in [reference/pillars.md](reference/pillars.md): a risk (low,
   medium, high), findings that quote the card, and Unknowns as questions.
8. **Cost.** Collect the numbers in [reference/cost-inputs.md](reference/cost-inputs.md) into a
   JSON file and run `python scripts/tco.py inputs.json`. Report its table; do not do the sums yourself.
9. **Acceptance criteria.** Propose quality, must-pass, speed and cost acceptance criteria for the pilot, to agree before it starts.

## Output

```markdown
# Use case assessment: <one line>
**Corner:** <accelerate | research | incubate | shelve> (value <high|low>, doable <high|low>)
**Gates:** <passed, or which failed>  ·  **Mode:** <automate | augment>
## Gaps to close first
- Unknown: <question for the owner>
## Well-Architected review
| Pillar | Risk | Findings (quoting the card) | Unknowns |
## Total cost of ownership
<the table from scripts/tco.py, and its biggest item>
## Pilot acceptance criteria
- Quality ... · Must-pass ... · Speed ... · Cost ...
```
