"""MLflow setup and configuration utilities."""

import os
from pathlib import Path
from typing import Any, Optional, Union

import mlflow
from mlflow.models.resources import DatabricksServingEndpoint, DatabricksFunction

from langgraph_agent.monitoring.logging import get_logger
from langgraph_agent.utils.config_loader import get_cached_config, get_config_value
from langgraph_agent.utils.auth import is_running_in_databricks

logger = get_logger(__name__)

# Load configuration
_config = get_cached_config()


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

        # Set experiment name - always required
        if not experiment_name:
            # Get from config if not provided
            experiment_name = get_config_value(_config, "mlflow.experiment_name", "MLFLOW_EXPERIMENT_NAME")
            if not experiment_name:
                raise ValueError(
                    "No MLflow experiment name provided. "
                    "Set via parameter, MLFLOW_EXPERIMENT_NAME env var, or mlflow.experiment_name in config."
                )

        mlflow.set_experiment(experiment_name)
        config["experiment_name"] = experiment_name
        logger.info(f"MLflow experiment set to: {experiment_name}")

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
    model_endpoint_name: Optional[str] = None,
    pip_requirements: list[str] | None = None,
    skip_validation: bool = True,
    config: Optional[Any] = None,
):
    """Log the agent model to MLflow using code-based logging.

    Args:
        model_code_path: Path to app.py (or "." to use package location)
        model_endpoint_name: Name of the LLM endpoint to use (for resource tracking).
                           If None, uses value from config.
        pip_requirements: List of pip dependencies
        skip_validation: Skip automatic validation during logging (avoids endpoint errors)
        config: Optional AgentConfig object with runtime configuration values

    Returns:
        MLflow model info
    """
    # Use config value if not provided
    if model_endpoint_name is None:
        model_endpoint_name = get_config_value(_config, "model.endpoint_name", "MODEL_ENDPOINT_NAME")

    logger.info(f"Logging model to MLflow with endpoint: {model_endpoint_name}")

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

            # Use passed config if available, otherwise use cached config
            runtime_config = config if config is not None else None

            # Log tags for organization
            tags = {
                "model_type": "langgraph_agent",
                "deployment_type": "databricks_ml_applications",
            }

            # Add config-based tags if runtime_config is available
            if runtime_config:
                tags.update(
                    {
                        "catalog": runtime_config.uc.catalog,
                        "schema": runtime_config.uc.schema_name,
                        "endpoint": runtime_config.model.endpoint_name,
                    }
                )
            else:
                # Fall back to cached config
                tags.update(
                    {
                        "catalog": get_config_value(_config, "uc.catalog"),
                        "schema": get_config_value(_config, "uc.schema_name"),
                        "endpoint": get_config_value(_config, "model.endpoint_name"),
                    }
                )

            # Filter out None values
            tags = {k: v for k, v in tags.items() if v is not None}
            if tags:
                mlflow.set_tags(tags)
                logger.info(f"Set {len(tags)} MLflow tags")

            # Log configuration parameters
            params = {}

            if runtime_config:
                # Use runtime config object (has actual values from environment/args)
                # Use getattr to safely access attributes that might not exist
                params = {
                    # Model configuration
                    "model.endpoint_name": runtime_config.model.endpoint_name,
                    "model.max_tokens": getattr(runtime_config.model, "max_tokens", None),
                    "model.temperature": getattr(runtime_config.model, "temperature", None),
                    "model.system_prompt": (
                        runtime_config.model.system_prompt[:100] if runtime_config.model.system_prompt else None
                    ),
                    # Prompt Registry configuration
                    "prompt.use_prompt_registry": runtime_config.model.use_prompt_registry,
                    "prompt.prompt_name": runtime_config.model.prompt_name,
                    "prompt.prompt_version": runtime_config.model.prompt_version,
                    # MCP configuration
                    "mcp.server_enabled": getattr(runtime_config.mcp, "server_enabled", None),
                    "mcp.server_name": getattr(runtime_config.mcp, "server_name", None),
                    "mcp.server_command": getattr(runtime_config.mcp, "server_command", None),
                    # Databricks configuration
                    "databricks.profile": getattr(runtime_config.databricks, "profile", None),
                    "databricks.workspace_url": getattr(runtime_config.databricks, "workspace_url", None),
                    # MLflow configuration
                    "mlflow.experiment_name": getattr(runtime_config.mlflow, "experiment_name", None),
                    "mlflow.enable_autolog": getattr(runtime_config.mlflow, "enable_autolog", None),
                    # Unity Catalog configuration
                    "uc.catalog": runtime_config.uc.catalog,
                    "uc.schema_name": runtime_config.uc.schema_name,
                    "uc.model_name": runtime_config.uc.model_name,
                    "uc.full_model_name": runtime_config.uc.full_model_name,
                    # Deployment configuration
                    "deployment.skip_validation": skip_validation,
                    "deployment.model_code_path": model_code_path,
                }
            else:
                # Fall back to cached config dictionary
                params = {
                    # Model configuration
                    "model.endpoint_name": get_config_value(_config, "model.endpoint_name"),
                    "model.max_tokens": get_config_value(_config, "model.max_tokens"),
                    "model.temperature": get_config_value(_config, "model.temperature"),
                    "model.system_prompt": (
                        (system_prompt := get_config_value(_config, "model.system_prompt")) and system_prompt[:100]
                    ),  # Truncate long prompts
                    # Prompt Registry configuration
                    "prompt.use_prompt_registry": get_config_value(_config, "model.use_prompt_registry"),
                    "prompt.prompt_name": get_config_value(_config, "model.prompt_name"),
                    "prompt.prompt_version": get_config_value(_config, "model.prompt_version"),
                    # MCP configuration
                    "mcp.server_enabled": get_config_value(_config, "mcp.server_enabled"),
                    "mcp.server_name": get_config_value(_config, "mcp.server_name"),
                    "mcp.server_command": get_config_value(_config, "mcp.server_command"),
                    # Databricks configuration
                    "databricks.profile": get_config_value(_config, "databricks.profile"),
                    "databricks.workspace_url": get_config_value(_config, "databricks.workspace_url"),
                    # MLflow configuration
                    "mlflow.experiment_name": get_config_value(_config, "mlflow.experiment_name"),
                    "mlflow.enable_autolog": get_config_value(_config, "mlflow.enable_autolog"),
                    # Unity Catalog configuration
                    "uc.catalog": get_config_value(_config, "uc.catalog"),
                    "uc.schema_name": get_config_value(_config, "uc.schema_name"),
                    "uc.model_name": get_config_value(_config, "uc.model_name"),
                    "uc.full_model_name": get_config_value(_config, "uc.full_model_name"),
                    # Deployment configuration
                    "deployment.skip_validation": skip_validation,
                    "deployment.model_code_path": model_code_path,
                }

            # Filter out None values and log parameters
            params = {k: v for k, v in params.items() if v is not None}
            mlflow.log_params(params)
            logger.info(f"Logged {len(params)} configuration parameters")

            # Get system prompt for logging
            if runtime_config:
                use_prompt_registry = runtime_config.model.use_prompt_registry
                prompt_name = runtime_config.model.prompt_name
                prompt_version = runtime_config.model.prompt_version
                system_prompt = runtime_config.model.system_prompt
            else:
                use_prompt_registry = get_config_value(_config, "model.use_prompt_registry", default=False)
                prompt_name = get_config_value(_config, "model.prompt_name")
                prompt_version = get_config_value(_config, "model.prompt_version")
                system_prompt = get_config_value(_config, "model.system_prompt")

            # Register and log the system prompt
            if use_prompt_registry and prompt_name:
                # If using prompt registry, load and log the actual prompt content
                try:
                    logger.info("Loading prompt from registry for logging to MLflow...")
                    actual_prompt = load_prompt_from_registry(
                        prompt_name=prompt_name,
                        prompt_version=prompt_version,
                    )
                    # Log the prompt as a text artifact
                    mlflow.log_text(actual_prompt, "prompt/system_prompt.txt")

                    # Register the prompt as an MLflow input
                    try:
                        from mlflow.entities import Prompt

                        prompt_obj = Prompt(
                            template=actual_prompt,
                            type="system",
                            parameters={
                                "registry_name": prompt_name,
                                "registry_version": str(prompt_version) if prompt_version else "latest",
                            },
                        )
                        mlflow.log_input(prompt_obj, context="system_prompt")
                        logger.info("✓ Registered system prompt from registry as MLflow input")
                    except Exception as e:
                        logger.debug(f"Could not log prompt as MLflow input (API may not be available): {e}")

                    # Also log prompt metadata
                    prompt_metadata = {
                        "prompt.content_length": len(actual_prompt),
                        "prompt.registry_uri": (
                            f"prompts:/{prompt_name}" + (f"/{prompt_version}" if prompt_version else "")
                        ),
                    }
                    mlflow.log_params(prompt_metadata)
                    logger.info("✓ Logged prompt content and metadata from registry")
                except Exception as e:
                    logger.warning(f"Could not load prompt from registry for logging: {e}")
            elif system_prompt:
                # If not using registry but have a system prompt, log it
                try:
                    # Log the system prompt as a text artifact
                    mlflow.log_text(system_prompt, "prompt/system_prompt.txt")

                    # Register the system prompt as an MLflow input
                    try:
                        from mlflow.entities import Prompt

                        prompt_obj = Prompt(template=system_prompt, type="system", parameters={"source": "config"})
                        mlflow.log_input(prompt_obj, context="system_prompt")
                        logger.info("✓ Registered system prompt as MLflow input")
                    except Exception as e:
                        logger.debug(f"Could not log prompt as MLflow input (API may not be available): {e}")

                    # Log prompt metadata
                    mlflow.log_params(
                        {
                            "prompt.content_length": len(system_prompt),
                            "prompt.source": "config",
                        }
                    )
                    logger.info("✓ Logged system prompt content and metadata from config")
                except Exception as e:
                    logger.warning(f"Could not log system prompt: {e}")

            # Log relevant metrics
            metrics = {}

            if runtime_config:
                # Configuration metrics
                if system_prompt:
                    metrics["config.prompt_length"] = len(system_prompt)

                # MCP metrics
                if hasattr(runtime_config, "mcp"):
                    metrics["mcp.servers_configured"] = 1 if getattr(runtime_config.mcp, "server_enabled", False) else 0

                # Model metrics
                if hasattr(runtime_config.model, "endpoint_name"):
                    metrics["model.endpoint_configured"] = 1

                # Unity Catalog metrics
                if hasattr(runtime_config, "uc"):
                    metrics["uc.catalog_configured"] = 1 if runtime_config.uc.catalog else 0
                    metrics["uc.schema_configured"] = 1 if runtime_config.uc.schema_name else 0

                # Deployment metrics
                metrics["deployment.skip_validation"] = 1 if skip_validation else 0

                # Prompt registry metrics
                if use_prompt_registry and prompt_name:
                    metrics["prompt.using_registry"] = 1
                else:
                    metrics["prompt.using_registry"] = 0

            # Filter out None values and log metrics
            metrics = {k: v for k, v in metrics.items() if v is not None}
            if metrics:
                mlflow.log_metrics(metrics)
                logger.info(f"Logged {len(metrics)} metrics")

            # Log as code-based model using app.py
            logged_agent_info = mlflow.pyfunc.log_model(
                name="agent",
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


def load_prompt_from_registry(
    prompt_name: str,
    prompt_version: Optional[Union[str, int]] = None,
    fallback_prompt: Optional[str] = None,
) -> str:
    """Load a prompt from MLflow Prompt Registry.

    This function loads prompts from the MLflow Prompt Registry, supporting:
    - Specific version numbers (e.g., 1, 2, 3)
    - Version aliases (e.g., "latest", "production", "champion")
    - Fallback to a default prompt if loading fails

    Args:
        prompt_name: Name of the prompt in the registry (e.g., "agent-system-prompt")
        prompt_version: Version number, "latest", or alias name. If None, loads latest version.
        fallback_prompt: Optional fallback prompt to use if registry load fails

    Returns:
        The prompt text loaded from the registry or the fallback prompt

    Examples:
        # Load latest version
        prompt = load_prompt_from_registry("agent-system-prompt")

        # Load specific version
        prompt = load_prompt_from_registry("agent-system-prompt", version=2)

        # Load by alias
        prompt = load_prompt_from_registry("agent-system-prompt", version="production")

        # With fallback
        prompt = load_prompt_from_registry(
            "agent-system-prompt",
            fallback_prompt="You are a helpful assistant."
        )
    """
    try:
        # Construct the prompt URI
        if prompt_version is None or prompt_version == "latest":
            # Load latest version - can use name only or @latest alias
            prompt_uri = f"prompts:/{prompt_name}"
            logger.info(f"Loading latest version of prompt: {prompt_name}")
        elif isinstance(prompt_version, int):
            # Load specific version number
            prompt_uri = f"prompts:/{prompt_name}/{prompt_version}"
            logger.info(f"Loading prompt: {prompt_name} version {prompt_version}")
        else:
            # Load by alias (e.g., "production", "champion")
            prompt_uri = f"prompts:/{prompt_name}@{prompt_version}"
            logger.info(f"Loading prompt: {prompt_name} with alias '{prompt_version}'")

        # Load the prompt from the registry
        prompt = mlflow.genai.load_prompt(prompt_uri)

        # Get the prompt text - handle both text and chat prompts
        if prompt.is_text_prompt:
            prompt_text = prompt.template
        else:
            # For chat prompts, extract the system message content
            system_messages = [msg for msg in prompt.template if msg.get("role") == "system"]
            if system_messages:
                prompt_text = system_messages[0].get("content", "")
            else:
                logger.warning("Chat prompt has no system message, using first message content")
                prompt_text = prompt.template[0].get("content", "") if prompt.template else ""

        logger.info(f"✓ Successfully loaded prompt from registry: {prompt_name}")
        logger.debug(f"Prompt preview: {prompt_text[:100]}...")

        return prompt_text

    except Exception as e:
        logger.warning(f"Failed to load prompt '{prompt_name}' from registry: {e}")

        if fallback_prompt:
            logger.info("Using fallback prompt")
            return fallback_prompt
        else:
            logger.error("No fallback prompt provided, re-raising exception")
            raise
