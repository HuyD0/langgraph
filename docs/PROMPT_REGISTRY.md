# MLflow Prompt Registry Integration

This guide explains how to use MLflow's Prompt Registry to manage your agent's system prompts with version control, aliasing, and centralized management.

## Overview

The agent now supports loading system prompts from the MLflow Prompt Registry, which provides:

- **Version Control**: Track prompt evolution with immutable versions
- **Aliasing**: Use named aliases like "production" or "champion" for flexible deployments
- **Centralization**: Share prompts across your organization
- **A/B Testing**: Easy rollbacks and testing of different prompt versions
- **Lineage**: Integration with MLflow tracking and evaluation

## Configuration

### Enable Prompt Registry

Update your configuration file (`configs/dev.yaml` or `configs/prod.yaml`):

```yaml
model:
  endpoint_name: "databricks-claude-3-7-sonnet"
  
  # Enable MLflow Prompt Registry
  use_prompt_registry: true
  prompt_name: "agent-system-prompt"
  prompt_version: "latest"  # or specific version: 1, 2, 3, etc.
```

### Configuration Options

| Option | Type | Description | Example |
|--------|------|-------------|---------|
| `use_prompt_registry` | boolean | Enable/disable prompt registry | `true` or `false` |
| `prompt_name` | string | Name of the prompt in the registry | `"agent-system-prompt"` |
| `prompt_version` | string/int | Version number, "latest", or alias name | `1`, `"latest"`, `"production"` |

### Environment Variables

You can also configure via environment variables:

```bash
export USE_PROMPT_REGISTRY=true
export PROMPT_NAME="agent-system-prompt"
export PROMPT_VERSION="latest"
```

## Creating Prompts in the Registry

### Method 1: Using MLflow UI

1. Run `mlflow ui` or navigate to your Databricks MLflow UI
2. Go to the **Prompts** tab
3. Click **Create Prompt**
4. Fill in:
   - **Name**: `agent-system-prompt`
   - **Template**: Your system prompt text
   - **Commit Message**: Description of changes (optional)
5. Click **Create**

### Method 2: Using Python API

```python
import mlflow

# Create a text prompt
mlflow.genai.create_prompt(
    name="agent-system-prompt",
    template="You are a helpful AI assistant with access to Databricks tools and MCP servers. "
             "You can help users with data analysis, SQL queries, and workspace operations.",
    commit_message="Initial system prompt for agent",
    tags={"project": "langgraph-agent", "environment": "production"}
)
```

### For Chat-Style Prompts

```python
import mlflow

# Create a chat prompt with system and user roles
chat_template = [
    {
        "role": "system",
        "content": "You are a helpful AI assistant with access to Databricks tools."
    },
    {
        "role": "user",
        "content": "{{question}}"
    }
]

mlflow.genai.create_prompt(
    name="agent-system-prompt",
    template=chat_template,
    commit_message="Chat-style system prompt"
)
```

## Updating Prompts

### Create New Version

```python
import mlflow

# Update with a new version
mlflow.genai.update_prompt(
    name="agent-system-prompt",
    template="You are an expert AI assistant specializing in Databricks and data engineering. "
             "You have access to MCP tools for advanced operations.",
    commit_message="Enhanced prompt with data engineering focus"
)
```

### Using Aliases

Aliases provide flexible deployment strategies:

```python
from mlflow import MlflowClient

client = MlflowClient()

# Set "production" alias to version 3
client.set_prompt_version_alias("agent-system-prompt", version=3, alias="production")

# Set "champion" alias for A/B testing
client.set_prompt_version_alias("agent-system-prompt", version=4, alias="champion")

# Set "latest" automatically points to the most recent version
# No need to set it manually
```

Then in your config:

```yaml
model:
  use_prompt_registry: true
  prompt_name: "agent-system-prompt"
  prompt_version: "production"  # or "champion" for A/B testing
```

## Loading Prompts in Code

The agent automatically loads prompts based on your configuration, but you can also load them manually:

```python
from langgraph_agent.utils.mlflow_setup import load_prompt_from_registry

# Load latest version
prompt = load_prompt_from_registry("agent-system-prompt")

# Load specific version
prompt = load_prompt_from_registry("agent-system-prompt", prompt_version=2)

# Load by alias
prompt = load_prompt_from_registry("agent-system-prompt", prompt_version="production")

# With fallback
prompt = load_prompt_from_registry(
    "agent-system-prompt",
    fallback_prompt="You are a helpful assistant."
)
```

