"""Pick a chat model from Azure OpenAI or Databricks Model Serving based on env."""

import os

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel

load_dotenv()


def get_chat_model(temperature: float | None = None) -> BaseChatModel:
    # Newer models (e.g. Claude 5.x) reject `temperature`, so only send it when asked.
    extra = {} if temperature is None else {"temperature": temperature}
    provider = os.getenv("LLM_PROVIDER", "azure").lower()

    if provider == "databricks":
        from databricks_langchain import ChatDatabricks

        # Auth comes from ~/.databrickscfg (`databricks auth login`) or DATABRICKS_HOST/TOKEN.
        return ChatDatabricks(
            endpoint=os.environ["DATABRICKS_LLM_ENDPOINT"],
            **extra,
        )

    from langchain_openai import AzureChatOpenAI

    kwargs: dict = dict(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        **extra,
    )
    if os.getenv("AZURE_OPENAI_API_KEY"):
        kwargs["api_key"] = os.environ["AZURE_OPENAI_API_KEY"]
    else:
        # Keyless auth via `az login` (Entra ID). Needs "Cognitive Services OpenAI User" role.
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        kwargs["azure_ad_token_provider"] = get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        )
    return AzureChatOpenAI(**kwargs)
