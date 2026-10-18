"""More Check questions for Experiment design with MLflow (modules/experiments.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "best_run": [
        ask("You try a new prompt on your eval set and it scores 82%. What do you need before you can "
            "say it helped?",
            ["The current version's score, run the same way", "A second new prompt to compare it with", "A bigger model to run it on"],
            answer=0,
            clue="82% compared with what?",
            why="You need a baseline: the version you have now, scored on the same eval set the same way. "
                "Without it, 82% has nothing to be better than."),
        ask("In an MLflow run you set the chunk size to 500, measured quality at 0.81, and saved the "
            "eval results as a file. Which one is a parameter?",
            ["The quality of 0.81", "The chunk size of 500", "The eval results file"],
            answer=1,
            clue="Parameters are the things you choose before the run starts.",
            why="A parameter is what you set. The quality is a metric you measured, and the results file "
                "is an artifact."),
    ],
    "plan_gaps": [
        ask("Your plan lists the question, the change, the metric and the winner rule, but says "
            "nothing about the eval set. What could go wrong?",
            ["Someone adds new questions halfway", "The runs cost too much to finish", "The metric is too hard to read"],
            answer=0,
            clue="What stays fixed between runs needs writing down too.",
            why="The eval set and its version are controls. If the plan doesn't pin them down, they can "
                "change between runs and the comparison stops being fair."),
        ask("Your two prompts end up almost tied. The plan said a tie means keep the current one and "
            "add examples. What do you do?",
            ["Pick the new one, it's slightly ahead", "Change the metric so one wins", "Keep the current one, add examples"],
            answer=2,
            clue="You already decided this before you saw any results.",
            why="Writing down what \"no result\" means is part of the plan. Following it stops you "
                "talking yourself into the answer you hoped for."),
    ],
    "param_grid": [
        ask("Your grid tests 2 models with several chunk sizes and values of k. You add a third model. "
            "What happens to the number of runs?",
            ["It goes up by just one run", "Every chunk size and k runs again for it", "Nothing until the next grid"],
            answer=1,
            clue="A grid tries every combination of the values.",
            why="In a grid every value is combined with every other one, so a new model needs a run for "
                "each chunk size and k. Adding a value multiplies the runs."),
        ask("Your plan tests 5 chunk sizes and 4 values of k with 2 models. Before you start, what "
            "should you work out?",
            ["Which model will win", "Which chunk size is best", "How many runs, and what they cost"],
            answer=2,
            clue="Each run pays for eval and judge calls.",
            why="Every value multiplies the number of runs, and each run costs money. Count the runs and "
                "their cost before you start."),
    ],
    "find_confounds": [
        ask("Runs A and B have the same settings in MLflow, but B scored much lower. Later you learn "
            "the provider updated the model behind the same name. What is that?",
            ["A confound: a control quietly moved", "A fair test: the name stayed the same", "A bug in how MLflow logs runs"],
            answer=0,
            clue="Something changed between the runs that you didn't plan to change.",
            why="A model updated behind the same name is a confound: a second change you didn't plan. "
                "Now you can't tell what caused the drop."),
        ask("Your RAG experiment runs over two weeks, and new documents arrive every day. How do you "
            "keep it fair?",
            ["Rebuild the index before every run", "Only run on days with no new files", "Build the index once from a fixed copy"],
            answer=2,
            clue="The documents shouldn't change underneath your experiment.",
            why="Freeze the documents: build the index once from a fixed copy, give it a version, and log "
                "it with every run. Otherwise you measure the documents, not your change."),
    ],
    "replay_tools": [
        ask("During a replay run, the agent asks a tool about an order that was never recorded. "
            "What should the test do?",
            ["Call the live tool to fill the gap", "Mark the call as missing", "Make up a likely answer"],
            answer=1,
            clue="You want to see when a run steps outside the frozen world.",
            why="Marking it missing shows the run left the frozen world. Calling the live tool quietly "
                "would bring back the changing data you were avoiding."),
        ask("Your agent says \"ticket closed\" at the end of each task. How should you check task "
            "success?",
            ["Trust the agent's own report", "Count the steps it took", "Look at the ticket's real end state"],
            answer=2,
            clue="An agent can say it finished when it didn't.",
            why="Task success is checked from the real end state, not from what the agent says about "
                "itself."),
    ],
    "cv_folds": [
        ask("Your model scores 0.91 on one train/test split. Why might that one number mislead you?",
            ["That split may have been lucky", "One split always scores too low", "Scores only count in production"],
            answer=0,
            clue="Think about what happens if you split the same data a different way.",
            why="One split can be lucky or unlucky. Cross-validation tests on each fold in turn, so you see "
                "the average and how much the scores vary."),
        ask("You compare two models with cross-validation, but each one used a different set of 5 "
            "folds. What should you change?",
            ["Nothing, 5 folds each is fair", "Use 10 folds each instead", "Run both on the same folds"],
            answer=2,
            clue="A fair comparison gives both models exactly the same tests.",
            why="Compare models on the same folds, so any difference comes from the models, not from "
                "which examples landed in which fold."),
    ],
    "examples_needed": [
        ask("You have 25 test questions and hope a change adds about 3 points. Can this eval set show "
            "that?",
            ["Yes, any change will show up", "No, the margin of error is too wide", "Yes, if you run it twice"],
            answer=1,
            clue="With 25 questions, a 70% score could really be anywhere from 50% to 90%.",
            why="Fewer examples mean a wider margin of error. If the change you hope for is smaller than "
                "the margin, the eval set can't show it, so add examples first."),
        ask("With 100 questions, your score could be about 10 points off either way. You want it to "
            "be only about 5 off. How many questions do you need?",
            ["About 400 questions", "About 200 questions", "About 110 questions"],
            answer=0,
            clue="Look at the lesson's table: which size gives about 5 points?",
            why="Halving the margin takes four times the questions, not twice: 100 are about 10 points "
                "off either way, and 400 about 5."),
    ],
    "smoke_set": [
        ask("You're building a 40-question smoke set. Which way of picking the questions is best?",
            ["A few from each group, plus all must-pass", "The 40 newest questions", "The 40 hardest questions"],
            answer=0,
            clue="It should look like the full set in miniature, and never miss the dangerous cases.",
            why="A smoke set is stratified: a few questions from every group, plus the whole must-pass "
                "set. Then it catches bad ideas of every kind."),
        ask("A new idea clearly loses on the smoke set, 12 to 28. What's a sensible next step?",
            ["Run it on the holdout set", "Drop it and try the next idea", "Ship it and see what users say"],
            answer=1,
            clue="What is the smoke set for?",
            why="The smoke set is a filter for obviously bad ideas. A clear loss means drop it; only "
                "finalists move on to the full dev set."),
    ],
    "wilson_interval": [
        ask("Your app passed 49 of 50 checks. The quick margin rule gives 84% to 112%. What should "
            "you do?",
            ["Use a Wilson interval instead", "Report 84% to 112% as it is", "Round the top down to 100%"],
            answer=0,
            clue="A pass rate can't go over 100%, so the quick rule has broken down here.",
            why="Near 0% or 100% the quick rule breaks down. The Wilson interval always stays between 0% "
                "and 100% and stays honest with extreme rates."),
        ask("You're reporting three pass rates from small eval sets. Which one should get a Wilson "
            "interval instead of the quick margin rule?",
            ["50 of 100 answers right", "29 of 30 answers right", "60 of 100 answers right"],
            answer=1,
            clue="The quick rule breaks down when a rate is close to one of the edges.",
            why="29 of 30 is close to 100%, where the quick rule can run past 100%. The Wilson interval "
                "stays between 0% and 100% there."),
    ],
    "clear_winner": [
        ask("You ran prompt A once and got 0.82, and prompt B once and got 0.80. A teammate says A "
            "wins. What do you say?",
            ["Run each a few times before deciding", "Agreed: 0.82 beats 0.80", "Test a third prompt to break the tie"],
            answer=0,
            clue="LLMs and LLM judges don't give the same score every time.",
            why="One run each may just be luck. Run each setup 3 to 5 times and only call a winner when "
                "the results clearly separate."),
        ask("After 3 runs each, the scores of A and B overlap, but B costs half as much. What's a "
            "sensible pick?",
            ["A, because it might be better", "B: no clear winner, so pick on cost", "Neither: start the experiment over"],
            answer=1,
            clue="When quality doesn't separate them, look at something else that matters.",
            why="Overlapping results mean no clear winner on quality. Then you choose on cost or speed, or "
                "test on more examples."),
    ],
    "paired_verdict": [
        ask("A and B ran on the same 100 questions. On 90 of them, both got the same result. Which "
            "questions tell you which one is better?",
            ["All 100 questions", "The 90 where they agree", "The 10 where they disagree"],
            answer=2,
            clue="If both pass or both fail a question, does it favour either one?",
            why="Only disagreements count in a paired comparison. A question both got right, or both got "
                "wrong, says nothing about which is better."),
        ask("You have overall scores for A and B, but each ran on its own set of questions. A teammate "
            "wants a paired comparison. What's needed?",
            ["Run both on the same questions", "Run each one more time", "Use a bigger judge model"],
            answer=0,
            clue="\"Paired\" means each question has two results side by side.",
            why="A paired comparison looks example by example, so both setups must answer the same "
                "examples. Then hard questions are hard for both and that cancels out."),
    ],
    "decide_release": [
        ask("Your new version fails two gates: cost is over budget, and one must-pass case fails. "
            "What should the report show?",
            ["Only the first gate that failed", "Both failed gates", "The quality score first"],
            answer=1,
            clue="The team wants to fix everything in one round.",
            why="Check every gate and list each one that fails, not just the first. Then the team can fix "
                "them all at once."),
        ask("Every gate passes, and on quality the new version is too close to call. What is the "
            "decision?",
            ["Ship it: every gate passed", "Drop the new version for good", "Keep the baseline for now"],
            answer=2,
            clue="Passing the gates only lets you look at quality. It doesn't decide by itself.",
            why="Too close to call keeps the baseline for now. Then add more examples, or choose on cost."),
    ],
    "biggest_gap": [
        ask("Your team plans to spend a month tuning retrieval in your RAG app. What would you run "
            "first, to see if it's worth it?",
            ["A run that hands it the right documents", "A grid of every chunk size and k", "The same eval again, to check the score"],
            answer=0,
            clue="Find out the most retrieval could gain before you spend time on it.",
            why="An oracle run shows retrieval's headroom. If perfect documents barely lift the score, a "
                "month of tuning retrieval is wasted."),
        ask("You want to run an oracle test on retrieval for your RAG app. What must your eval set "
            "have first?",
            ["Twice as many questions", "A second, bigger model", "The right document for each question"],
            answer=2,
            clue="To hand the model the perfect documents, you have to know what they are.",
            why="An oracle test needs the right answers for each step, like the correct document ids for "
                "each question. Without them you can't make retrieval perfect."),
    ],
    "ablation_report": [
        ask("You remove the reranker and rerun the same 200 questions. 20 answers that passed now "
            "fail, and only 1 that failed now passes. What do you do?",
            ["Keep the reranker: it does real work", "Remove it: one answer got better", "Nothing yet: it could just be luck"],
            answer=0,
            clue="Count only the questions where the two versions disagree. Is it close?",
            why="Without it, 20 answers broke and only 1 got fixed: a big, one-sided gap. The reranker "
                "is earning its cost."),
        ask("You remove the reranker and query rewriting in the same run, and the score drops 5 "
            "points. What can you say?",
            ["The reranker was worth 5 points", "Query rewriting was worth 5 points", "You can't tell which part did it"],
            answer=2,
            clue="An ablation takes out parts in a particular way.",
            why="An ablation removes one part at a time and keeps everything else. Remove two at once and "
                "you can't tell which one caused the drop."),
    ],
    "fluke_risk": [
        ask("A teammate tried 20 prompts, kept the best, and quotes its dev-set score as what to "
            "expect in production. What's wrong?",
            ["20 prompts is too few to try", "Dev-set scores always run low", "The best of 20 is partly luck"],
            answer=2,
            clue="If you try enough things, one will look good by chance.",
            why="The best of many is partly luck, so its score on the same eval set is too optimistic. "
                "Confirm it once on the holdout set."),
        ask("Someone wants to test 50 prompt ideas against the baseline tomorrow. What's a guard you'd "
            "add while planning?",
            ["Run all 50 on the holdout set", "Test fewer, with a stricter threshold", "Run each idea once to save money"],
            answer=1,
            clue="Each comparison has a small chance of a fake winner, and those chances add up.",
            why="Test fewer ideas, and use a stricter threshold for each one. The holdout is only for "
                "confirming the winner once, at the end."),
    ],
    "clumpy_margin": [
        ask("You can add 100 more questions to your eval. Which adds the most information?",
            ["100 questions about new documents", "100 more about documents you have", "100 rewordings of old questions"],
            answer=0,
            clue="Questions about the same document tend to pass or fail together.",
            why="New documents are new clumps. More questions about the same documents mostly repeat what you already "
                "know."),
        ask("Your report says \"92%, give or take 3 points\" from 900 answers about 30 products. What should "
            "you check first?",
            ["Whether answers about one product move together", "Whether 900 is a round enough number", "Whether 92% is above last month's"],
            answer=0,
            clue="Is 900 the real count of separate examples here?",
            why="If answers about one product pass or fail together, there are closer to 30 separate units than 900, "
                "and the margin is much wider than 3 points."),
    ],
    "examples_per_group": [
        ask("Your pass rate is about 70%. You can only get about 340 examples in each group. Which gain "
            "should you look for?",
            ["A gain of about 10 points or more", "Any gain at all, even 1 point", "A gain of about 5 points"],
            answer=0,
            clue="Look back at what the rule of thumb gave for 5 points and for 10.",
            why="About 340 examples in each group is enough for a 10-point gain at a 70% pass rate. A 5-point gain "
                "needs about 1,344."),
        ask("You want to notice a smaller gain: half the size you planned. Roughly how many more examples "
            "will you need?",
            ["About twice as many", "About four times as many", "About the same number"],
            answer=1,
            clue="In the rule, the difference is multiplied by itself.",
            why="The difference is multiplied by itself in the rule, so halving it means four times as many examples."),
    ],
    "assign_group": [
        ask("You roll out a new version to 10% of users, and next week to 50%. With a hash bucket, which "
            "users who had it keep it?",
            ["Everyone in buckets 0 to 9", "A fresh random 10%", "Nobody: everyone is reassigned"],
            answer=0,
            clue="The bucket depends only on the user's id.",
            why="Buckets 0 to 9 are below both 10 and 50, so those users stay in B; the rollout only adds buckets 10 "
                "to 49."),
        ask("Group B looks 4 points ahead after one day, so the team wants to stop and ship. What is the "
            "risk?",
            ["Stopping early rewards a lucky day", "One day is long enough to be sure of it", "Group A will feel left out of the change"],
            answer=0,
            clue="If you check every day, how many chances do you give luck?",
            why="Checking again and again and stopping when it looks good is like testing many variants: luck "
                "eventually looks like a win. Decide the users and stop date first."),
    ],
}
