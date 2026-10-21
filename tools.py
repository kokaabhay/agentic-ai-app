"""Built-in and approved generated tool registry.

Generated tools are declarative specs, not arbitrary Python source. This MVP
supports a small set of safe tool kinds; add new kinds in execute_tool only
after reviewing their implementation and permission requirements.
"""
import logging
from typing import Any
from ddgs import DDGS
from config import AGENT_ALLOW_INTERNET, GENERATED_TOOLS_DIR
from security import validate_name, validate_tool_spec

logger = logging.getLogger(__name__)
tool_logger = logging.getLogger("tool_activity")

def _web_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    if not AGENT_ALLOW_INTERNET:
        raise PermissionError("Internet access is disabled by configuration.")
    if not query or not query.strip():
        raise ValueError("query cannot be empty")
    max_results = max(1, min(int(max_results), 8))
    tool_logger.info("event=tool_started tool=web_search query_length=%d", len(query))
    with DDGS() as client:
        results = client.text(query, max_results=max_results)
        return [{"title": str(x.get("title", "")), "url": str(x.get("href", "")), "snippet": str(x.get("body", ""))} for x in results]

def _text_transform(text: str, operation: str = "uppercase") -> str:
    if operation == "uppercase":
        return text.upper()
    if operation == "lowercase":
        return text.lower()
    if operation == "word_count":
        return str(len(text.split()))
    if operation == "reverse":
        return text[::-1]
    raise ValueError("Supported operations: uppercase, lowercase, word_count, reverse")

def get_available_tools(allowed_tools: set[str] | None = None) -> list[dict[str, str]]:
    registry = {
        "web_search": "Search the public web. Arguments: query, max_results (optional).",
        "text_transform": "Transform text. Arguments: text, operation (uppercase/lowercase/word_count/reverse).",
    }
    for path in GENERATED_TOOLS_DIR.glob("*.json"):
        try:
            import json
            spec = validate_tool_spec(json.loads(path.read_text(encoding="utf-8")))
            registry[spec["name"]] = spec["description"]
        except Exception:
            logger.exception("Ignoring invalid generated tool file=%s", path.name)
    if allowed_tools is not None:
        registry = {k: v for k, v in registry.items() if k in allowed_tools}
    return [{"name": name, "description": desc} for name, desc in registry.items()]

def execute_tool(name: str, arguments: dict[str, Any], allowed_tools: set[str]) -> Any:
    if name not in allowed_tools:
        raise PermissionError(f"Tool '{name}' is not granted to this agent.")
    tool_logger.info("event=tool_invoked tool=%s", name)
    if name == "web_search":
        return _web_search(**arguments)
    if name == "text_transform":
        return _text_transform(**arguments)
    # Generated tools map to reviewed built-in kinds only.
    import json
    path = GENERATED_TOOLS_DIR / f"{name}.json"
    if not path.is_file():
        raise ValueError(f"Unknown tool: {name}")
    spec = validate_tool_spec(json.loads(path.read_text(encoding="utf-8")))
    if spec["kind"] == "web_search":
        return _web_search(**arguments)
    if spec["kind"] == "text_transform":
        return _text_transform(**arguments)
    raise ValueError("Unsupported tool kind.")
