import asyncio
from typing import Annotated, Any, Generator, List, Optional, Sequence, TypedDict, Union

import mlflow
import nest_asyncio
from databricks.sdk import WorkspaceClient
from databricks_langchain import (
    ChatDatabricks,
    UCFunctionToolkit,
    VectorSearchRetrieverTool,
)
from databricks_mcp import DatabricksMCPClient, DatabricksOAuthClientProvider
from langchain.messages import AIMessage, AIMessageChunk, AnyMessage
from langchain_core.language_models import LanguageModelLike
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt.tool_node import ToolNode
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client as connect
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    output_to_responses_items_stream,
    to_chat_completions_input,
)
from pydantic import create_model

nest_asyncio.apply()

############################################
## Define your LLM endpoint and system prompt
############################################
# TODO: Replace with your model serving endpoint
LLM_ENDPOINT_NAME = "databricks-claude-3-7-sonnet"
llm = ChatDatabricks(endpoint=LLM_ENDPOINT_NAME)

# TODO: Update with your system prompt
system_prompt = "You are a helpful assistant that can run Python code."

###############################################################################
## Configure MCP Servers for your agent
##
## This section sets up server connections so your agent can retrieve data or take actions.

## There are three connection types:
## 1. Managed MCP servers — fully managed by Databricks (no setup required)
## 2. External MCP servers — hosted outside Databricks but proxied through a
##    Managed MCP server proxy (some setup required)
## 3. Custom MCP servers — MCP servers hosted as Databricks Apps (OAuth setup required)
##
## Note: External MCP servers get added to the "managed" URL list
## because their proxy endpoints are managed by Databricks.
###############################################################################

# TODO: Choose your MCP server connection type and fill in the appropriate URLs.

# ---------------------------------------------------------------------------
# Managed MCP Server — simplest setup
# ---------------------------------------------------------------------------
# Databricks manages this connection automatically using your workspace settings.
# When running locally, it will use authentication from:
#   1. Databricks CLI OAuth profiles (recommended - run: databricks auth login)
#   2. Environment variables (DATABRICKS_HOST, DATABRICKS_CLIENT_ID, DATABRICKS_CLIENT_SECRET)
#   3. Default profile from ~/.databrickscfg

import os

# For local development, specify the profile name if you have multiple profiles
# Comment this out when running in Databricks notebooks
profile_name = os.getenv("DATABRICKS_CONFIG_PROFILE", "development")  # Use your profile name

try:
    # Try to use the specified profile (for local development)
    workspace_client = WorkspaceClient(profile=profile_name)
except Exception:
    # Fall back to default authentication (works in Databricks notebooks)
    workspace_client = WorkspaceClient()

host = workspace_client.config.host

# Managed MCP Servers URLS (includes both fully managed and proxied external MCP)
# - If you're using an external MCP server, create a UC connection and flag it
#   as an MCP connection. This reveals a proxy endpoint.
# - Add that proxy endpoint URL to this list.

MANAGED_MCP_SERVER_URLS = [
    f"{host}/api/2.0/mcp/functions/system/ai",  # Default managed MCP endpoint
    # Example for external MCP:
    # "https://<workspace-hostname>/api/2.0/mcp/external/{connection_name}"
]

# ---------------------------------------------------------------------------
# Custom MCP Server — hosted as a Databricks App
# ---------------------------------------------------------------------------
# Use this if you're running your own MCP server in Databricks.
# These require OAuth with a service principal for machine-to-machine (M2M) auth.
#
# Uncomment and fill in the settings below to use a custom MCP server.
#
# import os
# workspace_client = WorkspaceClient(
#     host="<DATABRICKS_WORKSPACE_URL>",
#     client_id=os.getenv("DATABRICKS_CLIENT_ID"),
#     client_secret=os.getenv("DATABRICKS_CLIENT_SECRET"),
#     auth_type="oauth-m2m",  # Enables service principal authentication
# )

# Custom MCP Servers — add URLs below (not managed or proxied by Databricks)
CUSTOM_MCP_SERVER_URLS = [
    # Example: "https://<custom-mcp-app-url>/mcp"
]


