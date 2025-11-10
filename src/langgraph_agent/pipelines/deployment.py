"""Deployment automation for the LangGraph MCP agent."""

import os
from pathlib import Path
from typing import Optional

from databricks import agents
from pkg_resources import get_distribution

from ..models import AgentConfig
from ..utils.mlflow_setup import (
    log_model_to_mlflow,
    register_model_to_uc,
    setup_mlflow_registry,
    setup_mlflow_tracking,
    validate_model,
)
from ..monitoring.logging import get_logger

logger = get_logger(__name__)


def get_model_dependencies() -> list:
    """Get the list of Python dependencies for the model.

    Returns:
        List of pip requirements
    """
    # Find the wheel file - priority order:
    # 1. Databricks workspace path (when running in DAB job)
    # 2. Local dist/ directory (when running locally)
    # 3. Installed package version (fallback)

    wheel_file = None

    # Try to find wheel in workspace (when running in Databricks)
    if os.getenv("DATABRICKS_RUNTIME_VERSION"):
        # We're running in Databricks
        # The wheel should already be installed via the job environment
        # So we can just reference the installed package
        logger.info("Running in Databricks - wheel should be pre-installed via job environment")
        wheel_file = None  # Will use installed version below
    else:
        # Running locally - use local wheel file
        project_root = Path(__file__).parent.parent.parent.parent
        dist_dir = project_root / "dist"

        if dist_dir.exists():
            wheel_files = list(dist_dir.glob("langgraph_mcp_agent-*.whl"))
            if wheel_files:
                # Use the most recent wheel file
                wheel_file = str(wheel_files[0].absolute())
                logger.info(f"Found local wheel file: {wheel_file}")

    deps = [
        "databricks-mcp",
        f"langgraph=={get_distribution('langgraph').version}",
        f"mcp=={get_distribution('mcp').version}",
        f"databricks-langchain=={get_distribution('databricks-langchain').version}",
        f"databricks-sdk=={get_distribution('databricks-sdk').version}",
        f"nest-asyncio=={get_distribution('nest-asyncio').version}",
        f"pydantic=={get_distribution('pydantic').version}",
    ]

    # Add the package itself
    if wheel_file:
        # Use local wheel file (for local testing)
        deps.append(wheel_file)
        logger.info("Using local wheel file for langgraph-mcp-agent")
    else:
        # Use installed version (for Databricks environment)
        # The package is already installed via the job environment dependencies
        try:
            version = get_distribution("langgraph-mcp-agent").version
            deps.append(f"langgraph-mcp-agent=={version}")
            logger.info(f"Using installed langgraph-mcp-agent=={version}")
        except Exception as e:
            logger.error(f"Could not determine langgraph-mcp-agent version: {e}")
            logger.error("Package may not be available in serving environment!")
            logger.error("Make sure the wheel is included in the job environment dependencies")
            raise RuntimeError(
                "langgraph-mcp-agent package not found. " "Ensure the wheel file is built and included in job dependencies."
            )

    logger.debug(f"Model dependencies ({len(deps)} total): {deps}")
    return deps


def log_and_register_model(
    config: AgentConfig,
    model_code_path: str = ".",
    validate: bool = True,
) -> tuple:
    """Log model to MLflow and register to Unity Catalog.

    Args:
        config: Agent configuration (includes MLflow metadata from configs/default.yaml)
        model_code_path: Path to project root (default: current directory)
        validate: Whether to validate the model before registration

    Returns:
        Tuple of (logged_model_info, uc_model_info)
    """
    logger.info("Starting model logging and registration process")
    logger.debug(f"Configuration: profile={config.databricks.profile}, model={config.uc.full_model_name}")

    # Setup MLflow tracking
    logger.info("Setting up MLflow tracking...")
    setup_mlflow_tracking(
        profile=config.databricks.profile,
        experiment_name=config.mlflow.experiment_name,
        enable_autolog=config.mlflow.enable_autolog,
    )

    # Log model to MLflow
    logger.info("Logging model to MLflow...")
    logged_model_info = log_model_to_mlflow(
        model_code_path=model_code_path,
        model_endpoint_name=config.model.endpoint_name,
        pip_requirements=get_model_dependencies(),
        config=config,
    )
    logger.info(f"✓ Model logged: {logged_model_info.model_uri}")

    # Validate model if requested
    if validate:
        logger.info("Validating model...")
        try:
            validation_result = validate_model(logged_model_info.run_id)
            logger.info(f"✓ Model validation successful: {validation_result}")
        except Exception as e:
            logger.warning(f"Model validation failed: {e}")
            logger.warning("Continuing with registration anyway...")

    # Setup Unity Catalog registry
    logger.info("Setting up Unity Catalog registry...")
    setup_mlflow_registry(config.databricks.profile)

    # Register to Unity Catalog
    logger.info(f"Registering model to Unity Catalog: {config.uc.full_model_name}")
    uc_model_info = register_model_to_uc(
        model_uri=logged_model_info.model_uri,
        uc_model_name=config.uc.full_model_name,
    )
    logger.info(f"✓ Model registered: {config.uc.full_model_name} (version {uc_model_info.version})")

    return logged_model_info, uc_model_info


def deploy_to_serving_endpoint(
    config: AgentConfig,
    model_version: Optional[int] = None,
) -> dict:
    """Deploy the model to a Databricks serving endpoint.

    Args:
        config: Agent configuration
        model_version: Model version to deploy (if None, uses latest)

    Returns:
        Deployment information
    """
    uc_model_name = config.uc.full_model_name

    # If no version specified, we need to get the latest
    if model_version is None:
        import mlflow

        client = mlflow.tracking.MlflowClient()
        latest_versions = client.get_latest_versions(uc_model_name, stages=["None"])
        if not latest_versions:
            raise ValueError(f"No versions found for model {uc_model_name}")
        model_version = latest_versions[0].version
        logger.info(f"Using latest model version: {model_version}")

    logger.info(f"Deploying {uc_model_name} version {model_version}...")
    deployment_info = agents.deploy(
        uc_model_name,
        model_version,
        scale_to_zero_enabled=config.deployment.scale_to_zero_enabled,
        tags=config.deployment.tags,
    )

    logger.info("✓ Agent deployed successfully!")
    logger.info(f"Endpoint: {deployment_info}")

    return deployment_info


def full_deployment_pipeline(
    config: AgentConfig,
    model_code_path: str = ".",
    validate: bool = True,
) -> dict:
    """Run the complete deployment pipeline.

    Args:
        config: Agent configuration (includes MLflow metadata)
        model_code_path: Path to project root (default: current directory)
        validate: Whether to validate before deployment        Returns:
            Dictionary with deployment information
    """
    logger.info("=" * 60)
    logger.info("Starting deployment pipeline...")
    logger.info("=" * 60)

    # Step 1: Log and register model
    logged_model_info, uc_model_info = log_and_register_model(
        config=config,
        model_code_path=model_code_path,
        validate=validate,
    )

    # Step 2: Deploy to serving endpoint
    deployment_info = deploy_to_serving_endpoint(
        config=config,
        model_version=uc_model_info.version,
    )

    logger.info("=" * 60)
    logger.info("Deployment pipeline complete!")
    logger.info("=" * 60)

    return {
        "logged_model": {
            "run_id": logged_model_info.run_id,
            "model_uri": logged_model_info.model_uri,
        },
        "registered_model": {
            "name": config.uc.full_model_name,
            "version": uc_model_info.version,
        },
        "deployment": deployment_info,
    }
