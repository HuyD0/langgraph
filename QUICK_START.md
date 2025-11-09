# Quick Start Guide

Get up and running in 5 minutes.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Databricks CLI configured with OAuth
- Databricks workspace with Unity Catalog

## 1. Install Dependencies

```bash
uv sync --dev
```

This installs all dependencies including:
- LangGraph and LangChain
- Databricks SDK
- MLflow
- Testing tools

## 2. Configure Authentication

```bash
# Login to Databricks (creates 'development' profile)
databricks auth login --profile development --host https://your-workspace.azuredatabricks.net

# Test authentication
databricks workspace list /
```

## 3. Configure Environment

```bash
# Copy example config
cp configs/.env.example .env

# Edit .env with your settings (optional - defaults work)
# - DATABRICKS_PROFILE=development
# - UC_CATALOG=rag
# - UC_SCHEMA=development
```

## 4. Validate Bundle

```bash
databricks bundle validate
```

Should output: `Validation OK!`

## 5. Deploy to Development

```bash
databricks bundle deploy -t dev
```

This creates:
- 2 jobs (evaluation, deployment)
- MLflow experiment
- Unity Catalog model registration

## 6. Run a Job

```bash
# Run deployment workflow
databricks bundle run agent_deployment -t dev
```

Watch progress in Databricks UI: **Workflows → Jobs**

## 7. Test Locally (Optional)

```bash
# Quick test
python scripts/test_agent.py

# Or interactive
langgraph-agent serve
```

## Common Commands

```bash
# Development
make test               # Run tests
make lint               # Check code
make format             # Format code

# Deployment
databricks bundle validate
databricks bundle deploy -t dev
databricks bundle deploy -t prod

# Jobs
databricks bundle run agent_evaluation -t dev
databricks bundle run agent_deployment -t dev

# Cleanup
databricks bundle destroy -t dev
```

## Troubleshooting

### "databricks command not found"

Install Databricks CLI:
```bash
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
```

### "uv command not found"

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "Bundle validation failed"

Check:
1. Wheel is built: `ls dist/` should show `*.whl` file
2. Run `uv build --wheel` to rebuild
3. Check `databricks.yml` syntax

### "Authentication failed"

Re-authenticate:
```bash
databricks auth login --profile development
```

## Next Steps

- Read [docs/START_HERE.md](docs/START_HERE.md) for overview
- See [docs/DATABRICKS_BUNDLES.md](docs/DATABRICKS_BUNDLES.md) for DAB details
- Check [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) for in-depth setup

## Need Help?

- Run `make help` to see all commands
- Check `docs/` for detailed documentation
- Run `databricks bundle --help` for DAB options

---

**That's it!** You're now running a production-grade AI agent on Databricks. 🎉