## Version Management

### List All Prompt Versions

```python
from mlflow import MlflowClient

client = MlflowClient()
versions = client.search_prompt_versions("agent-system-prompt")

for v in versions:
    print(f"Version {v.version}: {v.commit_message}")
```

### Compare Versions

In the MLflow UI:
1. Navigate to your prompt
2. Click the **Compare** tab
3. Select versions to compare side-by-side

### Delete a Version

```python
from mlflow import MlflowClient

client = MlflowClient()
client.delete_prompt_version("agent-system-prompt", version=2)
```

## Best Practices

### 1. Use Descriptive Commit Messages

```python
mlflow.genai.update_prompt(
    name="agent-system-prompt",
    template="...",
    commit_message="Added instructions for handling multi-step reasoning"
)
```

### 2. Use Aliases for Environments

```yaml
# dev.yaml
model:
  prompt_version: "latest"  # Always use latest in dev

# prod.yaml  
model:
  prompt_version: "production"  # Stable version in production
```

### 3. Add Tags for Organization

```python
mlflow.genai.set_prompt_tag("agent-system-prompt", "team", "data-science")
mlflow.genai.set_prompt_tag("agent-system-prompt", "language", "en")
```

### 4. Test Before Promoting

```python
# Test with champion alias first
client.set_prompt_version_alias("agent-system-prompt", version=5, alias="champion")

# After validation, promote to production
client.set_prompt_version_alias("agent-system-prompt", version=5, alias="production")
```

### 5. Use Fallback Prompts

Always configure a fallback in `model.system_prompt` in case the registry is unavailable:

```yaml
model:
  system_prompt: "You are a helpful assistant."  # Fallback
  use_prompt_registry: true
  prompt_name: "agent-system-prompt"
```

## Deployment Workflow

### Development
```yaml
# configs/dev.yaml
model:
  use_prompt_registry: true
  prompt_name: "agent-system-prompt"
  prompt_version: "latest"  # Always get latest for testing
```

### Staging
```yaml
# configs/staging.yaml
model:
  use_prompt_registry: true
  prompt_name: "agent-system-prompt"
  prompt_version: "champion"  # Test specific version
```

### Production
```yaml
# configs/prod.yaml
model:
  use_prompt_registry: true
  prompt_name: "agent-system-prompt"
  prompt_version: "production"  # Stable, validated version
```

## Troubleshooting

### Prompt Not Found

If you see "Failed to load prompt from registry", check:

1. The prompt exists: `mlflow.genai.search_prompts(filter_string="name='agent-system-prompt'")`
2. The version/alias exists
3. MLflow tracking URI is set correctly
4. You have permissions to access the prompt

### Fallback Behavior

If prompt loading fails, the agent falls back to:
1. `model.system_prompt` in config
2. `SYSTEM_PROMPT` environment variable
3. Default hardcoded prompt

Check logs for warnings about fallback usage.

## Examples

### Complete Configuration Example

```yaml
# configs/prod.yaml
model:
  endpoint_name: "databricks-claude-3-7-sonnet"
  temperature: 0.7
  
  # Fallback prompt (used if registry unavailable)
  system_prompt: "You are a helpful AI assistant with access to various tools."
  
  # MLflow Prompt Registry
  use_prompt_registry: true
  prompt_name: "agent-system-prompt"
  prompt_version: "production"
```

### Creating a Versioned Prompt Pipeline

```python
import mlflow
from mlflow import MlflowClient

client = MlflowClient()

# Create initial prompt
mlflow.genai.create_prompt(
    name="agent-system-prompt",
    template="Version 1: Basic assistant",
    commit_message="Initial version"
)

# Iterate and create new version
mlflow.genai.update_prompt(
    name="agent-system-prompt",
    template="Version 2: Enhanced with tool usage",
    commit_message="Added tool calling instructions"
)

# Set production alias to stable version
client.set_prompt_version_alias("agent-system-prompt", version=1, alias="production")

# Set champion to test new version
client.set_prompt_version_alias("agent-system-prompt", version=2, alias="champion")
```

## Additional Resources

- [MLflow Prompt Registry Documentation](https://mlflow.org/docs/latest/genai/prompt-registry/)
- [MLflow Prompt Management API](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.genai.html)
- [Prompt Engineering Best Practices](https://mlflow.org/docs/latest/genai/prompt-engineering/)
