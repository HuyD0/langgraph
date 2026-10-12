# Cost inputs for scripts/tco.py

Ask for what is known; anything missing counts as 0 and is listed as an Unknown. No prices are
assumed: take them from the Azure pricing calculator, the model's price page, Azure AI Search
and Azure Databricks pricing for the person's region and tier.

```json
{
  "years": 2,
  "llm": {"questions_per_month": 20000, "input_tokens": 3000, "output_tokens": 400,
          "usd_per_m_input": 2, "usd_per_m_output": 8,
          "embedding_tokens_per_month": 5000000, "usd_per_m_embedding": 0.1,
          "ptu_usd_per_month": 0},
  "retrieval": {"ai_search_units": 2, "usd_per_search_unit_month": 250,
                "vector_search_hours": 0, "usd_per_vector_search_hour": 0},
  "databricks": {"usd_per_dbu": 0.4, "job_dbus_per_hour": 4, "job_hours_per_month": 20,
                 "serving_dbus_per_hour": 0, "serving_hours_per_month": 0},
  "storage": {"gb": 200, "usd_per_gb_month": 0.02},
  "people_monthly": {"checking answers": 3000, "on call and upkeep": 500},
  "one_off": {"build": 40000, "eval set": 8000, "first indexing": 500}
}
```

If `ptu_usd_per_month` is above 0, it replaces the per-token answer cost (provisioned throughput).
