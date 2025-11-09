# Testing Guide for Prompt Registry

This document describes how to run tests for the MLflow Prompt Registry integration.

## Test Structure

```
tests/
├── unit/
│   ├── test_config.py                    # Config tests (updated with prompt registry)
│   └── test_prompt_registry.py           # Unit tests for prompt registry (NEW)
└── integration/
    └── test_prompt_registry_integration.py # Integration tests (NEW)
```

## Running Tests

### All Tests

Run all tests including unit and integration:

```bash
# Using pytest directly
pytest

# Using uv (recommended)
uv run pytest

# Using make (if configured)
make test
```

### Unit Tests Only

Unit tests use mocks and don't require MLflow connection:

```bash
pytest tests/unit/test_prompt_registry.py -v
```

### Integration Tests Only

Integration tests require a configured MLflow tracking server:

```bash
# Run all integration tests
pytest tests/integration/test_prompt_registry_integration.py -v

# Run specific test class
pytest tests/integration/test_prompt_registry_integration.py::TestPromptRegistryCreation -v

# Run with slow tests
pytest tests/integration/test_prompt_registry_integration.py -v --run-slow
```

### With Coverage

```bash
pytest --cov=langgraph_agent.utils.mlflow_setup --cov-report=html
```

## Test Categories

### Unit Tests (`tests/unit/test_prompt_registry.py`)

✅ **What's Tested:**
- `ModelConfig` with prompt registry settings
- Default values for prompt registry configuration
- Environment variable overrides
- `load_prompt_from_registry()` function with mocks
- Loading latest version
- Loading specific versions
- Loading by alias
- Chat prompts vs text prompts
- Fallback behavior
- Error handling

✅ **Requirements:**
- No external dependencies
- Fast execution
- Use mocks for MLflow

### Integration Tests (`tests/integration/test_prompt_registry_integration.py`)

✅ **What's Tested:**
- Creating prompts in actual MLflow registry
- Updating prompts (versioning)
- Loading prompts from registry
- Setting and using aliases
- Version tags
- Prompt-level tags
- Searching prompts
- Chat-style prompts
- Agent integration with registry

⚠️ **Requirements:**
- Configured MLflow tracking URI
- Databricks workspace access (for full tests)
- Appropriate permissions to create/delete prompts
- May take longer to run

## Test Configuration

### Environment Variables

Set these for integration tests:

```bash
# MLflow tracking
export MLFLOW_TRACKING_URI="databricks://your-profile"

# Or for Databricks
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token"
```

### Pytest Configuration

Add to `pytest.ini` or `pyproject.toml`:

```ini
[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]
```

## Test Scenarios Covered

### 1. Configuration Tests
- ✅ Default configuration values
- ✅ Environment variable overrides
- ✅ Config file loading
- ✅ Type validation (string vs int for version)

### 2. Prompt Loading Tests
- ✅ Load latest version
- ✅ Load specific version (by number)
- ✅ Load by alias (production, champion, etc.)
- ✅ Load text prompts
- ✅ Load chat prompts with system messages
- ✅ Load chat prompts without system messages
- ✅ Empty chat prompts
- ✅ Malformed templates

### 3. Error Handling Tests
- ✅ Prompt not found
- ✅ Network errors
- ✅ Permission errors
- ✅ Fallback behavior
- ✅ No fallback behavior (raises exception)

### 4. Integration Tests
- ✅ Create prompts in registry
- ✅ Update prompts (create versions)
- ✅ Delete prompts (cleanup)
- ✅ Set/get/delete aliases
- ✅ Set/get/delete tags
- ✅ Search prompts by name
- ✅ Search prompts by tags
- ✅ Version management

### 5. Agent Integration Tests
- ✅ Agent loads prompt from registry when enabled
- ✅ Agent uses config prompt when registry disabled
- ✅ Explicit prompt override works
- ✅ Fallback to config on registry error

## Running Specific Test Scenarios

### Test Configuration Loading
```bash
pytest tests/unit/test_config.py::test_model_config_defaults -v
pytest tests/unit/test_prompt_registry.py::TestModelConfigPromptRegistry -v
```

### Test Prompt Loading
```bash
pytest tests/unit/test_prompt_registry.py::TestLoadPromptFromRegistry -v
```

### Test Error Handling
```bash
pytest tests/unit/test_prompt_registry.py::TestPromptRegistryErrorHandling -v
```

### Test Agent Integration
```bash
pytest tests/unit/test_prompt_registry.py::TestPromptRegistryIntegration -v
```

### Test Real MLflow Operations
```bash
# Requires MLflow connection
pytest tests/integration/test_prompt_registry_integration.py::TestPromptRegistryCreation -v
```

## Common Issues and Solutions

### Issue: MLflow connection error in integration tests

**Solution:**
```bash
# Set up MLflow tracking
export MLFLOW_TRACKING_URI="databricks://your-profile"

# Or skip integration tests
pytest -m "not integration"
```

### Issue: Permission denied when creating prompts

**Solution:**
- Verify your Databricks token has correct permissions
- Check workspace access settings
- Try with a different experiment location

### Issue: Tests hang or timeout

**Solution:**
```bash
# Run with timeout
pytest --timeout=30

# Skip slow tests
pytest -m "not slow"
```

### Issue: Test prompts not cleaned up

**Solution:**
```bash
# Manually clean up test prompts
python -c "
from mlflow import MlflowClient
client = MlflowClient()
prompts = client.search_prompts(filter_string=\"tag.test='true'\")
for p in prompts:
    versions = client.search_prompt_versions(p.name)
    for v in versions:
        client.delete_prompt_version(p.name, v.version)
"
```

## Test Coverage Goals

Current coverage for prompt registry functionality:

- **Unit tests**: 95%+ coverage
- **Integration tests**: Key workflows covered
- **Error paths**: All error scenarios tested
- **Configuration**: All config options tested

Run coverage report:
```bash
pytest --cov=langgraph_agent --cov-report=term-missing
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run unit tests
  run: pytest tests/unit -v

- name: Run integration tests (if credentials available)
  if: env.DATABRICKS_TOKEN != ''
  run: pytest tests/integration -v
  env:
    DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
    DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
```

## Best Practices

1. **Always run unit tests before committing**
   ```bash
   pytest tests/unit/test_prompt_registry.py -v
   ```

2. **Run integration tests before deploying**
   ```bash
   pytest tests/integration -v
   ```

3. **Use markers to organize test runs**
   ```bash
   pytest -m "not slow and not integration"  # Quick tests only
   ```

4. **Check coverage regularly**
   ```bash
   pytest --cov --cov-report=html
   open htmlcov/index.html
   ```

5. **Clean up test data**
   - Integration tests include cleanup in fixtures
   - Verify cleanup ran successfully
   - Manually clean if needed

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [MLflow Testing Guide](https://mlflow.org/docs/latest/python_api/mlflow.html#testing)
- [Databricks Testing Best Practices](https://docs.databricks.com/dev-tools/testing.html)
