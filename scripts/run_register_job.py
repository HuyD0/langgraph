"""Databricks job script for model registration.

This script is called directly by Databricks jobs to avoid Click's SystemExit issues.
"""

import sys
from langgraph_agent.jobs import job_register_model

if __name__ == "__main__":
    # Parse arguments
    profile = sys.argv[1] if len(sys.argv) > 1 else None
    validate = sys.argv[2].lower() == "true" if len(sys.argv) > 2 else True

    # Run the job
    result = job_register_model(
        model_code_path=".",
        validate=validate,
        profile=profile,
    )

    print(f"\n✓ Job completed successfully")
    print(f"Result: {result}")
