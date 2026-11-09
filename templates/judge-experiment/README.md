# Judge experiment: a Declarative Automation Bundle template

Starts a judge experiment in a Databricks workspace with one command. It grades an app's answers with an LLM judge,
checks first that the eval set can fail, keeps every vote on its MLflow trace, and sends what the judge fails to a
person.

```bash
databricks bundle init https://github.com/HuyD0/langgraph --template-dir templates/judge-experiment
```

From a clone of this repository, `databricks bundle init templates/judge-experiment` works too. It asks for:

| Prompt | Default | Notes |
|---|---|---|
| `project_name` | `judge_experiment` | Names the folder, the bundle and the job |
| `catalog` | the workspace default catalog | Where the eval set and the results go; you need to be able to create a schema in it |
| `schema` | `judge_experiment` | Created if missing; in the `dev` target it gets your user name |
| `judge_model` | `databricks:/databricks-claude-opus-5-5` | `provider:/name`; on Unity Catalog model services, `databricks:/system.ai.<model>` |
| `jury_models` | empty | More judges to measure as a jury, comma-separated |
| `min_failures` | `96` | Known-bad answers needed before any judge is paid for |
| `warehouse` | `Serverless Starter Warehouse` | SQL warehouse MLflow uses to set up and read the Unity Catalog trace tables |

The generated project's README explains each step, what it costs, how to swap in your own answers, and how to read
the report. It runs on a 24-answer sample out of the box.

## Where the design comes from

The jury experiment in this repository (`uv run drill experiment jury`, PR #199) measured judges on the tutor's own
answers. The template packages what the numbers supported:

- **one strong judge**, because both juries did worse than their best member;
- **code checks for rules**, because judges that missed a rule missed it together;
- **the can-it-fail gate and synthetic failures**, because the first eval set held one bad answer in 197;
- **a review queue for a person**, because model labels, the drafting judge's and two AI labellers', passed answers a
  stricter judge showed were wrong.

The course teaches the same ideas in "A jury of judges" and "Check the set can fail" (Evals module).

## Checking a change to the template

```bash
databricks bundle init templates/judge-experiment --config-file <answers.json> --output-dir /tmp/out --profile <profile>
cd /tmp/out/<project_name> && databricks bundle validate --strict --profile <profile>
uv run --with pytest --with pandas pytest tests
```

`tests/test_judge_template.py` in this repository checks the template's files and runs its logic tests in CI.
