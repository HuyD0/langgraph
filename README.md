# LangGraph MCP Agent

A production-ready LangGraph agent with Model Context Protocol (MCP) integration for Databricks, structured as an **MLflow ML Application**.

## 🚀 Quick Start

```bash
# 1. Install dependencies
uv sync --dev

# 2. Validate bundle
databricks bundle validate

# 3. Deploy to dev
databricks bundle deploy -t dev

# 4. Register and deploy the agent
langgraph-mcp-agent deploy
```

📚 **Documentation**:
- **Start Here**: [`docs/START_HERE.md`](docs/START_HERE.md)
- **ML Application**: [`docs/ML_APPLICATION.md`](docs/ML_APPLICATION.md) ⭐ NEW
- **Getting Started**: [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md)

## 📂 Project Structure (ML Application)

```
lg-demo/
├── src/langgraph_agent/          # Main package
│   ├── mlflow.yaml               # ML Application definition ⭐
│   ├── app.py                    # Application entry point ⭐
│   ├── models/                   # Pydantic models & configs
│   ├── core/                     # Agent logic
│   ├── utils/                    # Utilities
│   ├── cli.py                    # CLI tool
│   ├── evaluate.py               # Evaluation
│   └── deploy.py                 # Deployment
├── resources/                     # DAB resources
├── databricks.yml                # Bundle configuration
├── tests/                        # Test suite
└── docs/                         # Documentation
```

**Note**: `mlflow.yaml` and `app.py` are inside the package so they're included in the wheel and available on Databricks.

## ✨ Key Features

- 🚀 **Serverless Single-Node Compute** - 70% faster startup, 50% cost savings
- 🏗️ **Infrastructure as Code** - Databricks Asset Bundles
- 🤖 **LangGraph Agent** - MCP tool integration
- 📊 **MLOps Ready** - MLflow + Unity Catalog
- 🎯 **ML Application** - Structured deployment pattern ⭐ NEW
- 🧪 **Modular Design** - Organized Pydantic models

## 🛠️ Development

### Setup

```bash
# Using uv (recommended)
uv sync --dev

# Or using pip
pip install -e ".[dev]"
```

### Testing

```bash
make test          # Run all tests
make test-unit     # Unit tests only
make test-cov      # With coverage
```

### Code Quality

```bash
make lint          # Check code style
make format        # Auto-format code
make clean         # Clean build artifacts
```

## 🚢 Deployment

# Validate configuration    ```

### Using Databricks Asset Bundles

databricks bundle validate

```bash

# Validate configuration2. To deploy a development copy of this project, type:

databricks bundle validate

# Deploy to dev (serverless)    ```

# Deploy to development

databricks bundle deploy -t devmake bundle-deploy-dev    $ databricks bundle deploy --target dev



# Run evaluation job    ```

databricks bundle run agent_evaluation -t dev

# Run evaluation    (Note that "dev" is the default target, so the `--target` parameter

# Run deployment job

databricks bundle run agent_deployment -t devmake bundle-run-eval    is optional here.)



# Deploy to production

databricks bundle deploy -t prod

# See all commands    This deploys everything that's defined for this project.

# Destroy environment

databricks bundle destroy -t devmake help    For example, the default template would deploy a pipeline called

```

```    `[dev yourname] langgraph_etl` to your workspace.

### Local Testing (Optional)

    You can find that resource by opening your workpace and clicking on **Jobs & Pipelines**.

```bash

# Quick agent test## 📚 Documentation

python scripts/test_agent.py

3. Similarly, to deploy a production copy, type:

# Start local server

langgraph-agent serveAll documentation is in the [`docs/`](docs/) directory:   ```

```

   $ databricks bundle deploy --target prod

## 📚 Documentation

- **Quick Start**: [`docs/START_HERE.md`](docs/START_HERE.md)   ```

All documentation is in [`docs/`](docs/):

- **Setup Guide**: [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md)   Note the default template has a includes a job that runs the pipeline every day

- **[START_HERE.md](docs/START_HERE.md)** - Quick overview

- **[GETTING_STARTED.md](docs/GETTING_STARTED.md)** - Setup guide- **DAB Guide**: [`docs/DATABRICKS_BUNDLES.md`](docs/DATABRICKS_BUNDLES.md)   (defined in resources/sample_job.job.yml). The schedule

- **[DATABRICKS_BUNDLES.md](docs/DATABRICKS_BUNDLES.md)** - Complete DAB guide

