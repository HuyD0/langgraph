# Configuration Packaging Fix

## Problem
Job failed with Pydantic validation error:
```
ValidationError: 2 validation errors for ModelConfig
endpoint_name: Input should be a valid string [type=string_type, input_value=None]
system_prompt: Input should be a valid string [type=string_type, input_value=None]
```

## Root Cause
The `configs/` folder with YAML configuration files was not being packaged into the wheel, causing:
1. `get_config_value()` to return `None` (no config files found)
2. Pydantic to reject `None` values for required string fields

## Solution

### 1. Moved Configs Into Package
```bash
mkdir -p src/langgraph_agent/configs/
cp configs/*.yaml src/langgraph_agent/configs/
```

Now configs are part of the package structure:
```
src/langgraph_agent/
├── configs/
│   ├── default.yaml
│   ├── dev.yaml
│   └── prod.yaml
├── utils/
│   └── config_loader.py
└── ...
```

### 2. Updated pyproject.toml
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/langgraph_agent"]
include = [
    "src/langgraph_agent/*.yaml", 
    "src/langgraph_agent/app.py",
    "src/langgraph_agent/configs/*.yaml"  # ← Added this
]
```

### 3. Updated config_loader.py Path Resolution
Changed to look for configs inside the package first:
```python
# First: langgraph_agent/configs/ (in installed wheel)
package_config = Path(__file__).parent.parent / "configs"

# Second: project/configs/ (local development)  
dev_config = Path(__file__).parent.parent.parent.parent / "configs"
```

### 4. Added Fallback Defaults
Updated `model_config.py` to provide hardcoded fallbacks:
```python
endpoint_name: str = Field(
    default_factory=lambda: get_config_value(
        _config, 
        "model.endpoint_name", 
        "MODEL_ENDPOINT_NAME", 
        "databricks-claude-3-7-sonnet"  # ← Fallback
    )
)
```

## Verification
```bash
# Check wheel contents
unzip -l dist/langgraph_mcp_agent-0.1.0-py3-none-any.whl | grep configs

# Output:
langgraph_agent/configs/default.yaml
langgraph_agent/configs/dev.yaml
langgraph_agent/configs/prod.yaml
```

## Benefits
1. ✅ Configs packaged with the wheel
2. ✅ Works in both local dev and deployed environments
3. ✅ Fallback defaults prevent validation errors
4. ✅ Configuration hierarchy still maintained
5. ✅ Both `configs/` locations work (project root + package)
