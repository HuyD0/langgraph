"""The learning path, one file per module. ORDER is the order the page shows them."""

from __future__ import annotations

import importlib

from drill.content.model import Module

ORDER = [
    'foundations',
    'experiments',
    'llm-apps',
    'rag',
    'agents',
    'security',
    'evals',
    'models',
    'tracing',
    'llmops',
    'production',
    'reliability',
    'shipping',
    'platform',
]

# The ML lifecycle strip at the top of the page: which modules belong to which stage.
LIFECYCLE = [
    ('Frame',
     'Decide the question, the metric and what success is worth.',
     ['foundations']),
    ('Design',
     'Plan the runs: what you vary, what you hold fixed, what it costs.',
     ['experiments']),
    ('Build and trace',
     'Build with LangGraph and Databricks, traced from the first line.',
     ['llm-apps', 'rag', 'agents', 'production', 'security']),
    ('Evaluate',
     'Score runs on the same eval set; compare quality, cost and latency.',
     ['evals', 'models']),
    ('Ship',
     'Register, promote and canary with a rule you wrote down first.',
     ['shipping', 'platform']),
    ('Monitor',
     'Watch real traffic in traces and feed failures back into evals.',
     ['tracing', 'llmops', 'reliability']),
]


def load(order: list[str] | None = None) -> list[Module]:
    """Import each module's file and return its MODULE, in path order."""
    loaded = []
    for module_id in order or ORDER:
        mod = importlib.import_module(f"drill.content.modules.{module_id.replace('-', '_')}")
        assert mod.MODULE.id == module_id, f"{module_id}.py defines MODULE {mod.MODULE.id!r}"
        loaded.append(mod.MODULE)
    return loaded
