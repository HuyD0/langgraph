"""Command-line interface for the LangGraph MCP agent."""

import os
from pathlib import Path
from typing import Optional

import click

from .models import get_config
from .core.agent import initialize_agent
from .deploy import full_deployment_pipeline, log_and_register_model
from .evaluate import run_evaluation_pipeline
from .utils.auth import get_workspace_client, verify_authentication
from .utils.mlflow_setup import setup_mlflow_tracking


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


@cli.command()
@click.option("--validate/--no-validate", default=True, help="Validate model before deployment")
@click.option("--profile", default=None, help="Databricks CLI profile")
def deploy(validate: bool, profile: Optional[str]):
    """Deploy the agent to Databricks serving endpoint."""
    config = get_config()
    if profile:
        config.databricks.profile = profile

    click.echo("Starting deployment pipeline...")

    deployment_result = full_deployment_pipeline(
        config=config,
        validate=validate,
    )

    click.echo(click.style("\n✓ Deployment successful!", fg="green"))
    click.echo(f"Model: {deployment_result['registered_model']['name']}")
    click.echo(f"Version: {deployment_result['registered_model']['version']}")
    click.echo(f"Deployment: {deployment_result['deployment']}")


@cli.command()
@click.option("--model-code", default="src/langgraph_agent/core/agent.py", help="Path to agent code")
@click.option("--validate/--no-validate", default=True, help="Validate model after logging")
@click.option("--profile", default=None, help="Databricks CLI profile")
def register(model_code: str, validate: bool, profile: Optional[str]):
    """Log and register model to Unity Catalog (without deployment)."""
    config = get_config()
    if profile:
        config.databricks.profile = profile

    click.echo("Logging and registering model...")

    logged_info, uc_info = log_and_register_model(
        config=config,
        model_code_path=model_code,
        validate=validate,
    )

    click.echo(click.style("\n✓ Model registered successfully!", fg="green"))
    click.echo(f"Run ID: {logged_info.run_id}")
    click.echo(f"Model: {config.uc.full_model_name}")
    click.echo(f"Version: {uc_info.version}")


@cli.command()
def config_show():
    """Show current configuration."""
    config = get_config()

    click.echo("Current Configuration:")
    click.echo("=" * 60)
    click.echo(f"\n[Model]")
    click.echo(f"  Endpoint: {config.model.endpoint_name}")
    click.echo(f"  System Prompt: {config.model.system_prompt[:50]}...")

    click.echo(f"\n[Databricks]")
    click.echo(f"  Profile: {config.databricks.profile}")
    click.echo(f"  Host: {config.databricks.host or 'auto-detected'}")

    click.echo(f"\n[Unity Catalog]")
    click.echo(f"  Model: {config.uc.full_model_name}")

    click.echo(f"\n[MLflow]")
    click.echo(f"  Experiment: {config.mlflow.experiment_name or 'not set'}")
    click.echo(f"  Autolog: {config.mlflow.enable_autolog}")

    click.echo(f"\n[MCP Servers]")
    click.echo(f"  Managed URLs: {len(config.mcp.managed_urls)} configured")
    click.echo(f"  Custom URLs: {len(config.mcp.custom_urls)} configured")

    click.echo("=" * 60)


def main():
    """Main CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
