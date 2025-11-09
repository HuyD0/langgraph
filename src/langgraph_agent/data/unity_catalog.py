"""Register evaluation dataset to Unity Catalog.

This script uploads the evaluation dataset as a Delta table in Unity Catalog,
making it accessible to all jobs and notebooks.
"""

import json
from pathlib import Path

from pyspark.sql import SparkSession

from langgraph_agent.models import get_config
from langgraph_agent.monitoring.logging import get_logger

logger = get_logger(__name__)


def register_eval_dataset_to_uc(
    dataset_path: str = "data/eval_dataset.json",
    catalog: str = None,
    schema: str = None,
    table_name: str = "agent_eval_dataset",
) -> str:
    """Register evaluation dataset as a Delta table in Unity Catalog.

    Args:
        dataset_path: Path to the JSON dataset file
        catalog: UC catalog name (defaults from config)
        schema: UC schema name (defaults from config)
        table_name: Table name for the dataset

    Returns:
        Full table name (catalog.schema.table)
    """
    config = get_config()

    # Use config defaults if not provided
    catalog = catalog or config.uc.catalog_name
    schema = schema or config.uc.schema_name
    full_table_name = f"{catalog}.{schema}.{table_name}"

    logger.info("=" * 60)
    logger.info("Registering evaluation dataset to Unity Catalog")
    logger.info(f"  Table: {full_table_name}")
    logger.info(f"  Source: {dataset_path}")
    logger.info("=" * 60)

    # Load dataset
    dataset_file = Path(dataset_path)
    if not dataset_file.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    with open(dataset_file, "r") as f:
        dataset = json.load(f)

    logger.info(f"Loaded {len(dataset)} evaluation examples")

    # Get Spark session
    spark = SparkSession.builder.getOrCreate()

    # Convert to DataFrame format suitable for MLflow evaluation
    # Flatten the nested structure
    rows = []
    for idx, item in enumerate(dataset):
        # Extract the user message from inputs
        user_content = None
        if "inputs" in item and "input" in item["inputs"]:
            for msg in item["inputs"]["input"]:
                if msg.get("role") == "user":
                    user_content = msg.get("content")
                    break

        rows.append(
            {
                "id": idx,
                "question": user_content,
                "expected_response": item.get("expected_response", ""),
                "inputs_json": json.dumps(item.get("inputs", {})),
            }
        )

    # Create DataFrame
    df = spark.createDataFrame(rows)

    # Show sample
    logger.info("Sample data:")
    df.show(2, truncate=False)

    # Create schema if it doesn't exist
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
    logger.info(f"✓ Schema {catalog}.{schema} ready")

    # Write to Delta table
    logger.info(f"Writing to {full_table_name}...")
    df.write.format("delta").mode("overwrite").saveAsTable(full_table_name)

    logger.info("=" * 60)
    logger.info("✓ Dataset registered successfully!")
    logger.info(f"  Table: {full_table_name}")
    logger.info(f"  Rows: {df.count()}")
    logger.info(f"  Columns: {', '.join(df.columns)}")
    logger.info("=" * 60)

    # Add table comment
    spark.sql(
        f"""
        COMMENT ON TABLE {full_table_name} IS 
        'Evaluation dataset for LangGraph MCP Agent. 
        Contains test questions and expected responses for agent evaluation.'
    """
    )

    return full_table_name


def load_eval_dataset_from_uc(
    catalog: str = None,
    schema: str = None,
    table_name: str = "agent_eval_dataset",
) -> list:
    """Load evaluation dataset from Unity Catalog.

    Args:
        catalog: UC catalog name
        schema: UC schema name
        table_name: Table name

    Returns:
        List of evaluation examples in MLflow format
    """
    config = get_config()
    catalog = catalog or config.uc.catalog_name
    schema = schema or config.uc.schema_name
    full_table_name = f"{catalog}.{schema}.{table_name}"

    logger.info(f"Loading evaluation dataset from {full_table_name}")

    spark = SparkSession.builder.getOrCreate()
    df = spark.table(full_table_name)

    # Convert back to original format
    rows = df.collect()
    dataset = []

    for row in rows:
        dataset.append(
            {
                "inputs": json.loads(row.inputs_json),
                "expected_response": row.expected_response,
            }
        )

    logger.info(f"Loaded {len(dataset)} examples from Unity Catalog")
    return dataset


if __name__ == "__main__":
    # Register the dataset
    import sys

    dataset_path = sys.argv[1] if len(sys.argv) > 1 else "data/eval_dataset.json"
    catalog = sys.argv[2] if len(sys.argv) > 2 else None
    schema = sys.argv[3] if len(sys.argv) > 3 else None

    table_name = register_eval_dataset_to_uc(
        dataset_path=dataset_path,
        catalog=catalog,
        schema=schema,
    )

    logger.info(f"\n✓ Dataset registered: {table_name}")
    logger.info("\nTo use in evaluation:")
    logger.info("  from langgraph_agent.data import load_eval_dataset_from_uc")
    logger.info("  dataset = load_eval_dataset_from_uc()")
