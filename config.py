
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"true", "1", "yes", "on"}


APP_NAME = os.getenv(
    "APP_NAME",
    "Agentic AI Application",
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

AZURE_OPENAI_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT", ""
).rstrip("/")

AZURE_OPENAI_BASE_URL = os.getenv(
    "AZURE_OPENAI_BASE_URL", ""
).strip()

AZURE_OPENAI_API_KEY = os.getenv(
    "AZURE_OPENAI_API_KEY", ""
)

AZURE_CHAT_DEPLOYMENT = os.getenv(
    "AZURE_CHAT_DEPLOYMENT",
    "gpt-5.5-nano",
)

AGENT_TIMEOUT_SECONDS = int(
    os.getenv("AGENT_TIMEOUT_SECONDS", "30")
)

MAX_AGENT_STEPS = int(
    os.getenv("MAX_AGENT_STEPS", "8")
)

MAX_AGENT_TOOL_CALLS = int(
    os.getenv("MAX_AGENT_TOOL_CALLS", "10")
)

REQUIRE_CODE_APPROVAL = get_bool(
    "REQUIRE_CODE_APPROVAL", True
)

AGENT_ALLOW_INTERNET = get_bool(
    "AGENT_ALLOW_INTERNET", True
)

AGENT_WORKSPACE = (
    BASE_DIR
    / os.getenv(
        "AGENT_WORKSPACE",
        "runtime/workspaces",
    )
).resolve()

LOGS_DIR = BASE_DIR / "logs"
AGENTS_DIR = BASE_DIR / "agents"
GENERATED_TOOLS_DIR = BASE_DIR / "generated_tools"


def validate_config() -> None:
    """Check required configuration before starting the application."""

    if not AZURE_OPENAI_API_KEY:
        raise ValueError(
            "AZURE_OPENAI_API_KEY is missing from .env"
        )

    if not AZURE_OPENAI_BASE_URL and not AZURE_OPENAI_ENDPOINT:
        raise ValueError(
            "Configure AZURE_OPENAI_ENDPOINT or "
            "AZURE_OPENAI_BASE_URL in .env"
        )

    if AGENT_TIMEOUT_SECONDS <= 0:
        raise ValueError(
            "AGENT_TIMEOUT_SECONDS must be positive"
        )

    if MAX_AGENT_STEPS < 1 or MAX_AGENT_TOOL_CALLS < 1:
        raise ValueError(
            "Agent step and tool-call limits must be positive"
        )
