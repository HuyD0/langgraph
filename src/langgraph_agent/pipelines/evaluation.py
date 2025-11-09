"""Evaluation pipeline for the LangGraph MCP agent."""

from typing import Any, List, Optional

import mlflow
from mlflow.genai.scorers import RelevanceToQuery, Safety

from langgraph_agent.monitoring.logging import get_logger

logger = get_logger(__name__)


def load_evaluation_dataset(
    dataset_path: Optional[str] = None,
    use_uc: bool = True,
    catalog: Optional[str] = None,
    schema: Optional[str] = None,
) -> List[dict]:
    """Load evaluation dataset from Unity Catalog or file.

    Args:
        dataset_path: Path to dataset file (JSON, CSV, etc.) - used if use_uc=False
        use_uc: If True, load from Unity Catalog (default)
        catalog: UC catalog name (uses config default if None)
        schema: UC schema name (uses config default if None)

    Returns:
        List of evaluation examples
    """
    # Try Unity Catalog first
    if use_uc:
        try:
            from langgraph_agent.data import load_eval_dataset_from_uc

            return load_eval_dataset_from_uc(catalog=catalog, schema=schema)
        except Exception as e:
            logger.warning(f"Could not load from Unity Catalog: {e}")
            logger.info("Falling back to file or default dataset...")

    # Fall back to file
    if dataset_path:
        import json

        with open(dataset_path, "r") as f:
            return json.load(f)

    # Default test dataset
    return [
        {
            "inputs": {"input": [{"role": "user", "content": "Calculate the 15th Fibonacci number"}]},
            "expected_response": "The 15th Fibonacci number is 610.",
        },
        {"inputs": {"input": [{"role": "user", "content": "What is 7*6 in Python?"}]}, "expected_response": "42"},
    ]


def evaluate_agent(
    agent,
    dataset: Optional[List[dict]] = None,
    dataset_path: Optional[str] = None,
    scorers: Optional[list] = None,
) -> Any:
    """Evaluate the agent using MLflow GenAI evaluation.

    Args:
        agent: The agent to evaluate
        dataset: Evaluation dataset (list of examples)
        dataset_path: Path to dataset file
        scorers: List of MLflow scorers to use

    Returns:
        Evaluation results
    """
    # Load dataset
    if dataset is None:
        dataset = load_evaluation_dataset(dataset_path)

    # Use default scorers if none provided
    if scorers is None:
        scorers = [RelevanceToQuery(), Safety()]

    # Run evaluation
    eval_results = mlflow.genai.evaluate(
        data=dataset,
        predict_fn=lambda input: agent.predict({"input": input}),
        scorers=scorers,
    )

    return eval_results


def run_evaluation_pipeline(
    agent,
    dataset_path: Optional[str] = None,
    experiment_name: Optional[str] = None,
) -> dict:
    """Run a complete evaluation pipeline with MLflow tracking.

    Args:
        agent: The agent to evaluate
        dataset_path: Path to evaluation dataset
        experiment_name: MLflow experiment name

    Returns:
        Dictionary with evaluation results and metrics
    """
    # Set experiment if provided
    if experiment_name:
        mlflow.set_experiment(experiment_name)

    # Load dataset
    dataset = load_evaluation_dataset(dataset_path)

    # Run evaluation
    logger.info(f"Running evaluation on {len(dataset)} examples...")
    eval_results = evaluate_agent(agent, dataset=dataset)

    # Extract metrics
    metrics = eval_results.metrics

    logger.info("Evaluation complete!")
    logger.info(f"Results: {metrics}")

    return {
        "results": eval_results,
        "metrics": metrics,
        "dataset_size": len(dataset),
    }
