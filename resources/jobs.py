"""Job resources for agent evaluation and deployment workflows."""

from databricks.sdk.service.jobs import (
    PythonWheelTask,
    Task,
)


def get_agent_evaluation_job(bundle):
    """Define the agent evaluation job.

    This job runs periodic evaluation of the deployed agent using
    the evaluation pipeline with serverless compute.
    """
    catalog = bundle.variables.get("catalog", "rag")
    schema = bundle.variables.get("schema", "development")

    return {
        "name": f"{bundle.target}_agent_evaluation",
        "tasks": [
            Task(
                task_key="run_evaluation",
                python_wheel_task=PythonWheelTask(
                    package_name="langgraph_agent",
                    entry_point="cli",
                    parameters=["evaluate", "--dataset", "data/eval_dataset.json"],
                ),
                libraries=[{"whl": "../dist/*.whl"}],
            )
        ],
        "tags": {
            "project": "langgraph-mcp-agent",
            "environment": bundle.target,
        },
        "max_concurrent_runs": 1,
    }


def get_agent_deployment_job(bundle):
    """Define the agent deployment job.

    This job handles the complete deployment pipeline with serverless compute:
    1. Log model to MLflow
    2. Register to Unity Catalog
    3. Deploy to serving endpoint
    """
    catalog = bundle.variables.get("catalog", "rag")
    schema = bundle.variables.get("schema", "development")

    return {
        "name": f"{bundle.target}_agent_deployment",
        "tasks": [
            Task(
                task_key="deploy_agent",
                python_wheel_task=PythonWheelTask(
                    package_name="langgraph_agent",
                    entry_point="cli",
                    parameters=["deploy", "--no-validate"],
                ),
                libraries=[{"whl": "../dist/*.whl"}],
            )
        ],
        "tags": {
            "project": "langgraph-mcp-agent",
            "environment": bundle.target,
        },
        "max_concurrent_runs": 1,
    }
