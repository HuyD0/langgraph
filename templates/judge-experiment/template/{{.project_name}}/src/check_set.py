# Databricks notebook source
# MAGIC %md
# MAGIC # 2 · Check the set can fail
# MAGIC
# MAGIC **Why:** a judge is only worth measuring on a set that holds bad answers. If nearly every answer is good, a judge
# MAGIC that passes everything looks perfect, and you learn nothing. This step makes sure the set can fail *before* any
# MAGIC judge is paid for.
# MAGIC
# MAGIC **What it does, in order:**
# MAGIC 1. **Reads people's verdicts back.** Answers a person reviewed in the last run's review queue (MLflow, Reviews)
# MAGIC    get their verdict as a label: `expected_pass` true or false. From then on the judge is measured against people.
# MAGIC 2. **Adds synthetic failures.** Copies of good answers with one rule broken on purpose, so they are bad by
# MAGIC    construction: another question's answer (`wrong_answer`), a number changed (`wrong_number`), a made-up fact
# MAGIC    (`made_up_fact`), and leaning on an earlier chat (`not_standalone`). Replace them with real failures as you
# MAGIC    collect them: a planted mistake is usually plainer than a real one.
# MAGIC 3. **Checks the gate.** It needs `min_failures` known-bad answers (96 by default: with a catch rate near a half,
# MAGIC    that gives a 95% range about 10 points each way). Too few, and the job stops here.
# MAGIC
# MAGIC **Writes:** `eval_set_checked`, the real answers plus the planted ones, for step 3.

# COMMAND ----------

# MAGIC %pip install -q "mlflow[databricks]>=3.17,<4" markdown

# COMMAND ----------

try:
    dbutils.library.restartPython()  # noqa: F821 - defined in a Databricks notebook
except NameError:
    pass  # on a laptop: nothing to restart

# COMMAND ----------

import pandas as pd

import judge_core as core
import review
import tables

a = tables.args(("--min-failures", {"type": int, "default": 96}))
real = tables.rows(tables.read(a, "eval_set"))

# 1. People's verdicts from the last review queue become labels. Only answers sent for review can have one.
found, changed = {}, 0
if a.experiment and tables.exists(a, "review_queue"):
    exp = tables.experiment(a)
    sent = tables.read(a, "review_queue")
    by_trace = {t: i for i, t in zip(sent["id"], sent["trace_id"]) if t}
    found = review.verdicts(exp.experiment_id, list(by_trace)) if exp else {}
    real, changed = core.apply_verdicts(real, {by_trace[t]: v for t, v in found.items()})
    if changed:
        tables.write(a, "eval_set", pd.DataFrame(real))
tables.say(f"### 1. People's verdicts\n\n**{len(found)}** answers in the last review queue have a person's verdict; "
           f"**{changed}** labels changed. " + ("" if found else "Nobody has reviewed anything yet, or this is the first run."))

# COMMAND ----------

# 2. Plant just enough of each kind to reach the bar, spread evenly over the kinds.
labelled_bad = sum(1 for r in real if r["expected_pass"] is False)
per_kind = max(0, -(-(a.min_failures - labelled_bad) // len(core.PLANT_KINDS)))
planted = core.plants(real, per_kind)
everything = real + planted
gate = core.measurable(everything, a.min_failures)
tables.say(f"### 2. Known-bad answers\n\n{len(real)} real answers ({labelled_bad} labelled bad by a person) plus "
           f"**{len(planted)} planted** ({per_kind} of each kind). By kind, then by group:")
tables.show(pd.DataFrame([{"kind of bad answer": k, "answers": n} for k, n in gate["by_kind"].items()]))
tables.show(pd.DataFrame([{"group": g, "bad answers": n} for g, n in gate["by_group"].items()]))

# COMMAND ----------

# 3. The gate.
if not gate["ok"]:
    tables.say(f"### 3. Gate: stopped\n\n**{gate['known_bad']}** known-bad answers, **{gate['need']}** needed. A catch rate "
               "measured on fewer would be too uncertain to decide anything. Add answers labelled bad (`expected_pass = "
               "false`), or more good answers to plant from, then run again.")
    raise SystemExit(f"This set can't measure catching: {gate['known_bad']} known-bad answers, {gate['need']} needed.")
tables.write(a, "eval_set_checked", pd.DataFrame([{**r, "planted": r.get("planted") or ""} for r in everything]))
tables.say(f"### 3. Gate: passed\n\n**{gate['known_bad']}** known-bad answers, **{gate['need']}** needed, and "
           f"**{gate['labelled_good']}** labelled good. Judging can start: {len(everything)} answers are in "
           f"`{tables.where(a, 'eval_set_checked')}`.")
