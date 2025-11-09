#!/bin/bash
# Pre-deployment validation script
# Run this before deploying to Databricks to catch errors early

set -e  # Exit on error

echo "=================================="
echo "Pre-Deployment Validation Checks"
echo "=================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        exit 1
    fi
}

# 1. Check code formatting
echo "1. Checking code formatting..."
make lint > /dev/null 2>&1
print_status "Code formatting checks passed"

# 2. Test imports
echo "2. Testing module imports..."
uv run python -c "from langgraph_agent import *" 2>/dev/null
print_status "Main package imports"

uv run python -c "from langgraph_agent.agents import *" 2>/dev/null
print_status "Agent module imports"

uv run python -c "from langgraph_agent.pipelines.evaluation import *" 2>/dev/null
print_status "Evaluation pipeline imports"

uv run python -c "from langgraph_agent.pipelines.deployment import *" 2>/dev/null
print_status "Deployment pipeline imports"

uv run python -c "from langgraph_agent.data import *" 2>/dev/null
print_status "Data module imports"

uv run python -c "from langgraph_agent.integrations import *" 2>/dev/null
print_status "Integrations module imports"

uv run python -c "from langgraph_agent.monitoring.logging import *" 2>/dev/null
print_status "Monitoring module imports"

uv run python -c "from langgraph_agent.cli import main" 2>/dev/null
print_status "CLI module imports"

# 3. Test CLI functionality
echo ""
echo "3. Testing CLI functionality..."
uv run langgraph-agent --version > /dev/null 2>&1
print_status "CLI version command"

uv run langgraph-agent --help > /dev/null 2>&1
print_status "CLI help command"

# 4. Build wheel
echo ""
echo "4. Building wheel package..."
uv build --wheel > /dev/null 2>&1
print_status "Wheel build successful"

# 5. Check wheel contents
echo ""
echo "5. Validating wheel package..."
WHEEL_FILE=$(ls -t dist/*.whl | head -n 1)
if [ -f "$WHEEL_FILE" ]; then
    echo -e "${GREEN}✓${NC} Wheel file found: $(basename $WHEEL_FILE)"
    
    # Check if wheel contains the console script
    unzip -l "$WHEEL_FILE" | grep -q "langgraph_mcp_agent"
    print_status "Console script entry point found in wheel"
else
    echo -e "${RED}✗${NC} No wheel file found in dist/"
    exit 1
fi

# 6. Run unit tests
echo ""
echo "6. Running unit tests..."
make test-unit > /dev/null 2>&1
print_status "Unit tests passed"

# 7. Validate Databricks bundle
echo ""
echo "7. Validating Databricks bundle configuration..."
databricks bundle validate -t dev > /dev/null 2>&1
print_status "Databricks bundle validation passed"

echo ""
echo "=================================="
echo -e "${GREEN}All pre-deployment checks passed!${NC}"
echo "=================================="
echo ""
echo "You can now safely run:"
echo "  databricks bundle deploy -t dev"
