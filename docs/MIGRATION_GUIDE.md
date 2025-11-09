# Migration Guide: CLI-based to Direct Scripts

This guide helps you migrate from the CLI-based job configuration to the cleaner direct script approach.

## Summary

We've introduced a cleaner approach for Databricks jobs that eliminates CLI overhead by using direct Python entry points instead of CLI commands.

## Changes Overview

### 1. New Python Scripts (`scripts/deployment/`)

Three new scripts provide direct entry points:
- `register_model.py` - Register model to Unity Catalog
- `evaluate_model.py` - Evaluate model quality
- `deploy_model.py` - Deploy to serving endpoint

### 2. New Entry Points (`pyproject.toml`)

```toml
[project.scripts]
# Direct entry points (no CLI parsing)
register_model = "scripts.deployment.register_model:main"
evaluate_model = "scripts.deployment.evaluate_model:main"
deploy_model = "scripts.deployment.deploy_model:main"
```

### 3. New Job Configuration (`agent_deployment_v2.yml`)

Uses environment variables instead of CLI parameters:

```yaml
python_wheel_task:
  entry_point: register_model  # Direct call
new_cluster:
  spark_env_vars:
    EXPERIMENT_NAME: ${var.experiment_name}  # Clean config
```

## Migration Steps

### Step 1: Update Your Workflow

**Old approach:**
```bash
databricks bundle run agent_deployment_pipeline -t dev
```

**New approach:**
```bash
databricks bundle run agent_deployment_pipeline_v2 -t dev
```

### Step 2: Test Locally (Optional)

Test the new scripts work:
```bash
make test-scripts
```

### Step 3: Validate

```bash
# Validate bundle includes new scripts
databricks bundle validate -t dev

# Check wheel includes scripts package
unzip -l dist/*.whl | grep scripts
```

### Step 4: Deploy and Test

```bash
# Deploy with new configuration
databricks bundle deploy -t dev

# Run new pipeline
databricks bundle run agent_deployment_pipeline_v2 -t dev
```

## What's Different?

### Configuration Passing

**Old (CLI):**
```yaml
parameters:
  - "register"
  - "--experiment-name"
  - "${var.experiment_name}"
  - "--catalog"
  - "${var.catalog}"
```

**New (Environment Variables):**
```yaml
spark_env_vars:
  EXPERIMENT_NAME: ${var.experiment_name}
  CATALOG: ${var.catalog}
```

### Script Structure

**Old (CLI-based):**
```python
@click.command()
@click.option("--experiment-name", ...)
def register(experiment_name):
    # CLI parsing overhead
    # Click validation
    # String to type conversion
    ...
```

**New (Direct):**
```python
def main():
    # Direct environment variable access
    experiment_name = os.getenv("EXPERIMENT_NAME")
    # Direct function calls
    log_and_register_model(...)
    return 0
```

## Impact on Testing

### New Make Targets

```bash
make test-scripts    # Test new script entry points
make test-imports    # Updated to include scripts
```

### New Unit Tests

`tests/unit/test_deployment_scripts.py` validates:
- Scripts can be imported
- Environment variables are used correctly
- Error handling works properly

## Impact on Makefile

### Updated Help

```bash
make help
```

Now shows both approaches:
- `agent_deployment_pipeline` - CLI-based (legacy)
- `agent_deployment_pipeline_v2` - Direct scripts (recommended)

### Updated Test Commands

```bash
make test-imports    # Now includes scripts package
make test-scripts    # New command to test entry points
```

## Backwards Compatibility

The CLI-based approach (`agent_deployment_pipeline`) is **still available** and will continue to work. This ensures:

✅ Existing deployments aren't broken  
✅ Teams can migrate at their own pace  
✅ CLI available for local development  

## Benefits of Migration

1. **Cleaner Configuration** - Environment variables vs CLI parameters
2. **Faster Execution** - No Click parsing overhead
3. **Easier Debugging** - Standard Python stack traces
4. **Better Separation** - Job logic separate from CLI
5. **Type Safety** - Native Python types from start
6. **Less Verbose** - Fewer lines of YAML configuration

## Rollback Plan

If you need to rollback:

```bash
# Use the legacy job
databricks bundle run agent_deployment_pipeline -t dev
```

The old configuration is preserved and fully functional.

## Questions?

See [`docs/JOB_CONFIGURATION_COMPARISON.md`](JOB_CONFIGURATION_COMPARISON.md) for detailed comparison.
