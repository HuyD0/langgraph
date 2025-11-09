"""State definitions for LangGraph agent."""

from typing import Annotated, Any, Optional, Sequence, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """The state for the agent workflow.

    Attributes:
        messages: The conversation history with message merging
        custom_inputs: Optional custom input data
        custom_outputs: Optional custom output data
    """

    messages: Annotated[Sequence[AnyMessage], add_messages]
    custom_inputs: Optional[dict[str, Any]]
    custom_outputs: Optional[dict[str, Any]]
