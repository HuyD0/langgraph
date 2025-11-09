"""Databricks job wrapper to avoid Click SystemExit issues.

This module provides job-safe entry points that don't raise SystemExit,
which Databricks jobs interpret as failures even with exit code 0.
"""

import sys
from typing import Optional

from langgraph_agent.models import get_config
from langgraph_agent.pipelines.deployment import log_and_register_model, full_deployment_pipeline
from langgraph_agent.pipelines.evaluation import run_evaluation_pipeline
from langgraph_agent.monitoring.logging import get_logger

logger = get_logger(__name__)


def job_register_model(
    model_code_path: Optional[str] = None,
    validate: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict:
    """Job-safe model registration (no SystemExit).

    Can be called from command line or programmatically.
    Command line args: model_code_path validate profile

    Args:
        model_code_path: Path to project root (default: ".")
        validate: "True" or "False" string (default: "True")
        profile: Databricks profile (default: None)

    Returns:
        Dictionary with registration info
    """
    # Handle command-line arguments
    if model_code_path is None and len(sys.argv) > 1:
        model_code_path = sys.argv[1]
    if validate is None and len(sys.argv) > 2:
        validate = sys.argv[2]
    if profile is None and len(sys.argv) > 3:
        profile = sys.argv[3]

    # Set defaults
    model_code_path = model_code_path or "."
    validate_bool = (validate or "True").lower() == "true"

    logger.info("=" * 60)
    logger.info("Starting model registration job")
    logger.info(f"  Model code path: {model_code_path}")
    logger.info(f"  Validate: {validate_bool}")
    logger.info(f"  Profile: {profile}")
    logger.info("=" * 60)

    try:
        config = get_config()
        if profile:
            config.databricks.profile = profile

        logger.info("Logging and registering model as ML Application...")

        logged_info, uc_info = log_and_register_model(
            config=config,
            model_code_path=model_code_path,
            validate=validate_bool,
        )

        result = {
            "status": "success",
            "run_id": logged_info.run_id,
            "model_name": config.uc.full_model_name,
            "version": uc_info.version,
        }

        logger.info("=" * 60)
        logger.info("✓ Model registered successfully!")
        logger.info(f"  Run ID: {logged_info.run_id}")
        logger.info(f"  Model: {config.uc.full_model_name}")
        logger.info(f"  Version: {uc_info.version}")
        logger.info("=" * 60)

        return result

    except Exception as e:
        logger.error(f"Model registration failed: {e}", exc_info=True)
        raise


def job_deploy_model(
    validate: bool = True,
    profile: Optional[str] = None,
) -> dict:
    """Job-safe model deployment (no SystemExit).

    Args:
        validate: Whether to validate model
        profile: Databricks profile

    Returns:
        Dictionary with deployment info
    """
    logger.info("=" * 60)
    logger.info("Starting deployment pipeline job")
    logger.info("=" * 60)

    try:
        config = get_config()
        if profile:
            config.databricks.profile = profile

        logger.info("Running full deployment pipeline...")

        deployment_result = full_deployment_pipeline(
            config=config,
            validate=validate,
        )

        logger.info("=" * 60)
        logger.info("✓ Deployment successful!")
        logger.info(f"  Model: {deployment_result['registered_model']['name']}")
        logger.info(f"  Version: {deployment_result['registered_model']['version']}")
        logger.info("=" * 60)

        return deployment_result

    except Exception as e:
        logger.error(f"Deployment failed: {e}", exc_info=True)
        raise


def job_evaluate_model(
    dataset_path: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict:
    """Job-safe model evaluation (no SystemExit).

    Args:
        dataset_path: Path to evaluation dataset
        profile: Databricks profile

    Returns:
        Dictionary with evaluation results
    """
    logger.info("=" * 60)
    logger.info("Starting evaluation job")
    logger.info("=" * 60)

    try:
        config = get_config()
        if profile:
            config.databricks.profile = profile

        logger.info("Running evaluation pipeline...")

        eval_results = run_evaluation_pipeline(
            config=config,
            dataset_path=dataset_path,
        )

        logger.info("=" * 60)
        logger.info("✓ Evaluation complete!")
        logger.info(f"  Results: {eval_results}")
        logger.info("=" * 60)

        return eval_results

    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise


# Job entry point that can be called directly
def run_job(job_name: str, **kwargs):
    """Run a specific job by name.

    Args:
        job_name: Name of the job (register, deploy, evaluate)
        **kwargs: Job-specific arguments
    """
    jobs = {
        "register": job_register_model,
        "deploy": job_deploy_model,
        "evaluate": job_evaluate_model,
    }

    if job_name not in jobs:
        raise ValueError(f"Unknown job: {job_name}. Available: {list(jobs.keys())}")

    logger.info(f"Running job: {job_name}")
    result = jobs[job_name](**kwargs)
    logger.info(f"Job {job_name} completed successfully")

    return result
