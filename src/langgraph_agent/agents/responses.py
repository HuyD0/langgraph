"""ResponsesAgent wrapper for LangGraph agents."""

from typing import Generator

import nest_asyncio
from langchain.messages import AIMessageChunk
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    output_to_responses_items_stream,
    to_chat_completions_input,
)

# Enable nested event loops for async operations
nest_asyncio.apply()


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
