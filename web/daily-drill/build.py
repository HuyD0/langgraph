"""Build the Daily Drill page: content/*.py + content/base_content.json + app.html -> dist/daily-drill.html.

Run: uv run python web/daily-drill/build.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "content"))
import new_problems, new_problems2, new_problems3, new_problems4, new_problems5, new_problems6, curriculum, curriculum2, curriculum3, curriculum4, curriculum5, plain
new_problems.check(); new_problems2.check(); new_problems3.check(); new_problems4.check(); new_problems5.check(); new_problems6.check()
MODULES = list(curriculum3.MODULES)
MODULES.insert([m[0] for m in MODULES].index("shipping"), curriculum4.MODULE)
MODULES.insert([m[0] for m in MODULES].index("agents") + 1, curriculum5.SECURITY)
MODULES.insert([m[0] for m in MODULES].index("production") + 1, curriculum5.RELIABILITY)
MODULES = [(i, t, b, ls + curriculum5.ADD.get(i, [])) for i, t, b, ls in MODULES]
LIFECYCLE = [(n, t, m + {"Build and trace": ["production", "security"], "Monitor": ["reliability"]}.get(n, [])) for n, t, m in curriculum3.LIFECYCLE]
old = json.load(open(HERE / "content" / "base_content.json", encoding="utf-8"))

bank = {p["id"]: p for p in old["BANK"]}
learn = old["LEARN"]
for p in new_problems.P + new_problems2.P + new_problems3.P + new_problems4.P + new_problems5.P + new_problems6.P:
    cases = []
    for c in p["cases"]:
        sample = c[-1] is True or c[-1] == "S"
        body = c[:-1] if sample else c
        d = {"args": list(body[:-1]), "expected": body[-1]}
        if sample: d["sample"] = True
        cases.append(d)
    q = {k: p[k] for k in ["id", "title", "topic", "difficulty", "fn", "prompt", "pattern", "target", "realworld", "starter", "solution"]}
    q.update(cases=cases, unordered=False)
    bank[p["id"]] = q
    learn[p["id"]] = dict(p["learn"], guided=p["guided"])
for pid, fx in plain.NEW_FIX.items():
    if "target" in fx: bank[pid]["target"] = fx["target"]
    if "why" in fx: learn[pid]["why"] = fx["why"]
    if "prompt_from" in fx:
        assert fx["prompt_from"] in bank[pid]["prompt"], pid
        bank[pid]["prompt"] = bank[pid]["prompt"].replace(fx["prompt_from"], fx["prompt_to"])
for pid, w in plain.CLASSIC_WHY.items():
    learn[pid]["why"] = w
for a, b in plain.OLD_FIX:
    hit = False
    for v in learn.values():
        if v.get("why") == a: v["why"] = b; hit = True
    assert hit, a[:40]

lessons = {}
for lid, l in curriculum.L.items():
    pattern, _, _, classic = l["angle"]
    text, say = plain.ANGLE[lid]
    lessons[lid] = dict(title=l["title"], learn=l["learn"], example=list(l["example"]), check=[l["check"][0], l["check"][1], l["check"][2], l["check"][3]], angle=[pattern, text, say, classic])
for lid, l in curriculum2.L.items():
    lessons[lid] = dict(title=l["title"], learn=l["learn"], example=list(l["example"]), check=list(l["check"]), angle=list(l["angle"]))
for lid, l in curriculum3.L.items():
    lessons[lid] = dict(title=l["title"], learn=l["learn"], example=list(l["example"]), check=list(l["check"]), angle=list(l["angle"]))
for lid, l in list(curriculum4.L.items()) + list(curriculum5.L.items()):
    lessons[lid] = dict(title=l["title"], learn=l["learn"], example=list(l["example"]), check=list(l["check"]), angle=list(l["angle"]))
for lid, box in list(curriculum3.STACK.items()) + list(curriculum4.STACK.items()) + list(curriculum5.STACK.items()):
    lessons[lid]["stack"] = list(box)
for lid, l in lessons.items():
    assert lid in bank, lid
    if l["angle"][3]: assert l["angle"][3] in bank, l["angle"][3]
path_ids = [x for *_, ls in MODULES for x in ls]
assert sorted(path_ids) == sorted(lessons), set(path_ids) ^ set(lessons)

classics = [p["id"] for p in old["BANK"] if p.get("track") == "basics"]
money = old["MINE_IDS"]
for p in bank.values(): p.pop("track", None)
gl = {g[0]: g for g in old["GLOSSARY"]}
order = ["AI words", "Terraform, Azure and Databricks", "Python basics", "Problem solving", "Terms from the notebooks"]
glossary = [gl[k] for k in order if k in gl] + [g for k, g in gl.items() if k not in order]

data = dict(modules=[dict(id=i, title=t, blurb=b, lessons=ls) for i, t, b, ls in MODULES],
            lifecycle=[dict(name=n, text=t, modules=m) for n, t, m in LIFECYCLE],
            lessons=lessons, bank=list(bank.values()), learn=learn, glossary=glossary,
            rules=old["RULES"], aiGotchas=old["AI_GOTCHAS"], iacGotchas=old["IAC_GOTCHAS"], classics=classics, money=money)

# plain-language guard: no Big-O notation in anything the learner reads (code fields excluded)
bad = []
def walk(x, path):
    if isinstance(x, str):
        if re.search(r"\bO\((n|1|log|k|V|rows|capacity|total)", x) and not any(s in path for s in ("solution", "starter", "guided")):
            if not path.startswith(".glossary"): bad.append((path, x[:90]))
    elif isinstance(x, list):
        for i, v in enumerate(x): walk(v, f"{path}[{i}]")
    elif isinstance(x, dict):
        for k, v in x.items(): walk(v, f"{path}.{k}")
walk(data, "")
for b in bad: print("BIG-O:", b)

html = open(HERE / "app.html", encoding="utf-8").read().replace("/*DATA*/", json.dumps(data, ensure_ascii=False))
(HERE / "dist").mkdir(exist_ok=True)
open(HERE / "dist" / "daily-drill.html", "w", encoding="utf-8").write(html)
if bad:
    sys.exit("Big-O notation found in learner-facing text; see BIG-O lines above.")
print("lessons", len(lessons), "bank", len(bank), "bytes", len(html), "bigO leftovers", len(bad))
