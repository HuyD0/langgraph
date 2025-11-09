# Migration to ML Application

This document explains the changes made to migrate from code-based logging to MLflow ML Application.

## What Changed

### File Structure

**Added:**
- `mlflow.yaml` - ML Application configuration
- `app.py` - Application entry point with `create_agent()` function
- `docs/ML_APPLICATION.md` - ML Application documentation

**Modified:**
- `src/langgraph_agent/utils/mlflow_setup.py` - Updated to log ML Applications
- `src/langgraph_agent/deploy.py` - Changed default path to "." (project root)
- `src/langgraph_agent/cli.py` - Updated help text and defaults

**Deprecated (but kept for reference):**
- `src/langgraph_agent/core/mlflow_model.py` - Old code-based logging approach

## Key Differences

### Before (Code-Based Logging)

```python
# mlflow_model.py
AGENT = initialize_agent(...)
mlflow.models.set_model(AGENT)

# Logged as:
mlflow.pyfunc.log_model(
    python_model="src/langgraph_agent/core/mlflow_model.py",
    ...
)
```

### After (ML Application)

```python
# app.py
def create_agent(...):
    return initialize_agent(...)

# mlflow.yaml
ml_application:
  entry:
    file: app.py
    function: create_agent

# Logged as:
mlflow.pyfunc.log_model(
    python_model=".",  # Project root with mlflow.yaml
    ...
)
```

## Benefits

1. **Better Structure**: Clear separation between configuration and code
2. **Parameterization**: Entry function can accept parameters
3. **Versioning**: Entire application versioned together
4. **Maintainability**: Easier to update and test
5. **Standard Pattern**: Follows MLflow best practices

## Usage Changes

### Registration (CLI)

No changes required! The CLI still works the same:

```bash
# Before and After - same command
langgraph-mcp-agent register

# But now it uses ML Application structure
```

### Deployment

No changes required:

```bash
# Before and After - same command
langgraph-mcp-agent deploy
```

### Programmatic Usage

```python
# Before
from langgraph_agent.deploy import log_and_register_model

log_and_register_model(
    config=config,
    model_code_path="src/langgraph_agent/core/mlflow_model.py"  # Old
)

# After
log_and_register_model(
    config=config,
    model_code_path="."  # New (default)
)
```

## Configuration

The ML Application can be configured via:

1. **Function parameters** in `app.py`:
   ```python
   def create_agent(
       llm_endpoint_name: Optional[str] = None,
       system_prompt: Optional[str] = None,
       ...
   )
   ```

2. **Environment variables**:
   ```bash
   export LLM_ENDPOINT_NAME="your-endpoint"
   export SYSTEM_PROMPT="Your prompt"
   ```

3. **mlflow.yaml** (for dependencies):
   ```yaml
   ml_application:
     requirements:
       - package-name==version
   ```

## Backward Compatibility

The old `mlflow_model.py` file is kept for reference but is no longer used. All new deployments use the ML Application structure.

If you have existing deployed models using the old approach, they will continue to work. New deployments will use the ML Application structure.

## Testing the Migration

To verify the migration worked:

1. **Validate the structure**:
   ```bash
   ls -la mlflow.yaml app.py
   ```

2. **Test registration**:
   ```bash
   langgraph-mcp-agent register --validate
   ```

3. **Check the logged model**:
   - View in MLflow UI
   - Should show "ML Application" structure
   - `app.py` should be included in artifacts

4. **Test deployment** (optional):
   ```bash
   langgraph-mcp-agent deploy
   ```

## Troubleshooting

### Error: "mlflow.yaml not found"

**Cause**: Running from wrong directory

**Solution**: 
```bash
cd /path/to/lg-demo  # Project root
langgraph-mcp-agent register
```

### Error: "Cannot import create_agent"

**Cause**: Missing dependencies or incorrect Python path

**Solution**:
```bash
uv sync --dev
pip install -e .
```

### Error: Model logs but doesn't load

**Cause**: Missing imports in `app.py`

**Solution**: Ensure all required packages are:
1. Imported in `app.py`
2. Listed in `mlflow.yaml` requirements
3. Installed in your environment

## Next Steps

1. Read [`docs/ML_APPLICATION.md`](ML_APPLICATION.md) for detailed documentation
2. Test the new structure with a dev deployment
3. Update any CI/CD pipelines if needed
4. Consider removing `mlflow_model.py` once migration is confirmed

## Rollback (if needed)

If you need to rollback to code-based logging:

1. Revert `mlflow_setup.py`:
   ```python
   logged_agent_info = mlflow.pyfunc.log_model(
       python_model="src/langgraph_agent/core/mlflow_model.py",
       ...
   )
   ```

2. Update defaults in `deploy.py` and `cli.py`

3. Remove `mlflow.yaml` and `app.py`

However, **ML Application is the recommended approach** going forward.
