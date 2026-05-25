import asyncio
import operator
import os
from typing import Annotated, Any, List, Optional, Sequence, TypedDict

import mlflow
import nest_asyncio
from azure.identity import ClientSecretCredential
from azure.search.documents import SearchClient
from databricks.sdk import WorkspaceClient
from databricks_langchain import (
    ChatDatabricks,
    UCFunctionToolkit,
    VectorSearchRetrieverTool,
)
from databricks_mcp import DatabricksMCPClient, DatabricksOAuthClientProvider
from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import AIMessage, AIMessageChunk, AnyMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command, Send, interrupt
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client as connect
from pydantic import BaseModel, Field, create_model

nest_asyncio.apply()

############################################
## LLM endpoint — reads from env, falls back to config default
############################################
LLM_ENDPOINT_NAME = os.getenv("DATABRICKS_ENDPOINT_NAME", "databricks-claude-3-7-sonnet")
llm = ChatDatabricks(endpoint=LLM_ENDPOINT_NAME)

system_prompt = "You are a helpful assistant that can run Python code."

###############################################################################
## Workspace client & MCP server URLs
###############################################################################
profile_name = os.getenv("DATABRICKS_PROFILE", os.getenv("DATABRICKS_CONFIG_PROFILE", "development"))

try:
    workspace_client = WorkspaceClient(profile=profile_name)
except Exception:
    workspace_client = WorkspaceClient()

host = workspace_client.config.host

MANAGED_MCP_SERVER_URLS = [
    f"{host}/api/2.0/mcp/functions/system/ai",
]
CUSTOM_MCP_SERVER_URLS = []

###############################################################################
## Azure AI Search configuration (primary retriever for RAG workers)
## All sensitive values come from environment variables — never hard-coded.
###############################################################################
AZURE_SEARCH_ENDPOINT = os.getenv("VECTOR_ENDPOINT")
AZURE_SEARCH_INDEX    = os.getenv("VECTOR_INDEX_NAME", "pdf_docs_ada2")
VS_NUM_RESULTS        = int(os.getenv("VS_NUM_RESULTS", "5"))

#####################
## MCP Tool Creation
#####################

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
        super().__init__(name=name, description=description, args_schema=args_schema)
        object.__setattr__(self, "server_url", server_url)
        object.__setattr__(self, "workspace_client", ws)
        object.__setattr__(self, "is_custom", is_custom)

    def _run(self, **kwargs) -> str:
        if self.is_custom:
            return asyncio.run(self._run_custom_async(**kwargs))
        else:
            mcp_client = DatabricksMCPClient(
                server_url=self.server_url, workspace_client=self.workspace_client
            )
            response = mcp_client.call_tool(self.name, kwargs)
            return "".join([c.text for c in response.content])

    async def _run_custom_async(self, **kwargs) -> str:
        async with connect(
            self.server_url, auth=DatabricksOAuthClientProvider(self.workspace_client)
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                response = await session.call_tool(self.name, kwargs)
                return "".join([c.text for c in response.content])


async def get_custom_mcp_tools(ws: WorkspaceClient, server_url: str):
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
    mcp_client = DatabricksMCPClient(server_url=server_url, workspace_client=ws)
    return mcp_client.list_tools()


def create_langchain_tool_from_mcp(mcp_tool, server_url: str, ws: WorkspaceClient, is_custom: bool = False):
    schema = mcp_tool.inputSchema.copy()
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    TYPE_MAPPING = {"integer": int, "number": float, "boolean": bool}
    field_definitions = {}
    for field_name, field_info in properties.items():
        field_type_str = field_info.get("type", "string")
        field_type = TYPE_MAPPING.get(field_type_str, str)
        if field_name in required:
            field_definitions[field_name] = (field_type, ...)
        else:
            field_definitions[field_name] = (field_type, None)

    args_schema = create_model(f"{mcp_tool.name}Args", **field_definitions)
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
    tools = []

    if managed_server_urls:
        for server_url in managed_server_urls:
            try:
                mcp_tools = get_managed_mcp_tools(ws, server_url)
                for mcp_tool in mcp_tools:
                    tools.append(create_langchain_tool_from_mcp(mcp_tool, server_url, ws, is_custom=False))
            except Exception as e:
                print(f"Error loading tools from managed server {server_url}: {e}")

    if custom_server_urls:
        for server_url in custom_server_urls:
            try:
                mcp_tools = await get_custom_mcp_tools(ws, server_url)
                for mcp_tool in mcp_tools:
                    tools.append(create_langchain_tool_from_mcp(mcp_tool, server_url, ws, is_custom=True))
            except Exception as e:
                print(f"Error loading tools from custom server {server_url}: {e}")

    return tools


#####################
## State definitions
#####################

class OverallState(TypedDict):
    query: str
    partitions: list[str]
    research_results: Annotated[list[str], operator.add]  # parallel worker outputs merged here
    final_answer: str


class WorkerState(TypedDict):
    partition_query: str  # isolated per worker — prevents context window bloat


class PartitionPlan(BaseModel):
    partitions: list[str] = Field(description="Non-overlapping sub-tasks that together cover the full query")


# Backward-compatible alias
AgentState = OverallState


#####################
## Prompt loading
#####################

def _load_prompt(registry_name: str, default: str) -> str:
    """Load a prompt from the MLflow prompt registry, falling back to the inline default."""
    try:
        return str(mlflow.load_prompt(f"prompts:/{registry_name}/1"))
    except Exception:
        return default


#####################
## Azure AI Search
#####################

def _build_azure_search_client() -> SearchClient:
    credential = ClientSecretCredential(
        tenant_id=os.getenv("AZURE_TENANT_ID"),
        client_id=os.getenv("AZURE_CLIENT_ID"),
        client_secret=os.getenv("AZURE_CLIENT_SECRET"),
    )
    return SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX,
        credential=credential,
    )


