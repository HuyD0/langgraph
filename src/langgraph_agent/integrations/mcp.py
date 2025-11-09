"""MCP (Model Context Protocol) client integration."""

from typing import List

from databricks.sdk import WorkspaceClient
from databricks_mcp import DatabricksMCPClient, DatabricksOAuthClientProvider
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client as connect
from pydantic import create_model

from langgraph_agent.monitoring.logging import get_logger

from .tools import MCPTool

logger = get_logger(__name__)


async def get_custom_mcp_tools(ws: WorkspaceClient, server_url: str):
    """Get tools from a custom MCP server using OAuth.

    Args:
        ws: Authenticated WorkspaceClient
        server_url: URL of the custom MCP server

    Returns:
        List of MCP tool definitions
    """
    async with connect(server_url, auth=DatabricksOAuthClientProvider(ws)) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools_response = await session.list_tools()
            return tools_response.tools


def get_managed_mcp_tools(ws: WorkspaceClient, server_url: str):
    """Get tools from a managed MCP server.

    Args:
        ws: Authenticated WorkspaceClient
        server_url: URL of the managed MCP server

    Returns:
        List of MCP tool definitions
    """
    mcp_client = DatabricksMCPClient(server_url=server_url, workspace_client=ws)
    return mcp_client.list_tools()


def create_langchain_tool_from_mcp(mcp_tool, server_url: str, ws: WorkspaceClient, is_custom: bool = False) -> MCPTool:
    """Create a LangChain tool from an MCP tool definition.

    Args:
        mcp_tool: MCP tool definition
        server_url: URL of the MCP server
        ws: Authenticated WorkspaceClient
        is_custom: Whether this is a custom MCP server

    Returns:
        MCPTool instance
    """
    schema = mcp_tool.inputSchema.copy()
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # Map JSON schema types to Python types for input validation
    TYPE_MAPPING = {"integer": int, "number": float, "boolean": bool}
    field_definitions = {}
    for field_name, field_info in properties.items():
        field_type_str = field_info.get("type", "string")
        field_type = TYPE_MAPPING.get(field_type_str, str)

        if field_name in required:
            field_definitions[field_name] = (field_type, ...)
        else:
            field_definitions[field_name] = (field_type, None)

    # Dynamically create a Pydantic schema for the tool's input arguments
    args_schema = create_model(f"{mcp_tool.name}Args", **field_definitions)

    # Return a configured MCPTool instance
    return MCPTool(
        name=mcp_tool.name,
        description=mcp_tool.description or f"Tool: {mcp_tool.name}",
        args_schema=args_schema,
        server_url=server_url,
        ws=ws,
        is_custom=is_custom,
    )


async def create_mcp_tools(
    ws: WorkspaceClient, managed_server_urls: List[str] = None, custom_server_urls: List[str] = None
) -> List[MCPTool]:
    """Create LangChain tools from both managed and custom MCP servers.

    Args:
        ws: Authenticated WorkspaceClient
        managed_server_urls: List of managed MCP server URLs
        custom_server_urls: List of custom MCP server URLs

    Returns:
        List of MCPTool instances
    """
    tools = []

    if managed_server_urls:
        # Load managed MCP tools
        for server_url in managed_server_urls:
            try:
                mcp_tools = get_managed_mcp_tools(ws, server_url)
                for mcp_tool in mcp_tools:
                    tool = create_langchain_tool_from_mcp(mcp_tool, server_url, ws, is_custom=False)
                    tools.append(tool)
            except Exception as e:
                logger.error(f"Error loading tools from managed server {server_url}: {e}")

    if custom_server_urls:
        # Load custom MCP tools (async)
        for server_url in custom_server_urls:
            try:
                mcp_tools = await get_custom_mcp_tools(ws, server_url)
                for mcp_tool in mcp_tools:
                    tool = create_langchain_tool_from_mcp(mcp_tool, server_url, ws, is_custom=True)
                    tools.append(tool)
            except Exception as e:
                logger.error(f"Error loading tools from custom server {server_url}: {e}")

    return tools
