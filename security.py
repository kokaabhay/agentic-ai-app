"""Safety checks for generated agent/tool artifacts.

These checks reduce accidental mistakes; they are NOT a security sandbox.
Generated agents in this MVP are declarative specifications and are not executed
as arbitrary Python. Do not activate arbitrary generated tool source on a
machine with secrets. Use an OS/container sandbox before supporting that.
"""
import ast
import re
from pathlib import Path

NAME_RE = re.compile(r"^[a-z][a-z0-9_]{1,48}$")

def validate_name(name: str) -> str:
    if not NAME_RE.fullmatch(name):
        raise ValueError("Names must be 2-49 characters: lowercase letters, digits, underscores; start with a letter.")
    return name

def validate_agent_source(source: str) -> dict:
    """Allow only a module-level AGENT_SPEC dictionary assignment."""
    tree = ast.parse(source)
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Assign):
        raise ValueError("Agent file must contain only one AGENT_SPEC assignment.")
    node = tree.body[0]
    if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name) or node.targets[0].id != "AGENT_SPEC":
        raise ValueError("Agent file must assign a single AGENT_SPEC variable.")
    if not isinstance(node.value, ast.Dict):
        raise ValueError("AGENT_SPEC must be a literal dictionary.")
    # literal_eval prevents execution of the file.
    import ast as _ast
    spec = _ast.literal_eval(node.value)
    required = {"name", "description", "system_prompt", "allowed_tools"}
    if not isinstance(spec, dict) or not required.issubset(spec):
        raise ValueError(f"AGENT_SPEC must include {sorted(required)}")
    validate_name(spec["name"])
    if not isinstance(spec["allowed_tools"], list) or not all(isinstance(x, str) for x in spec["allowed_tools"]):
        raise ValueError("allowed_tools must be a list of strings.")
    return spec

def validate_tool_spec(spec: dict) -> dict:
    required = {"name", "description", "kind"}
    if not isinstance(spec, dict) or not required.issubset(spec):
        raise ValueError(f"Tool spec must include {sorted(required)}")
    validate_name(spec["name"])
    if spec["kind"] not in {"web_search", "text_transform"}:
        raise ValueError("Supported generated tool kinds: web_search, text_transform.")
    return spec

def safe_child_path(root: Path, filename: str) -> Path:
    if Path(filename).name != filename:
        raise ValueError("Only simple filenames are allowed.")
    root = root.resolve()
    target = (root / filename).resolve()
    if not target.is_relative_to(root):
        raise ValueError("Path escapes allowed directory.")
    return target