- **[SERVERLESS_UPDATE_SUMMARY.md](docs/SERVERLESS_UPDATE_SUMMARY.md)** - Serverless features- **Serverless**: [`docs/SERVERLESS_UPDATE_SUMMARY.md`](docs/SERVERLESS_UPDATE_SUMMARY.md)   is paused when deploying in development mode (see

- **[PROJECT_README.md](docs/PROJECT_README.md)** - Full API reference

- **Full Reference**: [`docs/PROJECT_README.md`](docs/PROJECT_README.md)   https://docs.databricks.com/dev-tools/bundles/deployment-modes.html).

See [`docs/README.md`](docs/README.md) for complete index.



## 🏗️ Architecture

See [`docs/README.md`](docs/README.md) for complete documentation index.4. To run a job or pipeline, use the "run" command:

### Pydantic Models

   ```

Configuration organized in `src/langgraph_agent/models/`:

## 🏗️ Architecture Highlights   $ databricks bundle run

```python

from langgraph_agent.models import (   ```

    AgentConfig,        # Main configuration

    AgentState,         # Agent state### Modular Pydantic Models

    ModelConfig,        # LLM settings

    DatabricksConfig,   # Databricks settings5. Finally, to run tests locally, use `pytest`:

    UnityCatalogConfig, # UC settings

    get_config,         # Config loaderConfiguration is organized in `src/langgraph_agent/models/`:   ```

)

```   $ uv run pytest



### Serverless Compute```python   ```



- ⚡ 1-2 minute job startup (vs 5-8 min classic)from langgraph_agent.models import (

- 💰 ~50% cost reduction    AgentConfig,        # Main configuration

- 🔧 Auto-configured single-node clusters    AgentState,         # Agent state

- 📦 Auto-selected ML runtime    ModelConfig,        # LLM settings

    DatabricksConfig,   # Databricks settings

### DAB Structure    UnityCatalogConfig, # UC settings

    get_config,         # Config loader

```yaml)

databricks.yml              # Main bundle config```

resources/

  ├── agent_jobs.yml        # Job definitions### Serverless Single-Node

  ├── agent_serving.py      # Serving endpoints

  ├── experiments.py        # MLflow experimentsJobs use optimized single-node clusters:

  └── jobs.py               # Python job definitions- ⚡ 1-2 minute startup

```- 💰 50% cost reduction

- 🔧 Auto-configured runtime

## 🔧 Configuration

### Databricks Asset Bundles

Via environment variables or `.env` file:

Deploy everything with one command:

```bash```bash

# Databricksdatabricks bundle deploy -t dev

DATABRICKS_PROFILE=development```

DATABRICKS_HOST=https://your-workspace.azuredatabricks.net

## 🧪 Testing

# Model

MODEL_ENDPOINT_NAME=databricks-claude-3-7-sonnet```bash

# Run all tests

# Unity Catalogmake test

UC_CATALOG=rag

UC_SCHEMA=development# Run with coverage

UC_MODEL_NAME=langgraph_mcp_agentmake test-cov

```

# Unit tests only

See [`configs/.env.example`](configs/.env.example) for template.make test-unit

```

## 🧪 Testing

## 🚢 Deployment

```bash

# All tests### Databricks Asset Bundles (Recommended)

make test

DAB handles everything - no scripts needed!

# Unit tests only

make test-unit```bash

# Validate configuration

# With coverage reportdatabricks bundle validate

make test-cov

```# Deploy to dev

databricks bundle deploy -t dev

Tests are in `tests/unit/` and `tests/integration/`.

# Run jobs

## 🤝 Contributingdatabricks bundle run agent_deployment -t dev

databricks bundle run agent_evaluation -t dev

1. Create feature branch

2. Make changes# Deploy to prod

3. Run tests: `make test`databricks bundle deploy -t prod

4. Check code style: `make lint````

5. Validate bundle: `databricks bundle validate`

6. Submit PR### Local Testing (Optional)



## 📝 Recent UpdatesFor quick local testing before deploying:



- **Nov 8, 2025**: Simplified tooling - DAB replaces shell scripts```bash

- **Nov 8, 2025**: Reorganized with dedicated `models/` module# Test agent locally

- **Nov 8, 2025**: Migrated to serverless single-node computepython scripts/test_agent.py

- Added Databricks Asset Bundles support

- Complete project transformation from notebook# Or use the CLI

langgraph-agent serve

## 🆘 Support```



- **Documentation**: [`docs/`](docs/)## 📦 Installation

- **Quick Help**: `make help`

- **DAB Help**: `databricks bundle --help````bash

- **Issues**: GitHub Issues# Clone and setup

git clone <repo>

---cd lg-demo



**Ready to deploy?** Run `databricks bundle deploy -t dev` 🚀# Install dependencies with uv

uv sync --dev

# Or with pip
pip install -e ".[dev]"
```

## 🔧 Configuration

Configuration via environment variables or `.env` file:

```bash
# Databricks
DATABRICKS_PROFILE=development
DATABRICKS_HOST=https://your-workspace.azuredatabricks.net

# Model
MODEL_ENDPOINT_NAME=databricks-claude-3-7-sonnet

# Unity Catalog
UC_CATALOG=rag
UC_SCHEMA=development
UC_MODEL_NAME=langgraph_mcp_agent
```

See [`configs/.env.example`](configs/.env.example) for full template.

## 📝 Recent Updates

- **Nov 8, 2025**: Reorganized with dedicated `models/` module
- **Nov 8, 2025**: Migrated to serverless single-node compute
- Added Databricks Asset Bundles support
- Complete project transformation from notebook

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Run tests: `make test`
4. Validate bundle: `make bundle-validate`
5. Submit PR

## 📄 License

See LICENSE file.

## 🆘 Support

- Documentation: [`docs/`](docs/)
- Issues: GitHub Issues
- Quick help: `make help`

---

**Ready to deploy?** Run `make bundle-deploy-dev` 🚀
