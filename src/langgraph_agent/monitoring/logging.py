"""Logging configuration for the LangGraph MCP Agent.

This module provides centralized logging configuration with support for:
- Console and file logging
- Structured logging with context
- Different log levels per environment
- MLflow integration
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import os


class AgentLogger:
    """Centralized logging manager for the agent."""

    _loggers = {}

    @classmethod
    def get_logger(
        cls,
        name: str,
        level: Optional[str] = None,
        log_file: Optional[str] = None,
    ) -> logging.Logger:
        """Get or create a logger with the specified configuration.

        Args:
            name: Logger name (usually __name__)
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for file logging

        Returns:
            Configured logger instance
        """
        if name in cls._loggers:
            return cls._loggers[name]

        # Create logger
        logger = logging.getLogger(name)

        # Determine log level
        if level is None:
            level = os.getenv("LOG_LEVEL", "INFO").upper()

        logger.setLevel(getattr(logging, level))

        # Remove existing handlers to avoid duplicates
        logger.handlers = []

        # Create formatters
        detailed_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        simple_formatter = logging.Formatter(
            fmt="%(levelname)s - %(message)s",
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            try:
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)

                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(detailed_formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"Failed to create file handler: {e}")

        # Prevent propagation to root logger
        logger.propagate = False

        cls._loggers[name] = logger
        return logger

    @classmethod
    def setup_mlflow_logging(cls, enable: bool = True) -> None:
        """Configure MLflow logging integration.

        Args:
            enable: Whether to enable MLflow autologging
        """
        if enable:
            try:
                import mlflow

                mlflow.langchain.autolog()
                logger = cls.get_logger(__name__)
                logger.info("MLflow autologging enabled")
            except Exception as e:
                logger = cls.get_logger(__name__)
                logger.warning(f"Failed to enable MLflow autologging: {e}")

    @classmethod
    def set_level(cls, level: str) -> None:
        """Set log level for all existing loggers.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_level = getattr(logging, level.upper())
        for logger in cls._loggers.values():
            logger.setLevel(log_level)


# Convenience function for quick logger access
def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (defaults to caller's module name)

    Returns:
        Configured logger instance
    """
    if name is None:
        import inspect

        frame = inspect.currentframe().f_back
        name = frame.f_globals["__name__"]

    return AgentLogger.get_logger(name)


# Configure logging for databricks environment
def configure_databricks_logging():
    """Configure logging for Databricks environment."""
    # Suppress overly verbose loggers
    logging.getLogger("databricks").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)

    # Set root logger level
    logging.getLogger().setLevel(logging.INFO)
