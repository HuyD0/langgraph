"""Shared test fixtures.

Note what is *not* here: no Spark, no Databricks Connect, no cloud client of any
kind. The previous version of this file raised ImportError unless
``databricks-connect`` was installed, which meant `pytest` failed before
collecting a single test. A test suite you cannot run is not a test suite.

Every test in this project runs offline, with no credentials.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drill.config import DrillSettings, LLMSettings
from drill.deps import Deps
from drill.graph import build_drill_graph
from drill.progress import ProgressStore


class FakeChatModel:
    """A chat model that never touches the network.

    Records the messages it was sent so tests can assert on what the tutor
    actually asked, and returns canned replies in order (repeating the last one
    once they run out).
    """

    def __init__(self, replies: list[str] | None = None):
        self.replies = list(replies or ["a canned tutor reply"])
        self.calls: list[list] = []

    def invoke(self, messages, *args, **kwargs):
        self.calls.append(messages)
        index = min(len(self.calls) - 1, len(self.replies) - 1)

        class _Response:
            content = self.replies[index]

        return _Response()

    @property
    def last_prompt(self) -> str:
        """Everything sent in the most recent call, flattened to text."""
        return "\n".join(str(getattr(m, "content", m)) for m in self.calls[-1])


@pytest.fixture
def fake_model() -> FakeChatModel:
    return FakeChatModel()


@pytest.fixture
def progress_path(tmp_path: Path) -> Path:
    return tmp_path / "progress.json"


@pytest.fixture
def store(progress_path: Path) -> ProgressStore:
    return ProgressStore(progress_path)


@pytest.fixture
def settings(progress_path: Path) -> DrillSettings:
    """Settings that never read the real environment."""
    return DrillSettings(
        llm=LLMSettings(),
        max_attempts=3,
        sandbox_timeout=15,
        progress_path=progress_path,
        mlflow_tracking_uri=None,
        mlflow_experiment="test",
    )


@pytest.fixture
def deps(fake_model: FakeChatModel, settings: DrillSettings, store: ProgressStore) -> Deps:
    return Deps(chat_model=fake_model, settings=settings, progress=store)


@pytest.fixture
def graph():
    return build_drill_graph()


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch):
    """Stop a developer's real Azure variables from leaking into tests.

    Without this, running the suite on a machine that has AZURE_OPENAI_API_KEY set
    would exercise different code paths than CI, which is exactly the kind of
    "works on my machine" that wastes an afternoon.
    """
    for var in (
        "AZURE_OPENAI_ENDPOINT", "AZURE_INFERENCE_ENDPOINT", "AZURE_AI_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT", "AZURE_OPENAI_DEPLOYMENT_NAME", "AZURE_INFERENCE_MODEL",
        "AZURE_OPENAI_API_KEY", "AZURE_INFERENCE_CREDENTIAL", "AZURE_FOUNDRY_FLAVOUR",
        "AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET",
        "DRILL_MAX_ATTEMPTS", "DRILL_SANDBOX_TIMEOUT", "DRILL_PROGRESS_PATH",
        "MLFLOW_TRACKING_URI", "MLFLOW_EXPERIMENT_NAME",
    ):
        monkeypatch.delenv(var, raising=False)
