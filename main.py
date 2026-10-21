import argparse
import logging
import uvicorn
from config import APP_NAME
from logger_config import setup_logging

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
            print("\nMaster:", result.get("answer") or result.get("question") or result.get("message") or result)
            if result.get("status") == "pending_approval":
                print("Review pending code via the /approvals endpoint or approve it through Python.")
        except Exception:
            logging.getLogger(__name__).exception("CLI request failed")
            print("Request failed. Check logs/app.log.")

def run_api() -> None:
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)

def create_app():
    from fastapi import FastAPI
    from api.routes import router
    app = FastAPI(title=APP_NAME, version="0.1.0")
    app.include_router(router)
    return app

setup_logging()
app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["cli", "api"], default="cli")
    args = parser.parse_args()
    if args.mode == "cli":
        run_cli()
    else:
        run_api()
