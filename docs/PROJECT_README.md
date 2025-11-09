# LangGraph MCP Agent - AI/MLOps Project

A production-ready LangGraph agent with Model Context Protocol (MCP) integration, built for Databricks with complete MLOps tooling, **Databricks Asset Bundles (DAB)** support, and **Serverless Compute**.

## ✨ Key Features

- 🚀 **Serverless Compute**: 10-30 second job startup, automatic scaling
- 💰 **Cost Optimized**: ~30% savings through efficient serverless execution
- 🏗️ **Infrastructure as Code**: Complete DAB configuration
- 🤖 **LangGraph Agent**: MCP tool integration
- 📊 **MLflow Tracking**: Experiment tracking and model versioning
- 🗄️ **Unity Catalog**: Model registry integration
- 🔧 **CLI Tool**: Complete command-line interface
- 📈 **Evaluation Pipeline**: Automated testing and validation

## 🏗️ Project Structure

```
.
├── src/langgraph_agent/          # Main package
│   ├── core/                      # Core agent components
│   │   ├── agent.py              # LangGraph agent implementation
│   │   ├── tools.py              # MCP tool wrappers
│   │   ├── mcp_client.py         # MCP server client utilities
│   │   └── state.py              # Agent state definitions
│   ├── utils/                     # Utility modules
│   │   ├── auth.py               # Databricks authentication
│   │   └── mlflow_setup.py       # MLflow configuration
│   ├── config.py                  # Configuration management
│   ├── cli.py                     # Command-line interface
│   ├── evaluate.py                # Evaluation pipeline
│   └── deploy.py                  # Deployment automation
├── configs/                       # Configuration files
│   └── .env.example              # Environment variables template
├── resources/                     # Databricks Asset Bundle resources
│   ├── agent_jobs.yml            # Job definitions
│   ├── agent_serving.py          # Serving endpoints
│   ├── experiments.py            # MLflow experiments
│   └── jobs.py                   # Additional jobs
├── databricks.yml                # Main DAB configuration
├── data/                          # Datasets
│   └── eval_dataset.json         # Evaluation examples
├── notebooks/                     # Jupyter notebooks
├── scripts/                       # Utility scripts
│   ├── test_agent.py             # Quick agent test
│   └── deploy.sh                 # Deployment script
├── tests/                         # Test suite
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
├── deployments/                   # Deployment artifacts
├── pyproject.toml                # Python project configuration
└── Makefile                      # Common commands
```

## 🚀 Quick Start

### Method 1: Databricks Asset Bundles with Serverless (Recommended)

The **recommended** way to deploy using infrastructure as code with serverless compute:

```bash
# Validate configuration
databricks bundle validate

# Deploy to dev (serverless startup in ~30 seconds)
databricks bundle deploy -t dev

# Run deployment job on serverless compute
databricks bundle run agent_deployment -t dev
# 1. Setup
make install
databricks auth login --profile development

# 2. Validate and deploy
databricks bundle validate
databricks bundle deploy -t dev

# 3. Run deployment pipeline
databricks bundle run agent_deployment -t dev
```

📖 **See [QUICKSTART_DAB.md](./QUICKSTART_DAB.md) for complete DAB guide**

### Method 2: CLI (For Local Development)

Traditional CLI approach for local development:

### 1. Installation

```bash
# Clone the repository
git clone <your-repo>
cd lg-demo

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 2. Authentication Setup

Configure Databricks authentication using OAuth (recommended for local development):

```bash
# Install Databricks CLI
pip install databricks-cli

# Login using OAuth
databricks auth login --host https://your-workspace.cloud.databricks.com --profile development
```

For more authentication options, see [AUTHENTICATION.md](./AUTHENTICATION.md).

### 3. Configuration

Copy the example configuration and customize:

```bash
cp configs/.env.example .env
# Edit .env with your settings
```

Key configurations:
- `DATABRICKS_PROFILE`: CLI profile name (e.g., "development")
- `MODEL_ENDPOINT_NAME`: LLM serving endpoint
- `UC_CATALOG`, `UC_SCHEMA`, `UC_MODEL_NAME`: Unity Catalog model path
- `MLFLOW_EXPERIMENT_NAME`: MLflow experiment for tracking

### 4. Test the Agent

```bash
# Test authentication
langgraph-agent auth-test

# Run a quick test
python scripts/test_agent.py

# Or use the CLI
langgraph-agent serve
```

## 📋 CLI Commands

### Databricks Asset Bundle Commands

```bash
# Validate bundle
databricks bundle validate
make bundle-validate

# Deploy to environments
databricks bundle deploy -t dev      # Development
databricks bundle deploy -t prod     # Production
make bundle-deploy-dev
make bundle-deploy-prod

# Run jobs
databricks bundle run agent_deployment -t dev
databricks bundle run agent_evaluation -t dev
make bundle-run-deploy
make bundle-run-eval

# Destroy resources
databricks bundle destroy -t dev
make bundle-destroy-dev
```

### Legacy CLI (Local Development)

### Configuration
```bash
# Show current configuration
langgraph-agent config-show
```

### Testing & Development
```bash
# Test authentication
langgraph-agent auth-test --profile development

# Serve agent locally
langgraph-agent serve --host 0.0.0.0 --port 8000
```

### Evaluation
```bash
# Evaluate with default dataset
langgraph-agent evaluate

