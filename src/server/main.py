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
    parser.add_argument("--jwt-secret", type=str, help="JWT secret key for authentication", default=os.getenv("JWT_SECRET"))
    args = parser.parse_args()

    if not args.jwt_secret:
        raise ValueError("JWT secret must be provided via --jwt-secret or JWT_SECRET environment variable")

    import uvicorn
    uvicorn.run(build_server(args.jwt_secret, args.jsonl_file), host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
