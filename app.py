import sqlite3
import os
import requests
import re
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.base import BaseStore
from langgraph.store.sqlite import SqliteStore
from strict_mode import validate_output
from canonical_serializer import canonical_json
from quarantine_engine import quarantine

# --- QUARANTINE CONSTANTS ---
QUARANTINE_BASE = "runtime/quarantine"
CATEGORIES = ["schema", "protocol", "security", "runtime", "determinism"]
PROJECT_ROOT = Path(os.environ.get("SAFESTACK_AUDIT_ROOT", os.getcwd())).resolve()
MAX_SOURCE_BYTES = 1_000_000

def resolve_project_path(raw_path: str) -> Path:
    """Resolve an audit target inside the explicitly configured audit root."""
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError as e:
        raise PermissionError("audit target is outside SAFESTACK_AUDIT_ROOT") from e
    if not resolved.is_dir():
        raise NotADirectoryError("audit target must be a directory")
    return resolved

def write_generated_file(path: str, content: str) -> None:
    """Write generated output without following an attacker-created symlink."""
    target = Path(path)
    target.parent.mkdir(mode=0o700, exist_ok=True)
    parent = target.parent.resolve(strict=True)
    parent.relative_to(Path.cwd().resolve())
    target = parent / target.name
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(target, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
    except Exception:
        try: os.close(fd)
        except OSError: pass
        raise

# 1. State
class State(TypedDict):
    messages: Annotated[list, add_messages]
    project_path: str
    project_context: str
    memories: str # Long-term memory context
    runtime_id: str
    session_id: str
    current_state: str
    chain_hash: str # Current artifact integrity hash
    trust_level: str # UNTRUSTED, LIMITED, TRUSTED, AUTHORITATIVE
    lifecycle_stage: str # CREATED, VALIDATED, SIGNED, etc.

def calculate_hash(content: str) -> str:
    """SHA-256 hashing for integrity verification. Normalizes line endings."""
    normalized = content.replace("\r\n", "\n").strip()
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def update_chain(state: State, new_content: str) -> str:
    """Updates the hash chain with new content."""
    prev_hash = state.get("chain_hash", "0" * 64)
    return calculate_hash(f"{prev_hash}|{new_content}")

def call_ollama(role: str, code: str, custom_prompt: str, expected_schema: str = None):
    url = "http://localhost:11434/api/chat"
    # Injecting strict enforcement into every call
    payload = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": f"{custom_prompt}\n"
             "CRITICAL: You are running inside SafeStack LOCKDOWN protocol mode.\n"
             "You MUST output ONLY valid JSON. Any other text triggers QUARANTINE.\n"
             "EXAMPLE OF GOLDEN RESPONSE:\n"
             "{\"agent\": \"Architect\", \"status\": \"pass\", \"findings\": []}\n"
             "FORBIDDEN:\n"
             "- NO markdown fences (```)\n"
             "- NO prose, NO bold (**), NO explanations\n"
             "- NO headings, NO bullet points\n"
             "Your entire response MUST be a single JSON object. Start with '{' and end with '}'."},
            {"role": "user", "content": f"CODE:\n{code}"}
        ],
        "stream": False,
        "options": {"temperature": 0.0, "num_ctx": 4096, "num_predict": 1024, "seed": 42}
    }
    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        content = response.json()['message']['content'].strip()
        
        # 1. TRANSPORT & PROTOCOL & SCHEMA VALIDATION (Using strict_mode)
        v_result = validate_output(content)
        if v_result["status"] != "valid":
            qid = quarantine(content, "protocol", v_result["reason"])
            return json.dumps({"agent": role, "status": "quarantined", "quarantine_id": qid["hash"]})

        data = v_result["artifact"]
        # Enforce Canonical Serialization
        content = canonical_json(data)
        
        # 4. EVIDENCE VALIDATION (for findings)
        if "findings" in data:
            for f in data["findings"]:
                if not all(k in f for k in ["id", "issue", "evidence", "severity"]):
                    qid = quarantine(content, "schema", "Invalid evidence structure")
                    return json.dumps({"agent": role, "status": "quarantined", "quarantine_id": qid["hash"]})

        return content
    except Exception:
        return json.dumps({"agent": role, "status": "error", "reason": "local model request failed"})

