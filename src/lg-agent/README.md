# LangGraph MCP Tool-Calling Agent

A flexible, tool-using agent that integrates Databricks MCP (Model Context Protocol) servers with the Mosaic AI Agent Framework using LangGraph.

## Overview

This agent demonstrates how to:
- Connect to Databricks-managed MCP servers or custom MCP servers hosted as Databricks Apps
- Automatically discover and use tools from MCP servers
- Build a LangGraph agent workflow with tool-calling capabilities
- Wrap the agent with `ResponsesAgent` for Mosaic AI compatibility
- Evaluate, log, and deploy agents using MLflow

## Architecture

The agent consists of the following components:

1. **MCP Tool Wrappers** (`MCPTool`): Custom LangChain tools that wrap MCP server functionality
2. **Tool Discovery**: Automatic discovery and registration of tools from MCP servers
3. **LangGraph Agent Logic**: State machine workflow that handles conversation flow and tool execution
4. **ResponsesAgent Wrapper**: Makes the agent compatible with Mosaic AI Responses API
5. **MLflow Integration**: Automatic tracing, logging, and deployment capabilities

## Project Structure

```
src/langgraph_mcp_agent/
├── agent.py              # Core agent implementation
├── config.py            # Configuration (LLM endpoint, MCP servers, OAuth)
├── test_agent.ipynb     # Interactive testing notebook
└── README.md            # This file
```

## Prerequisites

- Databricks workspace with access to:
  - Model serving endpoints (e.g., Claude 3.7 Sonnet)
  - MCP servers (managed or custom)
  - Unity Catalog (for model registration)
- Python 3.10-3.13
- Required packages (see `pyproject.toml`)

## Quick Start

### 1. Install Dependencies

```bash
pip install -e .
```

Or in a Databricks notebook:
```python
%pip install -U -qqqq langgraph databricks-agents mlflow-skinny[databricks] databricks-mcp databricks-langchain
dbutils.library.restartPython()
```

### 2. Configure the Agent

Edit `config.py` to customize:

```python
# Update your LLM endpoint
LLM_ENDPOINT_NAME = "databricks-claude-3-7-sonnet"

# Update your system prompt
SYSTEM_PROMPT = "You are a helpful assistant that can run Python code."

# Configure MCP servers
MANAGED_MCP_SERVER_URLS = [
    f"{host}/api/2.0/mcp/functions/system/ai",  # Default managed MCP
]
```

### 3. Test the Agent

Use the interactive notebook `test_agent.ipynb` or test programmatically:

```python
from agent import AGENT

# Single prediction
response = AGENT.predict({
    "input": [
        {"role": "user", "content": "What is 7*6 in Python?"}
    ]
})

# Streaming prediction
for chunk in AGENT.predict_stream({
    "input": [
        {"role": "user", "content": "Calculate the 15th Fibonacci number"}
    ]
}):
    print(chunk)
```

## MCP Server Configuration

### Managed MCP Servers (Simplest)

Databricks manages these connections automatically using your workspace settings and PAT authentication:

```python
MANAGED_MCP_SERVER_URLS = [
    f"{host}/api/2.0/mcp/functions/system/ai",
]
```

### External MCP Servers (via Proxy)

For external MCP servers:
1. Create a UC connection
2. Flag it as an MCP connection
3. Add the proxy endpoint URL:

```python
MANAGED_MCP_SERVER_URLS = [
    "https://<workspace-hostname>/api/2.0/mcp/external/{connection_name}"
]
```

### Custom MCP Servers (Databricks Apps)

For custom MCP servers hosted as Databricks Apps, you need OAuth configuration:

```python
import os
from databricks.sdk import WorkspaceClient

workspace_client = WorkspaceClient(
    host="<DATABRICKS_WORKSPACE_URL>",
    client_id=os.getenv("DATABRICKS_CLIENT_ID"),
    client_secret=os.getenv("DATABRICKS_CLIENT_SECRET"),
    auth_type="oauth-m2m",
)

CUSTOM_MCP_SERVER_URLS = [
    "https://<custom-mcp-app-url>/mcp"
]
```

## Evaluation

Evaluate your agent using MLflow's built-in scorers:

```python
import mlflow
from mlflow.genai.scorers import RelevanceToQuery, Safety

eval_dataset = [
    {
        "inputs": {
            "input": [{"role": "user", "content": "Calculate the 15th Fibonacci number"}]
        },
        "expected_response": "The 15th Fibonacci number is 610."
    }
]

eval_results = mlflow.genai.evaluate(
    data=eval_dataset,
    predict_fn=lambda input: AGENT.predict({"input": input}),
    scorers=[RelevanceToQuery(), Safety()],
)
```

## Deployment

### 1. Log the Agent

```python
import mlflow
from mlflow.models.resources import DatabricksServingEndpoint, DatabricksFunction

resources = [
    DatabricksServingEndpoint(endpoint_name=LLM_ENDPOINT_NAME),
    DatabricksFunction(function_name="system.ai.python_exec")
]

with mlflow.start_run():
    logged_agent_info = mlflow.pyfunc.log_model(
        name="agent",
        python_model="agent.py",
        resources=resources,
        pip_requirements=[
            "databricks-mcp",
            "langgraph",
            "mcp",
            "databricks-langchain",
        ]
    )
```

### 2. Register to Unity Catalog

```python
mlflow.set_registry_uri("databricks-uc")

UC_MODEL_NAME = "main.default.langgraph_mcp_agent"
uc_registered_model_info = mlflow.register_model(
    model_uri=logged_agent_info.model_uri,
    name=UC_MODEL_NAME
)
```

### 3. Deploy to Endpoint

```python
from databricks import agents

agents.deploy(
    UC_MODEL_NAME,
    uc_registered_model_info.version,
    tags={"endpointSource": "langgraph_mcp"}
)
```

## Features

- **Automatic Tool Discovery**: The agent automatically discovers available tools from MCP servers
- **Multi-Step Reasoning**: Uses LangGraph to handle complex multi-turn conversations with tool calls
- **Streaming Support**: Supports both batch and streaming predictions
- **MLflow Integration**: Automatic tracing for debugging and monitoring
- **Mosaic AI Compatible**: Works seamlessly with AI Playground and Agent Evaluation
- **Flexible Configuration**: Easy to switch between managed and custom MCP servers

## Tracing

MLflow autologging is enabled by default. View traces in the MLflow UI to see:
- Each step the agent takes
- Tool calls and their results
- Model inputs and outputs
- Execution time and errors

## Troubleshooting

### Import Errors
Make sure all dependencies are installed:
```bash
pip install -e .
```

### Authentication Issues
- For managed MCP: Ensure you have valid Databricks PAT
- For custom MCP: Verify OAuth credentials are set correctly

### Tool Discovery Fails
Check that MCP server URLs are correct and accessible from your workspace.

## Learn More

- [Databricks MCP Documentation](https://docs.databricks.com/en/generative-ai/mcp/)
- [Mosaic AI Agent Framework](https://docs.databricks.com/en/generative-ai/agent-framework/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [MLflow Model Serving](https://docs.databricks.com/en/machine-learning/model-serving/)

## License

This project follows the same license as your Databricks workspace.
