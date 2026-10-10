"""Minimal tool-calling LangGraph agent.

Run with `uv run langgraph dev` (Studio) or `uv run python -m ai_starter.agent`.
"""

from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from ai_starter.llm import get_chat_model
from ai_starter.tools import TOOLS


def build_graph():
    llm = get_chat_model().bind_tools(TOOLS)

    def call_model(state: MessagesState) -> dict:
        return {"messages": [llm.invoke(state["messages"])]}

    g = StateGraph(MessagesState)
    g.add_node("model", call_model)
    g.add_node("tools", ToolNode(TOOLS))
    g.add_edge(START, "model")
    g.add_conditional_edges("model", tools_condition)  # -> "tools" or END
    g.add_edge("tools", "model")
    return g.compile()


graph = build_graph()


if __name__ == "__main__":
    import os

    import mlflow

    # Traces every run. Goes to Databricks when MLFLOW_TRACKING_URI=databricks.
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "ai-starter"))
    mlflow.langchain.autolog()
    result = graph.invoke({"messages": [("user", "What time is it, and what is 21 + 21?")]})
    print(result["messages"][-1].content)
