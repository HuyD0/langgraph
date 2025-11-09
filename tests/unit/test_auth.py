"""Unit tests for authentication utilities."""

from unittest.mock import MagicMock, patch

import pytest

from langgraph_agent.utils.auth import (
    get_workspace_client,
    get_workspace_host,
    verify_authentication,
)


@patch("langgraph_agent.utils.auth.WorkspaceClient")
def test_get_workspace_client_with_profile(mock_ws):
    """Test getting workspace client with profile."""
    mock_instance = MagicMock()
    mock_ws.return_value = mock_instance

    client = get_workspace_client(profile="test-profile")

    mock_ws.assert_called_once_with(profile="test-profile")
    assert client == mock_instance


@patch("langgraph_agent.utils.auth.WorkspaceClient")
def test_get_workspace_client_without_profile(mock_ws):
    """Test getting workspace client without profile."""
    mock_instance = MagicMock()
    mock_ws.return_value = mock_instance

    client = get_workspace_client()

    mock_ws.assert_called_once_with()
    assert client == mock_instance


@patch("langgraph_agent.utils.auth.WorkspaceClient")
def test_get_workspace_client_auth_failure(mock_ws):
    """Test authentication failure handling."""
    mock_ws.side_effect = Exception("Auth failed")

    with pytest.raises(Exception) as exc_info:
        get_workspace_client()

    assert "Failed to authenticate" in str(exc_info.value)


def test_get_workspace_host():
    """Test getting workspace host from client."""
    mock_client = MagicMock()
    mock_client.config.host = "https://test.databricks.com"

    host = get_workspace_host(mock_client)

    assert host == "https://test.databricks.com"


@patch("langgraph_agent.utils.auth.get_workspace_client")
def test_verify_authentication(mock_get_client):
    """Test authentication verification."""
    mock_client = MagicMock()
    mock_client.config.host = "https://test.databricks.com"
    mock_client.config.auth_type = "oauth"
    mock_get_client.return_value = mock_client

    result = verify_authentication(profile="test-profile")

    assert result["host"] == "https://test.databricks.com"
    assert result["profile"] == "test-profile"
    assert result["auth_type"] == "oauth"
