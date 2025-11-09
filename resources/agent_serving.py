"""Agent deployment and serving resources for Databricks Asset Bundles."""

from databricks.sdk.service.serving import (
    EndpointCoreConfigInput,
    ServedEntityInput,
    EndpointTag,
)


def get_agent_serving_endpoint(bundle):
    """Define the agent serving endpoint resource.

    This creates a serverless model serving endpoint for the LangGraph MCP agent
    registered in Unity Catalog.
    """
    catalog = bundle.variables.get("catalog", "rag")
    schema = bundle.variables.get("schema", "development")
    model_name = bundle.variables.get("model_name", "langgraph_mcp_agent")

    return {
        "name": f"{catalog}_{schema}_{model_name}_endpoint",
        "config": EndpointCoreConfigInput(
            name=f"{catalog}_{schema}_{model_name}_endpoint",
            served_entities=[
                ServedEntityInput(
                    entity_name=f"{catalog}.{schema}.{model_name}",
                    entity_version="1",  # Start with version 1, update as needed
                    scale_to_zero_enabled=True,
                    # Serverless endpoints don't require workload_size
                )
            ],
            tags=[
                EndpointTag(key="project", value="langgraph-mcp-agent"),
                EndpointTag(key="deployed_by", value="databricks-asset-bundle"),
                EndpointTag(key="environment", value=bundle.target),
                EndpointTag(key="compute_type", value="serverless"),
            ],
        ),
    }
