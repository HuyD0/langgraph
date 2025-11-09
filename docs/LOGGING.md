# Logging System

This project uses a structured logging system for comprehensive debugging and monitoring.

## Features

- **Centralized Configuration**: Single logger manager for consistent logging across modules
- **Multiple Handlers**: Console and file logging support
- **Environment-based Levels**: Configure via `LOG_LEVEL` environment variable
- **MLflow Integration**: Automatic logging integration with MLflow tracking
- **Databricks Optimization**: Suppresses verbose third-party loggers

## Usage

### Basic Usage

```python
from langgraph_agent.utils.logging import get_logger

logger = get_logger(__name__)

logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Warning messages")
logger.error("Error messages")
logger.critical("Critical errors")
```

### Configuration

Set log level via environment variable:

```bash
export LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### File Logging

Enable file logging:

```python
from langgraph_agent.utils.logging import AgentLogger

logger = AgentLogger.get_logger(
    __name__, 
    level="DEBUG",
    log_file="/tmp/agent.log"
)
```

### MLflow Integration

Enable MLflow autologging:

```python
from langgraph_agent.utils.logging import AgentLogger

AgentLogger.setup_mlflow_logging(enable=True)
```

## Log Format

### Console (Simple)
```
INFO - Starting agent initialization
WARNING - Model validation skipped
ERROR - Failed to connect to MCP server
```

### File (Detailed)
```
2025-11-09 10:30:45 - langgraph_agent.app - INFO - create_agent:42 - Starting agent initialization
2025-11-09 10:30:46 - langgraph_agent.deploy - WARNING - log_and_register:68 - Model validation skipped
2025-11-09 10:30:47 - langgraph_agent.core.mcp_client - ERROR - connect:15 - Failed to connect to MCP server
```

## Logging in Different Modules

### app.py
- Agent initialization steps
- MCP tool creation
- Model configuration

### deploy.py
- Model logging progress
- Registration status
- Deployment steps

### mlflow_setup.py
- MLflow tracking setup
- Registry configuration
- Model validation

## Best Practices

1. **Use appropriate levels**:
   - `DEBUG`: Detailed diagnostic information
   - `INFO`: Confirmation of expected behavior
   - `WARNING`: Something unexpected but not critical
   - `ERROR`: Serious problem that prevented operation
   - `CRITICAL`: System-level failure

2. **Include context**:
   ```python
   logger.info(f"Processing request for user: {user_id}")
   logger.error(f"Failed to connect to {endpoint}: {error}")
   ```

3. **Don't log sensitive data**:
   ```python
   # ❌ Bad
   logger.info(f"API key: {api_key}")
   
   # ✅ Good
   logger.info("API key configured")
   ```

4. **Use structured logging**:
   ```python
   logger.info(
       "Model registered",
       extra={
           "model_name": model_name,
           "version": version,
           "run_id": run_id
       }
   )
   ```

## Databricks Environment

When running on Databricks, the logging system automatically:
- Suppresses verbose third-party loggers (databricks, urllib3, azure)
- Uses console output for notebook integration
- Integrates with MLflow tracking

## Troubleshooting

### Logs not appearing

Check log level:
```python
import os
print(os.getenv("LOG_LEVEL", "INFO"))
```

### Too verbose

Set higher log level:
```bash
export LOG_LEVEL=WARNING
```

### Debug a specific issue

Temporarily enable debug logging:
```python
from langgraph_agent.utils.logging import AgentLogger

AgentLogger.set_level("DEBUG")
```

## Examples

### Deployment Logging

```python
logger.info("Starting deployment pipeline")
logger.debug(f"Config: {config}")

try:
    result = deploy_model(config)
    logger.info(f"✓ Deployment successful: {result.endpoint}")
except Exception as e:
    logger.error(f"Deployment failed: {e}", exc_info=True)
```

### Agent Execution Logging

```python
logger.info("Agent received request")
logger.debug(f"Input: {request.input}")

start_time = time.time()
response = agent.predict(request)
duration = time.time() - start_time

logger.info(f"✓ Request completed in {duration:.2f}s")
logger.debug(f"Output: {response.output}")
```
