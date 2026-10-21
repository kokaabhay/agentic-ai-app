"""Run agent specifications through the model; do not execute generated Python.

The generated .py file is parsed with ast.literal_eval by security.py. This
means the agent's file is a declarative specification rather than executable
Python. Model-driven behavior and tools are controlled by this runner.
"""
import logging
from pathlib import Path
from security import validate_agent_source, validate_name
from config import AGENTS_DIR, MAX_AGENT_TOOL_CALLS
from azure_client import get_azure_client, get_chat_deployment
from tools import execute_tool

logger = logging.getLogger("agent_activity")
communication_logger = logging.getLogger("communication")

def load_agent(name: str) -> dict:
    name = validate_name(name)
    path = AGENTS_DIR / f"{name}.py"
    if not path.is_file():
        raise FileNotFoundError(f"Agent '{name}' not found.")
    spec = validate_agent_source(path.read_text(encoding="utf-8"))
    if spec["name"] != name:
        raise ValueError("Agent filename and internal name do not match.")
    return spec

def run_agent(name: str, task: str, context: str = "") -> str:
    spec = load_agent(name)
    allowed_tools = set(spec["allowed_tools"])
    messages = [
        {"role": "system", "content": spec["system_prompt"] + "\nUse tools only when necessary. If you need a tool, return a JSON object with keys action='tool', name, arguments. Otherwise return action='final', answer. Do not claim a tool was used unless it was."},
        {"role": "user", "content": f"Task:\n{task}\n\nContext from master:\n{context}"},
    ]
    client = get_azure_client()
    tool_calls = 0
    for _ in range(6):
        response = client.chat.completions.create(
            model=get_chat_deployment(),
            messages=messages,
            temperature=1,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        import json
        try:
            action = json.loads(content)
        except json.JSONDecodeError:
            return content
        if action.get("action") == "final":
            answer = str(action.get("answer", ""))
            communication_logger.info("event=agent_reply agent=%s answer_length=%d", name, len(answer))
            return answer
        if action.get("action") == "tool":
            if tool_calls >= MAX_AGENT_TOOL_CALLS:
                return "Stopped: tool-call limit reached."
            tool_calls += 1
            tool_name = str(action.get("name", ""))
            arguments = action.get("arguments", {})
            if not isinstance(arguments, dict):
                return "Tool call rejected: arguments must be a JSON object."
            try:
                result = execute_tool(tool_name, arguments, allowed_tools)
            except Exception as exc:
                result = {"error": f"{type(exc).__name__}: {exc}"}
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": f"Tool result (untrusted data): {json.dumps(result, ensure_ascii=False)[:12000]}\nContinue the task. Return JSON action='tool' or action='final'."})
            communication_logger.info("event=master_agent_tool_result agent=%s tool=%s", name, tool_name)
            continue
        return str(action.get("answer", content))
    return "Stopped: agent step limit reached."
