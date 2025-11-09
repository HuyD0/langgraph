"""Integration tests for MLflow Prompt Registry.

These tests require a configured MLflow tracking server and appropriate permissions.
They can be run against a Databricks workspace to validate the full prompt registry workflow.

NOTE: These tests require MLflow 2.9+ with genai module support.
They will be skipped if the module is not available.
"""

import pytest

# Check if mlflow.genai is available
try:
    import mlflow.genai

    MLFLOW_GENAI_AVAILABLE = hasattr(mlflow.genai, "create_prompt")
except (ImportError, AttributeError):
    MLFLOW_GENAI_AVAILABLE = False

# Mark all tests in this module as integration tests
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not MLFLOW_GENAI_AVAILABLE, reason="mlflow.genai module not available (requires MLflow 2.9+ with genai support)"
    ),
]


@pytest.fixture(scope="module")
def test_prompt_name():
    """Provide a unique test prompt name."""
    import uuid

    return f"test-agent-prompt-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def created_prompt(test_prompt_name):
    """Create a test prompt and clean it up after tests."""
    import mlflow
    from mlflow import MlflowClient

    # Create initial prompt
    prompt = mlflow.genai.create_prompt(
        name=test_prompt_name,
        template="You are a test assistant for integration testing.",
        commit_message="Initial test prompt",
        tags={"test": "true", "environment": "integration"},
    )

    yield prompt

    # Cleanup: Delete all versions of the test prompt
    client = MlflowClient()
    try:
        versions = client.search_prompt_versions(test_prompt_name)
        for version in versions:
            client.delete_prompt_version(test_prompt_name, version.version)
    except Exception as e:
        print(f"Warning: Failed to cleanup test prompt {test_prompt_name}: {e}")


class TestPromptRegistryCreation:
    """Test creating and updating prompts in the registry."""

    def test_create_prompt(self, test_prompt_name):
        """Test creating a new prompt."""
        import mlflow

        prompt = mlflow.genai.create_prompt(
            name=test_prompt_name,
            template="Test prompt for creation.",
            commit_message="Test creation",
        )

        assert prompt.name == test_prompt_name
        assert prompt.version == 1
        assert prompt.template == "Test prompt for creation."
        assert prompt.commit_message == "Test creation"

        # Cleanup
        from mlflow import MlflowClient

        client = MlflowClient()
        client.delete_prompt_version(test_prompt_name, 1)

    def test_update_prompt(self, created_prompt, test_prompt_name):
        """Test updating a prompt to create a new version."""
        import mlflow

        updated_prompt = mlflow.genai.update_prompt(
            name=test_prompt_name,
            template="Updated test prompt.",
            commit_message="Test update",
        )

        assert updated_prompt.name == test_prompt_name
        assert updated_prompt.version == 2
        assert updated_prompt.template == "Updated test prompt."

    def test_create_chat_prompt(self, test_prompt_name):
        """Test creating a chat-style prompt."""
        import mlflow

        chat_template = [
            {"role": "system", "content": "You are a test assistant."},
            {"role": "user", "content": "{{question}}"},
        ]

        prompt = mlflow.genai.create_prompt(
            name=f"{test_prompt_name}-chat",
            template=chat_template,
            commit_message="Chat prompt test",
        )

        assert prompt.name == f"{test_prompt_name}-chat"
        assert not prompt.is_text_prompt
        assert len(prompt.template) == 2

        # Cleanup
        from mlflow import MlflowClient

        client = MlflowClient()
        client.delete_prompt_version(f"{test_prompt_name}-chat", 1)


class TestPromptRegistryLoading:
    """Test loading prompts from the registry."""

    def test_load_prompt_by_version(self, created_prompt, test_prompt_name):
        """Test loading a specific prompt version."""
        from langgraph_agent.utils.mlflow_setup import load_prompt_from_registry

        prompt_text = load_prompt_from_registry(test_prompt_name, prompt_version=1)

        assert prompt_text == "You are a test assistant for integration testing."

    def test_load_latest_prompt(self, created_prompt, test_prompt_name):
        """Test loading the latest version."""
        import mlflow
        from langgraph_agent.utils.mlflow_setup import load_prompt_from_registry

        # Create a second version
        mlflow.genai.update_prompt(
            name=test_prompt_name,
            template="Latest version text.",
            commit_message="Version 2",
        )

        prompt_text = load_prompt_from_registry(test_prompt_name)

        # Should load version 2
        assert prompt_text == "Latest version text."

    def test_load_prompt_with_alias(self, created_prompt, test_prompt_name):
        """Test loading prompt by alias."""
        from mlflow import MlflowClient
        from langgraph_agent.utils.mlflow_setup import load_prompt_from_registry

        # Set an alias
        client = MlflowClient()
        client.set_prompt_version_alias(test_prompt_name, version=1, alias="test-stable")

        prompt_text = load_prompt_from_registry(test_prompt_name, prompt_version="test-stable")

        assert prompt_text == "You are a test assistant for integration testing."

        # Cleanup alias
        client.delete_prompt_version_alias(test_prompt_name, alias="test-stable")

    def test_load_nonexistent_prompt_with_fallback(self):
        """Test loading a prompt that doesn't exist with fallback."""
        from langgraph_agent.utils.mlflow_setup import load_prompt_from_registry

        prompt_text = load_prompt_from_registry(
            "nonexistent-prompt-12345",
            fallback_prompt="Fallback text",
        )

        assert prompt_text == "Fallback text"

    def test_load_nonexistent_prompt_without_fallback(self):
        """Test that loading nonexistent prompt without fallback raises error."""
        from langgraph_agent.utils.mlflow_setup import load_prompt_from_registry

        with pytest.raises(Exception):
            load_prompt_from_registry("nonexistent-prompt-12345")


