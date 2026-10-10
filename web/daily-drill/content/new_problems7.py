"""MLflow Prompt Registry exercises. Sample cases are marked with the string "S"."""
import json
P = []
def add(**k): P.append(k)
H = "    # Replace every ___ with real code, then run the tests.\n"

REG = {"main.support.answer": {"versions": {"1": "Q: {{question}}", "2": "Use the context. {{context}} Q: {{question}}", "10": "Cite sources. {{context}} Q: {{question}}"},
                               "aliases": {"production": 2}}}

add(id="resolve_prompt", title="Load a Prompt by Alias", topic="llm-apps", difficulty="medium", fn="resolve_prompt",
 prompt="A prompt registry keeps every version of each prompt. `registry` maps a prompt name to `{\"versions\": {\"1\": template, ...}, \"aliases\": {\"production\": 2, ...}}`.\n\nApps load prompts by address, in one of two forms:\n- `prompts:/<name>/<version>`, like `prompts:/main.support.answer/2`\n- `prompts:/<name>@<alias>`, like `prompts:/main.support.answer@production`. The alias `latest` means the highest version number.\n\nReturn `[version, template]` with the version as a number, or `None` if the address doesn't start with `prompts:/`, or the name, version or alias doesn't exist.",
 pattern="Parse the address into its parts, then a couple of dict lookups.",
 target="one pass over the address, then lookups",
 realworld="This is how `mlflow.genai.load_prompt(\"prompts:/main.support.answer@production\")` works. Saved versions never change, so moving the `production` alias is how you ship or roll back a prompt without redeploying the app.",
 starter="def resolve_prompt(registry, uri):\n    # your code here\n    pass\n",
 solution="def resolve_prompt(registry, uri):\n    prefix = \"prompts:/\"\n    if not uri.startswith(prefix):\n        return None\n    rest = uri[len(prefix):]\n    if \"@\" in rest:\n        name, alias = rest.split(\"@\", 1)\n        entry = registry.get(name)\n        if entry is None:\n            return None\n        if alias == \"latest\":\n            version = max(int(v) for v in entry[\"versions\"])\n        elif alias in entry[\"aliases\"]:\n            version = entry[\"aliases\"][alias]\n        else:\n            return None\n    elif \"/\" in rest:\n        name, v = rest.split(\"/\", 1)\n        entry = registry.get(name)\n        if entry is None or not v.isdigit():\n            return None\n        version = int(v)\n    else:\n        return None\n    template = entry[\"versions\"].get(str(version))\n    if template is None:\n        return None\n    return [version, template]\n",
 cases=[(REG, "prompts:/main.support.answer@production", [2, "Use the context. {{context}} Q: {{question}}"], "S"),
        (REG, "prompts:/main.support.answer/10", [10, "Cite sources. {{context}} Q: {{question}}"]),
        (REG, "prompts:/main.support.answer@latest", [10, "Cite sources. {{context}} Q: {{question}}"]),
        (REG, "prompts:/main.support.answer@staging", None),
        (REG, "prompts:/main.support.answer/7", None),
        (REG, "prompts:/main.support.other@production", None),
        (REG, "runs:/abc123/model", None)],
 guided="def resolve_prompt(registry, uri):\n" + H + "\n    prefix = \"prompts:/\"\n    if not uri.startswith(prefix):\n        return None\n    rest = uri[len(prefix):]\n    if \"@\" in rest:\n        # Step 1: split once into the name and the alias.\n        name, alias = ___\n        entry = registry.get(name)\n        if entry is None:\n            return None\n        if alias == \"latest\":\n            # Step 2: the highest version, compared as numbers.\n            version = ___\n        elif alias in entry[\"aliases\"]:\n            version = ___\n        else:\n            return None\n    elif \"/\" in rest:\n        name, v = rest.split(\"/\", 1)\n        entry = registry.get(name)\n        if entry is None or not v.isdigit():\n            return None\n        version = int(v)\n    else:\n        return None\n    # Step 3: version keys are strings; return None if it's missing.\n    template = ___\n    if template is None:\n        return None\n    return [version, template]\n",
 fills=["rest.split(\"@\", 1)", "max(int(v) for v in entry[\"versions\"])", "entry[\"aliases\"][alias]", "entry[\"versions\"].get(str(version))"],
 learn=dict(concepts=[["split with a limit", "Split at the first separator only.", "\"a@b@c\".split(\"@\", 1)   # ['a', 'b@c']"],
                      ["max over converted values", "Convert each one as you go, then take the biggest.", "max(int(v) for v in [\"2\", \"10\"])   # 10"]],
  byhand="Strip prompts:/ and split at @: the name is main.support.answer, the alias is production. The alias points at 2. Look up \"2\" in versions: found, so return [2, its template].",
  why="One pass over the address, then a few dict lookups.",
  gotchas=[["Compare versions as numbers", "As text, \"9\" sorts after \"10\". Convert version strings to ints before picking the latest."],
           ["Don't ship @latest", "`latest` changes whenever anyone saves a version. Use it in notebooks; deployed agents load a named alias like `production`."]]))

