"""Tests for Databricks environment detection and authentication."""

import os
import pytest
from unittest.mock import patch

from langgraph_agent.utils.auth import is_running_in_databricks


class TestDatabricksDetection:
    """Tests for detecting if code is running in Databricks."""

    def test_not_running_in_databricks_by_default(self):
        """Test that local environment is not detected as Databricks."""
        assert is_running_in_databricks() is False

    @patch.dict(os.environ, {"DATABRICKS_RUNTIME_VERSION": "13.3"})
    def test_detects_databricks_runtime_version(self):
        """Test detection via DATABRICKS_RUNTIME_VERSION."""
        assert is_running_in_databricks() is True

    @patch.dict(os.environ, {"DATABRICKS_HOST": "https://workspace.cloud.databricks.com"})
    def test_detects_databricks_host(self):
        """Test detection via DATABRICKS_HOST."""
        assert is_running_in_databricks() is True

    @patch.dict(os.environ, {"DB_DRIVER_IP": "10.0.0.1"})
    def test_detects_db_driver_ip(self):
        """Test detection via DB_DRIVER_IP."""
        assert is_running_in_databricks() is True

    @patch.dict(
        os.environ,
        {
            "DATABRICKS_RUNTIME_VERSION": "13.3",
            "DATABRICKS_HOST": "https://workspace.cloud.databricks.com",
            "DB_DRIVER_IP": "10.0.0.1",
        },
    )
    def test_detects_multiple_databricks_vars(self):
        """Test detection with multiple Databricks environment variables."""
        assert is_running_in_databricks() is True

    def test_no_false_positives(self):
        """Test that random environment variables don't trigger detection."""
        with patch.dict(os.environ, {"SOME_OTHER_VAR": "value"}, clear=True):
            assert is_running_in_databricks() is False