#####################
## Graph nodes
#####################

# Module-level references populated by initialize_agent()
_azure_search_client: SearchClient = None
_planner_prompt: str = None
_synthesizer_prompt: str = None
partition_graph = None


def planner_node(state: OverallState, config: RunnableConfig) -> dict:
    structured_llm = llm.with_structured_output(PartitionPlan)
    result: PartitionPlan = structured_llm.invoke(
        [SystemMessage(content=_planner_prompt), HumanMessage(content=state["query"])],
        config,
    )
    # HITL: pause execution and surface the proposed partitions to the user
    feedback = interrupt({
        "message": "I'll research these sub-topics in parallel. Confirm or edit the list before I proceed.",
        "partitions": result.partitions,
    })
    approved = feedback.get("partitions", result.partitions) if isinstance(feedback, dict) else result.partitions
    return {"partitions": approved}


def research_worker_node(state: WorkerState, config: RunnableConfig) -> dict:
    """Isolated RAG worker — only sees its own partition_query, not the full conversation."""
    results = _azure_search_client.search(
        search_text=state["partition_query"],
        top=VS_NUM_RESULTS,
    )
    # Try common field names for document text content
    docs = "\n".join(
        r.get("content", r.get("chunk", r.get("text", r.get("page_content", str(r)))))
        for r in results
    )
    # Return as a single-element list so operator.add can concatenate across workers
    return {"research_results": [f"[{state['partition_query']}]\n{docs}"]}


def synthesizer_node(state: OverallState, config: RunnableConfig) -> dict:
    context = "\n\n---\n\n".join(state["research_results"])
    response = llm.invoke(
        [
            SystemMessage(content=_synthesizer_prompt),
            HumanMessage(content=f"Original query: {state['query']}\n\nResearch findings:\n{context}"),
        ],
        config,
    )
    return {"final_answer": response.content}


#####################
## Send API router
#####################

def route_to_workers(state: OverallState) -> list[Send]:
    return [Send("research_worker_node", {"partition_query": task}) for task in state["partitions"]]


#####################
## Graph assembly
#####################

def build_partition_graph():
    workflow = StateGraph(OverallState)
    workflow.add_node("planner_node", planner_node)
    workflow.add_node("research_worker_node", research_worker_node)
    workflow.add_node("synthesizer_node", synthesizer_node)

    workflow.set_entry_point("planner_node")
    # Conditional edge fans out to one worker per partition via Send
    workflow.add_conditional_edges("planner_node", route_to_workers, ["research_worker_node"])
    # All workers join at synthesizer (LangGraph waits for all Sends to complete)
    workflow.add_edge("research_worker_node", "synthesizer_node")
    workflow.add_edge("synthesizer_node", END)

    # MemorySaver checkpointer is required for HITL interrupt/resume to work
    return workflow.compile(checkpointer=MemorySaver())


#####################
## MLflow pyfunc model
#####################

class PartitionPlannerModel(mlflow.pyfunc.PythonModel):
    """
    Chat-compatible pyfunc model for the partition planner.

    First call: runs until the HITL interrupt, returns proposed partitions.
    Resume call: continues graph execution with approved partitions, returns final answer.
    """

    def predict(self, context, model_input: dict, params=None) -> dict:
        messages = model_input.get("messages", [])
        query = messages[-1]["content"] if messages else model_input.get("query", "")
        thread_id = model_input.get("thread_id", "default")
        thread_config = {"configurable": {"thread_id": thread_id}}

        result = partition_graph.invoke(
            {"query": query, "partitions": [], "research_results": [], "final_answer": ""},
            config=thread_config,
        )

        if "__interrupt__" in result:
            interrupt_val = result["__interrupt__"][0].value
            return {
                "status": "awaiting_confirmation",
                "message": interrupt_val["message"],
                "partitions": interrupt_val["partitions"],
                "thread_id": thread_id,
            }

        return {"status": "complete", "answer": result["final_answer"]}

    def resume(self, thread_id: str, approved_partitions: list) -> dict:
        """Resume the graph after the user confirms or edits the partition list."""
        thread_config = {"configurable": {"thread_id": thread_id}}
        result = partition_graph.invoke(
            Command(resume={"partitions": approved_partitions}),
            config=thread_config,
        )
        return {"status": "complete", "answer": result["final_answer"]}


#####################
## Initialization
#####################

def initialize_agent() -> PartitionPlannerModel:
    global _azure_search_client, _planner_prompt, _synthesizer_prompt, partition_graph

    _azure_search_client = _build_azure_search_client()

    _planner_prompt = _load_prompt(
        "partition_planner_prompt",
        (
            "You are a research planning assistant. Break the user's query into 2-5 "
            "non-overlapping, independent sub-questions. Each sub-question should be "
            "self-contained and answerable on its own. Together they must cover the full query."
        ),
    )
    _synthesizer_prompt = _load_prompt(
        "partition_synthesizer_prompt",
        (
            "You are a synthesis assistant. Given the user's original query and parallel "
            "research findings from multiple searches, produce a comprehensive, "
            "well-structured final answer. Cite specific findings where relevant."
        ),
    )

    partition_graph = build_partition_graph()
    return PartitionPlannerModel()


def setup_mlflow():
    try:
        mlflow.langchain.autolog()
        print("✓ MLflow autologging enabled")
    except Exception as e:
        print(f"Warning: MLflow autologging failed: {e}")


AGENT = initialize_agent()

try:
    setup_mlflow()
    mlflow.models.set_model(AGENT)
except Exception as e:
    print(f"Note: MLflow model tracking not available: {e}")
    print("Agent will work without MLflow tracking.")
