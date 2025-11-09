# Databricks notebook source

# MAGIC %md
# MAGIC # Model Deployment Approval Notebook
# MAGIC
# MAGIC This notebook implements a manual approval step for model deployment.
# MAGIC The deployment job will pause at this step and wait for approval before proceeding.
# MAGIC
# MAGIC **Instructions:**
# MAGIC 1. Review the model metrics and validation results
# MAGIC 2. Click "Approve" to continue deployment or "Reject" to stop

# COMMAND ----------

# Get job parameters
dbutils.widgets.text("model_name", "rag.development.langgraph_mcp_agent", "Model Name")
dbutils.widgets.text("model_version", "latest", "Model Version")

model_name = dbutils.widgets.get("model_name")
model_version = dbutils.widgets.get("model_version")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Model Information

# COMMAND ----------

import mlflow
from mlflow.tracking import MlflowClient
from databricks import agents
from databricks.sdk import WorkspaceClient

client = MlflowClient()
w = WorkspaceClient()

# Set registry URI for Unity Catalog
mlflow.set_registry_uri("databricks-uc")

print(f"Model Name: {model_name}")
print(f"Model Version: {model_version}")

# COMMAND ----------

# Get model version details
if model_version == "latest":
    # Get latest version
    versions = client.search_model_versions(f"name='{model_name}'")
    if not versions:
        raise ValueError(f"No versions found for model: {model_name}")
    # Sort by version number and get the latest
    model_version_obj = sorted(versions, key=lambda x: int(x.version), reverse=True)[0]
    actual_version = model_version_obj.version
else:
    model_version_obj = client.get_model_version(model_name, model_version)
    actual_version = model_version

print(f"\nDeploying Model Version: {actual_version}")
print(f"Status: {model_version_obj.status}")
print(f"Created: {model_version_obj.creation_timestamp}")
if model_version_obj.description:
    print(f"Description: {model_version_obj.description}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Display Model Metrics and Parameters

# COMMAND ----------

# Get run information
run_id = model_version_obj.run_id
run = client.get_run(run_id)

print("\n" + "=" * 60)
print("MODEL CONFIGURATION PARAMETERS")
print("=" * 60)

# Display key parameters
params = run.data.params
if params:
    for key, value in sorted(params.items()):
        print(f"{key}: {value}")
else:
    print("No parameters logged")

# COMMAND ----------

print("\n" + "=" * 60)
print("MODEL METRICS")
print("=" * 60)

# Display metrics
metrics = run.data.metrics
if metrics:
    for key, value in sorted(metrics.items()):
        print(f"{key}: {value}")
else:
    print("No metrics logged")

# COMMAND ----------

print("\n" + "=" * 60)
print("MODEL TAGS")
print("=" * 60)

# Display tags
tags = run.data.tags
if tags:
    for key, value in sorted(tags.items()):
        if not key.startswith("mlflow."):
            print(f"{key}: {value}")
else:
    print("No tags logged")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Approval Decision
# MAGIC
# MAGIC **Review the model information above and decide:**
# MAGIC - ✅ **Approve**: Continue with deployment to serving endpoint
# MAGIC - ❌ **Reject**: Stop the deployment pipeline
# MAGIC
# MAGIC Set the `approved` variable below:

# COMMAND ----------

# Set this to True to approve deployment, False to reject
# approved = True

if approved:
    print("✅ DEPLOYMENT APPROVED")
    print(f"Model {model_name} version {actual_version} will be deployed to serving endpoint.")

    # Update model version description with approval
    from datetime import datetime

    approval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    client.update_model_version(
        name=model_name, version=actual_version, description=f"Approved for deployment on {approval_time}"
    )

    # Exit successfully
    dbutils.notebook.exit("approved")
else:
    print("❌ DEPLOYMENT REJECTED")
    print(f"Model {model_name} version {actual_version} deployment has been cancelled.")

    # Exit with rejection
    raise Exception("Deployment rejected by approval notebook")