#####################
## MCP Tool Creation
#####################

# Define a custom LangChain tool that wraps functionality for calling MCP servers
class MCPTool(BaseTool):
    """Custom LangChain tool that wraps MCP server functionality"""

    def __init__(
        self,
        name: str,
        description: str,
        args_schema: type,
        server_url: str,
        ws: WorkspaceClient,
        is_custom: bool = False,
    ):
        # Initialize the tool
        super().__init__(name=name, description=description, args_schema=args_schema)
        # Store custom attributes: MCP server URL, Databricks workspace client, and whether the tool is for a custom server
        object.__setattr__(self, "server_url", server_url)
        object.__setattr__(self, "workspace_client", ws)
        object.__setattr__(self, "is_custom", is_custom)

    def _run(self, **kwargs) -> str:
        """Execute the MCP tool"""
        if self.is_custom:
            # Use the async method for custom MCP servers (OAuth required)
            return asyncio.run(self._run_custom_async(**kwargs))
        else:
            # Use managed MCP server via synchronous call
            mcp_client = DatabricksMCPClient(
                server_url=self.server_url, workspace_client=self.workspace_client
            )
            response = mcp_client.call_tool(self.name, kwargs)
            return "".join([c.text for c in response.content])

    async def _run_custom_async(self, **kwargs) -> str:
        """Execute custom MCP tool asynchronously"""
        async with connect(
            self.server_url, auth=DatabricksOAuthClientProvider(self.workspace_client)
        ) as (
            read_stream,
            write_stream,
            _,
        ):
            # Create an async session with the server and call the tool
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                response = await session.call_tool(self.name, kwargs)
                return "".join([c.text for c in response.content])


# Retrieve tool definitions from a custom MCP server (OAuth required)
async def get_custom_mcp_tools(ws: WorkspaceClient, server_url: str):
    """Get tools from a custom MCP server using OAuth"""
    async with connect(server_url, auth=DatabricksOAuthClientProvider(ws)) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools_response = await session.list_tools()
            return tools_response.tools


# Retrieve tool definitions from a managed MCP server
def get_managed_mcp_tools(ws: WorkspaceClient, server_url: str):
    """Get tools from a managed MCP server"""
    mcp_client = DatabricksMCPClient(server_url=server_url, workspace_client=ws)
    return mcp_client.list_tools()


# Convert an MCP tool definition into a LangChain-compatible tool
def create_langchain_tool_from_mcp(
    mcp_tool, server_url: str, ws: WorkspaceClient, is_custom: bool = False
):
    """Create a LangChain tool from an MCP tool definition"""
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


# Gather all tools from managed and custom MCP servers into a single list
async def create_mcp_tools(
    ws: WorkspaceClient, managed_server_urls: List[str] = None, custom_server_urls: List[str] = None
) -> List[MCPTool]:
    """Create LangChain tools from both managed and custom MCP servers"""
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
                print(f"Error loading tools from managed server {server_url}: {e}")

    if custom_server_urls:
        # Load custom MCP tools (async)
        for server_url in custom_server_urls:
            try:
                mcp_tools = await get_custom_mcp_tools(ws, server_url)
                for mcp_tool in mcp_tools:
                    tool = create_langchain_tool_from_mcp(mcp_tool, server_url, ws, is_custom=True)
                    tools.append(tool)
            except Exception as e:
                print(f"Error loading tools from custom server {server_url}: {e}")

    return tools


#####################
## Define agent logic
#####################


