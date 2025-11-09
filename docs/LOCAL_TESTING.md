# Local Testing Guide

This guide shows how to catch deployment errors locally before pushing to Databricks.

## Quick Reference

### Before Every Deployment

```bash
# Run comprehensive pre-deployment checks
make pre-deploy
```

This single command runs all checks below and will catch most deployment issues.

## Individual Check Commands

### 1. Code Quality

```bash
# Check code formatting and linting
make lint

# Auto-fix formatting issues
make format
```

### 2. Test Imports

```bash
# Test all module imports
make test-imports
```

This catches import errors like:
- Missing dependencies
- Incorrect type annotations
- Module import errors

### 3. Test CLI

```bash
# Test CLI commands work
make test-cli
```

Verifies:
- CLI entry points are configured correctly
- Commands can be invoked
- Help and version work

### 4. Build and Validate Wheel

```bash
# Build the wheel package
make build

# Check wheel contents
unzip -l dist/*.whl | grep entry_points
```

Ensures:
- Wheel builds successfully
- Console scripts are included
- Package structure is correct

### 5. Run Tests

```bash
# Run unit tests
make test-unit

# Run all tests
make test

# Run with coverage
make test-cov
```

### 6. Validate Databricks Configuration

```bash
# Validate bundle configuration
databricks bundle validate -t dev
```

## Common Errors and How to Catch Them Locally

### Import Errors

**Error in Databricks:** `ModuleNotFoundError: No module named 'X'`

**Catch locally:**
```bash
make test-imports
```

### Type Annotation Errors

**Error in Databricks:** `AttributeError: module 'mlflow.genai' has no attribute 'EvaluationResult'`

**Catch locally:**
```bash
make test-imports
# This will fail immediately when Python tries to parse the type annotation
```

### Missing Console Scripts

**Error in Databricks:** `Python wheel with name X could not be found`

**Catch locally:**
```bash
make build
unzip -l dist/*.whl | grep -A 5 entry_points.txt
# Check that your console scripts are listed
```

### CLI Entry Point Issues

**Error in Databricks:** Entry point not callable or doesn't exist

**Catch locally:**
```bash
make test-cli
uv run langgraph-agent --help
```

## Recommended Workflow

1. **Make changes to code**
2. **Format code:** `make format`
3. **Run pre-deployment checks:** `make pre-deploy`
4. **If all pass, deploy:** `databricks bundle deploy -t dev`

## Debugging Tips

### Test a specific module import

```bash
uv run python -c "from langgraph_agent.evaluate import *"
```

### Test wheel installation

```bash
# Build wheel
make build

# Install wheel in a temporary environment
pip install dist/langgraph_mcp_agent-0.1.0-py3-none-any.whl

# Test the installed package
python -c "import langgraph_agent; print(langgraph_agent.__version__)"
langgraph-agent --help
```

### Check actual wheel contents

```bash
# List all files in the wheel
unzip -l dist/*.whl

# Extract and inspect entry points
unzip -p dist/*.whl "*.dist-info/entry_points.txt"
```

### Simulate Databricks environment

```bash
# Create clean virtual environment
python -m venv test_env
source test_env/bin/activate

# Install only the wheel (not editable mode)
pip install dist/langgraph_mcp_agent-0.1.0-py3-none-any.whl

# Test as Databricks would
langgraph-mcp-agent evaluate --dataset data/eval_dataset.json
```

## Continuous Integration

Consider adding these checks to a CI pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run pre-deployment checks
  run: make pre-deploy
```
