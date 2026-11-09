"""Step 2: add synthetic failures, then check the set can fail before any judge is paid for.

A set with almost no bad answers makes every judge look perfect. This counts the known-bad answers (planted, or
labelled bad by a person) and stops the job when there are fewer than --min-failures.
"""

import json

import pandas as pd

import judge_core as core
import tables

a = tables.args(("--min-failures", {"type": int, "default": 96}))
real = tables.rows(tables.read(a, "eval_set"))
labelled_bad = sum(1 for r in real if r["expected_pass"] is False)
# Plant just enough of each kind to reach the bar, spread evenly over the kinds.
per_kind = max(0, -(-(a.min_failures - labelled_bad) // len(core.PLANT_KINDS)))
planted = core.plants(real, per_kind)
everything = real + planted
gate = core.measurable(everything, a.min_failures)
print(json.dumps(gate, indent=1))
if not gate["ok"]:
    raise SystemExit(f"This set can't measure catching: {gate['known_bad']} known-bad answers, {gate['need']} needed. "
                     "Add labelled failures (expected_pass = false) or more good answers to plant from.")
tables.write(a, "eval_set_checked", pd.DataFrame([{**r, "planted": r.get("planted") or ""} for r in everything]))
print(f"{len(real)} real answers, {len(planted)} planted, {gate['known_bad']} known bad: judging can start.")
