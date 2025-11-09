# Databricks Authentication for Local Development

This guide shows you how to authenticate with Databricks when running the LangGraph agent locally (outside of Databricks notebooks).

## Overview

The agent code is designed to work both in Databricks notebooks (where authentication is automatic) and locally on your machine. When running locally, you have several authentication options.

## ✅ Recommended: Databricks CLI OAuth (No PAT Required)

This is the **easiest and most secure** method for local development.

### Step 1: Install Databricks CLI

```bash
pip install databricks-cli
```

Or using Homebrew (macOS):
```bash
brew tap databricks/tap
brew install databricks
```

### Step 2: Authenticate via OAuth

```bash
databricks auth login --host https://your-workspace.cloud.databricks.com
```

This will:
1. Open your browser for authentication
2. Create a profile in `~/.databrickscfg`
3. Store OAuth tokens securely (no PAT needed!)

### Step 3: Verify Authentication

```bash
databricks auth profiles
```

You should see your profile listed with "Valid" status:
```
Name         Host                                                 Valid
development  https://adb-xxxxx.azuredatabricks.net              YES
```

### Step 4: Use in Your Code

The agent code automatically detects and uses your CLI profile:

```python
from databricks.sdk import WorkspaceClient

# Automatically uses the 'development' profile
workspace_client = WorkspaceClient(profile="development")
```

## Alternative: OAuth M2M with Service Principal

For CI/CD pipelines or automated environments, use OAuth machine-to-machine authentication:

### Step 1: Create a Service Principal

1. In Databricks workspace, go to **Settings** → **Identity and Access**
2. Click **Service Principals** → **Add Service Principal**
3. Note the **Application (client) ID**
4. Generate a **Client Secret**

### Step 2: Set Environment Variables

```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_CLIENT_ID="your-service-principal-client-id"
export DATABRICKS_CLIENT_SECRET="your-service-principal-secret"
```

### Step 3: Use in Your Code

```python
from databricks.sdk import WorkspaceClient

# Automatically uses environment variables
workspace_client = WorkspaceClient()
```

## Configuration Priority

The Databricks SDK tries authentication methods in this order:

1. **Environment variables** (`DATABRICKS_HOST`, `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET`)
2. **Specified profile** (`profile="development"` parameter)
3. **Default profile** (from `~/.databrickscfg`)
4. **Databricks notebook context** (when running in Databricks)

## Troubleshooting

### "Reading Databricks credential configuration failed"

**Solution**: Run `databricks auth login` to authenticate

```bash
databricks auth login --host https://your-workspace.cloud.databricks.com
```

### "Profile 'development' not found"

**Solution**: Either:
1. Create the profile: `databricks auth login`
2. Use a different profile name in the code
3. Check existing profiles: `databricks auth profiles`

### "Auth type not specified"

**Solution**: Make sure you've completed the OAuth login:

```bash
# Re-run authentication
databricks auth login --host https://your-workspace.cloud.databricks.com

# Verify it worked
databricks auth profiles
```

### MLflow Tracing Warnings

If you see warnings about MLflow tracing failing to connect, it's safe to ignore during local testing. MLflow tracing is optional and doesn't affect agent functionality.

To disable tracing warnings, comment out these lines in `agent.py`:

```python
# mlflow.langchain.autolog()  # Comment out for local testing
AGENT = initialize_agent()
# mlflow.models.set_model(AGENT)  # Comment out for local testing
```

## Testing Your Setup

Run the authentication test cell in the notebook:

```python
from databricks.sdk import WorkspaceClient
import os

profile_name = os.getenv("DATABRICKS_CONFIG_PROFILE", "development")
ws = WorkspaceClient(profile=profile_name)
print(f"✓ Successfully authenticated to: {ws.config.host}")
print(f"✓ Using profile: {profile_name}")
print(f"✓ Auth type: {ws.config.auth_type}")
```

Expected output:
```
✓ Successfully authenticated to: https://adb-xxxxx.azuredatabricks.net
✓ Using profile: development
✓ Auth type: oauth
```

## Security Best Practices

✅ **DO:**
- Use OAuth CLI authentication for local development
- Use service principals for CI/CD
- Store credentials in environment variables or secure vaults
- Use different profiles for different workspaces

❌ **DON'T:**
- Commit PATs or secrets to version control
- Share authentication tokens
- Use personal tokens for production/CI environments
- Hard-code credentials in code

## References

- [Databricks Authentication Documentation](https://docs.databricks.com/en/dev-tools/auth/index.html)
- [Databricks CLI Documentation](https://docs.databricks.com/en/dev-tools/cli/index.html)
- [Databricks SDK for Python](https://databricks-sdk-py.readthedocs.io/)