# Evaluate with custom dataset
langgraph-agent evaluate --dataset data/eval_dataset.json
```

### Deployment
```bash
# Full deployment pipeline (log, register, deploy)
langgraph-agent deploy

# Just register to Unity Catalog
langgraph-agent register

# Deploy without validation
langgraph-agent deploy --no-validate
```

## 🔧 Development Workflow

### 1. Local Development

```python
from langgraph_agent import get_config, initialize_agent
from langgraph_agent.utils import get_workspace_client

# Load configuration
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

### 2. Evaluation

Create evaluation datasets in `data/`:

```json
[
  {
    "inputs": {
      "input": [{"role": "user", "content": "Your test question"}]
    },
    "expected_response": "Expected answer"
  }
]
```

Run evaluation:

```bash
langgraph-agent evaluate --dataset data/eval_dataset.json
```

### 3. Deployment

Full deployment pipeline:

```bash
# This will:
# 1. Log model to MLflow
# 2. Validate the model
# 3. Register to Unity Catalog
# 4. Deploy to serving endpoint
langgraph-agent deploy
```

Or step-by-step:

```python
from langgraph_agent.config import get_config
from langgraph_agent.deploy import (
    log_and_register_model,
    deploy_to_serving_endpoint
)

config = get_config()

# Step 1: Log and register
logged_info, uc_info = log_and_register_model(config)

# Step 2: Deploy
deployment_info = deploy_to_serving_endpoint(
    config,
    model_version=uc_info.version
)
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_config.py

# Run with coverage
pytest --cov=langgraph_agent tests/
```

## 📊 MCP Server Configuration

The agent supports three types of MCP servers:

### 1. Managed MCP Servers
Fully managed by Databricks (no setup required):

```python
managed_urls = [
    f"{workspace_host}/api/2.0/mcp/functions/system/ai"
]
```

### 2. External MCP Servers (Proxied)
External servers proxied through Databricks:

```python
managed_urls = [
    f"{workspace_host}/api/2.0/mcp/external/{connection_name}"
]
```

### 3. Custom MCP Servers
MCP servers hosted as Databricks Apps:

```python
custom_urls = [
    "https://custom-mcp-app-url/mcp"
]
```

Configure in `.env`:
```bash
MCP_MANAGED_URLS=https://workspace.com/api/2.0/mcp/functions/system/ai
MCP_CUSTOM_URLS=https://custom-app.com/mcp
```

## 📁 Key Modules

### Configuration (`config.py`)
Centralized configuration using Pydantic Settings:
- Model configuration (endpoint, system prompt)
- MCP server URLs
- Databricks authentication
- MLflow tracking
- Unity Catalog model registry
- Deployment settings

### Core Agent (`core/agent.py`)
LangGraph agent implementation with:
- Tool-calling workflow
- ResponsesAgent wrapper for Mosaic AI
- Streaming support
- Custom state management

### Deployment (`deploy.py`)
Automated deployment pipeline:
- MLflow model logging
- Model validation
- Unity Catalog registration
- Serving endpoint deployment

### Evaluation (`evaluate.py`)
Evaluation framework with:
- Dataset loading
- MLflow GenAI evaluation
- Custom metrics support

## 🔐 Security Best Practices

1. **Never commit credentials**: Use `.env` (gitignored) for secrets
2. **Use OAuth authentication**: Recommended for local development
3. **Service principals for CI/CD**: Use M2M OAuth for automation
4. **Rotate credentials regularly**: Update service principal secrets
5. **Principle of least privilege**: Grant minimal required permissions

## 📝 Environment Variables

Complete list of supported environment variables:

```bash
# Databricks
DATABRICKS_PROFILE=development
DATABRICKS_HOST=https://workspace.cloud.databricks.com

# Model
MODEL_ENDPOINT_NAME=databricks-claude-3-7-sonnet
MODEL_SYSTEM_PROMPT=You are a helpful assistant

# MCP Servers
MCP_MANAGED_URLS=url1,url2
MCP_CUSTOM_URLS=url1,url2

# MLflow
MLFLOW_EXPERIMENT_NAME=/Users/user@example.com/experiment
MLFLOW_ENABLE_AUTOLOG=true

# Unity Catalog
UC_CATALOG=rag
UC_SCHEMA=development
UC_MODEL_NAME=langgraph_mcp_agent

# Deployment
DEPLOYMENT_SCALE_TO_ZERO_ENABLED=true
```

## 🛠️ Troubleshooting

### Authentication Issues
```bash
# Verify authentication
langgraph-agent auth-test

# Re-authenticate
databricks auth login --host <workspace-url> --profile development
```

### Module Import Errors
```bash
# Reinstall in editable mode
pip install -e .
```

### Azure Module Errors (Unity Catalog)
```bash
# Install Azure dependencies
pip install azure-identity azure-storage-blob azure-core
```

## 📚 Additional Resources

- [AUTHENTICATION.md](./AUTHENTICATION.md) - Complete authentication guide
- [Databricks Agents Documentation](https://docs.databricks.com/en/generative-ai/agent-framework/index.html)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [MCP Documentation](https://modelcontextprotocol.io/)

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Add tests
4. Run the test suite
5. Submit a pull request

## 📄 License

[Your License Here]

## 👥 Authors

- huy.d@hotmail.com

---

**Next Steps After Setup:**
1. Configure your MCP servers
2. Test the agent locally
3. Create evaluation datasets
4. Run evaluations
5. Deploy to Databricks
6. Monitor in AI Playground
