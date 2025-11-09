"""Deploy model task for Databricks job.

This script can be called directly from a Databricks job without CLI.
"""

import argparse
import os
import sys

from langgraph_agent.models import get_config
from langgraph_agent.pipelines.deployment import full_deployment_pipeline


def main(argv=None):
    """Deploy the agent to serving endpoint.

    Args:
        argv: Optional argument list. If None, uses sys.argv.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Deploy model to serving endpoint")
    parser.add_argument("--catalog", help="Unity Catalog catalog name")
    parser.add_argument("--schema", help="Unity Catalog schema name")
    parser.add_argument("--model-name", "--model_name", dest="model_name", help="Model name")
    args = parser.parse_args(argv)

    config = get_config()

    # Override Unity Catalog settings from environment variables or CLI args if provided
    catalog = args.catalog or os.getenv("CATALOG")
    schema = args.schema or os.getenv("SCHEMA")
    model_name = args.model_name or os.getenv("MODEL_NAME")

    if catalog:
        config.uc.catalog = catalog
    if schema:
        config.uc.schema_name = schema
    if model_name:
        config.uc.model_name = model_name

    print("Starting deployment pipeline...")
    print(f"  Model: {config.uc.full_model_name}")

    deployment_result = full_deployment_pipeline(
        config=config,
        validate=True,
    )

    print("\n✓ Deployment successful!")
    print(f"  Model: {deployment_result['registered_model']['name']}")
    print(f"  Version: {deployment_result['registered_model']['version']}")
    print(f"  Deployment: {deployment_result['deployment']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
