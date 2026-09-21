"""What the graph nodes need from the outside world, in one object.

Nodes receive this through ``config["configurable"]["deps"]`` rather than reaching
for module-level globals. That single choice is what makes the graph testable: a
test passes a fake chat model and a temp-file progress store, and the nodes cannot
tell the difference. The old agent used module globals and was untestable as a result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from drill.config import DrillSettings
from drill.progress import ProgressStore


@dataclass
class Deps:
    chat_model: Any
    settings: DrillSettings
    progress: ProgressStore

    @classmethod
    def from_env(cls, chat_model: Any | None = None) -> "Deps":
        """Build the real thing. Connects to Azure unless a model is supplied."""
        settings = DrillSettings.from_env()
        if chat_model is None:
            from drill.llm import build_chat_model

            chat_model = build_chat_model(settings.llm)
        return cls(
            chat_model=chat_model,
            settings=settings,
            progress=ProgressStore(settings.progress_path),
        )

    def as_config(self, thread_id: str) -> dict:
        """Wrap into the ``RunnableConfig`` shape LangGraph passes to nodes."""
        return {"configurable": {"thread_id": thread_id, "deps": self}}


def deps_from_config(config: Any) -> Deps:
    """Pull :class:`Deps` back out of a node's config, with a clear error if absent."""
    configurable = (config or {}).get("configurable", {}) if isinstance(config, dict) else {}
    deps = configurable.get("deps")
    if deps is None:
        raise RuntimeError(
            "No Deps in the graph config. Invoke the graph with "
            "`deps.as_config(thread_id)` so nodes can reach the model and settings."
        )
    return deps
