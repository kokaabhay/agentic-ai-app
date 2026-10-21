import json
import logging
from pathlib import Path
from config import BASE_DIR, PENDING_DIR, APPROVALS_DIR, AGENTS_DIR, GENERATED_TOOLS_DIR
from security import validate_agent_source, validate_tool_spec, safe_child_path

logger = logging.getLogger("agent_activity")
PENDING_DIR.mkdir(parents=True, exist_ok=True)
APPROVALS_DIR.mkdir(parents=True, exist_ok=True)

def save_pending_agent(name: str, source: str) -> dict:
    spec = validate_agent_source(source)
    if spec["name"] != name:
        raise ValueError("Agent name does not match AGENT_SPEC.name.")
    path = safe_child_path(PENDING_DIR, f"agent_{name}.py.pending")
    path.write_text(source, encoding="utf-8")
    meta = {"kind": "agent", "name": name, "pending_file": path.name}
    (APPROVALS_DIR / f"agent_{name}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    logger.info("event=code_pending kind=agent name=%s", name)
    return meta

def save_pending_tool(spec: dict) -> dict:
    spec = validate_tool_spec(spec)
    path = safe_child_path(PENDING_DIR, f"tool_{spec['name']}.json.pending")
    path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    meta = {"kind": "tool", "name": spec["name"], "pending_file": path.name}
    (APPROVALS_DIR / f"tool_{spec['name']}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    logger.info("event=code_pending kind=tool name=%s", spec["name"])
    return meta

def list_pending() -> list[dict]:
    result = []
    for meta_path in sorted(APPROVALS_DIR.glob("*.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            pending = PENDING_DIR / meta["pending_file"]
            if pending.exists():
                result.append(meta)
        except (OSError, ValueError, KeyError):
            logger.exception("Could not read approval metadata file=%s", meta_path.name)
    return result

def approve_pending(kind: str, name: str) -> dict:
    if kind not in {"agent", "tool"}:
        raise ValueError("kind must be 'agent' or 'tool'")
    meta_path = APPROVALS_DIR / f"{kind}_{name}.json"
    if not meta_path.is_file():
        raise FileNotFoundError("No pending approval found.")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    pending = safe_child_path(PENDING_DIR, meta["pending_file"])
    if kind == "agent":
        source = pending.read_text(encoding="utf-8")
        spec = validate_agent_source(source)
        destination = safe_child_path(AGENTS_DIR, f"{name}.py")
        # Existing versions are preserved as .bak.
        if destination.exists():
            destination.with_suffix(".py.bak").write_text(destination.read_text(encoding="utf-8"), encoding="utf-8")
        destination.write_text(source, encoding="utf-8")
    else:
        spec = validate_tool_spec(json.loads(pending.read_text(encoding="utf-8")))
        destination = safe_child_path(GENERATED_TOOLS_DIR, f"{name}.json")
        if destination.exists():
            destination.with_suffix(".json.bak").write_text(destination.read_text(encoding="utf-8"), encoding="utf-8")
        destination.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    pending.unlink(missing_ok=True)
    meta_path.unlink(missing_ok=True)
    logger.info("event=code_approved kind=%s name=%s", kind, name)
    return {"status": "approved", "kind": kind, "name": name, "file": str(destination.relative_to(BASE_DIR))}
