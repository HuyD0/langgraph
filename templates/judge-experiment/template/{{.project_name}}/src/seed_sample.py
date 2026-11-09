"""Step 1: put the sample eval set in place, only if there is no eval_set table yet.

Replace the sample with your own answers by creating <catalog>.<schema>.eval_set with the same columns:
id, group, context, question, answer, expected_pass (true, false, or empty when nobody has checked it).
"""

import pandas as pd

import tables

a = tables.args()
if tables.exists(a, "eval_set"):
    print("eval_set already exists: keeping it.")
else:
    sample = pd.read_csv(tables.root(a) / "fixtures" / "sample_eval_set.csv")
    tables.write(a, "eval_set", sample)
    print(f"Loaded the sample eval set: {len(sample)} answers.")
