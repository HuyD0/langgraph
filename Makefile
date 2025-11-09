.PHONY: help test lint format clean build test-imports test-cli pre-deploy

help:
	@echo "LangGraph MCP Agent - Development Commands"
	@echo "=========================================="
	@echo ""
	@echo "Development Commands:"
	@echo "  make test          Run all tests"
	@echo "  make test-unit     Run unit tests only"
	@echo "  make test-cov      Run tests with coverage"
	@echo "  make test-imports  Test that all imports work"
	@echo "  make test-cli      Test CLI commands locally"
	@echo "  make pre-deploy    Run all pre-deployment checks"
	@echo "  make lint          Check code style"
	@echo "  make format        Auto-format code"
	@echo "  make build         Build the wheel package"
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

test-imports:
	@echo "Testing all module imports..."
	uv run python -c "from langgraph_agent import *; print('✓ Main package imports OK')"
	uv run python -c "from langgraph_agent.core.agent import *; print('✓ Agent imports OK')"
	uv run python -c "from langgraph_agent.evaluate import *; print('✓ Evaluate imports OK')"
	uv run python -c "from langgraph_agent.deploy import *; print('✓ Deploy imports OK')"
	uv run python -c "from langgraph_agent.cli import main; print('✓ CLI imports OK')"
	@echo "All imports successful!"

test-cli:
	@echo "Testing CLI commands..."
	uv run langgraph-agent --version
	uv run langgraph-agent --help
	@echo "CLI is working!"

build:
	uv build --wheel
	@echo "Wheel built successfully in dist/"

pre-deploy:
	@./scripts/deployment/pre_deploy_check.sh

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
