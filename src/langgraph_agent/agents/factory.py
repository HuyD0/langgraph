"""Agent factory for creating initialized agents."""

import asyncio

from databricks.sdk import WorkspaceClient
from databricks_langchain import ChatDatabricks

from .graph import create_tool_calling_agent
from .responses import LangGraphResponsesAgent
from ..integrations.mcp import create_mcp_tools
from ..monitoring.logging import get_logger

logger = get_logger(__name__)


def initialize_agent(
    workspace_client: WorkspaceClient,
    llm_endpoint_name: str,
    system_prompt: str,
    managed_mcp_urls: list = None,
    custom_mcp_urls: list = None,
) -> LangGraphResponsesAgent:
    """Initialize the complete agent with MCP tools.

    Args:
        workspace_client: Authenticated WorkspaceClient
        llm_endpoint_name: Name of the LLM serving endpoint
        system_prompt: System prompt for the agent
        managed_mcp_urls: List of managed MCP server URLs
        custom_mcp_urls: List of custom MCP server URLs

    Returns:
        Initialized LangGraphResponsesAgent
    """
    logger.info(f"Initializing agent with endpoint: {llm_endpoint_name}")

    # Create LLM
    llm = ChatDatabricks(endpoint=llm_endpoint_name)
    logger.info("✓ LLM client created")

    # Create MCP tools from the configured servers
    logger.info("Creating MCP tools...")
    mcp_tools = asyncio.run(
        create_mcp_tools(
            ws=workspace_client,
            managed_server_urls=managed_mcp_urls or [],
            custom_server_urls=custom_mcp_urls or [],
        )
    )
    logger.info(f"✓ Created {len(mcp_tools)} MCP tools")

    # Create the agent graph with an LLM, tool set, and system prompt
    logger.info("Building agent graph...")
    agent = create_tool_calling_agent(llm, mcp_tools, system_prompt)
    logger.info("✓ Agent initialization complete")
    return LangGraphResponsesAgent(agent)