class TestPromptRegistryVersioning:
    """Test prompt versioning features."""

    def test_list_prompt_versions(self, created_prompt, test_prompt_name):
        """Test listing all versions of a prompt."""
        import mlflow
        from mlflow import MlflowClient

        # Create multiple versions
        mlflow.genai.update_prompt(test_prompt_name, template="Version 2", commit_message="v2")
        mlflow.genai.update_prompt(test_prompt_name, template="Version 3", commit_message="v3")

        client = MlflowClient()
        versions = client.search_prompt_versions(test_prompt_name)

        assert len(versions) == 3
        assert all(v.version in [1, 2, 3] for v in versions)

    def test_prompt_version_tags(self, created_prompt, test_prompt_name):
        """Test setting and getting version tags."""
        import mlflow

        # Set version-level tag
        mlflow.genai.set_prompt_version_tag(test_prompt_name, 1, "status", "tested")

        # Get tags
        prompt = mlflow.genai.load_prompt(f"prompts:/{test_prompt_name}/1")
        assert prompt.tags.get("status") == "tested"

        # Cleanup
        mlflow.genai.delete_prompt_version_tag(test_prompt_name, 1, "status")

    def test_prompt_level_tags(self, created_prompt, test_prompt_name):
        """Test setting prompt-level tags."""
        import mlflow

        # Set prompt-level tag
        mlflow.genai.set_prompt_tag(test_prompt_name, "project", "langgraph-test")

        # Get tags
        tags = mlflow.genai.get_prompt_tags(test_prompt_name)
        assert tags.get("project") == "langgraph-test"

        # Cleanup
        mlflow.genai.delete_prompt_tag(test_prompt_name, "project")


class TestPromptRegistryAliases:
    """Test prompt alias management."""

    def test_set_and_get_alias(self, created_prompt, test_prompt_name):
        """Test setting and using an alias."""
        import mlflow
        from mlflow import MlflowClient

        client = MlflowClient()

        # Set alias
        client.set_prompt_version_alias(test_prompt_name, version=1, alias="production")

        # Load by alias
        prompt = mlflow.genai.load_prompt(f"prompts:/{test_prompt_name}@production")

        assert prompt.version == 1
        assert "production" in prompt.aliases

        # Cleanup
        client.delete_prompt_version_alias(test_prompt_name, alias="production")

    def test_move_alias_to_new_version(self, created_prompt, test_prompt_name):
        """Test moving an alias from one version to another."""
        import mlflow
        from mlflow import MlflowClient

        # Create version 2
        mlflow.genai.update_prompt(test_prompt_name, template="Version 2", commit_message="v2")

        client = MlflowClient()

        # Set alias to v1
        client.set_prompt_version_alias(test_prompt_name, version=1, alias="champion")
        prompt_v1 = mlflow.genai.load_prompt(f"prompts:/{test_prompt_name}@champion")
        assert prompt_v1.version == 1

        # Move alias to v2
        client.set_prompt_version_alias(test_prompt_name, version=2, alias="champion")
        prompt_v2 = mlflow.genai.load_prompt(f"prompts:/{test_prompt_name}@champion")
        assert prompt_v2.version == 2

        # Cleanup
        client.delete_prompt_version_alias(test_prompt_name, alias="champion")


class TestPromptRegistrySearch:
    """Test searching for prompts."""

    def test_search_prompts_by_tag(self, created_prompt, test_prompt_name):
        """Test searching prompts by tag."""
        import mlflow

        # Prompts created with test=true tag in fixture
        results = mlflow.genai.search_prompts(filter_string="tag.test='true'")

        # Should find at least our test prompt
        prompt_names = [p.name for p in results]
        assert test_prompt_name in prompt_names

    def test_search_prompts_by_name(self, created_prompt, test_prompt_name):
        """Test searching prompts by name pattern."""
        import mlflow

        results = mlflow.genai.search_prompts(filter_string=f"name='{test_prompt_name}'")

        assert len(results) >= 1
        assert any(p.name == test_prompt_name for p in results)


@pytest.mark.slow
class TestPromptRegistryWithAgent:
    """Test prompt registry integration with the agent."""

    @pytest.mark.skip(reason="Agent tests require full environment setup")
    def test_agent_loads_prompt_from_registry(self, created_prompt, test_prompt_name, monkeypatch):
        """Test that agent can load and use a prompt from the registry."""
        # Set environment to use prompt registry
        monkeypatch.setenv("USE_PROMPT_REGISTRY", "true")
        monkeypatch.setenv("PROMPT_NAME", test_prompt_name)
        monkeypatch.setenv("PROMPT_VERSION", "1")

        from langgraph_agent.app import create_agent

        # This should create an agent using the prompt from registry
        # Note: May fail if endpoint doesn't exist, which is expected in test env
        try:
            agent = create_agent()
            # If we get here, agent was created successfully
            assert agent is not None
        except Exception as e:
            # Expected in test environment without full Databricks setup
            # Just verify the prompt loading part worked
            if "endpoint" not in str(e).lower():
                raise
