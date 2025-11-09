# Databricks notebook source
# MAGIC %md
# MAGIC # Register Evaluation Dataset to Unity Catalog
# MAGIC
# MAGIC This notebook registers the agent evaluation dataset as a Delta table in Unity Catalog.
# MAGIC This makes the dataset accessible to all jobs and notebooks without file dependencies.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Install Package (if not already installed)

# COMMAND ----------

# MAGIC %pip install /Workspace/Users/huy.d@hotmail.com/.bundle/langgraph/dev/artifacts/.internal/langgraph_mcp_agent-0.1.0-py3-none-any.whl --quiet
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Configuration
DATASET_PATH = "data/eval_dataset.json"
CATALOG = "rag"
SCHEMA = "development"
TABLE_NAME = "agent_eval_dataset"

print(f"Target table: {CATALOG}.{SCHEMA}.{TABLE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register Dataset

# COMMAND ----------

from langgraph_agent.data_utils import register_eval_dataset_to_uc

# Register the dataset
full_table_name = register_eval_dataset_to_uc(
    dataset_path=DATASET_PATH,
    catalog=CATALOG,
    schema=SCHEMA,
    table_name=TABLE_NAME,
)

print(f"\n✓ Dataset registered: {full_table_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Registration

# COMMAND ----------

# Query the table to verify
df = spark.table(full_table_name)
display(df)

# COMMAND ----------

# Show count
print(f"Total examples in dataset: {df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Loading from Unity Catalog

# COMMAND ----------

from langgraph_agent.data_utils import load_eval_dataset_from_uc

# Load the dataset
dataset = load_eval_dataset_from_uc(
    catalog=CATALOG,
    schema=SCHEMA,
    table_name=TABLE_NAME,
)

print(f"Loaded {len(dataset)} examples")
print("\nFirst example:")
print(dataset[0])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done!
# MAGIC
# MAGIC The dataset is now registered in Unity Catalog and can be used by:
# MAGIC - Evaluation jobs
# MAGIC - Notebooks
# MAGIC - Any code with access to the catalog
# MAGIC
# MAGIC The evaluation pipeline will automatically load from Unity Catalog instead of requiring file paths.
