
import logging
from typing import Any, Callable

from ddgs import DDGS

logger = logging.getLogger(__name__)
tool_logger = logging.getLogger("tool_activity")

# Tool name -> tool implementation and description.
TOOL_REGISTRY: dict[str, dict[str, Any]] = {}


def register_tool(
    name: str,
    description: str,
) -> Callable:
    """Register a function so approved agents can use it."""

    def decorator(function: Callable) -> Callable:
        if name in TOOL_REGISTRY:
            raise ValueError(f"Tool already registered: {name}")

        TOOL_REGISTRY[name] = {
            "description": description,
            "function": function,
        }

        logger.info("Registered tool: %s", name)
        return function

    return decorator


@register_tool(
    name="web_search",
    description=(
        "Search the public internet for information. "
        "Input: query (string), max_results (integer, optional)."
    ),
)
def web_search(
    query: str,
    max_results: int = 5,
) -> list[dict[str, str]]:
    """Search public websites and return concise result metadata."""

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    max_results = max(1, min(max_results, 8))

    tool_logger.info(
        "event=tool_started tool=web_search query_length=%d",
        len(query),
    )

    try:
        with DDGS() as search_client:
            results = search_client.text(
                query,
                max_results=max_results,
            )

            # Return only selected fields, not arbitrary objects.
            cleaned_results = [
                {
                    "title": str(item.get("title", "")),
                    "url": str(item.get("href", "")),
                    "snippet": str(item.get("body", "")),
                }
                for item in results
            ]

        tool_logger.info(
            "event=tool_completed tool=web_search result_count=%d",
            len(cleaned_results),
        )

        return cleaned_results

    except Exception:
        # Avoid logging credentials or full request internals.
        tool_logger.exception(
            "event=tool_failed tool=web_search"
        )
        raise


def get_available_tools() -> list[dict[str, str]]:
    """Return tool descriptions without exposing implementation code."""

    return [
        {
            "name": name,
            "description": item["description"],
        }
        for name, item in TOOL_REGISTRY.items()
    ]


def execute_tool(
    name: str,
    arguments: dict[str, Any],
    allowed_tools: set[str],
) -> Any:
    """Execute a tool only when the caller has been granted access."""

    if name not in allowed_tools:
        raise PermissionError(
            f"Access to tool '{name}' has not been granted"
        )

    if name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {name}")

    tool = TOOL_REGISTRY[name]

    tool_logger.info("event=tool_invoked tool=%s", name)

    return tool["function"](**arguments)
