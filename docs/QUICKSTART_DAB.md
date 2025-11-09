# Quick Start: Databricks Asset Bundles

This guide shows you how to use Databricks Asset Bundles (DAB) with your LangGraph MCP Agent.

## Prerequisites

✅ Databricks CLI installed  
✅ Authenticated with Databricks (`databricks auth login`)  
✅ Python 3.11+ installed  
✅ Project dependencies installed  

## 1. Initial Setup

```bash
# Install dependencies
make install

# Or manually
pip install -e ".[dev]"
```

## 2. Configure Databricks CLI

Set up profiles for different environments:

```bash
# Development profile
databricks auth login --host https://your-workspace.cloud.databricks.com --profile development

# Production profile (optional)
databricks auth login --host https://your-workspace.cloud.databricks.com --profile production
```

## 3. Validate Your Bundle

Check that everything is configured correctly:

```bash
# Validate bundle
databricks bundle validate

# Or using Make
make bundle-validate
```

Expected output:
```
✓ Bundle configuration is valid
```

## 4. Deploy to Development

Deploy all resources (jobs, experiments) to dev:

```bash
# Deploy to dev
databricks bundle deploy -t dev

# Or using Make
make bundle-deploy-dev
```

This will:
- Build the Python wheel
- Create/update jobs (evaluation, deployment)
- Create MLflow experiments
- Upload artifacts to Databricks

## 5. Run the Deployment Job

Execute the deployment pipeline:

```bash
# Run deployment job
databricks bundle run agent_deployment -t dev

# Or using Make
make bundle-run-deploy
```

This job will:
1. Log model to MLflow
2. Register model to Unity Catalog
3. Validate the model

## 6. View Results

Check the Databricks workspace:

### Jobs
1. Go to **Workflows** → **Jobs**
2. Look for `[dev your_name] agent_deployment`
3. Click to view run details

### MLflow Experiment
1. Go to **Machine Learning** → **Experiments**
2. Find `/Users/your.email@company.com/langgraph-mcp-agent-dev`
3. View tracked runs and models

### Unity Catalog Model
1. Go to **Catalog** → **Models**
2. Navigate to `rag.development.langgraph_mcp_agent`
3. View registered versions

## 7. Run Evaluation

Evaluate your deployed agent:

```bash
# Run evaluation job
databricks bundle run agent_evaluation -t dev

# Or using Make
make bundle-run-eval
```

## Common Workflows

### Full Development Cycle

```bash
# 1. Make code changes
vim src/langgraph_agent/core/agent.py

# 2. Test locally
python scripts/test_agent.py

# 3. Deploy to dev
make bundle-deploy-dev

# 4. Run deployment
make bundle-run-deploy

# 5. Evaluate
make bundle-run-eval
```

### Update Existing Deployment

```bash
# Redeploy with changes
make bundle-deploy-dev

# Run deployment job to update model
make bundle-run-deploy
```

### Deploy to Production

```bash
# Validate first
databricks bundle validate -t prod

# Deploy to prod
make bundle-deploy-prod

# Run deployment
databricks bundle run agent_deployment -t prod
```

## Available Make Commands

```bash
make help                  # Show all commands

# Bundle commands
make bundle-validate       # Validate configuration
make bundle-deploy-dev     # Deploy to dev
make bundle-deploy-prod    # Deploy to prod
make bundle-run-eval       # Run evaluation
make bundle-run-deploy     # Run deployment
make bundle-destroy-dev    # Destroy dev resources

# Local development
make quick-test            # Quick agent test
make serve                 # Serve locally
make evaluate              # Local evaluation
```

## Configuration

### Customize Variables

Edit `databricks.yml` to customize:

```yaml
variables:
  catalog: rag                           # Your catalog
  schema: development                    # Your schema
  model_name: langgraph_mcp_agent       # Model name
  user_email: your.email@company.com    # Your email
  llm_endpoint: databricks-claude-3-7-sonnet  # LLM endpoint
```

Or override at deployment:

```bash
databricks bundle deploy -t dev --var="catalog=custom_catalog"
```

## Troubleshooting

### "Bundle validation failed"

```bash
# Check syntax
databricks bundle validate -t dev

# Common issues:
# - YAML indentation errors
# - Missing variables
# - Invalid resource names
```

### "Authentication failed"

```bash
# Re-authenticate
databricks auth login --profile development

# Verify profiles
databricks auth profiles
```

### "Job failed to run"

1. Go to Databricks UI → **Workflows** → **Jobs**
2. Find your job (prefixed with `[dev your_name]`)
3. Click on latest run
4. Check logs for errors

### "Wheel not found"

```bash
# Build wheel manually
make build

# Check dist/ directory
ls -la dist/

# Redeploy
make bundle-deploy-dev
```

## Next Steps

1. **Customize Jobs**: Edit `resources/agent_jobs.yml`
2. **Add Resources**: Create new `.yml` or `.py` files in `resources/`
3. **Set Up CI/CD**: Use bundle commands in your pipeline
4. **Monitor**: Check jobs and experiments in Databricks UI

## Comparison: CLI vs Bundle

### Using CLI (Legacy)
```bash
# Manual steps
langgraph-agent deploy
# Configure in UI
# No version control
```

### Using Bundles (Recommended)
```bash
# Infrastructure as code
make bundle-deploy-dev
make bundle-run-deploy
# Everything in Git
```

**Benefits of Bundles**:
- ✅ Version controlled
- ✅ Reproducible
- ✅ Environment management
- ✅ CI/CD ready
- ✅ Team collaboration

## Learn More

- [Full DAB Guide](./DATABRICKS_BUNDLES.md) - Complete documentation
- [Databricks Docs](https://docs.databricks.com/dev-tools/bundles/) - Official documentation
- [Bundle Reference](https://docs.databricks.com/dev-tools/bundles/reference.html) - Configuration reference

## Quick Reference Card

```bash
# Validate
databricks bundle validate

# Deploy dev
databricks bundle deploy -t dev

# Run jobs
databricks bundle run agent_deployment -t dev
databricks bundle run agent_evaluation -t dev

# Deploy prod
databricks bundle deploy -t prod

# Destroy
databricks bundle destroy -t dev
```

---

**Ready to deploy?** Run `make bundle-deploy-dev` to get started! 🚀
