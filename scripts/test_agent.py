#!/usr/bin/env python3
"""Quick test script for the agent."""

import os
from langgraph_agent import get_config, initialize_agent
from langgraph_agent.utils import get_workspace_client
from langgraph_agent.utils.logging import get_logger

# Set debug logging for this test
os.environ.setdefault("LOG_LEVEL", "DEBUG")

logger = get_logger(__name__)


def main():
    """Test the agent with a simple query."""
    logger.info("Loading configuration...")
    config = get_config()

    logger.info(f"Initializing agent (profile: {config.databricks.profile})...")
    ws = get_workspace_client(config.databricks.profile)

    # Build MCP server URLs
    ws_host = ws.config.host
    managed_urls = config.mcp.managed_urls or [f"{ws_host}/api/2.0/mcp/functions/system/ai"]
    logger.debug(f"Managed MCP URLs: {managed_urls}")

    agent = initialize_agent(
        workspace_client=ws,
        llm_endpoint_name=config.model.endpoint_name,
        system_prompt=config.model.system_prompt,
        managed_mcp_urls=managed_urls,
        custom_mcp_urls=config.mcp.custom_urls,
    )

    logger.info("✓ Agent initialized!\n")

    # Test with a simple query
    test_query = "What is 7 multiplied by 6 in Python?"
    logger.info(f"Testing with query: {test_query}")
    print("-" * 60)

    response = agent.predict({"input": [{"role": "user", "content": test_query}]})

    print("\nResponse:")
    print(response)
    print("-" * 60)
    logger.info("✓ Test complete!")


if __name__ == "__main__":
    main()
