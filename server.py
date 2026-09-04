from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import sys

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
    task: str
    thread_id: str = "vscode_session"

@server.get("/")
async def root():
    return {"status": "online", "docs": "/docs"}

@server.post("/ask")
async def run_team(request: TaskRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    inputs = {
        "messages": [("user", request.task)], 
        "project_path": "", 
        "project_context": "",
        "memories": ""
    }
    os.makedirs("generated_code", exist_ok=True)
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
            "session_id": inputs.get("session_id", "N/A"),
            "results": results
        }
    except Exception as e:
        print(f"Klaida: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("\n" + "="*40)
    print("SafeStack AI Agents server starting...")
    print("Version: candidate — independent approval required")
    print("Address: http://localhost:8000")
    print("="*40 + "\n")
    uvicorn.run(server, host="127.0.0.1", port=8000)
