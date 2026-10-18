"""More Check questions for Evals (modules/evals.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "exact_match": [
        ask("Your eval cleans the model's answer but not the expected answer. The expected answer is "
            "\"New York.\" and the model says \"new york\". What happens?",
            ["It still counts as wrong", "It counts as right", "The eval skips that one"],
            answer=0,
            clue="Look at the expected answer: does it still have its capital letters and full stop?",
            why="Cleaning has to happen on both sides. The expected answer still has its capitals and "
                "full stop, so the two don't match."),
        ask("Your app writes short summaries of support calls. Two good summaries can use completely "
            "different words. How should you score them?",
            ["Exact match against one summary", "An LLM judge with a clear rubric", "Count how many words each one has"],
            answer=1,
            clue="There's no single right wording to compare against, so something has to read the meaning.",
            why="For open-ended answers, a second model, the judge, grades each one with written grading "
                "rules. You check the judge against human labels before trusting it."),
    ],
    "assign_splits": [
        ask("You've spent a week tuning your prompt, and you check the test set after every change. "
            "What's wrong with that?",
            ["Nothing, more checks find more bugs", "You're tuning against the test set", "The test set is too small to use"],
            answer=1,
            clue="Which set is the one you're allowed to look at as often as you like?",
            why="Day-to-day tuning belongs on the dev set. The test set is checked rarely, before a "
                "release, so its score stays honest."),
        ask("Your eval set is 100 questions you wrote and checked by hand last year. What would make it "
            "closer to how the app is really used?",
            ["Write another 100 questions by hand", "Ask a model to make up more questions", "Add real traffic and past failures"],
            answer=2,
            clue="Your own questions show what you guessed. Where would you see what really happens?",
            why="A good eval set mixes a hand-checked golden set with a sample of recent real traffic "
                "and past failures you never want to see again."),
    ],
    "stable_split": [
        ask("You split questions by hashing each one's id. Next week, 100 new questions are added. "
            "What happens to last week's questions?",
            ["They stay in the same split", "They get dealt out again", "They all move into dev"],
            answer=0,
            clue="Does adding new questions change an old question's id?",
            why="The split comes from the id alone, so an old question always lands where it did before. "
                "Only the new ones get placed."),
        ask("One conversation has 5 questions. You hash each question's id, and the conversation ends "
            "up split between test and dev. Which id should you hash instead?",
            ["The question text", "The conversation id", "The date it was asked"],
            answer=1,
            clue="Think about what all 5 questions have in common.",
            why="Hashing the conversation id gives all its questions the same number, so they land "
                "in the same split together and can't leak."),
    ],
    "weighted_score": [
        ask("Your weekly report shows one number: 90 percent. A manager asks if refund questions are "
            "working. What should the report have shown?",
            ["The same 90 percent, but in bold", "Last week's score next to it", "A score for each group, with its count"],
            answer=2,
            clue="A good average can sit on top of a group that fails half the time.",
            why="Report a score for each group, with how many examples it's based on. One average "
                "can hide a group that is failing."),
        ask("Real users have started asking about a new gift card, but your eval set has no gift card "
            "questions. How should the report treat that group?",
            ["Give it a score of zero", "Call it a blind spot to fill", "Leave it out, since it's new"],
            answer=1,
            clue="You haven't measured it at all, so you don't know if it's good or bad.",
            why="No examples means no measurement, not a fail. It's a blind spot: add gift card "
                "questions to the eval set."),
    ],
    "must_pass_gate": [
        ask("Last month the bot told customers the wrong refund policy. You've fixed it. What should "
            "you do with that question now?",
            ["Delete it, since the bug is fixed", "Add it to the must-pass set", "Keep it in the dev set only"],
            answer=1,
            clue="You never want this one to come back without anyone noticing.",
            why="Every serious production failure you fix goes into the must-pass set, so it can't "
                "quietly come back."),
        ask("Your team is starting a new project. When should you choose the must-pass cases?",
            ["At the start, before any experiment", "Halfway, once you see what passes", "At the end, just before you ship"],
            answer=0,
            clue="Should the version being tested get to shape its own test?",
            why="Choose them in the Frame stage, from what would be costly to get wrong. Picked later, "
                "they lean toward what already passes, and the gate stops protecting you."),
    ],
    "first_bad_version": [
        ask("You have 20 prompt versions. Version 1 passes and version 20 fails. You test version 10 "
            "and it passes. Where is the first bad one?",
            ["Somewhere from 1 to 10", "Somewhere from 11 to 20", "It must be version 20"],
            answer=1,
            clue="If the middle one still works, when did things break?",
            why="Version 10 passes, so the change that broke things came after it. Drop 1 to 10 and "
                "test the middle of what's left."),
        ask("A teammate plans to re-run the eval on all 50 old prompt versions, one by one, to find "
            "what broke. Each run costs money. What's cheaper?",
            ["Test only the newest few versions", "Test the oldest version first", "Test the middle, keep the half with the change"],
            answer=2,
            clue="How could one test rule out lots of versions at once?",
            why="Bisecting tests the middle version and keeps the half that holds the change. Each test "
                "throws away half, so a handful of runs is enough."),
    ],
    "judge_agreement": [
        ask("Human reviewers failed 20 answers. Your judge failed only 2 of those same 20. What does "
            "that tell you about the judge?",
            ["It agrees with humans well", "It is too strict on good ones", "It lets most bad answers through"],
            answer=2,
            clue="Look only at the answers people marked as bad.",
            why="It failed only 2 of the 20 answers people failed. That share, its true negative rate, "
                "is very low: most bad answers get through."),
        ask("Your team's answers come from one model, and the judge is a smaller, cheaper model from the "
            "same maker, built on the same base. What guards against self-preference bias?",
            ["A judge from a different model family", "A longer, stricter grading prompt", "Running the same judge a second time"],
            answer=0,
            clue="The grader may go easy on answers that sound like its own, so who else could grade them?",
            why="A judge goes easier on its own answers, and somewhat on its relatives' answers: that is "
                "self-preference bias. A judge from another family, or human labels on the same answers, "
                "shows whether it is being soft."),
    ],
    "vague_checks": [
        ask("Your checklist has correct, no giveaway, plain and friendly tone. Which checks should be "
            "must-pass gates, where one fail blocks the answer?",
            ["Correct and no giveaway", "Plain and friendly tone", "All four, to be safe"],
            answer=0,
            clue="Ask which failures would hurt the person who got that answer, and which would just make "
                 "it less nice to read.",
            why="A wrong fact or a handed-out answer does real harm, so those two are gates. A stiff tone "
                "or a long sentence just reads worse: those checks add up to a score instead."),
        ask("Your checklist says an answer must use plain words, sound friendly and stay under 200 words. "
            "Which part should code check instead of the judge?",
            ["The word count", "Whether the words are plain", "Whether it sounds friendly"],
            answer=0,
            clue="Which part has one exact answer that a program gets the same way every time?",
            why="Counting words is mechanical: code does it the same way every time and never argues. Code can "
                "also score readability and spot unexplained terms, but whether the words are truly plain, or the "
                "answer sounds friendly, still needs reading, so those stay with the judge, each with a definition."),
    ],
    "cohen_kappa": [
        ask("You check two judges against the same human labels. Judge A has a kappa of 0.75 and "
            "judge B has 0.1. Which one would you trust more?",
            ["Judge B, a lower kappa is stricter", "Judge A, it agrees well beyond luck", "Neither, kappa can't compare them"],
            answer=1,
            clue="Remember what 0 means on the kappa scale, and what counts as good.",
            why="0 means no better than luck and above 0.6 is good, so judge A really agrees with "
                "humans. Judge B is barely better than guessing."),
        ask("Your judge has a good kappa of 0.7. Do you still need to check how it does on passes "
            "and failures separately?",
            ["Yes, use both checks together", "No, kappa replaces that check", "Only if kappa drops below 0.6"],
            answer=0,
            clue="Kappa is one number. Can one number show you which kind of mistake the judge makes?",
            why="Kappa goes alongside the pass-and-fail check, not instead of it. The separate check "
                "shows whether the judge misses failures."),
    ],
    "checker_score": [
        ask("The agent replies \"I've refunded the order\", but the refund never went through. Your "
            "LLM judge reads only the reply and passes it. What would catch this?",
            ["A judge with a friendlier rubric", "Asking the agent to check itself", "A code check that reads the refund record"],
            answer=2,
            clue="Look at what really happened, not what the agent says happened.",
            why="That's a false success. A code-based grader checks the real end state, so it sees the "
                "refund never happened, whatever the reply claims."),
        ask("You plant mistakes in 10 runs. Your checker flags 6 of them, and it also flags 2 good "
            "runs. How many false alarms did it raise?",
            ["6, the mistakes it caught", "2, the good runs it flagged", "4, the mistakes it missed"],
            answer=1,
            clue="A false alarm happens on a run that had nothing wrong with it.",
            why="False alarms are good runs failed by mistake, so that's the 2. The 6 are catches "
                "and the other 4 are misses."),
    ],
    "memory_update_score": [
        ask("The office moved from Leeds to York. The agent answers \"It's in Leeds, or maybe York "
            "now.\" How do you score that answer?",
            ["Current, it gives the new fact", "Stale, it mentions the old fact", "Unsure, it sounds uncertain"],
            answer=1,
            clue="Can the user tell which city is right?",
            why="Any mention of the old fact makes it stale, even with the new one there, because the "
                "user can't tell which is right."),
        ask("As a baseline, you test a memory that never updates. It gets every changed fact right. "
            "What does that tell you?",
            ["The changed facts were easy ones", "This memory works better than you thought", "Your scoring isn't catching stale answers"],
            answer=2,
            clue="This stand-in should do badly on facts that changed. What if it doesn't?",
            why="A memory that never updates must fail the changed facts. If it passes, the scoring "
                "misses stale answers, like a judge that passes any answer containing \"York\"."),
    ],
    "review_queue": [
        ask("Your expert has time to check just one drafted label today. Which one should they see "
            "first?",
            ["A draft from a rare group", "A must-pass question's draft", "The draft written most recently"],
            answer=1,
            clue="Which wrong label would cost the most?",
            why="Must-pass questions come first, because a wrong label there is costly. Disagreeing "
                "drafts and rare groups come next."),
        ask("Two drafting runs give different expected facts for the same question. What does that "
            "usually mean?",
            ["The question is probably ambiguous", "One drafting run crashed early", "The source article is too short"],
            answer=0,
            clue="If two careful readers disagree, maybe the trouble is the question itself.",
            why="Disagreeing drafts usually mean the question can be read more than one way, so an "
                "expert should look at it early."),
    ],
    "change_report": [
        ask("You compare two versions on 200 questions. Most get the same result from both. Which "
            "questions should you read to understand the change?",
            ["The ones with the same result", "A random handful from all 200", "The ones where the versions differ"],
            answer=2,
            clue="A question that came out the same both times can't tell you what changed.",
            why="The questions where the versions disagree, the regressions and improvements, are the "
                "ones that explain what the change did."),
        ask("For one regression, you open the old and new traces side by side. What are you looking "
            "for?",
            ["The first step where they differ", "The step that took the longest", "The final answer's word count"],
            answer=0,
            clue="Both runs start out the same way. Where do they split apart?",
            why="Find the first step where the two traces differ, like a different document or tool. "
                "That's the cause to label."),
    ],
    "sort_changes": [
        ask("In one regression, the new version sent different articles to the generation step. "
            "Which part of the pipeline do you look at first?",
            ["The prompt that writes the answer", "Retrieval: how articles are found", "The scorer that grades the answer"],
            answer=1,
            clue="The answer step was handed different material to work with.",
            why="If different articles reached the generation step, the change started in retrieval, "
                "so look there first."),
        ask("A comparison gives you 60 regressions and improvements, and you have one afternoon. "
            "What's a sensible plan?",
            ["Read all 60 in the order they appear", "Read the 5 newest and skip the rest", "Sort them into buckets, read a few of each"],
            answer=2,
            clue="You can't read them all, but you want every kind of change covered.",
            why="Sorting first, then reading a sample from each bucket, gives you the error analysis "
                "for a fraction of the reading."),
    ],
    "mix_shift": [
        ask("Your company launched a new product last month, and lots of questions are now about it. "
            "Your eval set was built before that. What should you do?",
            ["Refresh the eval set with new questions", "Keep it, so old scores stay comparable", "Raise the pass mark on the old set"],
            answer=0,
            clue="Can the old set tell you how well the app handles the new product?",
            why="The mix of real questions has drifted. Refresh the eval set so its scores predict "
                "real quality again."),
        ask("You measure drift: how far the mix of real questions has moved from your eval set's mix. "
            "The measure (total variation distance) comes out at 0. What does that mean?",
            ["Real traffic is completely different", "Real traffic matches the eval set's mix", "The eval set has no questions in it"],
            answer=1,
            clue="The number adds up the gaps between the two mixes.",
            why="0 means the two mixes are the same, and 1 means completely different. At 0, the eval "
                "set still matches what users ask."),
    ],
    "judge_consistency": [
        ask("You judge the same 200 answers three times and keep the verdict that comes up at least twice. "
            "Why does that help?",
            ["Three runs cost less than one", "One odd verdict gets outvoted", "The judge learns from its own runs"],
            answer=1,
            clue="Think about what happens to a verdict that flipped just once.",
            why="Keeping the majority means a single unlucky flip no longer decides the verdict, so the result is steadier."),
        ask("You swap which of two answers you show the judge first, and it now prefers the other one. "
            "What have you found?",
            ["The judge favours whatever comes first", "The second answer is really better", "The judge is broken and must go"],
            answer=0,
            clue="Only the order changed. Did the answers change?",
            why="The answers were the same; only the order moved, and the verdict moved with it. That is position bias, a "
                "known habit of judges."),
    ],
    "disagreement": [
        ask("Your app drafts an answer three times, and the three drafts give three different dates. "
            "What should happen next?",
            ["Send the judge the first draft", "Write it again or send it to a person", "Average the three dates"],
            answer=1,
            clue="This flag is raised before the judge ever sees the draft. Who or what fixes a shaky draft?",
            why="Three drafts that disagree are a flag that the model is guessing. The flag belongs at drafting "
                "time: the draft is written again or handed to a person before any judge sees it."),
        ask("You score a confidence flag against the judge's verdicts and get a ROC-AUC of 0.52. The pass mark "
            "you wrote beforehand was 0.7. What do you do?",
            ["Add it: it is above 0.5", "Leave it out: it is barely better than guessing", "Lower the pass mark to 0.5 and add it"],
            answer=1,
            clue="What does 0.5 mean on this scale, and when was the pass mark set?",
            why="0.5 means the flag cannot tell a passing draft from a failing one, so 0.52 is close to luck. "
                "The pass mark was written first so the result could not talk you into moving it."),
    ],
    "gwet_ac1": [
        ask("Two judges both fail half the answers, and agree on 9 in 10. Kappa and AC1 come out almost the "
            "same. Why?",
            ["AC1 only differs when one verdict is rare", "Kappa and AC1 always give the same number", "Half and half breaks both measures"],
            answer=0,
            clue="When does kappa expect a lot of agreement by luck?",
            why="With passes and fails about equal, both count luck the same way. They only part when one verdict is "
                "much rarer than the other."),
        ask("Kappa is 0.2 and AC1 is 0.25 for your judge against people. What is the honest reading?",
            ["They really disagree; both are low", "AC1 rescues it, so trust the judge", "The rare verdict is causing it"],
            answer=0,
            clue="Is one number low and the other high, or are both low?",
            why="AC1 helps only when kappa is low but AC1 is high. Both low means the judge and the people really do "
                "disagree."),
    ],
    "judge_cost": [
        ask("Your judge reads 2,000 tokens and writes 200 for each call. You add a long reason to every "
            "verdict, and output grows to 800 tokens. At $2 in and $10 out per million, what happens?",
            ["The cost per call doubles", "The cost per call barely moves", "The cost per call halves"],
            answer=0,
            clue="Output costs five times input here. Work out both parts before and after.",
            why="Before: 2,000 times $2 plus 200 times $10, divided by a million = $0.006. After: 2,000 times "
                "$2 plus 800 times $10 = $0.012. Output is the dear part, so long reasons cost."),
        ask("Your team wants a judge a twentieth of the price. What do you do first?",
            ["Check it agrees with people and itself", "Switch now: cheaper is always better", "Run it only on easy examples"],
            answer=0,
            clue="What did the last lessons check before trusting a judge?",
            why="A cheap judge that disagrees with people gives verdicts you can't use. Check its "
                "agreement first, then switch if it passes."),
    ],
    "eval_cost": [
        ask("Labelling 200 examples takes 3 minutes each, and an hour of an expert's time costs $60. "
            "What does the golden set cost to label?",
            ["$600", "$60", "$36,000"],
            answer=0,
            clue="Minutes into hours first, then times the hourly cost.",
            why="200 times 3 minutes is 600 minutes, which is 10 hours. 10 times $60 = $600."),
        ask("Which change cuts the eval bill without making the eval less trustworthy?",
            ["Batch the full runs, which can wait", "Score half of each answer", "Drop the must-pass cases"],
            answer=0,
            clue="Which one changes the price, not what gets checked?",
            why="Batch processing halves the price of the same calls, so the verdicts are as good as "
                "before. The other two check less."),
    ],
}
