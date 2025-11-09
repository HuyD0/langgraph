# Getting Started with LangGraph MCP Agent

This guide will walk you through setting up and using the LangGraph MCP Agent project.

## Prerequisites

- Python 3.10 or later
- Databricks workspace access
- Git (for cloning the repository)

## Step 1: Clone and Install

```bash
# Navigate to the project directory
cd lg-demo

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in development mode
pip install -e ".[dev]"
```

## Step 2: Configure Authentication

### Option A: OAuth (Recommended for Local Development)

```bash
# Install Databricks CLI if not already installed
pip install databricks-cli

# Authenticate using OAuth
databricks auth login --host https://your-workspace.cloud.databricks.com --profile development
```

### Option B: Service Principal (For CI/CD)

Create a `.env` file:

```bash
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_CLIENT_ID=your-service-principal-client-id
DATABRICKS_CLIENT_SECRET=your-service-principal-secret
```

### Verify Authentication

```bash
langgraph-agent auth-test
```

## Step 3: Configure the Agent

Copy the example configuration:

```bash
cp configs/.env.example .env
```

Edit `.env` and update the following:

```bash
# Your Databricks profile name
DATABRICKS_PROFILE=development

# Your LLM endpoint name
MODEL_ENDPOINT_NAME=databricks-claude-3-7-sonnet

# Your MLflow experiment (use your email)
MLFLOW_EXPERIMENT_NAME=/Users/your.email@company.com/langgraph-mcp-agent

# Unity Catalog model path
UC_CATALOG=rag
UC_SCHEMA=development
UC_MODEL_NAME=langgraph_mcp_agent
```

### View Current Configuration

```bash
langgraph-agent config-show
```

## Step 4: Test the Agent Locally

### Quick Test

```bash
# Run the test script
python scripts/test_agent.py
```

### Using the CLI

```bash
# Serve the agent locally
langgraph-agent serve
```

### Using Python

```python
from langgraph_agent import get_config, initialize_agent
from langgraph_agent.utils import get_workspace_client

# Load config
config = get_config()

# Initialize agent
ws = get_workspace_client(config.databricks.profile)
agent = initialize_agent(
    workspace_client=ws,
    llm_endpoint_name=config.model.endpoint_name,
    system_prompt=config.model.system_prompt,
    managed_mcp_urls=[f"{ws.config.host}/api/2.0/mcp/functions/system/ai"],
)

# Test
response = agent.predict({
    "input": [{"role": "user", "content": "What is 7*6?"}]
})
print(response)
```

### Using Jupyter Notebook

```bash
# Start Jupyter
jupyter notebook

# Open notebooks/quickstart.ipynb
```

## Step 5: Evaluate the Agent

### Using Default Dataset

```bash
langgraph-agent evaluate
```

### Using Custom Dataset

Create your evaluation dataset in `data/my_eval.json`:

```json
[
  {
    "inputs": {
      "input": [
        {"role": "user", "content": "Your test question"}
      ]
    },
    "expected_response": "Expected answer"
  }
]
```

Run evaluation:

```bash
langgraph-agent evaluate --dataset data/my_eval.json
```

## Step 6: Deploy to Databricks

### Full Deployment Pipeline

This will log the model, validate it, register to Unity Catalog, and deploy to a serving endpoint:

```bash
langgraph-agent deploy
```

### Step-by-Step Deployment

If you want more control:

```bash
# Step 1: Register to Unity Catalog (without deployment)
langgraph-agent register

# Step 2: Manually deploy from Databricks UI or use the API
```

### Verify Deployment

After deployment:
1. Go to Databricks workspace
2. Navigate to "Serving" → "Endpoints"
3. Find your endpoint (named after your UC model)
4. Test in AI Playground

## Step 7: Monitor and Iterate

### Check MLflow Experiments

1. Go to Databricks workspace
2. Navigate to "Machine Learning" → "Experiments"
3. Find your experiment (from `MLFLOW_EXPERIMENT_NAME`)
4. Review runs, metrics, and artifacts

### Monitor Serving Endpoint

1. Navigate to "Serving" → "Endpoints"
2. Click on your endpoint
3. Monitor:
   - Request/response logs
   - Performance metrics
   - Error rates
   - Traces

### Update and Redeploy

After making changes:

```bash
# Test locally
python scripts/test_agent.py

# Run evaluation
langgraph-agent evaluate

# Deploy new version
langgraph-agent deploy
```

## Common Workflows

### Development Workflow

```bash
# 1. Make code changes
vim src/langgraph_agent/core/agent.py

# 2. Test locally
python scripts/test_agent.py

# 3. Run tests
make test

# 4. Format code
make format

# 5. Evaluate
langgraph-agent evaluate

# 6. Deploy
langgraph-agent deploy
```

### Using Makefile Commands

```bash
make help          # Show all commands
make install       # Install dependencies
make test          # Run tests
make format        # Format code
make lint          # Check code quality
make deploy        # Deploy to Databricks
make serve         # Serve locally
```

## Configuring MCP Servers

### Managed MCP Servers

Default configuration (no setup needed):

```bash
# In .env
MCP_MANAGED_URLS=https://your-workspace.com/api/2.0/mcp/functions/system/ai
```

### External MCP Servers (Proxied)

1. Create a UC connection in Databricks
2. Flag it as an MCP connection
3. Use the proxy endpoint:

```bash
# In .env
MCP_MANAGED_URLS=https://workspace.com/api/2.0/mcp/external/my_connection
```

### Custom MCP Servers (Databricks Apps)

1. Deploy your MCP server as a Databricks App
2. Configure OAuth for the app
3. Add the app URL:

```bash
# In .env
MCP_CUSTOM_URLS=https://custom-mcp-app.com/mcp
```

## Troubleshooting

### Authentication Fails

```bash
# Re-authenticate
databricks auth login --host <workspace-url> --profile development

# Verify
langgraph-agent auth-test
```

### Import Errors

```bash
# Reinstall in editable mode
pip install -e .
```

### Azure Module Errors

```bash
# Install Azure dependencies
pip install azure-identity azure-storage-blob azure-core
```

### MLflow Tracking Errors

Check your configuration:

```bash
langgraph-agent config-show
```

Ensure `MLFLOW_EXPERIMENT_NAME` is set and you have permissions.

## Next Steps

1. **Customize the Agent**
   - Update `MODEL_SYSTEM_PROMPT` in `.env`
   - Add custom MCP servers
   - Modify agent logic in `src/langgraph_agent/core/agent.py`

2. **Create Better Evaluation Datasets**
   - Add more test cases in `data/`
   - Create domain-specific evaluations
   - Use custom metrics

3. **Integrate with Your Workflow**
   - Set up CI/CD for automated deployments
   - Add monitoring and alerting
   - Create custom dashboards

4. **Scale and Optimize**
   - Tune model parameters
   - Optimize MCP tool calls
   - Implement caching strategies

## Additional Resources

- [Project README](./PROJECT_README.md) - Complete project documentation
- [Authentication Guide](./AUTHENTICATION.md) - Detailed authentication setup
- [Databricks Agents Docs](https://docs.databricks.com/en/generative-ai/agent-framework/index.html)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

## Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Review logs in the terminal
3. Check Databricks job/serving logs
4. Consult the documentation
5. Open an issue in the project repository
