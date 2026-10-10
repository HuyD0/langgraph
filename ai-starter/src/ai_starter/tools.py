"""Tools the agent can call. Kept separate so they can be tested without LLM credentials."""

from datetime import UTC, datetime

from langchain_core.tools import tool


@tool
def current_time() -> str:
    """Return the current UTC time in ISO 8601 format."""
    return datetime.now(UTC).isoformat()


@tool
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


TOOLS = [current_time, add]
