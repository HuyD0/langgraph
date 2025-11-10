"""Unit tests for MLflow Prompt Registry integration."""

import os
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from langgraph_agent.models import ModelConfig
from langgraph_agent.utils.mlflow_setup import load_prompt_from_registry


class TestModelConfigPromptRegistry:
    """Test ModelConfig with prompt registry settings."""

    def test_model_config_prompt_registry_defaults(self):
        """Test that prompt registry is enabled by default."""
        config = ModelConfig()
        assert config.use_prompt_registry is True
        assert config.prompt_name == "agent-system-prompt"
        assert config.prompt_version == "latest"

    def test_model_config_with_prompt_registry_enabled(self):
        """Test ModelConfig with prompt registry enabled via environment."""
        with patch.dict(
            os.environ,
            {
                "USE_PROMPT_REGISTRY": "true",
                "PROMPT_NAME": "test-prompt",
                "PROMPT_VERSION": "production",
            },
        ):
            # Need to reload module to pick up env changes
            from importlib import reload
            from langgraph_agent.models import model_config

            reload(model_config)

            config = model_config.ModelConfig()
            assert config.use_prompt_registry is True
            assert config.prompt_name == "test-prompt"
            assert config.prompt_version == "production"

    def test_model_config_prompt_version_as_int(self):
        """Test ModelConfig with integer prompt version."""
        with patch.dict(
            os.environ,
            {
                "PROMPT_VERSION": "2",
            },
        ):
            from importlib import reload
            from langgraph_agent.models import model_config

            reload(model_config)

            config = model_config.ModelConfig()
            # Should accept string "2" which can be converted to int
            assert config.prompt_version in ["2", 2]


class TestLoadPromptFromRegistry:
    """Test load_prompt_from_registry function."""

    @patch("langgraph_agent.utils.mlflow_setup.mlflow.genai.load_prompt")
    def test_load_latest_version(self, mock_load_prompt):
        """Test loading latest version of a prompt."""
        # Mock the prompt object
        mock_prompt = MagicMock()
        mock_prompt.is_text_prompt = True
        mock_prompt.template = "You are a helpful assistant."
        mock_load_prompt.return_value = mock_prompt

        result = load_prompt_from_registry("test-prompt")

        assert result == "You are a helpful assistant."
        mock_load_prompt.assert_called_once_with("prompts:/test-prompt")

    @patch("langgraph_agent.utils.mlflow_setup.mlflow.genai.load_prompt")
    def test_load_specific_version(self, mock_load_prompt):
        """Test loading a specific version number."""
        mock_prompt = MagicMock()
        mock_prompt.is_text_prompt = True
        mock_prompt.template = "You are a helpful assistant v2."
        mock_load_prompt.return_value = mock_prompt

        result = load_prompt_from_registry("test-prompt", prompt_version=2)

        assert result == "You are a helpful assistant v2."
        mock_load_prompt.assert_called_once_with("prompts:/test-prompt/2")

    @patch("langgraph_agent.utils.mlflow_setup.mlflow.genai.load_prompt")
    def test_load_by_alias(self, mock_load_prompt):
        """Test loading a prompt by alias."""
        mock_prompt = MagicMock()
        mock_prompt.is_text_prompt = True
        mock_prompt.template = "Production prompt."
        mock_load_prompt.return_value = mock_prompt

        result = load_prompt_from_registry("test-prompt", prompt_version="production")

        assert result == "Production prompt."
        mock_load_prompt.assert_called_once_with("prompts:/test-prompt@production")

    @patch("langgraph_agent.utils.mlflow_setup.mlflow.genai.load_prompt")
    def test_load_chat_prompt_with_system_message(self, mock_load_prompt):
        """Test loading a chat-style prompt with system message."""
        mock_prompt = MagicMock()
        mock_prompt.is_text_prompt = False
        mock_prompt.template = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "{{question}}"},
        ]
        mock_load_prompt.return_value = mock_prompt

        result = load_prompt_from_registry("test-prompt")

        assert result == "You are a helpful assistant."

    @patch("langgraph_agent.utils.mlflow_setup.mlflow.genai.load_prompt")
    def test_load_chat_prompt_without_system_message(self, mock_load_prompt):
        """Test loading a chat prompt without system message."""
        mock_prompt = MagicMock()
        mock_prompt.is_text_prompt = False
        mock_prompt.template = [
            {"role": "user", "content": "First message content"},
        ]
        mock_load_prompt.return_value = mock_prompt

        result = load_prompt_from_registry("test-prompt")

        # Should fall back to first message content
        assert result == "First message content"

    @patch("langgraph_agent.utils.mlflow_setup.mlflow.genai.load_prompt")
    def test_load_prompt_with_fallback_on_error(self, mock_load_prompt):
        """Test fallback when prompt loading fails."""
        mock_load_prompt.side_effect = Exception("Prompt not found")

        fallback = "Fallback prompt text"
        result = load_prompt_from_registry("test-prompt", fallback_prompt=fallback)

        assert result == fallback

    @patch("langgraph_agent.utils.mlflow_setup.mlflow.genai.load_prompt")
    def test_load_prompt_raises_without_fallback(self, mock_load_prompt):
        """Test that exception is raised when no fallback provided."""
        mock_load_prompt.side_effect = Exception("Prompt not found")

        with pytest.raises(Exception, match="Prompt not found"):
            load_prompt_from_registry("test-prompt")

    @patch("langgraph_agent.utils.mlflow_setup.mlflow.genai.load_prompt")
    def test_load_prompt_with_latest_string(self, mock_load_prompt):
        """Test loading with 'latest' as version string."""
        mock_prompt = MagicMock()
        mock_prompt.is_text_prompt = True
        mock_prompt.template = "Latest prompt."
        mock_load_prompt.return_value = mock_prompt

        result = load_prompt_from_registry("test-prompt", prompt_version="latest")

        assert result == "Latest prompt."
        # Should use the simple URI format for "latest"
        mock_load_prompt.assert_called_once_with("prompts:/test-prompt")

    @patch("langgraph_agent.utils.mlflow_setup.mlflow.genai.load_prompt")
    def test_load_empty_chat_prompt(self, mock_load_prompt):
        """Test loading an empty chat prompt."""
        mock_prompt = MagicMock()
        mock_prompt.is_text_prompt = False
        mock_prompt.template = []
        mock_load_prompt.return_value = mock_prompt

        result = load_prompt_from_registry("test-prompt")

        # Should return empty string for empty template
        assert result == ""


