"""Command-line interface for the LangGraph MCP agent."""

from typing import Optional

import click

from .models import get_config
from .agents import initialize_agent
from .pipelines.deployment import full_deployment_pipeline, log_and_register_model
from .pipelines.evaluation import run_evaluation_pipeline
from .utils.auth import get_workspace_client, verify_authentication
from .utils.mlflow_setup import setup_mlflow_tracking
from .data import register_eval_dataset_to_uc


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """LangGraph MCP Agent CLI - Manage your AI agent lifecycle."""
    pass


@cli.command()
@click.option("--profile", default="development", help="Databricks CLI profile")
def auth_test(profile: str):
    """Test Databricks authentication."""
    click.echo("Testing Databricks authentication...")
    try:
        auth_info = verify_authentication(profile)
        click.echo(click.style("✓ Authentication successful!", fg="green"))
        click.echo(f"  Host: {auth_info['host']}")
        click.echo(f"  Profile: {auth_info['profile']}")
        click.echo(f"  Auth type: {auth_info['auth_type']}")
    except Exception as e:
        click.echo(click.style(f"✗ Authentication failed: {e}", fg="red"))
        raise click.Abort()


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to serve on")
@click.option("--port", default=8000, help="Port to serve on")
@click.option("--profile", default=None, help="Databricks CLI profile")
def serve(host: str, port: int, profile: Optional[str]):
    """Serve the agent locally for testing."""
    config = get_config()
    if profile:
        config.databricks.profile = profile

    click.echo(f"Initializing agent with profile: {config.databricks.profile}...")

    # Get workspace client
    ws = get_workspace_client(config.databricks.profile)
    ws_host = ws.config.host

    # Build MCP server URLs
    managed_urls = config.mcp.managed_urls or [f"{ws_host}/api/2.0/mcp/functions/system/ai"]

    # Initialize agent
    agent = initialize_agent(
        workspace_client=ws,
        llm_endpoint_name=config.model.endpoint_name,
        system_prompt=config.model.system_prompt,
        managed_mcp_urls=managed_urls,
        custom_mcp_urls=config.mcp.custom_urls,
    )

    click.echo(click.style("✓ Agent initialized successfully!", fg="green"))

    # Simple test
    click.echo("\nTesting agent...")
    test_response = agent.predict({"input": [{"role": "user", "content": "Hello, are you working?"}]})
    click.echo(f"Test response: {test_response}")

    click.echo(f"\n🚀 Agent is ready! (Would serve on {host}:{port} with FastAPI)")
    click.echo("Note: Full serving implementation would use FastAPI/Uvicorn")


@cli.command()
@click.option("--dataset", default=None, help="Path to evaluation dataset")
@click.option("--profile", default=None, help="Databricks CLI profile")
def evaluate(dataset: Optional[str], profile: Optional[str]):
    """Evaluate the agent using MLflow."""
    try:
        config = get_config()
        if profile:
            config.databricks.profile = profile

        click.echo("Setting up MLflow tracking...")
        setup_mlflow_tracking(
            profile=config.databricks.profile,
            experiment_name=config.mlflow.experiment_name,
            enable_autolog=False,
        )

        click.echo("Initializing agent...")
        ws = get_workspace_client(config.databricks.profile)
        ws_host = ws.config.host
        managed_urls = config.mcp.managed_urls or [f"{ws_host}/api/2.0/mcp/functions/system/ai"]

        agent = initialize_agent(
            workspace_client=ws,
            llm_endpoint_name=config.model.endpoint_name,
            system_prompt=config.model.system_prompt,
            managed_mcp_urls=managed_urls,
            custom_mcp_urls=config.mcp.custom_urls,
        )

        click.echo("Running evaluation...")
        results = run_evaluation_pipeline(
            agent=agent,
            dataset_path=dataset,
            experiment_name=config.mlflow.experiment_name,
        )

        click.echo(click.style("✓ Evaluation complete!", fg="green"))
        click.echo(f"Metrics: {results['metrics']}")

        # Return success without calling sys.exit() for Databricks jobs
        return 0
    except Exception as e:
        click.echo(click.style(f"\n✗ Error: {e}", fg="red"), err=True)
        raise  # Re-raise to let Databricks handle it


