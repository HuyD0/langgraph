# Testing Strategy

This project uses a two-tier testing approach to ensure code quality while avoiding dependency on live Databricks authentication.

## Test Organization

### Unit Tests (`tests/unit/`)
- Fast, isolated tests for individual components
- No external dependencies
- Test configuration models, utility functions, and business logic
- Run automatically in CI/CD pipelines

### Integration Tests (`tests/integration/`)
- Tests agent creation and initialization with mocked dependencies
- Verifies component integration without requiring authentication
- Uses `unittest.mock` to simulate Databricks services
- Safe to run in CI/CD environments

### Manual Testing (`scripts/validate_agent.py`)
- For testing against live Databricks endpoints
- Requires Databricks authentication
- Provides interactive and batch testing modes
- Used by developers for validation with real services

## Running Tests

### Automated Tests (No Authentication Required)
```bash
# Run all unit and integration tests
make test
# or
uv run pytest tests/

# Run only integration tests
uv run pytest tests/integration/ -v

# Run only unit tests
uv run pytest tests/unit/ -v
```

### Manual Testing (Requires Authentication)
```bash
# Single query test
make validate-agent
# or
uv run python scripts/validate_agent.py --query "What is 7*6?"

# Interactive chat mode
make validate-agent-interactive
# or
uv run python scripts/validate_agent.py --interactive

# Batch testing
uv run python scripts/validate_agent.py --batch

# With specific profile
uv run python scripts/validate_agent.py --profile <profile-name> --interactive
```

## Authentication Setup for Manual Testing

Before running `scripts/validate_agent.py`, ensure you have Databricks authentication configured:

**Option 1: Databricks CLI Profile**
```bash
databricks auth login --host <your-workspace-url>
```

**Option 2: Environment Variables**
```bash
export DATABRICKS_HOST=<your-workspace-url>
export DATABRICKS_TOKEN=<your-token>
```

**Option 3: Configuration File**
Create or update `~/.databrickscfg`:
```ini
[DEFAULT]
host = <your-workspace-url>
token = <your-token>
```

## Test Coverage

- **Unit Tests**: Configuration models, utilities, authentication detection
- **Integration Tests**: Agent creation, tool binding, ResponsesAgent wrapper
- **Manual Tests**: End-to-end agent queries with live LLM and tools

## Why This Approach?

1. **CI/CD Friendly**: Automated tests don't require secrets or authentication
2. **Fast Feedback**: Unit and integration tests run in <1 second
3. **Real Validation**: Manual testing script validates against actual Databricks services
4. **Developer Experience**: Interactive mode provides immediate feedback during development
5. **Security**: No credentials stored in code or test files

## Adding New Tests

### For New Features (Use Automated Tests)
Add tests to `tests/unit/` or `tests/integration/` that use mocks:

```python
from unittest.mock import Mock, patch
from langgraph_agent.agents.graph import create_tool_calling_agent

def test_my_feature():
    mock_llm = Mock()
    mock_llm.bind_tools = Mock(return_value=mock_llm)
    
    agent = create_tool_calling_agent(
        model=mock_llm,
        tools=[],
        system_prompt="Test"
    )
    
    assert agent is not None
```

### For Live Validation (Use Manual Script)
Use `scripts/validate_agent.py` for validation against real services. Add test queries to `DEFAULT_TEST_QUERIES` if needed.

## Test Exclusions

The following test class is marked as skipped because it requires live authentication:

- `TestAgentLiveIntegration` in `tests/integration/test_agent_creation.py`

These tests serve as documentation but won't run automatically. Use `scripts/validate_agent.py` instead for live testing.
