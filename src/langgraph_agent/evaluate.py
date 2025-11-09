"""Evaluation pipeline for the LangGraph MCP agent."""

from typing import List, Optional

import mlflow
from mlflow.genai.scorers import RelevanceToQuery, Safety


def load_evaluation_dataset(dataset_path: Optional[str] = None) -> List[dict]:
    """Load evaluation dataset.

    Args:
        dataset_path: Path to dataset file (JSON, CSV, etc.)

    Returns:
        List of evaluation examples
    """
    if dataset_path:
        # Load from file
        import json

        with open(dataset_path, "r") as f:
            return json.load(f)
    else:
        # Return default test dataset
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
) -> mlflow.genai.EvaluationResult:
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
    print(f"Running evaluation on {len(dataset)} examples...")
    eval_results = evaluate_agent(agent, dataset=dataset)

    # Extract metrics
    metrics = eval_results.metrics

    print("Evaluation complete!")
    print(f"Results: {metrics}")

    return {
        "results": eval_results,
        "metrics": metrics,
        "dataset_size": len(dataset),
    }
