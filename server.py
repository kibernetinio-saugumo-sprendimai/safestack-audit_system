from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
import uvicorn
import os
import sys
import secrets

try:
    from app import app
except ImportError as e:
    print(f"\n[KLAIDA] Nepavyko rasti 'app.py' failo arba jame yra klaidų: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n[KRITINĖ KLAIDA] app.py faile yra klaidų: {e}")
    sys.exit(1)

server = FastAPI(title="SafeStack AI Agents API")

class TaskRequest(BaseModel):
    task: str = Field(min_length=1, max_length=4000)
    thread_id: str | None = Field(default=None, min_length=1, max_length=128)

@server.get("/")
async def root():
    return {"status": "online", "docs": "/docs"}

@server.post("/ask")
async def run_team(request: TaskRequest, x_api_key: str | None = Header(default=None)):
    # A client never chooses a checkpoint namespace; this prevents cross-session
    # state access through guessed thread IDs.
    thread_id = secrets.token_urlsafe(24)
    expected_key = os.environ.get("SAFESTACK_API_KEY")
    if not expected_key:
        raise HTTPException(status_code=503, detail="API authentication is not configured")
    if not secrets.compare_digest(x_api_key or "", expected_key):
        raise HTTPException(status_code=401, detail="unauthorized")
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {
        "messages": [("user", request.task)], 
        "project_path": "", 
        "project_context": "",
        "memories": ""
    }
    results = []
    try:
        for event in app.stream(inputs, config=config):
            for node, value in event.items():
                print(f"Agent: {node.upper()} is working...")
                msg_content = ""
                if "messages" in value:
                    msg = value["messages"][-1]
                    msg_content = msg.content if hasattr(msg, "content") else (msg[1] if isinstance(msg, tuple) else str(msg))
                
                results.append({
                    "agent": node.upper(), 
                    "state": value.get("current_state", "AUDITING"),
                    "trust_level": value.get("trust_level", "UNTRUSTED"),
                    "runtime_id": value.get("runtime_id", "N/A"),
                    "integrity_hash": value.get("chain_hash", "N/A"),
                    "content": msg_content
                })
        return {
            "status": "success", 
            "session_id": thread_id,
            "results": results
        }
    except Exception as e:
        print(f"Klaida: {e}")
        raise HTTPException(status_code=500, detail="audit execution failed")

if __name__ == "__main__":
    print("\n" + "="*40)
    print("SafeStack AI Agents server starting...")
    print("Version: 1.0.0-GOLDEN [AUTHORITATIVE]")
    print("Address: http://localhost:8000")
    print("="*40 + "\n")
    uvicorn.run(server, host="127.0.0.1", port=8000)
