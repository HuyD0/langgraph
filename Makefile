.PHONY: help test lint format clean

help:
	@echo "LangGraph MCP Agent - Development Commands"
	@echo "=========================================="
	@echo ""
	@echo "Development Commands:"
	@echo "  make test          Run all tests"
	@echo "  make test-unit     Run unit tests only"
	@echo "  make test-cov      Run tests with coverage"
	@echo "  make lint          Check code style"
	@echo "  make format        Auto-format code"
	@echo "  make clean         Clean build artifacts"
	@echo ""
	@echo "Databricks Bundle Commands:"
	@echo "  databricks bundle validate"
	@echo "  databricks bundle deploy -t dev"
	@echo "  databricks bundle deploy -t prod"
	@echo "  databricks bundle run agent_evaluation -t dev"
	@echo "  databricks bundle run agent_deployment -t dev"
	@echo "  databricks bundle destroy -t dev"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. uv sync --dev                    # Install dependencies"
	@echo "  2. databricks bundle validate       # Validate config"
	@echo "  3. databricks bundle deploy -t dev  # Deploy to dev"
	@echo ""

test:
	uv run pytest tests/ -v

test-unit:
	uv run pytest tests/unit/ -v

test-cov:
	uv run pytest tests/ --cov=langgraph_agent --cov-report=html --cov-report=term

lint:
	uv run ruff check src/
	uv run black --check src/

format:
	uv run black src/
	uv run ruff check --fix src/

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

.DEFAULT_GOAL := help
