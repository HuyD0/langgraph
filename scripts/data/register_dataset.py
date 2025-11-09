#!/usr/bin/env python
"""Quick script to register the evaluation dataset to Unity Catalog."""

import sys
from langgraph_agent.data_utils import register_eval_dataset_to_uc

if __name__ == "__main__":
    print("Registering evaluation dataset to Unity Catalog...")

    dataset_path = sys.argv[1] if len(sys.argv) > 1 else "data/eval_dataset.json"

    try:
        table_name = register_eval_dataset_to_uc(
            dataset_path=dataset_path,
        )
        print(f"\n✓ Success! Dataset registered: {table_name}")
        print("\nYou can now run evaluation jobs without specifying a dataset path.")
        print("The dataset will be automatically loaded from Unity Catalog.")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
