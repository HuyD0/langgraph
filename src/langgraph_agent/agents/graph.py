"""LangGraph agent workflow definition."""

from typing import Optional, Sequence, Union

from langchain_core.language_models import LanguageModelLike
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_core.tools import BaseTool
from langchain.messages import AIMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt.tool_node import ToolNode

from ..models import AgentState
from ..monitoring.logging import get_logger

logger = get_logger(__name__)


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
            logger.debug(f"Agent continuing with {len(last_message.tool_calls)} tool calls")
            return "continue"
        else:
            logger.debug("Agent workflow ending")
            return "end"

    # Preprocess: optionally prepend a system prompt to the conversation history
    if system_prompt:
        logger.debug("Using system prompt preprocessing")
        preprocessor = RunnableLambda(lambda state: [{"role": "system", "content": system_prompt}] + state["messages"])
    else:
        preprocessor = RunnableLambda(lambda state: state["messages"])

    model_runnable = preprocessor | model  # Chain the preprocessor and the model

    def call_model(state: AgentState, config: RunnableConfig):
        """Invoke the model within the workflow."""
        logger.debug(f"Calling model with {len(state['messages'])} messages")
        response = model_runnable.invoke(state, config)
        return {"messages": [response]}

    logger.info("Building agent workflow graph")
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

    logger.info("✓ Agent workflow compiled successfully")
    # Compile and return the tool-calling agent workflow
    return workflow.compile()
