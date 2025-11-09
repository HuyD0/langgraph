"""Unit tests for configuration management."""

import os
from unittest.mock import patch

import pytest

from langgraph_agent.models import (
    AgentConfig,
    DatabricksConfig,
    MCPServerConfig,
    ModelConfig,
    UnityCatalogConfig,
)


def test_model_config_defaults():
    """Test ModelConfig default values."""
    config = ModelConfig()
    assert config.endpoint_name == "databricks-claude-3-7-sonnet"
    assert config.system_prompt == "You are a helpful AI assistant with access to various tools."


def test_databricks_config_defaults():
    """Test DatabricksConfig default values."""
    config = DatabricksConfig()
    assert config.profile == "development"
    assert config.host is None


def test_unity_catalog_config():
    """Test UnityCatalogConfig with full model name."""
    config = UnityCatalogConfig(catalog="test_catalog", schema="test_schema", model_name="test_model")
    assert config.full_model_name == "test_catalog.test_schema.test_model"


def test_mcp_server_config_defaults():
    """Test MCPServerConfig default values."""
    config = MCPServerConfig()
    assert config.managed_urls == []
    assert config.custom_urls == []


def test_agent_config_from_env():
    """Test AgentConfig loading from environment."""
    with patch.dict(
        os.environ,
        {
            "DATABRICKS_PROFILE": "test-profile",
            "MODEL_ENDPOINT_NAME": "test-endpoint",
            "UC_CATALOG": "test-catalog",
        },
    ):
        from langgraph_agent.models import get_config

        config = get_config()
        assert config.databricks.profile == "test-profile"
        assert config.model.endpoint_name == "test-endpoint"
        assert config.uc.catalog == "test-catalog"


def test_get_config():
    """Test get_config function."""
    from langgraph_agent.models import get_config

    config = get_config()
    assert isinstance(config, AgentConfig)
    assert isinstance(config.model, ModelConfig)
    assert isinstance(config.databricks, DatabricksConfig)