@cli.command()
@click.option("--validate/--no-validate", default=True, help="Validate model before deployment")
@click.option("--profile", default=None, help="Databricks CLI profile")
@click.option("--catalog", default=None, help="Unity Catalog catalog name (overrides config)")
@click.option("--schema", default=None, help="Unity Catalog schema name (overrides config)")
@click.option("--model-name", default=None, help="Model name (overrides config)")
def deploy(
    validate: bool,
    profile: Optional[str],
    catalog: Optional[str],
    schema: Optional[str],
    model_name: Optional[str],
):
    """Deploy the agent to Databricks serving endpoint."""
    try:
        config = get_config()
        if profile:
            config.databricks.profile = profile

        # Override Unity Catalog settings if provided
        if catalog:
            config.uc.catalog = catalog
        if schema:
            config.uc.schema_name = schema
        if model_name:
            config.uc.model_name = model_name

        click.echo("Starting deployment pipeline...")
        click.echo(f"  Model: {config.uc.full_model_name}")

        deployment_result = full_deployment_pipeline(
            config=config,
            validate=validate,
        )

        click.echo(click.style("\n✓ Deployment successful!", fg="green"))
        click.echo(f"Model: {deployment_result['registered_model']['name']}")
        click.echo(f"Version: {deployment_result['registered_model']['version']}")
        click.echo(f"Deployment: {deployment_result['deployment']}")

        # Return success without calling sys.exit() for Databricks jobs
        return 0
    except Exception as e:
        click.echo(click.style(f"\n✗ Error: {e}", fg="red"), err=True)
        raise  # Re-raise to let Databricks handle it


@cli.command()
@click.option("--model-code", default=".", help="Path to project root")
@click.option("--validate/--no-validate", default=True, help="Validate model after logging")
@click.option("--profile", default=None, help="Databricks CLI profile")
@click.option("--experiment-name", default=None, help="MLflow experiment name (overrides config)")
def register(model_code: str, validate: bool, profile: Optional[str], experiment_name: Optional[str]):
    """Log and register model to Unity Catalog (without deployment)."""
    try:
        config = get_config()
        if profile:
            config.databricks.profile = profile

        # Override experiment name if provided
        if experiment_name:
            config.mlflow.experiment_name = experiment_name

        click.echo("Logging and registering model as ML Application...")
        click.echo(f"  Experiment: {config.mlflow.experiment_name}")

        logged_info, uc_info = log_and_register_model(
            config=config,
            model_code_path=model_code,
            validate=validate,
        )

        click.echo(click.style("\n✓ Model registered successfully!", fg="green"))
        click.echo(f"Run ID: {logged_info.run_id}")
        click.echo(f"Model: {config.uc.full_model_name}")
        click.echo(f"Version: {uc_info.version}")

        # Return success without calling sys.exit() for Databricks jobs
        return 0
    except Exception as e:
        click.echo(click.style(f"\n✗ Error: {e}", fg="red"), err=True)
        raise  # Re-raise to let Databricks handle it


@cli.command()
def config_show():
    """Show current configuration."""
    config = get_config()

    click.echo("Current Configuration:")
    click.echo("=" * 60)
    click.echo("\n[Model]")
    click.echo(f"  Endpoint: {config.model.endpoint_name}")
    click.echo(f"  System Prompt: {config.model.system_prompt[:50]}...")

    click.echo("\n[Databricks]")
    click.echo(f"  Profile: {config.databricks.profile}")
    click.echo(f"  Host: {config.databricks.host or 'auto-detected'}")

    click.echo("\n[Unity Catalog]")
    click.echo(f"  Model: {config.uc.full_model_name}")

    click.echo("\n[MLflow]")
    click.echo(f"  Experiment: {config.mlflow.experiment_name or 'not set'}")
    click.echo(f"  Autolog: {config.mlflow.enable_autolog}")

    click.echo("\n[MCP Servers]")
    click.echo(f"  Managed URLs: {len(config.mcp.managed_urls)} configured")
    click.echo(f"  Custom URLs: {len(config.mcp.custom_urls)} configured")

    click.echo("=" * 60)


@cli.command()
@click.option("--dataset", default="data/eval_dataset.json", help="Path to evaluation dataset JSON file")
@click.option("--catalog", default=None, help="Unity Catalog catalog name")
@click.option("--schema", default=None, help="Unity Catalog schema name")
@click.option("--table", default="agent_eval_dataset", help="Table name for the dataset")
def register_dataset(dataset: str, catalog: Optional[str], schema: Optional[str], table: str):
    """Register evaluation dataset to Unity Catalog."""
    click.echo("Registering dataset to Unity Catalog...")
    click.echo(f"  Source: {dataset}")

    try:
        full_table_name = register_eval_dataset_to_uc(
            dataset_path=dataset,
            catalog=catalog,
            schema=schema,
            table_name=table,
        )

        click.echo(click.style("\n✓ Dataset registered successfully!", fg="green"))
        click.echo(f"  Table: {full_table_name}")
        click.echo("\nTo use in jobs, evaluation will automatically load from Unity Catalog.")

    except Exception as e:
        click.echo(click.style(f"\n✗ Error: {e}", fg="red"), err=True)
        raise


def main():
    """Main CLI entry point."""
    # Use standalone_mode=False to prevent SystemExit in Databricks jobs
    cli(standalone_mode=False)


if __name__ == "__main__":
    main()