class TestPromptRegistryIntegration:
    """Integration tests for prompt registry with agent creation."""

    @pytest.mark.skip(reason="Requires full Databricks environment setup")
    @patch("langgraph_agent.app.load_prompt_from_registry")
    @patch("langgraph_agent.app.WorkspaceClient")
    @patch("langgraph_agent.app.create_mcp_tools")
    @patch("langgraph_agent.app.ChatDatabricks")
    def test_create_agent_with_prompt_registry_enabled(self, mock_chat_db, mock_mcp_tools, mock_workspace, mock_load_prompt):
        """Test that create_agent loads from registry when enabled."""
        from langgraph_agent.app import create_agent
        from langgraph_agent.utils.config_loader import get_cached_config

        # Mock workspace client
        mock_workspace.return_value = MagicMock()

        # Mock MCP tools
        mock_mcp_tools.return_value = []

        # Mock ChatDatabricks
        mock_chat_db.return_value = MagicMock()

        # Mock prompt registry
        mock_load_prompt.return_value = "Registry prompt text"

        # Mock config to enable prompt registry
        with patch("langgraph_agent.app.get_config_value") as mock_get_config:

            def config_side_effect(config, key, default=None):
                config_map = {
                    "model.endpoint_name": "test-endpoint",
                    "model.use_prompt_registry": True,
                    "model.prompt_name": "test-prompt",
                    "model.prompt_version": "production",
                    "model.system_prompt": "fallback prompt",
                }
                return config_map.get(key, default)

            mock_get_config.side_effect = config_side_effect

            # Create agent
            agent = create_agent()

            # Verify prompt was loaded from registry
            mock_load_prompt.assert_called_once_with(
                prompt_name="test-prompt",
                prompt_version="production",
                fallback_prompt="fallback prompt",
            )

    @pytest.mark.skip(reason="Requires full Databricks environment setup")
    @patch("langgraph_agent.app.load_prompt_from_registry")
    @patch("langgraph_agent.app.WorkspaceClient")
    @patch("langgraph_agent.app.create_mcp_tools")
    @patch("langgraph_agent.app.ChatDatabricks")
    def test_create_agent_with_prompt_registry_disabled(
        self, mock_chat_db, mock_mcp_tools, mock_workspace, mock_load_prompt
    ):
        """Test that create_agent uses config prompt when registry disabled."""
        from langgraph_agent.app import create_agent

        # Mock workspace client
        mock_workspace.return_value = MagicMock()

        # Mock MCP tools
        mock_mcp_tools.return_value = []

        # Mock ChatDatabricks
        mock_chat_db.return_value = MagicMock()

        # Mock config to disable prompt registry
        with patch("langgraph_agent.app.get_config_value") as mock_get_config:

            def config_side_effect(config, key, default=None):
                config_map = {
                    "model.endpoint_name": "test-endpoint",
                    "model.use_prompt_registry": False,
                    "model.system_prompt": "config prompt text",
                }
                return config_map.get(key, default)

            mock_get_config.side_effect = config_side_effect

            # Create agent
            agent = create_agent()

            # Verify prompt was NOT loaded from registry
            mock_load_prompt.assert_not_called()

    @pytest.mark.skip(reason="Requires full Databricks environment setup")
    @patch("langgraph_agent.app.load_prompt_from_registry")
    @patch("langgraph_agent.app.WorkspaceClient")
    @patch("langgraph_agent.app.create_mcp_tools")
    @patch("langgraph_agent.app.ChatDatabricks")
    def test_create_agent_with_prompt_override(self, mock_chat_db, mock_mcp_tools, mock_workspace, mock_load_prompt):
        """Test that explicit system_prompt parameter overrides registry."""
        from langgraph_agent.app import create_agent

        # Mock workspace client
        mock_workspace.return_value = MagicMock()

        # Mock MCP tools
        mock_mcp_tools.return_value = []

        # Mock ChatDatabricks
        mock_chat_db.return_value = MagicMock()

        with patch("langgraph_agent.app.get_config_value") as mock_get_config:

            def config_side_effect(config, key, default=None):
                config_map = {
                    "model.endpoint_name": "test-endpoint",
                    "model.use_prompt_registry": True,
                    "model.prompt_name": "test-prompt",
                }
                return config_map.get(key, default)

            mock_get_config.side_effect = config_side_effect

            # Create agent with explicit prompt
            agent = create_agent(system_prompt="Override prompt")

            # Verify prompt registry was NOT called (explicit override takes precedence)
            mock_load_prompt.assert_not_called()


