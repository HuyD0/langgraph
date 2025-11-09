"""MLflow ML Application entry point for LangGraph MCP Agent.

This file defines the ML application structure for deploying the agent.
"""

import asyncio
import os
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

from langgraph_agent.core.mcp_client import create_mcp_tools
from langgraph_agent.models import AgentState
from langgraph_agent.utils.logging import get_logger, configure_databricks_logging

# Configure logging for Databricks environment
configure_databricks_logging()
logger = get_logger(__name__)

# Enable nested event loops for async operations
nest_asyncio.apply()
logger.debug("Nested event loops enabled")


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


def create_agent(
    llm_endpoint_name: Optional[str] = None,
    system_prompt: Optional[str] = None,
    managed_mcp_urls: Optional[list] = None,
    custom_mcp_urls: Optional[list] = None,
) -> LangGraphResponsesAgent:
    """Create and return the agent (ML Application entry point).

    This function is referenced in mlflow.yaml and called by MLflow
    when the model is loaded.

    Args:
        llm_endpoint_name: Name of the LLM serving endpoint
        system_prompt: System prompt for the agent
        managed_mcp_urls: List of managed MCP server URLs
        custom_mcp_urls: List of custom MCP server URLs

    Returns:
        Initialized LangGraphResponsesAgent
    """
    logger.info("Initializing LangGraph MCP Agent...")

    # Enable MLflow autologging
    mlflow.langchain.autolog()
    logger.debug("MLflow autologging enabled")

    # Use environment variables or defaults
    llm_endpoint_name = llm_endpoint_name or os.getenv("LLM_ENDPOINT_NAME", "databricks-meta-llama-3-1-70b-instruct")
    system_prompt = system_prompt or os.getenv(
        "SYSTEM_PROMPT", "You are a helpful AI assistant with access to various tools."
    )
    logger.info(f"Using LLM endpoint: {llm_endpoint_name}")
    logger.debug(f"System prompt: {system_prompt[:50]}...")

    # Create workspace client
    logger.debug("Creating Databricks workspace client...")
    workspace_client = WorkspaceClient()
    logger.info(f"Connected to workspace: {workspace_client.config.host}")

    # Setup MCP server URLs
    if managed_mcp_urls is None:
        host = workspace_client.config.host
        managed_mcp_urls = [f"{host}/api/2.0/mcp/functions/system/ai"]

    if custom_mcp_urls is None:
        custom_mcp_urls = []

    logger.info(f"Managed MCP URLs: {len(managed_mcp_urls)}")
    logger.info(f"Custom MCP URLs: {len(custom_mcp_urls)}")

    # Check if we're in validation-skip mode (during MLflow logging)
    skip_validation = os.getenv("MLFLOW_SKIP_VALIDATION") == "1"
    if skip_validation:
        logger.warning("⚠️  Running in validation-skip mode - agent will be created but endpoint may not be validated")
        logger.warning(f"   Ensure endpoint '{llm_endpoint_name}' exists before serving this model")

    # Create LLM
    logger.debug("Initializing ChatDatabricks model...")
    try:
        llm = ChatDatabricks(endpoint=llm_endpoint_name)
        logger.info(f"✓ ChatDatabricks initialized with endpoint: {llm_endpoint_name}")
    except Exception as e:
        if skip_validation:
            logger.warning(f"Failed to initialize ChatDatabricks (expected in skip mode): {e}")
            logger.info("Creating placeholder LLM for validation bypass")
            # Create a basic placeholder that won't be called during validation
            llm = ChatDatabricks(endpoint=llm_endpoint_name)
        else:
            logger.error(f"Failed to initialize ChatDatabricks: {e}")
            raise

    # Create MCP tools from the configured servers
    logger.info("Creating MCP tools...")
    mcp_tools = asyncio.run(
        create_mcp_tools(
            ws=workspace_client,
            managed_server_urls=managed_mcp_urls,
            custom_server_urls=custom_mcp_urls,
        )
    )
    logger.info(f"✓ Created {len(mcp_tools)} MCP tools")

    # Create the agent graph with an LLM, tool set, and system prompt
    logger.info("Building agent workflow graph...")
    agent = create_tool_calling_agent(llm, mcp_tools, system_prompt)
    logger.info("✓ Agent initialized successfully")

    return LangGraphResponsesAgent(agent)


# Initialize the agent at module level for code-based logging
logger.info("Starting module-level agent initialization...")
# Enable MLflow autologging
mlflow.langchain.autolog()

# Initialize with default configuration
# Configuration can be overridden via environment variables
logger.info("Creating default agent instance...")
AGENT = create_agent()
logger.info("✓ Default agent instance created")

# Register the agent with MLflow for code-based logging
mlflow.models.set_model(AGENT)
logger.info("✓ Agent registered with MLflow")
