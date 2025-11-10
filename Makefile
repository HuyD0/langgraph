.PHONY: help test lint format clean build test-imports test-cli validate-agent validate-agent-interactive pre-deploy verify bundle-validate

help:
	@echo "LangGraph MCP Agent - Development Commands"
	@echo "=========================================="
	@echo ""
	@echo "Development Commands:"
	@echo "  make test               Run all tests"
	@echo "  make test-unit          Run unit tests only"
	@echo "  make test-cov           Run tests with coverage"
	@echo "  make test-imports       Test that all imports work"
	@echo "  make test-cli           Test CLI commands locally"
	@echo "  make test-scripts       Test deployment scripts locally"
	@echo "  make validate-agent     Validate agent with single query"
	@echo "  make validate-agent-interactive  Validate agent in interactive mode"
	@echo ""
	@echo "Deployment Commands:"
	@echo "  make deploy-dev         Deploy to development environment"
	@echo "  make run-pipeline       Run the registration & validation pipeline"
	@echo "  make run-deploy         Run the deployment job"
	@echo "  make verify             Run all pre-deployment checks (build + lint + test + bundle validate)"
	@echo "  make verify-all         Run comprehensive checks (scripts + imports + tests + bundle)"
	@echo "  make pre-deploy         Run pre-deployment script checks"
	@echo "  make bundle-validate    Validate Databricks bundle configuration"
	@echo "  make build              Build the wheel package"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint               Check code style"
	@echo "  make format             Auto-format code"
	@echo "  make clean              Clean build artifacts"
	@echo ""
	@echo "Databricks Bundle Commands:"
	@echo "  databricks bundle validate -t dev"
	@echo "  databricks bundle deploy -t dev"
	@echo "  databricks bundle deploy -t prod"
	@echo "  databricks bundle run agent_deployment_pipeline -t dev  # Register & validate model"
	@echo "  databricks bundle run agent_deploy -t dev              # Deploy to serving"
	@echo "  databricks bundle run agent_evaluation -t dev          # Run evaluation"
	@echo "  databricks bundle destroy -t dev"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. uv sync --dev                    # Install dependencies"
	@echo "  2. make verify                      # Run all checks"
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
	uv run python -c "from langgraph_agent.agents import *; print('✓ Agents imports OK')"
	uv run python -c "from langgraph_agent.pipelines.deployment import *; print('✓ Deployment imports OK')"
	uv run python -c "from langgraph_agent.pipelines.evaluation import *; print('✓ Evaluation imports OK')"
	uv run python -c "from langgraph_agent.cli import main; print('✓ CLI imports OK')"
	uv run python -c "from scripts.deployment import register_model, evaluate_model, deploy_model; print('✓ Deployment scripts imports OK')"
	@echo "All imports successful!"

test-cli:
	@echo "Testing CLI commands..."
	uv run langgraph-agent --version
	uv run langgraph-agent --help
	uv run langgraph-agent config-show
	@echo "CLI is working!"

test-scripts:
	@echo "Testing deployment script entry points..."
	@echo "Note: These will fail without proper Databricks auth and config"
	uv run python -c "from scripts.deployment.register_model import main; print('✓ register_model entry point OK')"
	uv run python -c "from scripts.deployment.evaluate_model import main; print('✓ evaluate_model entry point OK')"
	uv run python -c "from scripts.deployment.deploy_model import main; print('✓ deploy_model entry point OK')"
	@echo "All script entry points validated!"

validate-agent:
	@echo "Validating agent with default query..."
	uv run python scripts/validate_agent.py

validate-agent-interactive:
	@echo "Starting agent in interactive mode..."
	uv run python scripts/validate_agent.py --interactive

build:
	uv build --wheel
	@echo "Wheel built successfully in dist/"

bundle-validate:
	@echo "Validating Databricks bundle configuration..."
	databricks bundle validate -t dev

verify: clean build lint test bundle-validate
	@echo ""
	@echo "=========================================="
	@echo "✅ All verification checks passed!"
	@echo "=========================================="
	@echo "Ready to deploy with: databricks bundle deploy -t dev"
	@echo ""

verify-all: test-scripts test-imports test bundle-validate
	@echo ""
	@echo "=========================================="
	@echo "✅ All comprehensive checks passed!"
	@echo "=========================================="
	@echo "  ✓ Script entry points validated"
	@echo "  ✓ All imports working"
	@echo "  ✓ Test suite passed"
	@echo "  ✓ Bundle configuration valid"
	@echo ""
	@echo "Ready to deploy with: databricks bundle deploy -t dev"
	@echo ""

pre-deploy:
	@./scripts/deployment/pre_deploy_check.sh

deploy-dev: verify
	@echo "Deploying to development environment..."
	databricks bundle deploy -t dev
	@echo "✓ Deployment complete!"

run-pipeline:
	@echo "Running agent_log_register pipeline (register & validate)..."
	databricks bundle run agent_log_register -t dev

run-deploy:
	@echo "Running agent_deploy job..."
	@echo "Note: Ensure model is registered first with 'make run-pipeline'"
	databricks bundle run agent_deploy -t dev

lint:
	uv run ruff check src/
	uv run black --check src/

format:
	uv run black src/
	uv run ruff check --fix src/

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache/ .ruff_cache/ .coverage htmlcov/
	rm -rf mlruns/.trash/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✓ Cleaned all build artifacts and cache files"

.DEFAULT_GOAL := help
