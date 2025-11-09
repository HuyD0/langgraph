# Troubleshooting Guide

## Common Errors and Solutions

### Error: ENDPOINT_NOT_FOUND (404)

**Full Error:**
```
NotFoundError: Error code: 404 - {'error_code': 'ENDPOINT_NOT_FOUND', 
'message': 'The given endpoint does not exist, please retry after checking 
the specified model and version deployment exists.'}
```

**What's Happening:**
During model logging/registration, MLflow automatically validates ResponsesAgent models by calling `predict()`. This validation attempts to connect to the LLM endpoint specified in your configuration. If the endpoint doesn't exist or isn't accessible, the deployment fails.

**Solutions:**

#### Option 1: Verify Endpoint Name (Recommended)

1. **List available endpoints in your workspace:**
   ```python
   from databricks.sdk import WorkspaceClient
   
   ws = WorkspaceClient()
   endpoints = ws.serving_endpoints.list()
   
   for ep in endpoints:
       print(f"- {ep.name}")
   ```

2. **Update the endpoint name in `databricks.yml`:**
   ```yaml
   variables:
     llm_endpoint:
       default: YOUR_ACTUAL_ENDPOINT_NAME  # Use the name from step 1
   ```

3. **Common endpoint names:**
   - `databricks-meta-llama-3-1-70b-instruct`
   - `databricks-meta-llama-3-1-405b-instruct`
   - `databricks-dbrx-instruct`
   - Foundation Model API endpoints (check your workspace)

#### Option 2: Use Environment Variable

Set the endpoint name at runtime:

```bash
# In databricks.yml job configuration
env:
  - LLM_ENDPOINT_NAME: "your-endpoint-name"
```

Or in your notebook:
```python
import os
os.environ["LLM_ENDPOINT_NAME"] = "your-endpoint-name"
```

#### Option 3: Check Endpoint Access

Verify you have access to the endpoint:

```python
from databricks.sdk import WorkspaceClient
from databricks_langchain import ChatDatabricks

ws = WorkspaceClient()

# Test endpoint access
try:
    llm = ChatDatabricks(endpoint="databricks-claude-3-7-sonnet")
    response = llm.invoke("Hello")
    print(f"✓ Endpoint is accessible: {response}")
except Exception as e:
    print(f"✗ Endpoint error: {e}")
```

### Error: Authentication Issues

**Symptoms:**
- 401 Unauthorized
- Token validation errors
- "Invalid authentication credentials"

**Solutions:**

1. **Verify Databricks CLI profile:**
   ```bash
   databricks auth profiles
   databricks auth env --profile development
   ```

2. **Check token validity:**
   ```bash
   databricks clusters list --profile development
   ```

3. **Regenerate token if expired:**
   - Go to Databricks Workspace → User Settings → Access Tokens
   - Generate new token
   - Update `~/.databrickscfg`

### Error: Module Import Failures

**Symptoms:**
- `ModuleNotFoundError: No module named 'langgraph_agent'`
- Import errors during job execution

**Solutions:**

1. **Rebuild and redeploy:**
   ```bash
   make clean
   make build
   databricks bundle deploy -t dev
   ```

2. **Verify wheel contains all files:**
   ```bash
   unzip -l dist/langgraph_mcp_agent-0.1.0-py3-none-any.whl
   ```

3. **Check pyproject.toml includes necessary files:**
   ```toml
   [tool.hatch.build.targets.wheel]
   packages = ["src/langgraph_agent"]
   include = ["src/langgraph_agent/**/*.yaml"]
   ```

### Error: MCP Tool Connection Issues

**Symptoms:**
- "Failed to connect to MCP server"
- Tool execution timeouts
- Empty tool list

**Solutions:**

1. **Verify MCP server URLs:**
   ```python
   from databricks.sdk import WorkspaceClient
   
   ws = WorkspaceClient()
   host = ws.config.host
   mcp_url = f"{host}/api/2.0/mcp/functions/system/ai"
   print(f"MCP URL: {mcp_url}")
   ```

2. **Test MCP server accessibility:**
   ```python
   import asyncio
   from langgraph_agent.core.mcp_client import create_mcp_tools
   
   tools = asyncio.run(create_mcp_tools(
       ws=ws,
       managed_server_urls=[mcp_url],
       custom_server_urls=[]
   ))
   print(f"Found {len(tools)} tools")
   ```

## Debug Mode

Enable debug logging to get more information:

```bash
export LOG_LEVEL=DEBUG
python scripts/test_agent.py
```

Or in your code:
```python
import os
os.environ["LOG_LEVEL"] = "DEBUG"

from langgraph_agent.utils.logging import get_logger
logger = get_logger(__name__)
```

## Getting Help

If you're still experiencing issues:

1. **Check logs:**
   - Job run output in Databricks UI
   - MLflow run logs
   - Application logs (if file logging enabled)

2. **Verify configuration:**
   ```bash
   cat databricks.yml
   cat configs/.env.example
   ```

3. **Test locally first:**
   ```bash
   python scripts/test_agent.py
   ```

4. **Common configuration files:**
   - `databricks.yml` - Infrastructure and deployment config
   - `src/langgraph_agent/models/model_config.py` - Default endpoint name
   - `configs/.env.example` - Environment variable examples

## Quick Fixes Checklist

- [ ] Endpoint name is correct in `databricks.yml`
- [ ] Endpoint exists in your Databricks workspace
- [ ] You have access to the endpoint (test with ChatDatabricks)
- [ ] Databricks CLI is authenticated (`databricks auth profiles`)
- [ ] Package is rebuilt after code changes (`make build`)
- [ ] Bundle is deployed (`databricks bundle deploy -t dev`)
- [ ] Job is using the correct wheel version
- [ ] Environment variables are set correctly in job configuration
