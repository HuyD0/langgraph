"""MLflow setup and tracking utilities."""

import mlflow
import os
from typing import Optional
from mlflow.models.resources import DatabricksServingEndpoint, DatabricksFunction

from .auth import is_running_in_databricks
from .logging import get_logger

logger = get_logger(__name__)


def setup_mlflow_tracking(profile: str, experiment_name: Optional[str] = None, enable_autolog: bool = True) -> dict:
    """Configure MLflow tracking with Databricks.

    Args:
        profile: Databricks CLI profile name (ignored when running in Databricks)
        experiment_name: MLflow experiment name (e.g., "/Users/user@example.com/experiment")
        enable_autolog: Enable MLflow autologging

    Returns:
        Dictionary with tracking configuration details
    """
    config = {}

    try:
        # When running in Databricks, use 'databricks' (no profile)
        # When running locally, use 'databricks://{profile}'
        if is_running_in_databricks():
            tracking_uri = "databricks"
        else:
            tracking_uri = f"databricks://{profile}"

        mlflow.set_tracking_uri(tracking_uri)
        config["tracking_uri"] = tracking_uri
        logger.info(f"MLflow tracking URI set to: {tracking_uri}")

        # Set experiment name if provided
        if experiment_name:
            mlflow.set_experiment(experiment_name)
            config["experiment_name"] = experiment_name
            logger.info(f"MLflow experiment set to: {experiment_name}")
        else:
            # If no experiment name provided, get or create a default
            experiment = mlflow.set_experiment("/Shared/langgraph-mcp-agent")
            config["experiment_name"] = experiment.name
            logger.info(f"MLflow experiment set to default: {experiment.name}")

        # Enable autologging if requested
        if enable_autolog:
            mlflow.langchain.autolog()
            config["autolog_enabled"] = True
            logger.info("MLflow autologging enabled")

        return config

    except Exception as e:
        logger.warning(f"MLflow tracking configuration failed: {e}")
        logger.warning("Agent will work without MLflow tracking.")
        return {"error": str(e)}


def setup_mlflow_registry(profile: str) -> str:
    """Configure MLflow model registry with Unity Catalog.

    Args:
        profile: Databricks CLI profile name (ignored when running in Databricks)

    Returns:
        Registry URI string
    """
    # When running in Databricks, use 'databricks-uc' (no profile)
    # When running locally, use 'databricks-uc://{profile}'
    if is_running_in_databricks():
        registry_uri = "databricks-uc"
    else:
        registry_uri = f"databricks-uc://{profile}"

    mlflow.set_registry_uri(registry_uri)
    logger.info(f"MLflow registry URI set to: {registry_uri}")
    return registry_uri


def log_model_to_mlflow(
    model_code_path: str = ".",
    model_endpoint_name: str = "databricks-claude-3-7-sonnet",
    pip_requirements: list[str] | None = None,
    skip_validation: bool = True,
):
    """Log the agent model to MLflow using code-based logging.

    Args:
        model_code_path: Path to app.py (or "." to use package location)
        model_endpoint_name: Name of the LLM endpoint to use (for resource tracking)
        pip_requirements: List of pip dependencies
        skip_validation: Skip automatic validation during logging (avoids endpoint errors)

    Returns:
        MLflow model info
    """
    from pathlib import Path

    logger.info("Starting model logging to MLflow...")

    # Check environment variable override
    skip_validation = skip_validation or os.getenv("SKIP_MODEL_VALIDATION", "").lower() in ("true", "1", "yes")

    # Define resources needed by the model
    resources = [
        DatabricksServingEndpoint(endpoint_name=model_endpoint_name),
        DatabricksFunction(function_name="system.ai.python_exec"),
    ]
    logger.debug(f"Configured resources: {[r.to_dict() for r in resources]}")

    if skip_validation:
        logger.warning("⚠️  Skipping automatic model validation during logging")
        logger.warning(f"   Make sure the endpoint '{model_endpoint_name}' exists before serving the model")
        logger.info("   Setting MLFLOW_SKIP_VALIDATION=1 to bypass automatic prediction test")
        os.environ["MLFLOW_SKIP_VALIDATION"] = "1"
    # Determine the app.py path
    if model_code_path and model_code_path != ".":
        # Use provided path (should be app.py)
        app_py_path = model_code_path
        logger.info(f"Using provided model code path: {app_py_path}")
    else:
        # Use the package location (where app.py is now located)
        import langgraph_agent

        package_dir = Path(langgraph_agent.__file__).parent
        app_py_path = str(package_dir / "app.py")
        logger.info(f"Using package app.py: {app_py_path}")

    # Verify app.py exists
    if not Path(app_py_path).exists():
        logger.error(f"app.py not found at {app_py_path}")
        raise FileNotFoundError(
            f"app.py not found at {app_py_path}. " f"Expected app.py to be in the package with create_agent() function."
        )

    logger.info(f"✓ Logging model using app.py from: {app_py_path}")
    logger.debug(f"Pip requirements: {pip_requirements}")

    try:
        with mlflow.start_run() as run:
            logger.info(f"Started MLflow run: {run.info.run_id}")
            # Log as code-based model using app.py
            logged_agent_info = mlflow.pyfunc.log_model(
                artifact_path="agent",
                python_model=app_py_path,
                resources=resources,
                pip_requirements=pip_requirements,
            )
            logger.info(f"✓ Model logged successfully: {logged_agent_info.model_uri}")

        return logged_agent_info
    finally:
        # Clean up environment variable
        if skip_validation and "MLFLOW_SKIP_VALIDATION" in os.environ:
            del os.environ["MLFLOW_SKIP_VALIDATION"]
            logger.debug("Cleaned up MLFLOW_SKIP_VALIDATION environment variable")


def register_model_to_uc(
    model_uri: str,
    uc_model_name: str,
) -> mlflow.entities.model_registry.model_version.ModelVersion:
    """Register a logged model to Unity Catalog.

    Args:
        model_uri: URI of the logged model (e.g., "runs:/run_id/agent")
        uc_model_name: Full UC model name (e.g., "catalog.schema.model")

    Returns:
        ModelVersion object with registration details
    """
    return mlflow.register_model(model_uri=model_uri, name=uc_model_name)


def validate_model(
    run_id: str,
    model_name: str = "agent",
    test_input: Optional[dict] = None,
) -> dict:
    """Validate a logged model before deployment.

    Args:
        run_id: MLflow run ID
        model_name: Name of the model artifact
        test_input: Test input data for validation

    Returns:
        Model prediction result
    """
    if test_input is None:
        test_input = {"input": [{"role": "user", "content": "Hello, are you working?"}]}

    return mlflow.models.predict(
        model_uri=f"runs:/{run_id}/{model_name}",
        input_data=test_input,
        env_manager="uv",
    )
