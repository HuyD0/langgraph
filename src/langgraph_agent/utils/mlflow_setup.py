"""MLflow setup and tracking utilities."""

import mlflow
from typing import Optional

from .auth import is_running_in_databricks


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

        # Set experiment name if provided
        if experiment_name:
            mlflow.set_experiment(experiment_name)
            config["experiment_name"] = experiment_name
        else:
            # If no experiment name provided, get or create a default
            experiment = mlflow.set_experiment("/Shared/langgraph-mcp-agent")
            config["experiment_name"] = experiment.name

        # Enable autologging if requested
        if enable_autolog:
            mlflow.langchain.autolog()
            config["autolog_enabled"] = True

        return config

    except Exception as e:
        print(f"Warning: MLflow tracking configuration failed: {e}")
        print("Agent will work without MLflow tracking.")
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
    return registry_uri


def log_model_to_mlflow(
    model_code_path: str,
    model_endpoint_name: str,
    pip_requirements: list,
):
    """Log agent model to MLflow.

    Args:
        model_code_path: Path to Python module containing the agent (can be module path like 'langgraph_agent.core.agent' or file path)
        model_endpoint_name: Name of the model serving endpoint
        pip_requirements: List of Python package requirements

    Returns:
        MLflow ModelInfo object with run and model details
    """
    import os
    from mlflow.models.resources import DatabricksServingEndpoint, DatabricksFunction

    resources = [
        DatabricksServingEndpoint(endpoint_name=model_endpoint_name),
        DatabricksFunction(function_name="system.ai.python_exec"),
    ]

    # If the path doesn't exist as a file, try to import it as a module
    # This handles both local development (file path) and Databricks execution (installed package)
    python_model = model_code_path
    if not os.path.exists(model_code_path):
        # Convert file path to module path (e.g., "src/langgraph_agent/core/agent.py" -> "langgraph_agent.core.agent")
        module_path = model_code_path.replace("src/", "").replace("/", ".").replace(".py", "")
        python_model = module_path

    with mlflow.start_run():
        logged_agent_info = mlflow.pyfunc.log_model(
            name="agent", python_model=python_model, resources=resources, pip_requirements=pip_requirements
        )

    return logged_agent_info


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
