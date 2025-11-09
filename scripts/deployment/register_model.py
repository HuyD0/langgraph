"""Register model task for Databricks job.

This script can be called directly from a Databricks job without CLI.
"""

import argparse
import os
import sys

from langgraph_agent.models import get_config
from langgraph_agent.pipelines.deployment import log_and_register_model


def main(argv=None):
    """Register model to Unity Catalog.

    Args:
        argv: Optional argument list. If None, uses sys.argv.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Register model to Unity Catalog")
    parser.add_argument("--experiment-name", "--experiment_name", dest="experiment_name", help="MLflow experiment name")
    args = parser.parse_args(argv)

    # Get configuration from DAB variables (passed as environment variables or CLI args)
    experiment_name = args.experiment_name or os.getenv("EXPERIMENT_NAME")

    config = get_config()

    # Override with environment variables if provided
    if experiment_name:
        config.mlflow.experiment_name = experiment_name

    print("Logging and registering model as ML Application...")
    print(f"  Experiment: {config.mlflow.experiment_name}")
    print(f"  Model: {config.uc.full_model_name}")

    logged_info, uc_info = log_and_register_model(
        config=config,
        model_code_path=".",
        validate=True,
    )

    print("\n✓ Model registered successfully!")
    print(f"  Run ID: {logged_info.run_id}")
    print(f"  Model: {config.uc.full_model_name}")
    print(f"  Version: {uc_info.version}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
