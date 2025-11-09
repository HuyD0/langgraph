"""MCP tool wrapper for LangChain."""

import asyncio

from databricks.sdk import WorkspaceClient
from databricks_mcp import DatabricksMCPClient, DatabricksOAuthClientProvider
from langchain_core.tools import BaseTool
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client as connect


class MCPTool(BaseTool):
    """Custom LangChain tool that wraps MCP server functionality.

    This tool can handle both managed and custom MCP servers with
    appropriate authentication.
    """

    def __init__(
        self,
        name: str,
        description: str,
        args_schema: type,
        server_url: str,
        ws: WorkspaceClient,
        is_custom: bool = False,
    ):
        """Initialize the MCP tool.

        Args:
            name: Tool name
            description: Tool description
            args_schema: Pydantic schema for tool arguments
            server_url: MCP server URL
            ws: Authenticated WorkspaceClient
            is_custom: Whether this is a custom MCP server
        """
        super().__init__(name=name, description=description, args_schema=args_schema)
        # Store custom attributes
        object.__setattr__(self, "server_url", server_url)
        object.__setattr__(self, "workspace_client", ws)
        object.__setattr__(self, "is_custom", is_custom)

    def _run(self, **kwargs) -> str:
        """Execute the MCP tool.

        Args:
            **kwargs: Tool arguments

        Returns:
            Tool execution result as string
        """
        if self.is_custom:
            # Use the async method for custom MCP servers (OAuth required)
            return asyncio.run(self._run_custom_async(**kwargs))
        else:
            # Use managed MCP server via synchronous call
            mcp_client = DatabricksMCPClient(server_url=self.server_url, workspace_client=self.workspace_client)
            response = mcp_client.call_tool(self.name, kwargs)
            return "".join([c.text for c in response.content])

    async def _run_custom_async(self, **kwargs) -> str:
        """Execute custom MCP tool asynchronously.

        Args:
            **kwargs: Tool arguments

        Returns:
            Tool execution result as string
        """
        async with connect(self.server_url, auth=DatabricksOAuthClientProvider(self.workspace_client)) as (
            read_stream,
            write_stream,
            _,
        ):
            # Create an async session with the server and call the tool
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                response = await session.call_tool(self.name, kwargs)
                return "".join([c.text for c in response.content])
