# LangGraph MCP Agent Documentation

## Quick Start
- [START_HERE.md](START_HERE.md) - **Start here!** Quick overview of what the project is
- [GETTING_STARTED.md](GETTING_STARTED.md) - Step-by-step setup guide

## Core Documentation
- [PROJECT_README.md](PROJECT_README.md) - Complete project reference and API docs
- [AUTHENTICATION.md](AUTHENTICATION.md) - Authentication setup guide
- [PROMPT_REGISTRY.md](PROMPT_REGISTRY.md) - **NEW:** MLflow Prompt Registry integration

## Databricks Asset Bundles
- [QUICKSTART_DAB.md](QUICKSTART_DAB.md) - Quick start for DAB deployment
- [DATABRICKS_BUNDLES.md](DATABRICKS_BUNDLES.md) - Complete DAB guide (400+ lines)
- [DAB_INTEGRATION.md](DAB_INTEGRATION.md) - DAB integration summary

## Technical Guides
- [SERVERLESS_UPDATE_SUMMARY.md](SERVERLESS_UPDATE_SUMMARY.md) - **Latest:** Serverless compute update
- [SERVERLESS_MIGRATION.md](SERVERLESS_MIGRATION.md) - Serverless migration guide  
- [TRANSFORMATION_SUMMARY.md](TRANSFORMATION_SUMMARY.md) - Project transformation details

## Project Structure

```
lg-demo/
├── README.md                      # Main project README
├── docs/                          # All documentation (you are here)
├── src/langgraph_agent/          # Main package
│   ├── models/                   # Pydantic models and configs
│   │   ├── agent_config.py      # Main configuration
│   │   ├── agent_state.py       # Agent state definitions
│   │   ├── databricks_config.py # Databricks settings
│   │   ├── deployment_config.py # Deployment settings
│   │   ├── mcp_config.py        # MCP server config
│   │   ├── mlflow_config.py     # MLflow config
│   │   ├── model_config.py      # LLM model config
│   │   └── unity_catalog_config.py  # UC config
│   ├── core/                     # Core agent components
│   │   ├── agent.py             # LangGraph agent
│   │   ├── tools.py             # MCP tools
│   │   └── mcp_client.py        # MCP client
│   ├── utils/                    # Utilities
│   │   ├── auth.py              # Authentication
│   │   └── mlflow_setup.py      # MLflow setup
│   ├── cli.py                    # CLI interface
│   ├── evaluate.py               # Evaluation pipeline
│   └── deploy.py                 # Deployment automation
├── resources/                     # DAB resources
│   ├── agent_jobs.yml            # Job definitions
│   ├── agent_serving.py          # Serving endpoints
│   ├── experiments.py            # MLflow experiments
│   └── jobs.py                   # Python job definitions
├── databricks.yml                # Main DAB configuration
├── tests/                        # Test suite
├── notebooks/                    # Jupyter notebooks
├── scripts/                      # Utility scripts
└── configs/                      # Configuration files

```

## Key Features

### ✨ Serverless Single-Node Compute
- 70% faster job startup (1-2 min vs 5-8 min)
- 50% cost savings per run
- Auto-optimized runtime

### 🏗️ Infrastructure as Code
- Databricks Asset Bundles for all resources
- Dev/prod environment management
- One-command deployment

### 🤖 LangGraph Agent
- Model Context Protocol (MCP) integration
- Managed and custom MCP servers
- Responses-style agent wrapper

### 📊 MLOps Integration
- MLflow tracking and registry
- Unity Catalog model management
- Automated evaluation pipeline
- Model serving endpoints

## Getting Help

1. **Quick Questions**: Check [START_HERE.md](START_HERE.md)
2. **Setup Issues**: See [GETTING_STARTED.md](GETTING_STARTED.md)
3. **DAB Questions**: Read [QUICKSTART_DAB.md](QUICKSTART_DAB.md)
4. **Deep Dive**: Browse [PROJECT_README.md](PROJECT_README.md)

## Documentation Updates

- **November 8, 2025**: Project structure reorganized with dedicated `models/` module
- **November 8, 2025**: Migrated to Databricks serverless single-node compute
- **Previous**: Added Databricks Asset Bundles support
- **Previous**: Complete project transformation from notebook to production app