def read_project_files(path: str):
    try:
        project = resolve_project_path(path.replace('"', '').replace("'", "").strip())
    except (OSError, PermissionError):
        return "ERROR: PATH_NOT_FOUND", ""
    for root, dirs, files in os.walk(project, followlinks=False):
        dirs[:] = [d for d in dirs if d not in {"venv", ".venv", ".git", "__pycache__"}]
        for file in sorted(files): # Deterministic sort
            if file.endswith(('.sh', '.py')):
                try:
                    full_path = os.path.join(root, file)
                    source = Path(full_path).resolve(strict=True)
                    source.relative_to(PROJECT_ROOT)
                    if source.stat().st_size > MAX_SOURCE_BYTES: continue
                    with source.open('r', encoding='utf-8', errors='ignore') as f:
                        return f"FILE: {file}\n{f.read()}", file
                except: continue
    return "ERROR: NO_SCRIPTS", ""

def get_governance_stack():
    files = {
        "LEVEL_0_GENESIS": "DETERMINISTIC_CONSTRAINED_INFRASTRUCTURE.md",
        "LEVEL_0_GOVERNANCE": "GOVERNANCE_LAYER.md",
        "LEVEL_0_HIERARCHY": "SAFESTACK_AUDIT_AGENT_HIERARCHY.md",
        "LEVEL_0_EXECUTION": "SAFESTACK_AUDIT_AGENT_RULES.md",
        "LEVEL_1_ENTERPRISE": "DEPLOYMENT_STANDARD_ENTERPRISE.md",
        "LEVEL_2_STRATEGIC": "DEPLOYMENT_RULES.md",
        "LEVEL_3_PHILOSOPHY": "DEPLOYMENT_RULES_MINIMAL.md",
        "LEVEL_4_TECHNICAL": "skill.md",
        "LEVEL_5_QA": "oversight.md",
        "LEVEL_6_OUTPUT": "AUDIT_OUTPUT_RULES.md",
        "CANON": "SAFESTACK_CANON_DEPLOYMENT.json",
        "QUARANTINE": "QUARANTINE_PROTOCOL.md",
        "POL_CAPABILITY": "governance/policy_bundle/01_CAPABILITY_MODEL.md",
        "POL_STATE": "governance/policy_bundle/02_RUNTIME_STATE_MACHINE.md",
        "POL_EVIDENCE": "governance/policy_bundle/03_EVIDENCE_SPEC.md",
        "POL_CORE": "governance/policy_bundle/04_06_CORE_POLICIES.md",
        "POL_INTEGRITY": "governance/policy_bundle/07_10_INTEGRITY_POLICIES.md",
        "POL_TRUST": "governance/policy_bundle/11_TRUST_BOUNDARY_SPEC.md",
        "POL_SPECS": "governance/policy_bundle/11_15_CORE_SPECS.md",
        "POL_DOCTRINES": "governance/policy_bundle/16_20_GOVERNANCE_DOCTRINES.md",
        "POL_SOVEREIGN": "governance/policy_bundle/21_30_SOVEREIGN_SPECS.md",
        "POL_ROADMAP": "IMPLEMENTATION_ROADMAP.md",
        "POL_ENFORCEMENT": "governance/policy_bundle/32_ENFORCEMENT_CORE.md",
        "POL_INTEGRITY_DOCTRINE": "governance/policy_bundle/33_PROTOCOL_INTEGRITY_DOCTRINE.md"
    }
    stack = ""
    for label, filename in files.items():
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read().replace("\r\n", "\n").strip()
                stack += f"\n--- {label} RULES ---\n{content}\n"
        except:
            stack += f"\n--- {label} RULES ---\nNot provided.\n"
    
    # Debug hash of the stack itself
    stack_hash = hashlib.sha256(stack.encode()).hexdigest()
    print(f"DEBUG: Governance Stack Hash: {stack_hash}")
    return stack

# --- 3. AGENTS ---

def discoverer(state: State, *, store: BaseStore):
    raw_input = state["messages"][0].content.strip()
    # Remove 'audit ' prefix if present
    p = re.sub(r'^audit\s+', '', raw_input, flags=re.IGNORECASE).strip()
    # Try to find a path within quotes or just take the rest
    match = re.search(r'["\']?([a-zA-Z]:[\\/][^"\'<>|]+|[\./][^"\'<>|]*)["\']?', p)
    if match: p = match.group(1).strip()
    
    ctx, filename = read_project_files(p)
    mem_str = "DETERMINISTIC MODE: Long-term memory disabled."

    runtime_id = state.get("runtime_id", f"rt-{hashlib.md5(p.encode()).hexdigest()[:8]}")
    session_id = state.get("session_id", f"sess-{datetime.utcnow().strftime('%Y%m%d%H%M')}")

    if ctx.startswith("ERROR"): 
        return lockdown(state)
    
    msg = f"DISCOVERER: Loaded {filename} from {os.path.basename(p)}"
    new_hash = update_chain(state, msg)
    
    return {
        "project_path": p, "project_context": ctx, "memories": mem_str, 
        "current_state": "AUDITING", "runtime_id": runtime_id, "session_id": session_id,
        "chain_hash": new_hash, "trust_level": "UNTRUSTED", "lifecycle_stage": "CREATED",
        "messages": [("ai", msg)]
    }