class TestPromptRegistryErrorHandling:
    """Test error handling scenarios for prompt registry."""

    @patch("langgraph_agent.utils.mlflow_setup.mlflow.genai.load_prompt")
    def test_malformed_prompt_template(self, mock_load_prompt):
        """Test handling of malformed prompt templates."""
        mock_prompt = MagicMock()
        mock_prompt.is_text_prompt = False
        # Malformed: message without 'content' key
        mock_prompt.template = [
            {"role": "system"},  # Missing 'content'
        ]
        mock_load_prompt.return_value = mock_prompt

        result = load_prompt_from_registry("test-prompt", fallback_prompt="fallback")

        # Should return empty string for malformed template (no content key)
        assert result == ""

    @patch("langgraph_agent.utils.mlflow_setup.mlflow.genai.load_prompt")
    def test_network_error_with_fallback(self, mock_load_prompt):
        """Test network error handling with fallback."""
        mock_load_prompt.side_effect = ConnectionError("Network unavailable")

        result = load_prompt_from_registry("test-prompt", fallback_prompt="fallback text")

        assert result == "fallback text"

    @patch("langgraph_agent.utils.mlflow_setup.mlflow.genai.load_prompt")
    def test_permission_error(self, mock_load_prompt):
        """Test permission error handling."""
        mock_load_prompt.side_effect = PermissionError("Access denied")

        with pytest.raises(PermissionError, match="Access denied"):
            load_prompt_from_registry("test-prompt")
