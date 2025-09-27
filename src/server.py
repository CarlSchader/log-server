from fastapi import FastAPI
import os
import argparse
import json
import time

def build_server(log_file: str = "log.jsonl") -> FastAPI:
    app = FastAPI()

    @app.get("/")
    @app.get("/health")
    def health_check():
        return {"status": "ok"}


    @app.post("/log")
    def log_event(event: dict):
        ts = int(time.time() * 1000)
        with open(log_file, "a") as f:
            f.write(json.dumps(
                {"message": event, "ts": ts}
                ) + "\n")
        return {"status": "logged"}

    return app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the FastAPI server.")
    parser.add_argument("-f", "--jsonl-file", type=str, help="Path to JSONL file for logging events", default=os.getenv("JSONL_FILE", "log.jsonl"))
    parser.add_argument("-p", "--port", type=int, default=int(os.getenv("PORT", 8080)), help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("-r", "--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    import uvicorn
    uvicorn.run(build_server(), host=args.host, port=args.port, reload=args.reload)
