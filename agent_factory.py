import json
import logging
from pathlib import Path
from azure_client import get_azure_client, get_chat_deployment
from approval import save_pending_agent
from config import AGENTS_DIR
from security import validate_name, validate_agent_source

logger = logging.getLogger("agent_activity")

def list_agents() -> list[dict]:
    agents = []
    for path in sorted(AGENTS_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        try:
            spec = validate_agent_source(path.read_text(encoding="utf-8"))
            agents.append({k: spec[k] for k in ("name", "description", "allowed_tools")})
        except Exception:
            logger.exception("Ignoring invalid agent file=%s", path.name)
    return agents

def generate_agent(name: str, description: str, allowed_tools: list[str]) -> dict:
    name = validate_name(name)
    if not description.strip():
        raise ValueError("description cannot be empty")
    prompt = f"""
Create a specialist agent specification as a Python source file.
The file MUST contain exactly one assignment named AGENT_SPEC whose value
is a literal Python dictionary. No imports, functions, classes, expressions,
or executable statements are allowed.
Required keys: name, description, system_prompt, allowed_tools.
Name: {name}
Description: {description}
Allowed tools: {json.dumps(allowed_tools)}
system_prompt must explain the specialist's role, limits, and output style.
allowed_tools must be a subset of the provided allowed tools.
Return only Python source code, no markdown fences.
"""
    response = get_azure_client().chat.completions.create(
        model=get_chat_deployment(),
        messages=[
            {"role": "system", "content": "Generate only a safe declarative Python dictionary. Never include executable code."},
            {"role": "user", "content": prompt},
        ],
        temperature=1,
    )
    source = (response.choices[0].message.content or "").strip()
    if source.startswith("```"):
        source = source.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    spec = validate_agent_source(source)
    if spec["name"] != name:
        raise ValueError("Model returned a different agent name.")
    if not set(spec["allowed_tools"]).issubset(set(allowed_tools)):
        raise ValueError("Generated agent requested unapproved tools.")
    logger.info("event=agent_generated_pending name=%s", name)
    return save_pending_agent(name, source)

def modify_agent(name: str, description: str, allowed_tools: list[str]) -> dict:
    name = validate_name(name)
    path = AGENTS_DIR / f"{name}.py"
    if not path.is_file():
        raise FileNotFoundError(f"Agent '{name}' does not exist.")
    current = validate_agent_source(path.read_text(encoding="utf-8"))
    revised_description = f"{description}\nPrevious configuration: {json.dumps(current)}"
    return generate_agent(name, revised_description, allowed_tools)
