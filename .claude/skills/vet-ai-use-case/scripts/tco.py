"""Total cost of ownership for an AI use case, from a JSON file of inputs (see reference/cost-inputs.md).

Usage: python scripts/tco.py inputs.json   (or pipe the JSON in on stdin)
Prints a markdown table of every line over the system's life, the monthly run cost and the
biggest item. Only the Python standard library is used.
"""

from __future__ import annotations

import json
import sys


def lines(inputs: dict) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    """(monthly lines, one-off lines) in dollars."""
    g = lambda section, key: float((inputs.get(section) or {}).get(key) or 0)
    llm_answers = g("llm", "ptu_usd_per_month") or g("llm", "questions_per_month") * (
        g("llm", "input_tokens") * g("llm", "usd_per_m_input") + g("llm", "output_tokens") * g("llm", "usd_per_m_output")) / 1e6
    monthly = [
        ("LLM: answers", llm_answers),
        ("LLM: embeddings", g("llm", "embedding_tokens_per_month") * g("llm", "usd_per_m_embedding") / 1e6),
        ("Azure AI Search", g("retrieval", "ai_search_units") * g("retrieval", "usd_per_search_unit_month")),
        ("Databricks Vector Search", g("retrieval", "vector_search_hours") * g("retrieval", "usd_per_vector_search_hour")),
        ("Databricks jobs: chunk and embed", g("databricks", "job_dbus_per_hour") * g("databricks", "job_hours_per_month") * g("databricks", "usd_per_dbu")),
        ("Databricks serving", g("databricks", "serving_dbus_per_hour") * g("databricks", "serving_hours_per_month") * g("databricks", "usd_per_dbu")),
        ("Storage", g("storage", "gb") * g("storage", "usd_per_gb_month")),
    ] + [(name, float(v or 0)) for name, v in (inputs.get("people_monthly") or {}).items()]
    one_off = [(name, float(v or 0)) for name, v in (inputs.get("one_off") or {}).items()]
    return monthly, one_off


def tco(inputs: dict) -> dict:
    years = max(1, int(inputs.get("years") or 2))
    months = 12 * years
    monthly, one_off = lines(inputs)
    life = [(n, v) for n, v in one_off] + [(n, v * months) for n, v in monthly]
    life = [(n, round(v)) for n, v in life if v > 0]
    life.sort(key=lambda row: row[1], reverse=True)
    return {"years": years, "per_month": round(sum(v for _, v in monthly)), "total": sum(v for _, v in life),
            "biggest": life[0][0] if life else None, "lines": life}


def report(result: dict) -> str:
    rows = "\n".join(f"| {name} | ${value:,} |" for name, value in result["lines"])
    return (f"| Item | Over {result['years']} years |\n|---|---|\n{rows}\n\n"
            f"**Total: ${result['total']:,}**, of which ${result['per_month']:,} a month to run. "
            f"Biggest item: {result['biggest'] or 'none'}.")


if __name__ == "__main__":
    raw = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    print(report(tco(json.loads(raw))))
