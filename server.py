from __future__ import annotations

import os
import secrets
import threading
from typing import Any

import uvicorn
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

try:
    from app import app
except ImportError as error:
    print(f"\n[ERROR] SafeStack application could not be imported: {error}")
    raise

server = FastAPI(title="SafeStack AI Agents API")

# A single SQLite checkpointer and bounded model calls support one active graph.
# Reject overload instead of queuing attacker-controlled trees indefinitely.
_audit_slot = threading.Lock()


class TaskRequest(BaseModel):
    task: str = Field(min_length=1, max_length=4000)
    thread_id: str | None = Field(default=None, min_length=1, max_length=128)


def _stream_audit(inputs: dict[str, Any], config: dict[str, Any]) -> tuple[list, dict]:
    results = []
    final_state = {}
    try:
        for event in app.stream(inputs, config=config):
            for node, value in event.items():
                final_state = value
                messages = value.get("messages", [])
                content = ""
                if messages:
                    message = messages[-1]
                    content = message.content if hasattr(message, "content") else (message[1] if isinstance(message, tuple) else str(message))
                results.append({"agent": node.upper(), "state": value.get("current_state", "AUDITING"),
                                "trust_level": value.get("trust_level", "UNTRUSTED"),
                                "runtime_id": value.get("runtime_id", "N/A"),
                                "integrity_hash": value.get("chain_hash", "N/A"), "content": content})
    finally:
        # The API already returns a complete run; persistent checkpoints would
        # otherwise retain source files and model output without a user-facing need.
        app.checkpointer.delete_thread(config["configurable"]["thread_id"])
    return results, final_state


@server.get("/")
async def root():
    return {"status": "online", "docs": "/docs"}


@server.post("/ask")
async def run_team(request: TaskRequest, x_api_key: str | None = Header(default=None)):
    expected_key = os.environ.get("SAFESTACK_API_KEY")
    if not expected_key:
        raise HTTPException(status_code=503, detail="API authentication is not configured")
    if not secrets.compare_digest(x_api_key or "", expected_key):
        raise HTTPException(status_code=401, detail="unauthorized")
    if not _audit_slot.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="an audit is already running")
    thread_id = secrets.token_urlsafe(24)
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [("user", request.task)], "project_path": "", "project_context": "", "memories": ""}
    try:
        results, final_state = await run_in_threadpool(_stream_audit, inputs, config)
    except Exception as error:
        # Keep exception details out of client responses and server logs.
        raise HTTPException(status_code=500, detail="audit execution failed") from error
    finally:
        _audit_slot.release()
    complete = final_state.get("current_state") == "COMPLETE"
    return {"status": "success" if complete else "failed", "session_id": thread_id,
            "state": final_state.get("current_state", "UNKNOWN"),
            "trust_level": final_state.get("trust_level", "UNTRUSTED"),
            "report_path": final_state.get("report_path"), "results": results}


if __name__ == "__main__":
    uvicorn.run(server, host="127.0.0.1", port=8000)
