#!/usr/bin/env python3
import json
import requests
import sys
import os
import shutil
from pathlib import Path
from validator import ValidationError, validate
from enforcement_engine import build_supervisor_result

def hard_validate(raw: str, agent: str):
    raw_stripped = raw.strip()
    
    if agent == "FIXER":
        if not raw_stripped.startswith("---"):
            raise ValidationError("FIXER NOT PATCH")
        return # Skip JSON check for patch

    if not raw_stripped.startswith("{"):
        raise ValidationError("NON-JSON OUTPUT")
    
    forbidden = ["hello", "i'm", "analysis", "here is"]
    for f in forbidden:
        if f in raw.lower():
            raise ValidationError(f"FORBIDDEN PHRASE: {f}")

def call_ollama(agent_name: str, code_context: str, findings: str = ""):
    url = "http://localhost:11434/api/chat"
    instruction_path = Path(f"agents/{agent_name.lower()}.md")
    system_prompt = instruction_path.read_text(encoding="utf-8") if instruction_path.exists() else "Output JSON only."
    
    user_content = f"CODE:\n{code_context}"
    if findings:
        user_content = f"FIX THESE FINDINGS:\n{findings}\n\nORIGINAL CODE:\n{code_context}\n\nOUTPUT ONLY THE FULL FIXED CODE."

    payload = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "stream": False,
        "options": {"temperature": 0.01, "num_ctx": 8192}
    }
    try:
        response = requests.post(url, json=payload, timeout=120)
        return response.json()['message']['content'].strip()
    except Exception as e:
        return f"ERROR: {e}"

def patch_validator_check_scope(original: str, fixed: str) -> tuple[bool, str]:
    # Check if Fixer reported a JSON failure
    if fixed.strip().startswith("{"):
        try:
            data = json.loads(fixed)
            if data.get("agent") == "FIXER" and data.get("status") == "fail":
                return False, f"FIXER_REJECTED: {data.get('reason', 'Unknown reason')}"
        except:
            pass # Not valid JSON failure, just noise
        return False, "INVALID_FORMAT: Output contains JSON fluff."
    
    if "I'm sorry" in fixed or "Hello" in fixed or "Here is" in fixed:
        return False, "INVALID_FORMAT: Output contains conversational noise."
    
    if "#!" not in fixed and "set " not in fixed and "diff" not in fixed.lower():
        return False, "INVALID_CONTENT: No script or diff detected."
    
    return True, "OK"

def run_audit(target_file: Path):
    code_content = target_file.read_text(encoding="utf-8", errors="ignore")
    results, invalid = [], []
    for agent in ["ARCHITECT", "CODER", "SECURITY", "DOCUMENTER"]:
        print(f"[>] Running {agent}...")
        raw_output = call_ollama(agent, code_content)
        try:
            hard_validate(raw_output, agent)
            parsed = validate(raw_output)
            results.append(parsed)
            
            # STOP CONDITION: Kritinis pažeidimas
            for f in parsed.get("findings", []):
                if f.get("severity") == "critical":
                    print(f"[!!!] EMERGENCY STOP: Critical finding found by {agent}!")
                    return build_supervisor_result(results, invalid)
                    
        except ValidationError as exc:
            invalid.append({"agent": agent, "error": str(exc)})
            # STOP CONDITION: Sugadintas protokolas (Blocked)
            print(f"[!] PROTOCOL BREACH: {agent} output is invalid. Blocking audit.")
            return build_supervisor_result(results, invalid)
            
    return build_supervisor_result(results, invalid)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 audit_orchestrator.py <file> [--apply]")
        sys.exit(2)

    target = Path(sys.argv[1])
    apply_mode = "--apply" in sys.argv
    
    # 1. INITIAL AUDIT
    print(f"[*] STEP 1: INITIAL AUDIT -> {target.name}")
    status = run_audit(target)
    
    # FINAL SAFETY KILL-SWITCH
    report_str = json.dumps(status)
    if "Hello" in report_str or "I'm sorry" in report_str:
        print("[!!!] GLOBAL PROTOCOL BREACH: Forbidden phrases found in final report. ABORTING.")
        sys.exit(1)
    
    if status["status"] == "pass":
        print("[+] RESULT: PASS. System is compliant.")
        sys.exit(0)

    # 3. SUPERVISOR DECISION
    print(f"[!] RESULT: {status['status'].upper()}. Reason: {status['reason']}")
    
    # 4. FIXER (Dry-run mode)
    print(f"[*] STEP 2: FIXER (Dry-run) -> Generating patch for {len(status['approved_findings'])} findings...")
    findings_str = json.dumps(status["approved_findings"], indent=2)
    fixed_code = call_ollama("FIXER", target.read_text(encoding="utf-8"), findings_str)
    
    try:
        hard_validate(fixed_code, "FIXER")
    except ValidationError as exc:
        print(f"[!!] FIXER VALIDATION FAILED: {exc}")
        sys.exit(1)
    
    # PATCH VALIDATION
    is_valid, v_msg = patch_validator_check_scope(target.read_text(encoding="utf-8"), fixed_code)
    if not is_valid:
        print(f"[!!] SCOPE VALIDATION FAILED: {v_msg}")
        sys.exit(1)
    
    # DRY-RUN SAVE
    gen_dir = Path("generated_code")
    gen_dir.mkdir(exist_ok=True)
    temp_file = gen_dir / f"fixed_{target.name}"
    temp_file.write_text(fixed_code, encoding="utf-8")
    print(f"[+] DRY-RUN SUCCESS: Fixed code saved to {temp_file}")

    # 5. OPTIONAL REAL APPLY
    if apply_mode:
        print(f"[*] STEP 3: APPLY -> Overwriting {target}...")
        shutil.copy(temp_file, target)
        
        # 6. RE-AUDIT
        print(f"[*] STEP 4: RE-AUDIT -> Verifying applied changes...")
        final_status = run_audit(target)
        if final_status["status"] == "pass":
            print("[++] FINAL RESULT: PASS. System hardened successfully.")
            sys.exit(0)
        else:
            print(f"[!!] FINAL RESULT: FAIL. Issues remain: {final_status['reason']}")
            sys.exit(1)
    else:
        print("\n[NOTICE] SAFE MODE: No files were changed. Review 'generated_code/' and run with --apply to finalize.")
        sys.exit(0)

if __name__ == "__main__":
    main()
