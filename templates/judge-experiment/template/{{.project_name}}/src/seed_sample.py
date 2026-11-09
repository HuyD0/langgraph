# Databricks notebook source
# MAGIC %md
# MAGIC # 1 · Load the eval set
# MAGIC
# MAGIC **What this does:** makes sure there is an eval set to grade. If `<catalog>.<schema>.eval_set` doesn't exist yet,
# MAGIC it loads the 24-answer help-centre sample from `fixtures/sample_eval_set.csv`. If it exists, it leaves it alone,
# MAGIC so your own answers are never overwritten.
# MAGIC
# MAGIC **To use your own answers:** create `eval_set` before the first run, with these columns:
# MAGIC
# MAGIC | Column | Holds |
# MAGIC |---|---|
# MAGIC | `id` | A unique id per answer |
# MAGIC | `group` | A group to report by, such as a product area |
# MAGIC | `context` | What the answer must stick to: the documents, the policy |
# MAGIC | `question` | What was asked |
# MAGIC | `answer` | Your app's answer |
# MAGIC | `expected_pass` | `true` or `false` if a person has checked it, empty if nobody has |
# MAGIC
# MAGIC **Next:** step 2 checks the set holds enough bad answers to measure a judge.

# COMMAND ----------

# MAGIC %pip install -q "mlflow[databricks]>=3.17,<4" markdown

# COMMAND ----------

try:
    dbutils.library.restartPython()  # noqa: F821 - defined in a Databricks notebook
except NameError:
    pass  # on a laptop: nothing to restart

# COMMAND ----------

import pandas as pd

import tables

a = tables.args()
if tables.exists(a, "eval_set"):
    current = tables.read(a, "eval_set")
    tables.say(f"### Kept your eval set\n\n`{tables.where(a, 'eval_set')}` already exists with **{len(current)} answers**, "
               "so nothing was loaded. The first rows:")
else:
    current = pd.read_csv(tables.root(a) / "fixtures" / "sample_eval_set.csv")
    tables.write(a, "eval_set", current)
    tables.say(f"### Loaded the sample\n\n**{len(current)} answers** from `fixtures/sample_eval_set.csv` are now in "
               f"`{tables.where(a, 'eval_set')}`. Replace them with your own answers whenever you like. The first rows:")
rows = tables.rows(current)
counts = pd.DataFrame({"group": sorted({str(r.get('group')) for r in rows})})
counts["answers"] = counts["group"].map(lambda g: sum(1 for r in rows if str(r.get("group")) == g))
counts["labelled good"] = counts["group"].map(lambda g: sum(1 for r in rows if str(r.get("group")) == g and r["expected_pass"] is True))
counts["labelled bad"] = counts["group"].map(lambda g: sum(1 for r in rows if str(r.get("group")) == g and r["expected_pass"] is False))
tables.show(current.head(10))
tables.say("**Answers per group, and how many a person has labelled:**")
tables.show(counts)
