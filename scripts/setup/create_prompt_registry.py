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

    client = MlflowClient()

    # First, create the prompt (name only)
    try:
        prompt = client.create_prompt(
            name="agent-system-prompt",
            description="System prompt for LangGraph MCP Agent",
            tags={"project": "langgraph-mcp-agent", "author": "data-team", "language": "en"},
        )
        print(f"✓ Created prompt: {prompt.name}")
    except Exception as e:
        if "RESOURCE_ALREADY_EXISTS" in str(e):
            print(f"✓ Prompt 'agent-system-prompt' already exists")
        else:
            raise

    # Then create the first version with the template
    prompt_version = client.create_prompt_version(
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
        description="Initial system prompt for LangGraph MCP Agent",
        tags={"version": "v1", "status": "initial"},
    )

    print(f"✓ Created prompt version: {prompt_version.version}")
    return prompt_version


def update_prompt_with_improvements():
    """Create an improved version of the prompt."""
    print("\nCreating improved version...")

    client = MlflowClient()

    prompt_version = client.create_prompt_version(
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
        description="Enhanced prompt with detailed guidelines and capabilities",
        tags={"version": "v2", "status": "improved"},
    )

    print(f"✓ Created prompt version: {prompt_version.version}")
    return prompt_version


def set_aliases(version: int):
    """Set aliases for prompt versions."""
    print(f"\nSetting aliases for version {version}...")

    client = MlflowClient()

    # Set production alias
    client.set_prompt_alias("agent-system-prompt", version=version, alias="production")
    print(f"✓ Set 'production' alias to version {version}")

    # Set champion alias
    client.set_prompt_alias("agent-system-prompt", version=version, alias="champion")
    print(f"✓ Set 'champion' alias to version {version}")


def list_prompt_versions():
    """List all versions of the agent system prompt."""
    print("\nListing all prompt versions...")

    client = MlflowClient()

    try:
        versions = client.search_prompt_versions("agent-system-prompt")
        print(f"\nFound {len(versions)} version(s):\n")
        for v in versions:
            print(f"Version {v.version}:")
            print(f"  Description: {v.description or 'No description'}")
            print(f"  Tags: {v.tags or 'None'}")
            print(f"  Created: {v.creation_timestamp}")
            print()
    except Exception as e:
        # Fall back to getting prompt info if search isn't supported
        print(f"Note: Full version listing requires Unity Catalog registry")
        print(f"Showing prompt info instead...\n")
        try:
            prompt = client.get_prompt("agent-system-prompt")
            print(f"Prompt: {prompt.name}")
            print(f"Description: {prompt.description or 'No description'}")
            print(f"Tags: {prompt.tags or 'None'}")
            print(f"\nTo see all versions, use Unity Catalog registry or check MLflow UI")
        except Exception as inner_e:
            print(f"Could not retrieve prompt info: {inner_e}")


def load_and_display_prompt(version=None):
    """Load and display a prompt from the registry."""
    client = MlflowClient()

    if version:
        print(f"\nLoading prompt version {version}...")
        prompt_version = client.get_prompt_version("agent-system-prompt", version=version)
    else:
        print("\nLoading latest prompt...")
        versions = client.search_prompt_versions("agent-system-prompt", order_by=["version DESC"], max_results=1)
        if versions:
            prompt_version = versions[0]
        else:
            print("No prompt versions found")
            return None

    print(f"\nPrompt: agent-system-prompt")
    print(f"Version: {prompt_version.version}")
    print(f"Template:\n{'-' * 60}")
    print(prompt_version.template)
    print("-" * 60)

    return prompt_version


def search_prompts():
    """Search for prompts with filters."""
    print("\nSearching for all agent-related prompts...")

    client = MlflowClient()

    try:
        prompts = client.search_prompts(filter_string="name LIKE '%agent%'")
        print(f"\nFound {len(prompts)} prompt(s):\n")
        for p in prompts:
            print(f"- {p.name}")
            # Get versions for each prompt
            try:
                versions = client.search_prompt_versions(p.name)
                print(f"  Versions: {len(versions)}")
            except:
                print(f"  Versions: Use Unity Catalog registry to list versions")
    except Exception as e:
        print(f"Note: Search requires Unity Catalog registry")
        print(f"The prompt 'agent-system-prompt' has been created successfully.")


def main():
    """Run the example workflow."""
    print("=" * 60)
    print("MLflow Prompt Registry Example")
    print("=" * 60)

    try:
        # Step 1: Create initial prompt (or skip if exists)
        try:
            initial_prompt = create_initial_prompt()
            version_1 = 1
        except Exception as e:
            if "already exists" in str(e):
                print("Prompt already exists, creating new version instead...")
                client = MlflowClient()
                # Create a new version
                initial_prompt = client.create_prompt_version(
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
                    description="Updated system prompt for LangGraph MCP Agent",
                    tags={"version": "updated", "status": "active"},
                )
                print(f"✓ Created new prompt version: {initial_prompt.version}")
                version_1 = initial_prompt.version
            else:
                raise

        # Step 2: Load and display it
        load_and_display_prompt(version=version_1)

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
        print("\nYour prompt versions:")
        print(f"- Version {version_1}: Initial/Updated prompt")
        print(f"- Version {improved_prompt.version}: Improved prompt (production, champion)")
        print("\nNext steps:")
        print("1. Your config is already set to use the prompt registry:")
        print("   use_prompt_registry: true")
        print("   prompt_name: 'agent-system-prompt'")
        print("   prompt_version: 'latest'  # or 'production' or specific version")
        print("\n2. Deploy your agent to use the registered prompt:")
        print("   databricks bundle deploy -t dev")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure:")
        print("- MLflow tracking URI is configured")
        print("- You have permissions to create prompts")
        print("- The prompt doesn't already exist (or use update_prompt instead)")


if __name__ == "__main__":
    main()
