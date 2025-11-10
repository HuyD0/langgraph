# Python for Databricks Asset Bundles (DABs) Migration Guide

## Overview

This project has been migrated to use **Python for Databricks Asset Bundles** instead of YAML-based configurations. This provides better code organization, type checking, dynamic resource generation, and reusability.

## What Changed

### 1. Configuration Structure

**Before (YAML-only):**
```yaml
# databricks.yml
include:
  - resources/**/*.yml
```

**After (Python + YAML):**
```yaml
# databricks.yml
python:
  venv_path: .venv
  resources:
    - resources:load_resources

include:
  - resources/**/*.yml  # Keep for unsupported resource types
```

### 2. Resource Definitions

**Before:** YAML files in `resources/jobs/*.yml`

**After:** Python files in `resources/jobs/*.py`

```python
# resources/__init__.py
from databricks.bundles.core import Resources

def load_resources() -> Resources:
    resources = Resources()
    # Load jobs programmatically
    return resources
```

### 3. Job Definitions

**Before:** YAML syntax
```yaml
resources:
  jobs:
    agent_deployment_pipeline:
      name: ${bundle.target}_agent_log_register
      tasks:
        - task_key: register_model
          ...
```

**After:** Python with type checking
```python
from databricks.bundles.jobs import Job

jobs["agent_deployment_pipeline"] = Job.from_dict({
    "name": "${bundle.target}_agent_log_register",
    "tasks": [
        {
            "task_key": "register_model",
            ...
        }
    ]
})
```

## Benefits of Python DABs

1. **Type Safety**: Python provides type checking and IDE autocompletion
2. **Reusability**: Share common configurations across jobs using functions
3. **Dynamic Generation**: Generate resources programmatically based on parameters
4. **Better Organization**: Modular Python files instead of large YAML files
5. **Testability**: Unit test resource definitions before deployment
6. **Parameterization**: Environment-specific logic using Python conditionals

## File Structure

```
resources/
├── __init__.py                    # Main entry point with load_resources()
├── jobs/
│   ├── __init__.py
│   ├── agent_deployment.py        # Deployment job definitions (Python)
│   ├── agent_evaluation.py        # Evaluation job definition (Python)
│   ├── agent_deployment.yml.bak   # Original YAML (backup)
│   └── agent_evaluation.yml.bak   # Original YAML (backup)
└── models/
    ├── __init__.py
    ├── agent_experiment.py         # (Not yet supported in Python)
    └── agent_experiment.yml        # Keep YAML for experiments
```

## Currently Supported Resource Types

Python for DABs currently supports:
- ✅ **Jobs** (`databricks.bundles.jobs.Job`)
- ✅ **Pipelines** (`databricks.bundles.pipelines.Pipeline`)
- ✅ **Schemas** (`databricks.bundles.schemas.Schema`)
- ✅ **Volumes** (`databricks.bundles.volumes.Volume`)

Not yet supported (keep in YAML):
- ⚠️ **Experiments** (`resources/models/agent_experiment.yml`)
- ⚠️ **Model Serving Endpoints** (`resources/serving/*.yml`)
- ⚠️ **Other resource types**

## How to Add New Jobs

### Option 1: Using Job.from_dict() (Easiest Migration)

```python
from databricks.bundles.jobs import Job

def get_my_job():
    return {
        "my_job": Job.from_dict({
            "name": "my_job_name",
            "tasks": [...]
        })
    }
```

### Option 2: Using Dataclasses (Type-Safe)

```python
from databricks.bundles.jobs import Job, Task, NotebookTask

def get_my_job():
    return {
        "my_job": Job(
            name="my_job_name",
            tasks=[
                Task(
                    task_key="my_task",
                    notebook_task=NotebookTask(
                        notebook_path="/path/to/notebook"
                    )
                )
            ]
        )
    }
```

### Option 3: Dynamic Generation

```python
def get_jobs_for_environments(envs: list[str]):
    jobs = {}
    for env in envs:
        jobs[f"job_{env}"] = Job.from_dict({
            "name": f"{env}_job",
            "tags": {"environment": env}
        })
    return jobs
```

## Deployment Commands

All existing commands work the same:

```bash
# Validate configuration
databricks bundle validate

# Deploy to dev
databricks bundle deploy -t dev

# Deploy to UAT
databricks bundle deploy -t uat

# Run a job
databricks bundle run agent_deployment_pipeline -t dev
```

## Migration Notes

1. **Backward Compatibility**: YAML and Python resources can coexist
2. **Gradual Migration**: Migrate resources incrementally
3. **Validation**: Always run `databricks bundle validate` after changes
4. **Virtual Environment**: Ensure `.venv` exists with `databricks-bundles>=0.276.0`

## Requirements

- **Databricks CLI**: 0.275.0 or higher
- **Python Package**: `databricks-bundles==0.276.0` (in dev dependencies)
- **Python Version**: 3.10-3.13
- **Virtual Environment**: `.venv` configured in `databricks.yml`

## Testing

```bash
# Install dev dependencies
uv sync --all-groups

# Validate bundle
make validate

# Deploy to dev (dry run)
databricks bundle deploy -t dev --dry-run
```

## Troubleshooting

### "No module named 'databricks.bundles'"
```bash
# Ensure databricks-bundles is installed
uv sync --all-groups
```

### "Failed to load resources"
- Check that `load_resources()` returns a `Resources` object
- Verify imports: `from databricks.bundles.core import Resources`
- Ensure function signature: `def load_resources() -> Resources:`

### "Unexpected updated resources"
- Duplicate resource names between YAML and Python
- Rename or remove YAML files to avoid conflicts
- Use `.bak` extension for YAML backups

### "AssertionError: isinstance(resources, Resources)"
- `load_resources()` must return `Resources` object, not a dict
- Use `resources.add_job()` instead of dict updates

## Resources

- [Python for Databricks Asset Bundles Documentation](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/python-dabs)
- [databricks-bundles PyPI Package](https://pypi.org/project/databricks-bundles/)
- [Databricks CLI Documentation](https://docs.databricks.com/dev-tools/cli/index.html)

## Examples

See the following files for reference implementations:
- `resources/__init__.py` - Main entry point
- `resources/jobs/agent_deployment.py` - Multi-task job with dependencies
- `resources/jobs/agent_evaluation.py` - Simple single-task job
