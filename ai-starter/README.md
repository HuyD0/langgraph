# ai-starter

LangGraph agent template wired for **Azure OpenAI** (keyless via `az login`) or **Databricks Model Serving**,
with MLflow tracing.

```bash
cp .env.example .env     # fill in your endpoint/deployment
uv sync                  # creates .venv with Python 3.12
uv run langgraph dev     # LangGraph Studio at http://localhost:2024
uv run python -m ai_starter.agent   # one-shot run from the terminal
```

Switch providers with `LLM_PROVIDER=azure|databricks` in `.env`. The `.env` here is set to Databricks
with `databricks-claude-sonnet-5-5`; list other endpoints with `databricks serving-endpoints list`.

Traces go to a local MLflow database. View them with:

```bash
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Sending traces to Databricks currently fails with a 403 from the workspace's Azure storage account,
which usually means its firewall blocks your network. Ask the workspace admin to allow it, then switch
the MLflow lines in `.env`.

## Databricks notes
- `databricks auth login --host https://<ws>.azuredatabricks.net` stores an OAuth profile in `~/.databrickscfg`; the SDK and `databricks-langchain` pick it up automatically.
- To run code against a cluster from VS Code add `databricks-connect` **pinned to your runtime** (e.g. `uv add "databricks-connect==16.4.*"`). It is not in the default deps because the version must match the cluster.
- Deploy this agent to Model Serving with `mlflow.langchain.log_model` + Agent Framework, or as a Databricks Asset Bundle (`databricks bundle init`).

## Azure notes
- Give your user the **Cognitive Services OpenAI User** role on the Azure OpenAI resource so keyless auth works.
- `azd` can scaffold hosting (Container Apps / Functions): `azd init -t azure-search-openai-demo` etc.
