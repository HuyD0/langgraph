"""The learning path and the platform track, one file per module.

PATH is the AI engineering path, phase by phase (LIFECYCLE). TRACKS are learning tracks beside it,
with their own order: the platform track is the Azure Databricks, Terraform and Spacelift work.
ORDER is every module, the path first, which is the order the page and the tools load them in.
"""

from __future__ import annotations

import importlib

from drill.content.model import Module

# Phase by phase, as LIFECYCLE below lists them, so "next lesson" never jumps ahead a phase.
PATH = [
    'use-case', 'foundations', 'pricing',                                  # Frame
    'experiments',                                                         # Design
    'llm-apps', 'rag', 'agents', 'agent-teams', 'databricks-ai',           # Build and trace
    'production', 'security',
    'evals', 'models',                                                     # Evaluate
    'shipping',                                                            # Ship
    'tracing', 'llmops', 'reliability',                                    # Monitor
]

# The ML lifecycle strip at the top of the page: which modules belong to which stage.
LIFECYCLE = [
    ('Frame',
     'Pick the use case, decide how to measure it and what success is worth.',
     ['use-case', 'foundations', 'pricing']),
    ('Design',
     'Plan the runs: what you vary, what you hold fixed, what it costs.',
     ['experiments']),
    ('Build and trace',
     'Build with LangGraph and Databricks, traced from the first line.',
     ['llm-apps', 'rag', 'agents', 'agent-teams', 'databricks-ai', 'production', 'security']),
    ('Evaluate',
     'Score runs on the same eval set; compare quality, cost and latency.',
     ['evals', 'models']),
    ('Ship',
     'Release it to real users, a few at a time, by a rule you wrote down first.',
     ['shipping']),
    ('Monitor',
     'Watch real traffic in traces and feed failures back into evals.',
     ['tracing', 'llmops', 'reliability']),
]


# Tracks beside the path: (id, name, one line, modules in order). A track's lessons have their own
# order and numbering (P1.1 ...) and their own sticker shape, and never move the path's "next lesson".
TRACKS = [
    ('platform', 'Platform track',
     'Azure Databricks as code: the workspace, Terraform and Spacelift work behind an ML platform.',
     # How the pieces fit, then each tool in the order a change meets it, then what to do when a run
     # fails; the deeper workspace, access and platform modules come after.
     ['platform-repos', 'azure-databricks', 'terraform', 'spacelift', 'troubleshooting',
      'workspace', 'access', 'platform']),
]

ORDER = PATH + [mid for _, _, _, ms in TRACKS for mid in ms]


def load(order: list[str] | None = None) -> list[Module]:
    """Import each module's file and return its MODULE, in path order."""
    loaded = []
    for module_id in order or ORDER:
        mod = importlib.import_module(f"drill.content.modules.{module_id.replace('-', '_')}")
        assert mod.MODULE.id == module_id, f"{module_id}.py defines MODULE {mod.MODULE.id!r}"
        loaded.append(mod.MODULE)
    return loaded
