# Agentic AI Application

A beginner-friendly multi-agent prototype using an Azure OpenAI-compatible Foundry deployment, CLI, and FastAPI.

## Features

- Master agent selects direct answering, tool use, delegation, agent creation/modification, or tool creation/modification.
- Agent definitions are Python files containing a declarative `AGENT_SPEC` dictionary.
- Generated agents and tools are saved as pending and require approval before activation.
- Generated tools are declarative JSON definitions supporting the built-in `web_search` and `text_transform` implementations.
- Controlled web search through a dedicated tool.
- Rotating logs in `logs/`.
- CLI and FastAPI interfaces.

## Important safety boundary

This MVP deliberately does not execute generated Python source. Agent `.py` files must contain only a literal `AGENT_SPEC` dictionary and are parsed with `ast.literal_eval`. Generated tools are declarative JSON mapped to reviewed built-in implementations. This reduces the risks of model-generated executable code.

The current application process is not a full security sandbox. Do not add arbitrary Python tool execution without a separately configured OS/container sandbox, least-privilege account, filesystem isolation, network controls, and resource limits. The FastAPI approval endpoints have no authentication in this local prototype: keep the server bound to localhost and do not expose it to an untrusted network.

## Setup

1. Install Python 3.11 or newer.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env`.
5. Configure the Azure OpenAI-compatible endpoint, key, and deployment name. Never commit `.env`.

The default client uses the Azure OpenAI-compatible `/openai/v1/` endpoint. If Foundry shows a different supported inference endpoint, set `AZURE_OPENAI_BASE_URL` accordingly. The deployment name must exactly match the deployment in your resource.

## Run the CLI

```powershell
python main.py --mode cli
```

Enter `exit` to stop.

## Run the API

```powershell
python main.py --mode api
```

Open `http://127.0.0.1:8000/docs`.

- `POST /chat`: submit a request.
- `GET /approvals`: list pending agent/tool changes.
- `POST /approvals/approve`: approve a pending item with JSON body such as `{"kind":"agent","name":"research_agent"}`.
- `GET /health`: health check.

Only approve code you intended to generate. This prototype has no authentication on approval endpoints; use it locally only.

## Logs

- `logs/app.log`
- `logs/agent_activity.log`
- `logs/communication.log`
- `logs/tool_activity.log`

Logs are rotated. Avoid logging secrets or sensitive user content.

## Current limitations

- Generated agent specs can use approved registered tools, but the model is responsible for following their declared role.
- Generated tools are limited to two reviewed implementation kinds. Adding a genuinely new kind requires a developer to implement and review the corresponding handler.
- Existing tool modifications remain pending until approved.
- The web search provider may change behavior or availability; check its terms and operational requirements.
- Before production use, add authentication, authorization, rate limiting, request-size limits, audit retention policies, robust URL validation, and sandboxed execution.
