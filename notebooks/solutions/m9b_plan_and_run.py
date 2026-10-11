"""Milestone 9b answer key - reading a reranker's reply safely."""

from __future__ import annotations

import re


def parse_ranking(reply, candidates, k):
    """The ids the model ranked, in its order, keeping only real candidates, topped up from the original order.

    Never trust a model's output format: it may add words around the JSON, invent an
    id, or repeat one. Pulling ids out with a pattern and checking each against the
    candidates handles all three.
    """
    ranked = []
    for doc_id in re.findall(r"kb-\d+", reply) + candidates:
        if doc_id in candidates and doc_id not in ranked:
            ranked.append(doc_id)
    return ranked[:k]
