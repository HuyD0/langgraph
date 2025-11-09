"""ML Lifecycle pipelines.

This module contains pipeline implementations for:
- Training and model registration
- Model evaluation
- Model deployment
"""

from .deployment import (
    log_and_register_model,
    deploy_to_serving_endpoint,
    full_deployment_pipeline,
    get_model_dependencies,
)

from .evaluation import (
    load_evaluation_dataset,
    evaluate_agent,
    run_evaluation_pipeline,
)

__all__ = [
    # Deployment
    "log_and_register_model",
    "deploy_to_serving_endpoint",
    "full_deployment_pipeline",
    "get_model_dependencies",
    # Evaluation
    "load_evaluation_dataset",
    "evaluate_agent",
    "run_evaluation_pipeline",
]
