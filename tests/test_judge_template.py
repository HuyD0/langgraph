"""The judge-experiment bundle template (templates/judge-experiment): its prompts, its sample and its logic.

Rendering the template needs the Databricks CLI, so CI checks what it can without it: the schema is valid, every
templated name it uses is a prompt, the sample loads, and the generated project's own logic tests pass.
"""

from __future__ import annotations

import csv
import importlib.util
import inspect
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "templates" / "judge-experiment"
PROJECT = ROOT / "template" / "{{.project_name}}"


def test_schema_prompts_are_valid_and_used_names_are_prompts():
    schema = json.loads((ROOT / "databricks_template_schema.json").read_text(encoding="utf-8"))
    props = schema["properties"]
    assert {"project_name", "catalog", "schema", "judge_model", "jury_models", "min_failures"} <= set(props)
    for name, p in props.items():
        if "pattern" in p and p.get("default"):
            assert re.fullmatch(p["pattern"], p["default"]), f"{name}'s default doesn't match its own pattern"
    used = set()
    for f in PROJECT.rglob("*.tmpl"):
        used |= set(re.findall(r"\{\{\s*\.(\w+)\s*\}\}", f.read_text(encoding="utf-8")))
    used |= set(re.findall(r"\{\{\s*\.(\w+)\s*\}\}", str(PROJECT)))
    assert used <= set(props), f"templated names with no prompt: {used - set(props)}"


def test_sample_eval_set_has_the_documented_columns_and_numbers():
    with (PROJECT / "fixtures" / "sample_eval_set.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows and set(rows[0]) == {"id", "group", "context", "question", "answer", "expected_pass"}
    assert len({r["id"] for r in rows}) == len(rows)
    assert all(re.search(r"\d", r["answer"]) for r in rows), "every sample answer needs a number, for the wrong_number plant"


def test_generated_projects_logic_tests_pass():
    sys.path.insert(0, str(PROJECT / "src"))
    try:
        spec = importlib.util.spec_from_file_location("judge_template_tests", PROJECT / "tests" / "test_judge_core.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        tests = [getattr(mod, n) for n in dir(mod) if n.startswith("test_")]
        assert len(tests) >= 7
        for t in tests:
            if "monkeypatch" in inspect.signature(t).parameters:
                with pytest.MonkeyPatch.context() as mp:
                    t(mp)
            else:
                t()
    finally:
        sys.path.remove(str(PROJECT / "src"))
        for name in ("judge_core", "tables", "review"):
            sys.modules.pop(name, None)
