"""Authentication utilities for Databricks."""

import os
from typing import Optional

from databricks.sdk import WorkspaceClient


def get_workspace_client(profile: Optional[str] = None) -> WorkspaceClient:
    """Get a Databricks workspace client with appropriate authentication.

    Authentication priority:
    1. If profile is provided, use CLI OAuth profile
    2. Environment variables (DATABRICKS_HOST, DATABRICKS_CLIENT_ID, DATABRICKS_CLIENT_SECRET)
    3. Default profile from ~/.databrickscfg
    4. Notebook context (when running in Databricks)

    Args:
        profile: Databricks CLI profile name (e.g., "development")

    Returns:
        Authenticated WorkspaceClient instance

    Raises:
        Exception: If authentication fails
    """
    try:
        if profile:
            # Use the specified profile (for local development)
            return WorkspaceClient(profile=profile)
        else:
            # Fall back to default authentication
            return WorkspaceClient()
    except Exception as e:
        raise Exception(
            f"Failed to authenticate with Databricks: {e}\n"
            "To fix, run: databricks auth login --host https://your-workspace.cloud.databricks.com"
        ) from e


def get_workspace_host(client: WorkspaceClient) -> str:
    """Get the workspace host URL from the client.

    Args:
        client: Authenticated WorkspaceClient

    Returns:
        Workspace host URL (e.g., "https://workspace.cloud.databricks.com")
    """
    return client.config.host


def verify_authentication(profile: Optional[str] = None) -> dict:
    """Verify Databricks authentication and return connection details.

    Args:
        profile: Databricks CLI profile name

    Returns:
        Dictionary with connection details (host, profile, auth_type)
    """
    client = get_workspace_client(profile)
    return {
        "host": client.config.host,
        "profile": profile or "default",
        "auth_type": client.config.auth_type,
    }