# The state for the agent workflow, including the conversation and any custom data
class AgentState(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    custom_inputs: Optional[dict[str, Any]]
    custom_outputs: Optional[dict[str, Any]]


# Define the LangGraph agent that can call tools
def create_tool_calling_agent(
    model: LanguageModelLike,
    tools: Union[ToolNode, Sequence[BaseTool]],
    system_prompt: Optional[str] = None,
):
    model = model.bind_tools(tools)  # Bind tools to the model

    # Function to check if agent should continue or finish based on last message
    def should_continue(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        # If function (tool) calls are present, continue; otherwise, end
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "continue"
        else:
            return "end"

    # Preprocess: optionally prepend a system prompt to the conversation history
    if system_prompt:
        preprocessor = RunnableLambda(
            lambda state: [{"role": "system", "content": system_prompt}] + state["messages"]
        )
    else:
        preprocessor = RunnableLambda(lambda state: state["messages"])

    model_runnable = preprocessor | model  # Chain the preprocessor and the model

    # The function to invoke the model within the workflow
    def call_model(
        state: AgentState,
        config: RunnableConfig,
    ):
        response = model_runnable.invoke(state, config)
        return {"messages": [response]}

    workflow = StateGraph(AgentState)  # Create the agent's state machine

    workflow.add_node("agent", RunnableLambda(call_model))  # Agent node (LLM)
    workflow.add_node("tools", ToolNode(tools))  # Tools node

    workflow.set_entry_point("agent")  # Start at agent node
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",  # If the model requests a tool call, move to tools node
            "end": END,  # Otherwise, end the workflow
        },
    )
    workflow.add_edge("tools", "agent")  # After tools are called, return to agent node

    # Compile and return the tool-calling agent workflow
    return workflow.compile()


# ResponsesAgent class to wrap the compiled agent and make it compatible with Mosaic AI Responses API
class LangGraphResponsesAgent(ResponsesAgent):
    def __init__(self, agent):
        self.agent = agent

    # Make a prediction (single-step) for the agent
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        outputs = [
            event.item
            for event in self.predict_stream(request)
            if event.type == "response.output_item.done" or event.type == "error"
        ]
        return ResponsesAgentResponse(output=outputs, custom_outputs=request.custom_inputs)

    # Stream predictions for the agent, yielding output as it's generated
    def predict_stream(
        self,
        request: ResponsesAgentRequest,
    ) -> Generator[ResponsesAgentStreamEvent, None, None]:
        cc_msgs = to_chat_completions_input([i.model_dump() for i in request.input])
        # Stream events from the agent graph
        for event in self.agent.stream({"messages": cc_msgs}, stream_mode=["updates", "messages"]):
            if event[0] == "updates":
                # Stream updated messages from the workflow nodes
                for node_data in event[1].values():
                    if len(node_data.get("messages", [])) > 0:
                        yield from output_to_responses_items_stream(node_data["messages"])
            elif event[0] == "messages":
                # Stream generated text message chunks
                try:
                    chunk = event[1][0]
                    if isinstance(chunk, AIMessageChunk) and (content := chunk.content):
                        yield ResponsesAgentStreamEvent(
                            **self.create_text_delta(delta=content, item_id=chunk.id),
                        )
                except:
                    pass


# Initialize the entire agent, including MCP tools and workflow
def initialize_agent():
    """Initialize the agent with MCP tools"""
    # Create MCP tools from the configured servers
    mcp_tools = asyncio.run(
        create_mcp_tools(
            ws=workspace_client,
            managed_server_urls=MANAGED_MCP_SERVER_URLS,
            custom_server_urls=CUSTOM_MCP_SERVER_URLS,
        )
    )

    # Create the agent graph with an LLM, tool set, and system prompt (if given)
    agent = create_tool_calling_agent(llm, mcp_tools, system_prompt)
    return LangGraphResponsesAgent(agent)


# Configure MLflow for Databricks deployment (optional for local testing)
# Only enable if you want to track runs to Databricks workspace
def setup_mlflow():
    """Setup MLflow tracking and model registration"""
    try:
        mlflow.langchain.autolog()
        print("✓ MLflow autologging enabled")
    except Exception as e:
        print(f"Warning: MLflow autologging failed: {e}")

# Initialize agent
AGENT = initialize_agent()

# Try to set up MLflow model tracking (optional)
try:
    setup_mlflow()
    mlflow.models.set_model(AGENT)
except Exception as e:
    print(f"Note: MLflow model tracking not available: {e}")
    print("Agent will work without MLflow tracking.")