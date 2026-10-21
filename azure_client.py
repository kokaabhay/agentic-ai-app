
from openai import OpenAI

from config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_BASE_URL,
    AZURE_OPENAI_ENDPOINT,
    AZURE_CHAT_DEPLOYMENT,
    validate_config,
)

_client = None


def get_azure_client() -> OpenAI:
    """Create the shared Azure OpenAI-compatible client."""

    global _client

    if _client is None:
        validate_config()

        base_url = AZURE_OPENAI_BASE_URL or (
            f"{AZURE_OPENAI_ENDPOINT}/openai/v1/"
        )

        _client = OpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            base_url=base_url,
            timeout=60.0,
            max_retries=2,
        )

    return _client


def get_chat_deployment() -> str:
    return AZURE_CHAT_DEPLOYMENT
