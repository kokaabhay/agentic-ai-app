import json
import logging
from azure_client import get_azure_client, get_chat_deployment
from approval import save_pending_tool
from security import validate_name, validate_tool_spec

logger = logging.getLogger("tool_activity")
SUPPORTED_KINDS = {"web_search", "text_transform"}

def generate_tool(name: str, description: str, kind: str) -> dict:
    name = validate_name(name)
    if kind not in SUPPORTED_KINDS:
        raise ValueError(f"kind must be one of {sorted(SUPPORTED_KINDS)}")
    prompt = f"""
Return a JSON object with exactly these fields:
name, description, kind.
name={name}
description={description}
kind={kind}
This is a declarative tool definition, not executable Python.
Do not add other fields.
"""
    response = get_azure_client().chat.completions.create(
        model=get_chat_deployment(),
        messages=[
            {"role": "system", "content": "Return valid JSON only. Do not generate source code."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    spec = json.loads(response.choices[0].message.content or "{}")
    spec["name"] = name
    spec["kind"] = kind
    spec["description"] = description
    spec = validate_tool_spec(spec)
    logger.info("event=tool_generated_pending name=%s kind=%s", name, kind)
    return save_pending_tool(spec)

def modify_tool(name: str, description: str, kind: str) -> dict:
    # The approved existing version remains active until this new version is approved.
    return generate_tool(name, description, kind)
