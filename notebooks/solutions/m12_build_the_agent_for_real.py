"""Answer key for milestone 12: build the agent for real."""

import mlflow
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, interrupt
from mlflow.entities import SpanType

RUNBOOKS: dict = {}  # defined in the notebook


@tool
def search_runbooks(query: str) -> str:
    """Search the platform runbooks with a short query, like 'quota', 'restart' or 'access'."""
    hits = [text for key, text in RUNBOOKS.items() if key in query.lower()]
    return "\n".join(hits) or "Nothing found."


def build_agent(model, tools, checkpointer=None):
    bound = model.bind_tools(tools)

    def agent(state: MessagesState):
        return {"messages": [bound.invoke(state["messages"])]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    return graph.compile(checkpointer=checkpointer)


def ask(graph, thread_id, question):
    out = graph.invoke({"messages": [HumanMessage(question)]}, {"configurable": {"thread_id": thread_id}})
    return out["messages"][-1].content


def build_approving_agent(model, tools, checkpointer):
    bound = model.bind_tools(tools)

    def agent(state: MessagesState):
        return {"messages": [bound.invoke(state["messages"])]}

    def approve(state: MessagesState):
        last = state["messages"][-1]
        risky = [c for c in last.tool_calls if c["name"] == "restart_cluster"]
        if risky and not interrupt({"tool": risky[0]["name"], "args": risky[0]["args"]}):
            declined = [ToolMessage("A person declined this action.", tool_call_id=c["id"]) for c in last.tool_calls]
            return Command(goto="agent", update={"messages": declined})
        return Command(goto="tools")

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent)
    graph.add_node("approve", approve)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "approve", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile(checkpointer=checkpointer)


def stream_steps(graph, question, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    return [node for update in graph.stream({"messages": [HumanMessage(question)]}, config, stream_mode="updates")
            for node in update]


def tool_calls_in_last_trace():
    mlflow.flush_trace_async_logging()
    trace = mlflow.get_trace(mlflow.get_last_active_trace_id())
    return [span.name for span in trace.data.spans if span.span_type == SpanType.TOOL]
