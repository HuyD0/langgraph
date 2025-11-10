"""
Python-based Databricks Asset Bundle resources.

This module defines all Databricks resources (jobs, experiments, models, etc.)
programmatically using Python instead of YAML. This enables:
- Better code organization and reusability
- Type checking and validation
- Dynamic resource generation
- Parameterization and environment-specific logic

The load_resources() function is the entry point called by Databricks CLI.

Note: Currently Python resources support jobs, pipelines, schemas, and volumes.
Other resource types (experiments, models, serving endpoints) remain in YAML.
"""

from databricks.bundles.core import Resources
from .jobs.agent_deployment import get_deployment_jobs
from .jobs.agent_evaluation import get_evaluation_job


def load_resources() -> Resources:
    """
    Load all Databricks Asset Bundle resources.

    This function is called by Databricks CLI when deploying the bundle.
    It returns a Resources object with all job definitions.

    Returns:
        Resources object with job definitions
    """
    resources = Resources()

    # Load deployment jobs (register and deploy)
    deployment_jobs = get_deployment_jobs()
    for job_name, job in deployment_jobs.items():
        resources.add_job(job_name, job)

    # Load evaluation job
    evaluation_job = get_evaluation_job()
    for job_name, job in evaluation_job.items():
        resources.add_job(job_name, job)

    return resources
