# Job Configuration Comparison: CLI vs Direct Scripts

This document compares the two approaches for running Databricks jobs.

## Approach 1: CLI-based (Current - agent_deployment.yml)

```yaml
tasks:
  - task_key: register_model
    python_wheel_task:
      package_name: langgraph_mcp_agent
      entry_point: langgraph_mcp_agent  # Goes through CLI
      parameters:
        - "register"
        - "--model-code"
        - "."
        - "--validate"
        - "--experiment-name"
        - "${var.experiment_name}"
```

### Pros:
- Interactive CLI available for local testing
- Familiar command-line interface
- Help text and validation built-in

### Cons:
- **Parameter parsing overhead** - Click parses strings
- **Verbose configuration** - Each parameter is a separate list item
- **String-based** - All values passed as strings, need conversion
- **Error handling complexity** - CLI exceptions vs application exceptions
- **Harder to debug** - Need to understand Click internals

---

## Approach 2: Direct Script Entry Points (Recommended - agent_deployment_v2.yml)

```yaml
tasks:
  - task_key: register_model
    python_wheel_task:
      package_name: langgraph_mcp_agent
      entry_point: register_model  # Direct Python function call
    new_cluster:
      spark_env_vars:
        EXPERIMENT_NAME: ${var.experiment_name}  # Clean env var passing
```

### Pros:
- ✅ **No CLI overhead** - Direct Python execution
- ✅ **Cleaner configuration** - Environment variables instead of parameters
- ✅ **Type-safe** - Native Python types from the start
- ✅ **Easier to debug** - Standard Python stack traces
- ✅ **More maintainable** - Simple scripts vs CLI command definitions
- ✅ **Better separation** - Job logic separate from interactive CLI
- ✅ **Faster execution** - Skip Click parsing and validation

### Implementation:

**Entry point in pyproject.toml:**
```toml
[project.scripts]
# Old: CLI-based
langgraph_mcp_agent = "langgraph_agent.cli:main"

# New: Direct entry points
register_model = "scripts.deployment.register_model:main"
evaluate_model = "scripts.deployment.evaluate_model:main"
deploy_model = "scripts.deployment.deploy_model:main"
```

**Simple Python script (scripts/deployment/register_model.py):**
```python
def main():
    """Register model to Unity Catalog."""
    # Get config from environment
    experiment_name = os.getenv("EXPERIMENT_NAME")
    
    config = get_config()
    if experiment_name:
        config.mlflow.experiment_name = experiment_name
    
    # Direct function call
    logged_info, uc_info = log_and_register_model(
        config=config,
        model_code_path=".",
        validate=True,
    )
    
    return 0
```

---

## Recommendation

**Use Approach 2 (Direct Scripts)** for Databricks jobs because:

1. **Simpler** - No CLI parameter parsing
2. **Faster** - Direct Python execution
3. **Cleaner** - Environment variables are idiomatic for jobs
4. **More maintainable** - Easier to understand and modify
5. **Better errors** - Standard Python exceptions

**Keep Approach 1 (CLI)** available for:
- Local development and testing
- Manual operations
- Interactive workflows

---

## Migration Path

1. ✅ Created new scripts in `scripts/deployment/`
2. ✅ Added entry points to `pyproject.toml`
3. ✅ Created new job definition `agent_deployment_v2.yml`
4. Test the new job: `databricks bundle deploy -t dev && databricks bundle run agent_deployment_v2 -t dev`
5. Once validated, can deprecate old CLI-based job
