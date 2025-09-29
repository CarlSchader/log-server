from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import argparse
import json
import time
import jwt
from pydantic import BaseModel

class LogRequest(BaseModel):
    payload: dict

def build_server(jwt_secret: str, log_file: str = "log.jsonl") -> FastAPI:
    app = FastAPI()
    
    # JWT Configuration
    security = HTTPBearer()
    
    def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
        try:
            payload = jwt.decode(credentials.credentials, jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))


    @app.get("/")
    @app.get("/health")
    def health_check():
        return {"status": "ok"}


    @app.post("/log")
    async def log_event(request: Request, token: dict = Depends(verify_jwt)):
        try:
            body = await request.json()
            if not isinstance(body, dict):
                raise HTTPException(status_code=400, detail="Request body must be a JSON object")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        if "sub" not in token:
            raise HTTPException(status_code=400, detail="JWT token must contain 'sub' claim")

        sub = token["sub"]

        ts = int(time.time() * 1000)
        log_dict = {"ts": ts, "sub": sub, "payload": body}

        with open(log_file, "a") as f:
            f.write(json.dumps(log_dict) + "\n")
        return {"status": "logged"}

    return app


def main():
    parser = argparse.ArgumentParser(description="Run the FastAPI server.")
    parser.add_argument("-f", "--jsonl-file", type=str, help="Path to JSONL file for logging events", default=os.getenv("JSONL_FILE", "logs.jsonl"))
    parser.add_argument("-p", "--port", type=int, default=int(os.getenv("PORT", 8080)), help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("-r", "--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("-j", "--jwt-secret-file", type=str, help="path to file with JWT secret key for authentication", default=os.getenv("JWT_SECRET_PATH"))
    args = parser.parse_args()

    if not args.jwt_secret_file:
        raise ValueError("JWT secret file path must be provided via --jwt-secret-file or JWT_SECRET environment variable")

    if not os.path.exists(args.jwt_secret_file):
        raise ValueError(f"JWT secret file not found at {args.jwt_secret_file}")

    with open(args.jwt_secret_file, "r") as f:
        jwt_secret = f.read().strip()

    # check if the log file exists and is writable
    if not os.path.exists(args.jsonl_file):
        file_dir = os.path.dirname(args.jsonl_file)

        if file_dir and not os.path.exists(file_dir):
            os.makedirs(os.path.dirname(args.jsonl_file), exist_ok=True)
        try:
            with open(args.jsonl_file, "w"):
                pass
        except Exception as e:
            raise ValueError(f"Cannot create log file at {args.jsonl_file}: {e}")
    elif not os.access(args.jsonl_file, os.W_OK):
        raise ValueError(f"Log file at {args.jsonl_file} is not writable")


    import uvicorn
    uvicorn.run(build_server(jwt_secret, args.jsonl_file), host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
