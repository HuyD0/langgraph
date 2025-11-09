"""Unit tests for deployment scripts.

These tests verify that the deployment script entry points are properly configured
and can be imported without errors.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestDeploymentScripts:
    """Test deployment script entry points."""

    def test_register_model_import(self):
        """Test that register_model script can be imported."""
        from scripts.deployment import register_model

        assert hasattr(register_model, "main")
        assert callable(register_model.main)

    def test_evaluate_model_import(self):
        """Test that evaluate_model script can be imported."""
        from scripts.deployment import evaluate_model

        assert hasattr(evaluate_model, "main")
        assert callable(evaluate_model.main)

    def test_deploy_model_import(self):
        """Test that deploy_model script can be imported."""
        from scripts.deployment import deploy_model

        assert hasattr(deploy_model, "main")
        assert callable(deploy_model.main)

    @patch("scripts.deployment.register_model.get_config")
    @patch("scripts.deployment.register_model.log_and_register_model")
    @patch.dict("os.environ", {"EXPERIMENT_NAME": "/test/experiment"})
    def test_register_model_with_env_var(self, mock_log_register, mock_get_config):
        """Test register_model uses environment variables."""
        from scripts.deployment.register_model import main

        # Setup mock config
        mock_config = MagicMock()
        mock_config.mlflow.experiment_name = "/default/experiment"
        mock_config.uc.full_model_name = "catalog.schema.model"
        mock_get_config.return_value = mock_config

        # Setup mock return values
        mock_logged_info = MagicMock()
        mock_logged_info.run_id = "test_run_id"
        mock_uc_info = MagicMock()
        mock_uc_info.version = "1"
        mock_log_register.return_value = (mock_logged_info, mock_uc_info)

        # Run the main function
        result = main([])

        # Verify environment variable was used
        assert mock_config.mlflow.experiment_name == "/test/experiment"
        assert result == 0

    @patch("scripts.deployment.deploy_model.get_config")
    @patch("scripts.deployment.deploy_model.full_deployment_pipeline")
    @patch.dict("os.environ", {"CATALOG": "test_catalog", "SCHEMA": "test_schema", "MODEL_NAME": "test_model"})
    def test_deploy_model_with_env_vars(self, mock_pipeline, mock_get_config):
        """Test deploy_model uses environment variables for UC settings."""
        from scripts.deployment.deploy_model import main

        # Setup mock config
        mock_config = MagicMock()
        mock_config.uc.catalog = "default_catalog"
        mock_config.uc.schema_name = "default_schema"
        mock_config.uc.model_name = "default_model"
        mock_config.uc.full_model_name = "test_catalog.test_schema.test_model"
        mock_get_config.return_value = mock_config

        # Setup mock return values
        mock_pipeline.return_value = {
            "registered_model": {"name": "test_catalog.test_schema.test_model", "version": "1"},
            "deployment": {"endpoint": "test_endpoint"},
        }

        # Run the main function
        result = main([])

        # Verify environment variables were used
        assert mock_config.uc.catalog == "test_catalog"
        assert mock_config.uc.schema_name == "test_schema"
        assert mock_config.uc.model_name == "test_model"
        assert result == 0

    @patch("scripts.deployment.register_model.get_config")
    @patch("scripts.deployment.register_model.log_and_register_model")
    def test_register_model_handles_exceptions(self, mock_log_register, mock_get_config):
        """Test register_model handles exceptions properly."""
        from scripts.deployment.register_model import main

        # Setup mock to raise exception
        mock_get_config.side_effect = Exception("Config error")

        # Verify exception is raised (not caught)
        with pytest.raises(Exception, match="Config error"):
            main([])
