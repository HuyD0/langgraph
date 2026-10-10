"""Lessons for the MLflow Prompt Registry. AFTER says which lesson each new one follows in the path."""
AFTER = {"resolve_prompt": "fill_template", "prompt_rollout": "route_request"}

L = {}
def lesson(id, title, learn, example, check, angle):
    L[id] = dict(title=title, learn=learn, example=example, check=check, angle=angle)
Q = lambda q, opts, a, why: (q, opts, a, why)

lesson("resolve_prompt", "The prompt registry",
 ["Changing one word in a prompt can change every answer, so treat prompts like code. The **MLflow Prompt Registry** stores them the way the model registry stores models: each save makes a new numbered **version**, and versions never change.",
  "Your app loads an **alias** like `production`, not a number. Shipping or rolling back a prompt means moving the alias: no code change, no redeploy. On Databricks, prompts live in Unity Catalog, with the same three-part names and permissions as tables and models."],
 ("Versions and an alias", "main.support.answer\n  v1  Q: {{question}}\n  v2  Use the context. {{context}} Q: {{question}}   ← production\n  v3  Cite sources. {{context}} Q: {{question}}\n\nload_prompt(\"prompts:/main.support.answer@production\")  → v2"),
 Q("Version 3 of a prompt made answers worse in production. What's the fastest safe fix?",
   ["Edit version 3 back to the old wording", "Point the production alias back at version 2", "Paste the old prompt into the code and redeploy"], 1,
   "Versions never change, so version 2 is exactly what ran before. Moving the alias is instant and leaves a record."),
 ("Parse, then look up", "Split the address into a name and a version or alias, then a few dict lookups. Interviewers like hearing about settings you can change without a deploy.",
  "\"Prompts are versioned and never edited in place. The app loads by alias, so promoting or rolling back is moving a pointer, not shipping code.\"", None))

lesson("prompt_rollout", "Rolling out a new prompt",
 ["Before a new prompt version gets the `production` alias, score it offline with `mlflow.genai.evaluate`, then give it a small share of real traffic.",
  "Tag every trace with the prompt version it used. Then you can compare versions on real questions and decide with a rule you wrote down first: promote, keep testing, or roll back."],
 ("Same traffic, two versions", "v2 (production): 6 of 8 passed  → 75%\nv3 (candidate):  4 of 4 passed  → 100%\nrule: at least 4 traces and 5 points better → promote v3"),
 Q("A candidate prompt passed 2 out of 2 traces. Should you promote it?",
   ["Yes, it's perfect", "Not yet: 2 traces is too few to tell", "Roll it back"], 1,
   "With tiny samples, luck decides. Set a minimum number of traces before you compare."),
 ("Group and count", "One walk through the traces, counting totals and passes per version in dicts, then a few comparisons.",
  "\"I tag traces with the prompt version, compare pass rates once each version has enough traffic, and promote only on a gain I set in advance.\"", None))

STACK = {
 "resolve_prompt": ("MLflow Prompt Registry in Unity Catalog",
  "import mlflow\n\np = mlflow.genai.register_prompt(\n    name=\"main.support.answer\",\n    template=\"Use the context. {{context}} Q: {{question}}\",\n    commit_message=\"Ground answers in retrieved context\",\n)\nmlflow.genai.set_prompt_alias(\"main.support.answer\", alias=\"production\", version=p.version)\n\nprompt = mlflow.genai.load_prompt(\"prompts:/main.support.answer@production\")\ntext = prompt.format(context=docs, question=q)\n\n# LangChain templates use single braces:\nlc_prompt = ChatPromptTemplate.from_template(prompt.to_single_brace_format())"),
 "prompt_rollout": ("Tag traces with the prompt version, then compare",
  "prod = mlflow.genai.load_prompt(\"prompts:/main.support.answer@production\")\ncand = mlflow.genai.load_prompt(\"prompts:/main.support.answer@candidate\")\n\n@mlflow.trace\ndef answer(question, user_id):\n    prompt = cand if bucket(user_id) < 10 else prod   # 10% to the candidate\n    mlflow.update_current_trace(tags={\"prompt_version\": str(prompt.version)})\n    ...\n\nmlflow.search_traces(filter_string=\"tags.prompt_version = '3'\")\n\n# when the rule says promote:\nmlflow.genai.set_prompt_alias(\"main.support.answer\", alias=\"production\", version=3)"),
}
