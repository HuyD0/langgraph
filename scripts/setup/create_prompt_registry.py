#!/usr/bin/env python3
"""
Example script for managing prompts in MLflow Prompt Registry.

This script demonstrates how to:
- Create prompts in the registry
- Update prompts with new versions
- Manage aliases
- Search and list prompts
"""

import mlflow
from mlflow import MlflowClient


def create_initial_prompt():
    """Create the initial agent system prompt."""
    print("Creating initial system prompt...")

    prompt = mlflow.genai.create_prompt(
        name="agent-system-prompt",
        template=(
            "You are a helpful AI assistant with access to Databricks tools and MCP servers. "
            "You can help users with:\n"
            "- Data analysis and SQL queries\n"
            "- Workspace operations\n"
            "- Unity Catalog management\n"
            "- General questions about Databricks\n\n"
            "Always be helpful, accurate, and provide clear explanations."
        ),
        commit_message="Initial system prompt for LangGraph MCP Agent",
        tags={"project": "langgraph-mcp-agent", "author": "data-team", "language": "en"},
    )

    print(f"✓ Created prompt: {prompt.name} (version {prompt.version})")
    return prompt


def update_prompt_with_improvements():
    """Create an improved version of the prompt."""
    print("\nCreating improved version...")

    prompt = mlflow.genai.update_prompt(
        name="agent-system-prompt",
        template=(
            "You are an expert AI assistant specializing in Databricks and data engineering. "
            "You have access to MCP tools that allow you to:\n"
            "- Execute SQL queries and analyze data\n"
            "- Manage Unity Catalog objects (tables, schemas, catalogs)\n"
            "- Access workspace files and notebooks\n"
            "- Perform vector search operations\n\n"
            "Guidelines:\n"
            "1. Always explain your reasoning before using tools\n"
            "2. Break down complex tasks into steps\n"
            "3. Verify results and provide summaries\n"
            "4. Ask for clarification when needed\n"
            "5. Be proactive in suggesting helpful follow-up actions"
        ),
        commit_message="Enhanced prompt with detailed guidelines and capabilities",
    )

    print(f"✓ Updated prompt: {prompt.name} (version {prompt.version})")
    return prompt


def set_aliases(version: int):
    """Set aliases for prompt versions."""
    print(f"\nSetting aliases for version {version}...")

    client = MlflowClient()

    # Set production alias
    client.set_prompt_version_alias("agent-system-prompt", version=version, alias="production")
    print(f"✓ Set 'production' alias to version {version}")

    # Set champion alias
    client.set_prompt_version_alias("agent-system-prompt", version=version, alias="champion")
    print(f"✓ Set 'champion' alias to version {version}")


def list_prompt_versions():
    """List all versions of the agent system prompt."""
    print("\nListing all prompt versions...")

    client = MlflowClient()
    versions = client.search_prompt_versions("agent-system-prompt")

    print(f"\nFound {len(versions)} version(s):\n")
    for v in versions:
        print(f"Version {v.version}:")
        print(f"  Commit: {v.commit_message or 'No commit message'}")
        print(f"  Aliases: {v.aliases or 'None'}")
        print(f"  Created: {v.creation_timestamp}")
        print()


def load_and_display_prompt(version=None):
    """Load and display a prompt from the registry."""
    if version:
        print(f"\nLoading prompt version {version}...")
        prompt_uri = f"prompts:/agent-system-prompt/{version}"
    else:
        print("\nLoading latest prompt...")
        prompt_uri = "prompts:/agent-system-prompt"

    prompt = mlflow.genai.load_prompt(prompt_uri)

    print(f"\nPrompt: {prompt.name}")
    print(f"Version: {prompt.version}")
    print(f"Template:\n{'-' * 60}")
    print(prompt.template)
    print("-" * 60)

    return prompt


def search_prompts():
    """Search for prompts with filters."""
    print("\nSearching for all agent-related prompts...")

    prompts = mlflow.genai.search_prompts(filter_string="name LIKE '%agent%'")

    print(f"\nFound {len(prompts)} prompt(s):\n")
    for p in prompts:
        print(f"- {p.name} (version {p.version})")


def main():
    """Run the example workflow."""
    print("=" * 60)
    print("MLflow Prompt Registry Example")
    print("=" * 60)

    try:
        # Step 1: Create initial prompt
        initial_prompt = create_initial_prompt()

        # Step 2: Load and display it
        load_and_display_prompt(version=1)

        # Step 3: Create improved version
        improved_prompt = update_prompt_with_improvements()

        # Step 4: Set aliases to the improved version
        set_aliases(version=improved_prompt.version)

        # Step 5: List all versions
        list_prompt_versions()

        # Step 6: Search prompts
        search_prompts()

        print("\n" + "=" * 60)
        print("✓ Example completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Update your config to use the prompt registry:")
        print("   use_prompt_registry: true")
        print("   prompt_name: 'agent-system-prompt'")
        print("   prompt_version: 'production'")
        print("\n2. Deploy your agent to use the registered prompt")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure:")
        print("- MLflow tracking URI is configured")
        print("- You have permissions to create prompts")
        print("- The prompt doesn't already exist (or use update_prompt instead)")


if __name__ == "__main__":
    main()
