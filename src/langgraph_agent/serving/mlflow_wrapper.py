"""Agent code for MLflow code-based logging.

This file defines the agent that will be logged to MLflow using code-based approach.
It follows the Databricks pattern for deploying LangGraph MCP agents.
"""

import asyncio
from typing import Generator, Optional, Sequence, Union

import mlflow
import nest_asyncio
from databricks.sdk import WorkspaceClient
from databricks_langchain import ChatDatabricks
from langchain.messages import AIMessage, AIMessageChunk
from langchain_core.language_models import LanguageModelLike
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph
from langgraph.prebuilt.tool_node import ToolNode
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    output_to_responses_items_stream,
    to_chat_completions_input,
)

from langgraph_agent.integrations.mcp import create_mcp_tools
from langgraph_agent.models import AgentState
from langgraph_agent.utils.config_loader import get_cached_config, get_config_value

# Enable nested event loops for async operations
nest_asyncio.apply()

# Load configuration
_config = get_cached_config()


def create_tool_calling_agent(
    model: LanguageModelLike,
    tools: Union[ToolNode, Sequence[BaseTool]],
    system_prompt: Optional[str] = None,
):
    """Create a LangGraph agent that can call tools.

    Args:
        model: Language model to use
        tools: List of tools or ToolNode
        system_prompt: Optional system prompt to prepend

    Returns:
        Compiled LangGraph workflow
    """
    model = model.bind_tools(tools)  # Bind tools to the model

    def should_continue(state: AgentState):
        """Check if agent should continue or finish based on last message."""
        messages = state["messages"]
        last_message = messages[-1]
        # If function (tool) calls are present, continue; otherwise, end
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "continue"
        else:
            return "end"

    # Preprocess: optionally prepend a system prompt to the conversation history
    if system_prompt:
        preprocessor = RunnableLambda(lambda state: [{"role": "system", "content": system_prompt}] + state["messages"])
    else:
        preprocessor = RunnableLambda(lambda state: state["messages"])

    model_runnable = preprocessor | model  # Chain the preprocessor and the model

    def call_model(state: AgentState, config: RunnableConfig):
        """Invoke the model within the workflow."""
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


class LangGraphResponsesAgent(ResponsesAgent):
    """ResponsesAgent wrapper for LangGraph agent.

    This makes the agent compatible with Mosaic AI Responses API.
    """

    def __init__(self, agent):
        """Initialize the responses agent.

        Args:
            agent: Compiled LangGraph agent
        """
        self.agent = agent

    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        """Make a prediction (single-step) for the agent.

        Args:
            request: Agent request with input messages

        Returns:
            Agent response with output items
        """
        outputs = [
            event.item
            for event in self.predict_stream(request)
            if event.type == "response.output_item.done" or event.type == "error"
        ]
        return ResponsesAgentResponse(output=outputs, custom_outputs=request.custom_inputs)

    def predict_stream(
        self,
        request: ResponsesAgentRequest,
    ) -> Generator[ResponsesAgentStreamEvent, None, None]:
        """Stream predictions for the agent, yielding output as it's generated.

        Args:
            request: Agent request with input messages

        Yields:
            ResponsesAgentStreamEvent for each output item
        """
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
                except Exception:
                    pass


def initialize_agent(
    llm_endpoint_name: str,
    system_prompt: str,
    managed_mcp_urls: list = None,
    custom_mcp_urls: list = None,
) -> LangGraphResponsesAgent:
    """Initialize the complete agent with MCP tools.

    Args:
        llm_endpoint_name: Name of the LLM serving endpoint
        system_prompt: System prompt for the agent
        managed_mcp_urls: List of managed MCP server URLs
        custom_mcp_urls: List of custom MCP server URLs

    Returns:
        Initialized LangGraphResponsesAgent
    """
    # Create workspace client
    workspace_client = WorkspaceClient()

    # Create LLM
    llm = ChatDatabricks(endpoint=llm_endpoint_name)

    # Create MCP tools from the configured servers
    mcp_tools = asyncio.run(
        create_mcp_tools(
            ws=workspace_client,
            managed_server_urls=managed_mcp_urls or [],
            custom_server_urls=custom_mcp_urls or [],
        )
    )

    # Create the agent graph with an LLM, tool set, and system prompt
    agent = create_tool_calling_agent(llm, mcp_tools, system_prompt)
    return LangGraphResponsesAgent(agent)


# Enable MLflow autologging
mlflow.langchain.autolog()

# Initialize the agent with configuration from YAML
# This will be executed when the model is loaded
LLM_ENDPOINT_NAME = get_config_value(_config, "model.endpoint_name", "LLM_ENDPOINT_NAME")
system_prompt = get_config_value(_config, "model.system_prompt", "SYSTEM_PROMPT")
workspace_client = WorkspaceClient()
host = workspace_client.config.host
MANAGED_MCP_SERVER_URLS = [f"{host}/api/2.0/mcp/functions/system/ai"]
CUSTOM_MCP_SERVER_URLS = []

AGENT = initialize_agent(
    llm_endpoint_name=LLM_ENDPOINT_NAME,
    system_prompt=system_prompt,
    managed_mcp_urls=MANAGED_MCP_SERVER_URLS,
    custom_mcp_urls=CUSTOM_MCP_SERVER_URLS,
)

# Register the agent with MLflow
mlflow.models.set_model(AGENT)
