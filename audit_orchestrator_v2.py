#!/usr/bin/env python3
import json
import requests
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Any

AGENTS = ["ARCHITECT", "CODER", "SECURITY", "DOCUMENTER"]
BLOCKING_SEVERITIES = {"critical", "high"}

class AuditBlocked(Exception):
    pass

def verify_evidence(code: str, evidence: str) -> bool:
    return evidence.strip() in code

def output_firewall(raw: str, agent: str, code_context: str = ""):
    raw_stripped = raw.strip()
    
    # 2️⃣ FIXER LOCK (Tik Unified Diff)
    if agent == "FIXER":
        if not raw_stripped.startswith("---"):
            raise AuditBlocked("FIXER OUTPUT NOT PATCH -> BLOCKED")
        return

    # 4️⃣ REVIEWER & AUDIT AGENTS (Tik JSON)
    if not raw_stripped.startswith("{"):
        raise AuditBlocked(f"{agent}: NON-JSON BLOCKED")

    forbidden = ["hello", "i'm", "analysis", "here is", "senior", "expert"]
    lower_raw = raw_stripped.lower()
    for f in forbidden:
        if f in lower_raw:
            raise AuditBlocked(f"{agent}: FORBIDDEN -> {f}")

    # 3. EVIDENCE ENFORCEMENT
    try:
        data = json.loads(raw_stripped)
        if data.get("agent") != agent: raise Exception("Agent mismatch")
        for f in data.get("findings", []):
            if not verify_evidence(code_context, f.get("evidence", "")):
                raise AuditBlocked(f"{agent}: HALLUCINATED EVIDENCE")
    except json.JSONDecodeError:
        raise AuditBlocked(f"{agent}: INVALID JSON")

def call_ollama(agent_name: str, code_context: str, findings: str = ""):
    url = "http://localhost:11434/api/chat"
    instruction_path = Path(f"agents/{agent_name.lower()}.md")
    system_prompt = instruction_path.read_text(encoding="utf-8") if instruction_path.exists() else "STRICT_JSON"
    
    user_content = f"CODE:\n{code_context}"
    if findings:
        user_content = f"FIX_FINDINGS:\n{findings}\n\nORIGINAL_CODE:\n{code_context}\n\nOUTPUT_PATCH_ONLY"

    payload = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": system_prompt + "\nOUTPUT ONLY JSON OR PATCH. NO PROSE."},
            {"role": "user", "content": user_content}
        ],
        "stream": False,
        "options": {"temperature": 0.0, "num_ctx": 8192}
    }
    try:
        response = requests.post(url, json=payload, timeout=180)
        return response.json()['message']['content'].strip()
    except Exception as e: return f"ERROR: {e}"

def run_audit(target_file: Path):
    code_content = target_file.read_text(encoding="utf-8", errors="ignore")
    valid_results = []
    
    for agent in AGENTS:
        print(f"[*] Auditing with {agent}...")
        raw = call_ollama(agent, code_content)
        try:
            output_firewall(raw, agent, code_content)
            valid_results.append(json.loads(raw))
        except AuditBlocked as exc:
            # 3️⃣ HARD STOP: Jokių tęsiam.
            print(f"[!!!] HARD STOP: {exc}")
            return {"status": "blocked", "reason": str(exc), "approved_findings": []}

    approved = []
    for r in valid_results: approved.extend(r.get("findings", []))
    status = "fail" if any(f['severity'] in BLOCKING_SEVERITIES for f in approved) else "pass"
    return {"status": status, "approved_findings": approved}

def main():
    if len(sys.argv) < 2: sys.exit(2)
    target = Path(sys.argv[1])
    apply_mode = "--apply" in sys.argv

    print(f"[*] STARTING LOCKED AUDIT: {target.name}")
    status = run_audit(target)

    if status["status"] == "blocked":
        print(f"[!] AUDIT BLOCKED: {status['reason']}")
        sys.exit(1)

    if status["status"] == "pass":
        print("[+] PASS: System verified.")
        sys.exit(0)

    if status["status"] == "fail":
        print(f"[!] AUDIT FAILED. Findings detected: {len(status['approved_findings'])}")
        for f in status['approved_findings']:
            print(f" - [{f['severity'].upper()}] {f['id']}: {f['issue']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
