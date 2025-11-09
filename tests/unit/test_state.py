"""Unit tests for agent state."""

from langgraph_agent.models import AgentState


def test_agent_state_structure():
    """Test AgentState structure."""
    state = AgentState(messages=[], custom_inputs={"key": "value"}, custom_outputs={"result": "output"})

    assert "messages" in state
    assert "custom_inputs" in state
    assert "custom_outputs" in state
    assert state["custom_inputs"]["key"] == "value"
    assert state["custom_outputs"]["result"] == "output"