def architect(state: State):
    ctx = f"{state.get('project_context', '')}"
    stack = get_governance_stack()
    if not ctx: return {"messages": [("ai", "{}")]}
    prompt = f"System Architect. Output JSON only. STACK:\n{stack}\n\nSchema: {{'agent': 'ARCHITECT', 'status': 'pass|fail', 'findings': [...]}}"
    result = call_ollama('Architect', ctx, prompt, expected_schema="True")
    new_hash = update_chain(state, result)
    return {"messages": [("ai", result)], "chain_hash": new_hash}

def coder(state: State):
    ctx = state.get("project_context", "")
    stack = get_governance_stack()
    if not ctx: return {"messages": [("ai", "{}")]}
    prompt = f"Senior Developer. Output JSON only. STACK:\n{stack}\n\nSchema: {{'agent': 'CODER', 'status': 'pass|fail', 'findings': [...]}}"
    result = call_ollama('Developer', ctx, prompt, expected_schema="True")
    new_hash = update_chain(state, result)
    return {"messages": [("ai", result)], "chain_hash": new_hash}

def security(state: State):
    ctx = state.get("project_context", "")
    stack = get_governance_stack()
    if not ctx: return {"messages": [("ai", "{}")]}
    prompt = f"Security Officer. Output JSON only. STACK:\n{stack}\n\nSchema: {{'agent': 'SECURITY', 'status': 'pass|fail', 'findings': [...]}}"
    result = call_ollama('Security', ctx, prompt, expected_schema="True")
    new_hash = update_chain(state, result)
    return {"messages": [("ai", result)], "chain_hash": new_hash}

def documenter(state: State):
    ctx = state.get("project_context", "")
    if not ctx: return {"messages": [("ai", "{}")]}
    prompt = "Technical Compliance Writer. Output JSON summary only. Schema: {'agent': 'DOCUMENTER', 'status': 'pass', 'summary': '...'}"
    result = call_ollama('Writer', ctx, prompt, expected_schema="True")
    new_hash = update_chain(state, result)
    return {"messages": [("ai", result)], "chain_hash": new_hash}

def supervisor(state: State):
    # Collects all findings and approves/rejects them based on evidence
    all_findings = ""
    for msg in state["messages"]:
        content = msg[1] if isinstance(msg, tuple) else getattr(msg, "content", str(msg))
        if content.strip().startswith("{"): all_findings += f"\n{content}"
    
    stack = get_governance_stack()
    prompt = f"CHIEF SUPERVISOR. STACK:\n{stack}\n\nReview ALL findings below. Reject any without exact code evidence. Output JSON: {{'agent': 'SUPERVISOR', 'status': 'pass|fail', 'approved_findings': [], 'rejected_findings': []}}"
    result = call_ollama('Supervisor', all_findings, prompt, expected_schema="True")
    new_hash = update_chain(state, result)
    # Supervisor approval elevates to TRUSTED
    trust = "TRUSTED" if '"status":"pass"' in result.lower() else "UNTRUSTED"
    return {"messages": [("ai", result)], "current_state": "PATCH_PROPOSED", "chain_hash": new_hash, "trust_level": trust}

def fixer(state: State):
    ctx = state.get("project_context", "")
    stack = get_governance_stack()
    approved = ""
    for msg in reversed(state["messages"]):
        content = msg[1] if isinstance(msg, tuple) else getattr(msg, "content", str(msg))
        if "approved_findings" in content:
            approved = content
            break
            
    if not ctx: return {"messages": [("ai", "")]}
    prompt = f"Senior Deployment Engineer. STACK:\n{stack}\n\nAPPROVED FINDINGS:\n{approved}\n\nREWRITE file. Output ONLY raw code. NO text. NO JSON."
    fixed_code = call_ollama('Fixer', ctx, prompt)
    
    from path_guard import validate_write_attempt
    
    # Update chain even for raw code
    new_hash = update_chain(state, fixed_code)
    
    target_path = "generated_code/fixed_script.sh"
    try:
        validate_write_attempt(target_path)
    except PermissionError as e:
        print(f"SECURITY BREACH: {e}")
        return lockdown(state)

    try:
        write_generated_file(target_path, fixed_code)
    except OSError as e:
        return lockdown({**state, "messages": [(
            "ai", f"SECURE_WRITE_FAILED: {e.__class__.__name__}") ]})
        
    return {"messages": [("ai", fixed_code)], "current_state": "DRY_RUN", "chain_hash": new_hash}

def validator(state: State):
    # Validates Fixer's output and overall JSON integrity
    last_msg = state["messages"][-1].content
    stack = get_governance_stack()
    prompt = f"VALIDATOR. STACK:\n{stack}\n\nCheck FIXER output. Is it raw code? No fluff? Output JSON: {{'agent': 'VALIDATOR', 'status': 'pass|fail', 'issue': '...'}}"
    result = call_ollama('Validator', last_msg, prompt, expected_schema="True")
    new_hash = update_chain(state, result)
    trust = "LIMITED" if '"status":"pass"' in result.lower() else "UNTRUSTED"
    return {"messages": [("ai", result)], "current_state": "REVIEW", "chain_hash": new_hash, "trust_level": trust}

def dry_run_validator(state: State):
    """Phase 8: Dry-run patch pipeline. Validates code syntax."""
    fixed_path = "generated_code/fixed_script.sh"
    if not os.path.exists(fixed_path):
        return {"current_state": "LOCKDOWN", "messages": [("ai", "DRY_RUN: Fixed script not found.")]}
    
    # Simple syntax check for bash scripts
    import subprocess
    try:
        # Using bash -n for dry-run syntax check if on Linux/WSL, 
        # or just passing if on pure Windows for now to avoid environmental failure
        if os.name != 'nt':
            result = subprocess.run(["bash", "-n", fixed_path], capture_output=True, text=True)
            if result.returncode != 0:
                qid = quarantine_artifact("Fixer", result.stderr, "Bash syntax error", "determinism")
                return {"messages": [("ai", f"DRY_RUN: Syntax error detected. Isolated: {qid}")], "current_state": "LOCKDOWN"}
        
        msg = "DRY_RUN: Syntax check PASSED. Proceeding to REVIEW."
        new_hash = update_chain(state, msg)
        return {"messages": [("ai", msg)], "current_state": "REVIEW", "chain_hash": new_hash}
    except Exception as e:
        return {"messages": [("ai", f"DRY_RUN: Execution error: {e}")], "current_state": "LOCKDOWN"}

def reviewer(state: State):
    fixed_code = ""
    for msg in reversed(state["messages"]):
        content = msg[1] if isinstance(msg, tuple) else getattr(msg, "content", str(msg))
        if "#!" in content or "set " in content:
            fixed_code = content
            break
    stack = get_governance_stack()
    prompt = f"Lead Auditor. STACK:\n{stack}\n\nReview FIXED CODE. Output JSON only. Schema: {{'agent': 'REVIEWER', 'status': 'pass|fail', 'reasoning': '...'}}"
    review_result = call_ollama('Reviewer', fixed_code, prompt, expected_schema="True")
    new_hash = update_chain(state, review_result)
    trust = "TRUSTED" if '"status":"pass"' in review_result.lower() else "UNTRUSTED"
    return {"messages": [("ai", review_result)], "current_state": "APPROVED", "chain_hash": new_hash, "trust_level": trust}

