
import argparse
import logging
import uvicorn

from config import APP_NAME
from logger_config import setup_logging
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def run_cli() -> None:
    from master_agent import handle_request

    print(f"{APP_NAME} CLI. Type 'exit' to quit.")

    while True:
        try:
            message = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if message.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        if not message:
            continue

        try:
            result = handle_request(message)

            print(
                "\nMaster:",
                result.get("answer")
                or result.get("question")
                or result.get("message")
                or result,
            )

            if result.get("status") == "pending_approval":
                print(
                    "Review pending code via the /approvals endpoint "
                    "or approve it through Python."
                )

        except Exception:
            logging.getLogger(__name__).exception("CLI request failed")
            print("Request failed. Check logs/app.log.")


def run_api() -> None:
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


def create_app() -> FastAPI:
    from api.routes import router

    application = FastAPI(
        title=APP_NAME,
        version="0.1.0",
    )

    application.include_router(router)

    return application


setup_logging()
app = create_app()






def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    # Use OpenAPI 3.0.3 for Swagger file-upload compatibility.
    schema["openapi"] = "3.0.3"

    components = schema.setdefault("components", {}).setdefault(
        "schemas", {}
    )

    request_body = (
        schema["paths"]["/chat"]["post"]["requestBody"]
        ["content"]["multipart/form-data"]["schema"]
    )

    body_ref = request_body.get("$ref", "")
    body_name = body_ref.rsplit("/", 1)[-1]

    body_schema = components.get(body_name, {})

    # Define files directly as an array of binary uploads.
    properties = body_schema.setdefault("properties", {})
    properties["files"] = {
        "type": "array",
        "items": {
            "type": "string",
            "format": "binary",
        },
        "title": "Files",
    }

    # Files must be optional; message remains required.
    required = body_schema.get("required", [])
    if "files" in required:
        required.remove("files")

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi

