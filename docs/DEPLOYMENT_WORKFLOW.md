# Deployment Workflow

This document describes the complete deployment workflow for the LangGraph MCP Agent.

## Pre-Deployment Verification

Before deploying, run comprehensive checks:

```bash
make verify
```

This command runs:
1. **Clean** - Remove old build artifacts
2. **Build** - Build the Python wheel package
3. **Lint** - Check code style with ruff and black
4. **Test** - Run all unit and integration tests
5. **Bundle Validate** - Validate Databricks bundle configuration

## Deployment Process

### 1. Deploy Bundle (Infrastructure)

```bash
databricks bundle deploy -t dev
```

This deploys:
- MLflow Experiment (`agent_experiment`)
- Job Definitions (`agent_deployment_pipeline`, `agent_evaluation`)
- Python Wheel Artifact

### 2. Run Deployment Pipeline

```bash
databricks bundle run agent_deployment_pipeline -t dev
```

This executes 3 sequential tasks:
1. **register_model** - Register agent to Unity Catalog
2. **validate_model** - Run evaluation on registered model
3. **deploy_to_serving** - Deploy model to serving endpoint

### 3. Ongoing Evaluation (Optional)

```bash
databricks bundle run agent_evaluation -t dev
```

Run standalone evaluations for monitoring or testing.

## Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ LOCAL DEVELOPMENT                                           │
├─────────────────────────────────────────────────────────────┤
│ 1. make verify                                              │
│    ├── Clean artifacts                                      │
│    ├── Build wheel                                          │
│    ├── Lint code (ruff + black)                            │
│    ├── Run tests (22 unit/integration)                     │
│    └── Validate bundle config                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ DATABRICKS DEPLOYMENT                                       │
├─────────────────────────────────────────────────────────────┤
│ 2. databricks bundle deploy -t dev                         │
│    ├── Upload wheel artifact                               │
│    ├── Deploy experiment resource                          │
│    └── Deploy job definitions                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ DEPLOYMENT PIPELINE                                         │
├─────────────────────────────────────────────────────────────┤
│ 3. databricks bundle run agent_deployment_pipeline -t dev  │
│                                                             │
│    ┌──────────────────────┐                                │
│    │ Task 1: Register     │                                │
│    │ - Log model to MLflow│                                │
│    │ - Register to UC     │                                │
│    └──────────┬───────────┘                                │
│               │                                             │
│               ▼                                             │
│    ┌──────────────────────┐                                │
│    │ Task 2: Validate     │                                │
│    │ - Run evaluation     │                                │
│    │ - Check metrics      │                                │
│    └──────────┬───────────┘                                │
│               │                                             │
│               ▼                                             │
│    ┌──────────────────────┐                                │
│    │ Task 3: Deploy       │                                │
│    │ - Create endpoint    │                                │
│    │ - Configure serving  │                                │
│    └──────────────────────┘                                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ MONITORING (Optional)                                       │
├─────────────────────────────────────────────────────────────┤
│ databricks bundle run agent_evaluation -t dev              │
│ - Run on schedule or manually                              │
│ - Monitor model performance                                │
└─────────────────────────────────────────────────────────────┘
```

## Quick Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `make verify` | Run all checks | Before every deployment |
| `databricks bundle deploy -t dev` | Deploy infrastructure | First time, or when config changes |
| `databricks bundle run agent_deployment_pipeline -t dev` | Full deployment | Deploy new model version |
| `databricks bundle run agent_evaluation -t dev` | Evaluate model | Testing, monitoring |

## Production Deployment

For production:

```bash
# 1. Verify locally
make verify

# 2. Deploy to production
databricks bundle deploy -t prod

# 3. Run production deployment pipeline
databricks bundle run agent_deployment_pipeline -t prod
```

## Troubleshooting

### Verification Fails

```bash
# Check individual components
make lint        # Code style issues
make test        # Test failures
make build       # Build issues
databricks bundle validate -t dev  # Bundle config issues
```

### Deployment Pipeline Fails

Check the specific task that failed:
- **register_model** - Check MLflow configuration, Unity Catalog permissions
- **validate_model** - Check evaluation dataset, model functionality
- **deploy_to_serving** - Check serving endpoint quotas, permissions

### View Job Run Details

```bash
# In Databricks workspace, navigate to:
# Workflows > Jobs > [dev huy_d] dev_agent_deployment_pipeline > Latest Run
```

## Best Practices

1. ✅ Always run `make verify` before deploying
2. ✅ Test in dev environment first
3. ✅ Review job run logs after deployment
4. ✅ Set up scheduled evaluations for monitoring
5. ✅ Use version control for all configuration changes