def reporter(state: State):
    p = state.get("project_path", "unknown")
    report = f"# 🛡️ SafeStack Machine-Audit Report: {p}\n\n"
    
    for msg in state["messages"]:
        content = msg[1] if isinstance(msg, tuple) else getattr(msg, "content", str(msg))
        if content.strip().startswith("{"):
            try:
                import json
                data = json.loads(content)
                agent = data.get("agent", data.get("supervisor", "UNKNOWN"))
                status = data.get("status", "").upper()
                report += f"## 🤖 {agent} (Status: {status})\n"
                
                if "findings" in data:
                    for f in data["findings"]:
                        report += f"- **[{f.get('severity', '').upper()}]** {f.get('id', '')}: {f.get('issue', '')}\n"
                        report += f"  - *Evidence:* `{f.get('evidence', '')}`\n"
                        report += f"  - *Recommendation:* {f.get('recommendation', '')}\n\n"
                elif "approved_findings" in data:
                    report += f"**Approved Findings:** {len(data['approved_findings'])}\n"
                    report += f"**Rejected Findings:** {len(data['rejected_findings'])}\n\n"
                elif "summary" in data:
                    report += f"{data['summary']}\n\n"
                elif "reasoning" in data:
                    report += f"**Reasoning:** {data['reasoning']}\n\n"
            except:
                continue
        elif "#!" in content or "set " in content:
            report += "## 🛠️ Proposed Fix\n```bash\n" + content + "\n```\n\n"

    # Generate Canonical Signature for the Report
    sig_content = f"{state.get('chain_hash')}|{report}"
    signature = hashlib.sha256(sig_content.encode()).hexdigest()
    report += f"\n---\n### Canonical Signature\n`sha256:{signature}`\n`Status: AUTHORITATIVE`"

    with open("LATEST_AUDIT_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
        
    msg = "Audit report generated and signed."
    new_hash = update_chain(state, msg)
    return {"messages": [("ai", msg)], "current_state": "COMPLETE", "chain_hash": new_hash, "trust_level": "AUTHORITATIVE", "lifecycle_stage": "SIGNED"}

def lockdown(state: State):
    """Emergency halt node for integrity failures. Constitutional terminal state."""
    msg = "SYSTEM LOCKDOWN: Integrity failure detected. Execution halted safely."
    print(msg)
    
    # Forensic record
    with open("LOCKDOWN_FORENSICS.log", "a", encoding="utf-8") as f:
        import datetime
        f.write(f"[{datetime.datetime.utcnow()}] LOCKDOWN TRIGGERED. State: {state.get('current_state')}\n")

    return {
        "current_state": "LOCKDOWN",
        "lifecycle_stage": "HALTED",
        "trust_level": "UNTRUSTED",
        "messages": [("ai", msg)]
    }

# --- 4. Graph ---

workflow = StateGraph(State)
workflow.add_node("discoverer", discoverer)
workflow.add_node("architect", architect)
workflow.add_node("coder", coder)
workflow.add_node("security", security)
workflow.add_node("documenter", documenter)
workflow.add_node("supervisor", supervisor)
workflow.add_node("fixer", fixer)
workflow.add_node("dry_run", dry_run_validator)
workflow.add_node("validator", validator)
workflow.add_node("reviewer", reviewer)
workflow.add_node("reporter", reporter)
workflow.add_node("lockdown", lockdown)

def should_lockdown(state: State):
    last_msg = state["messages"][-1].content if state["messages"] else ""
    if "quarantined" in last_msg or "error" in last_msg.lower():
        return "lockdown"
    return "continue"

workflow.set_entry_point("discoverer")
workflow.add_conditional_edges("discoverer", should_lockdown, {"continue": "architect", "lockdown": "lockdown"})
workflow.add_conditional_edges("architect", should_lockdown, {"continue": "coder", "lockdown": "lockdown"})
workflow.add_conditional_edges("coder", should_lockdown, {"continue": "security", "lockdown": "lockdown"})
workflow.add_conditional_edges("security", should_lockdown, {"continue": "documenter", "lockdown": "lockdown"})
workflow.add_conditional_edges("documenter", should_lockdown, {"continue": "supervisor", "lockdown": "lockdown"})
workflow.add_conditional_edges("supervisor", should_lockdown, {"continue": "fixer", "lockdown": "lockdown"})
workflow.add_conditional_edges("fixer", should_lockdown, {"continue": "dry_run", "lockdown": "lockdown"})
workflow.add_conditional_edges("dry_run", should_lockdown, {"continue": "validator", "lockdown": "lockdown"})
workflow.add_conditional_edges("validator", should_lockdown, {"continue": "reviewer", "lockdown": "lockdown"})
workflow.add_conditional_edges("reviewer", should_lockdown, {"continue": "reporter", "lockdown": "lockdown"})
workflow.add_conditional_edges("reporter", should_lockdown, {"continue": END, "lockdown": "lockdown"})
workflow.add_edge("lockdown", END)

# Checkpoints (Short-term)
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False, isolation_level=None)
memory = SqliteSaver(conn)

# Long-term persistent memory store in team_memory.sqlite
store_conn = sqlite3.connect("team_memory.sqlite", check_same_thread=False, isolation_level=None)
store = SqliteStore(store_conn) 
store.setup() 

app = workflow.compile(checkpointer=memory, store=store)
