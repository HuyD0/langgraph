# Agent Application Files

This directory contains the agent application files:

- `app.py` - Agent code with `create_agent()` function and module-level initialization
- `mlflow.yaml` - ML Application metadata (kept for reference)

These files are included in the Python wheel so they're available when the package is installed on Databricks.

## How it works

The agent uses **code-based logging** with `app.py`:

1. `app.py` contains:
   - `create_agent()` function - Factory function for creating agents
   - Module-level initialization - `AGENT = create_agent()` and `mlflow.models.set_model(AGENT)`

2. When `langgraph-agent register` is called:
   - The code finds `app.py` in the package directory
   - MLflow logs it as a code-based model
   - The agent is registered to Unity Catalog

3. When deployed:
   - Databricks loads `app.py`  
   - The module-level code executes, initializing `AGENT`
   - MLflow serves the agent via the Responses API

## Configuration

The agent can be configured via environment variables:

```bash
export LLM_ENDPOINT_NAME="your-endpoint-name"
export SYSTEM_PROMPT="Your custom prompt"
```

## Local Development

```bash
# Register the model (uses package location automatically)
langgraph-agent register

# Deploy
langgraph-agent deploy
```

The code automatically detects the package location and uses `app.py`.