add(id="prompt_rollout", title="Promote a Prompt Version", topic="shipping", difficulty="medium", fn="prompt_rollout",
 prompt="You're testing a new prompt version on a slice of real traffic. Each trace is `[version, ok]`: the prompt version it used and whether the judge passed it.\n\nCompute each version's pass rate as a whole percent, rounded down (`100 * passed // total`). Then decide, comparing `candidate` against `current`:\n- `\"wait\"` if `current` has no traces or `candidate` has fewer than `min_traces`\n- `\"promote\"` if the candidate's rate is at least `min_gain` points higher\n- `\"rollback\"` if it's lower\n- `\"keep\"` otherwise (keep testing)\n\nReturn `{\"decision\": ..., \"current\": rate, \"candidate\": rate}`, using `None` for a version with no traces.",
 pattern="Count per key in one walk, then apply a rule you wrote down before looking at the numbers.",
 target="one walk through the traces",
 realworld="Tag every trace with the prompt version it used, and MLflow can split production quality by version. Decide the minimum sample and the gain you need first, so a lucky afternoon doesn't ship a worse prompt.",
 starter="def prompt_rollout(traces, current, candidate, min_traces, min_gain):\n    # your code here\n    pass\n",
 solution="def prompt_rollout(traces, current, candidate, min_traces, min_gain):\n    total, passed = {}, {}\n    for version, ok in traces:\n        total[version] = total.get(version, 0) + 1\n        if ok:\n            passed[version] = passed.get(version, 0) + 1\n    def rate(v):\n        if total.get(v, 0) == 0:\n            return None\n        return 100 * passed.get(v, 0) // total[v]\n    cur, cand = rate(current), rate(candidate)\n    if cur is None or total.get(candidate, 0) < min_traces:\n        decision = \"wait\"\n    elif cand >= cur + min_gain:\n        decision = \"promote\"\n    elif cand < cur:\n        decision = \"rollback\"\n    else:\n        decision = \"keep\"\n    return {\"decision\": decision, \"current\": cur, \"candidate\": cand}\n",
 cases=[([[2, True], [3, True], [2, True], [2, False], [3, True], [2, True], [1, False], [2, True], [3, True], [2, False], [2, True], [3, True], [2, True]], 2, 3, 4, 5,
         {"decision": "promote", "current": 75, "candidate": 100}, "S"),
        ([[2, True], [3, True], [3, False]], 2, 3, 4, 5, {"decision": "wait", "current": 100, "candidate": 50}),
        ([], 2, 3, 1, 5, {"decision": "wait", "current": None, "candidate": None}),
        ([[3, True]], 2, 3, 1, 5, {"decision": "wait", "current": None, "candidate": 100}),
        ([[1, True], [1, True], [2, True], [2, False]], 1, 2, 2, 5, {"decision": "rollback", "current": 100, "candidate": 50}),
        ([[1, True], [1, True], [1, True], [1, False], [2, True], [2, True], [2, True], [2, False]], 1, 2, 4, 5, {"decision": "keep", "current": 75, "candidate": 75})],
 guided="def prompt_rollout(traces, current, candidate, min_traces, min_gain):\n" + H + "\n    total, passed = {}, {}\n    for version, ok in traces:\n        # Step 1: count every trace, and the passing ones.\n        total[version] = ___\n        if ok:\n            passed[version] = passed.get(version, 0) + 1\n    def rate(v):\n        if total.get(v, 0) == 0:\n            return None\n        # Step 2: whole percent, rounded down.\n        return ___\n    cur, cand = rate(current), rate(candidate)\n    # Step 3: not enough evidence yet?\n    if cur is None or ___:\n        decision = \"wait\"\n    elif ___:\n        decision = \"promote\"\n    elif cand < cur:\n        decision = \"rollback\"\n    else:\n        decision = \"keep\"\n    return {\"decision\": decision, \"current\": cur, \"candidate\": cand}\n",
 fills=["total.get(version, 0) + 1", "100 * passed.get(v, 0) // total[v]", "total.get(candidate, 0) < min_traces", "cand >= cur + min_gain"],
 learn=dict(concepts=[["Counting per key", "get with a default of 0, then add one.", "seen[v] = seen.get(v, 0) + 1"],
                      ["Whole percent, rounded down", "// divides and drops the remainder.", "100 * 6 // 8   # 75"]],
  byhand="Version 2: 6 passed out of 8, so 75. Version 3: 4 of 4, so 100. Version 1 isn't part of the test: ignore it. Version 3 has at least 4 traces, and 100 is at least 75 + 5: promote.",
  why="One walk through the traces, then a few comparisons.",
  gotchas=[["Same traffic, same judge", "Compare versions on the same kind of questions with the same scorer, or the difference may come from the questions, not the prompt."],
           ["Prompt and model travel together", "A prompt tuned for one model can get worse on another. Tag the model on the trace too, and re-test prompts when you change models."]]))

def check():
    for p in P:
        for variant in ("solution", "guided"):
            code = p["solution"] if variant == "solution" else p["guided"].replace("# Replace every ___ with real code, then run the tests.", "#")
            if variant == "guided":
                for f in p["fills"]:
                    assert "___" in code, (p["id"], "too many fills"); code = code.replace("___", f, 1)
                assert "___" not in code, (p["id"], "unfilled")
            ns = {}; exec(code, ns); fn = ns[p["fn"]]
            for c in p["cases"]:
                body = c[:-1] if c[-1] == "S" else c
                args, exp = list(body[:-1]), body[-1]
                got = fn(*json.loads(json.dumps(args)))
                assert got == exp, (p["id"], variant, args, exp, got)
    print("verified", len(P), "prompt-registry problems")
if __name__ == "__main__":
    check()
