"""Data handling utilities for the agent.

This module provides utilities for:
- Loading and processing datasets
- Unity Catalog integration
- Data validation
"""

from .unity_catalog import (
    register_eval_dataset_to_uc,
    load_eval_dataset_from_uc,
)

__all__ = [
    "register_eval_dataset_to_uc",
    "load_eval_dataset_from_uc",
]
