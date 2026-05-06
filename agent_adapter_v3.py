#!/usr/bin/env python3
"""
agent_adapter_v3.py

SafeStack deterministic agent adapter v3.

Purpose:
- load one agent contract
- read target source file
- build strict JSON-only generation request
- execute an LLM command/provider if configured
- otherwise use deterministic local fallback
- print ONLY raw agent output
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


CONTRACTS_DIR = Path("agent_contracts")

VALID_JSON_AGENTS = {
    "ARCHITECT",
    "CODER",
    "SECURITY",
    "DOCUMENTER",
    "REVIEWER",
}

VALID_PATCH_AGENTS = {
    "FIXER",
}

VALID_AGENTS = VALID_JSON_AGENTS | VALID_PATCH_AGENTS

TOKEN_LIMITS = {
    "ARCHITECT": 700,
    "CODER": 700,
    "SECURITY": 700,
    "DOCUMENTER": 500,
    "REVIEWER": 500,
    "FIXER": 500,
}

class AdapterError(Exception):
    pass

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def load_contract(agent: str) -> str:
    path = CONTRACTS_DIR / f"{agent.lower()}.contract.md"
    if not path.exists():
        raise AdapterError(f"Missing contract: {path}")
    return read_text(path)

def build_prompt(agent: str, contract: str, source_path: Path, source: str) -> str:
    required_output = "ONLY valid unified diff. No JSON. No prose." if agent == "FIXER" else "ONLY valid JSON object matching the contract schema. No prose."
    
    return f"""
SYSTEM_LOCKDOWN=true
AGENT={agent}
TEMPERATURE=0
TOP_P=0
MAX_TOKENS={TOKEN_LIMITS[agent]}

NON_NEGOTIABLE_OUTPUT_RULE:
{required_output}

ABSOLUTE_FORBIDDEN:
- greeting, apology, roleplay, explanation, markdown, code fences, headings, bullet lists, summary, conversational text, invented evidence, invented files, invented commands

IDENTITY_SUPPRESSION:
You do not introduce yourself. You do not say what role you are. You do not say "I". You do not say "Here is". You do not say "Analysis". You are a protocol-output generator.

CONTRACT:
{contract}

SOURCE_FILE:
{source_path}

SOURCE_CONTENT_BEGIN
{source}
SOURCE_CONTENT_END

FINAL_OUTPUT_REQUIREMENT:
Return only the final machine-parseable output.
"""

def call_external_provider(prompt: str) -> str | None:
    command = os.environ.get("SAFESTACK_AGENT_COMMAND")
    if not command: return None
    result = subprocess.run(command, input=prompt, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True, check=False)
    return result.stdout.strip()

def deterministic_fallback(agent: str, target_file: Path, source: str) -> str:
    if agent == "FIXER": return ""
    findings: list[dict[str, str]] = []
    
    if agent == "DOCUMENTER":
        missing = [s for s in ["Purpose", "Usage", "Requirements", "Environment Variables", "Safety Notes", "Expected Result", "Failure Behavior"] if s not in source]
        if missing:
            findings.append({"id": "missing-documentation-sections", "severity": "medium", "file": str(target_file), "evidence": "#", "issue": f"Missing sections: {', '.join(missing)}", "recommendation": "Add missing sections."})
    elif agent == "SECURITY":
        if "TARGET_USER" in source and "=~" not in source:
            findings.append({"id": "missing-target-user-validation", "severity": "high", "file": str(target_file), "evidence": "TARGET_USER", "issue": "No regex validation for user input.", "recommendation": "Validate TARGET_USER."})
        if "rm -f /swap.img" in source:
            findings.append({"id": "unsafe-swap-delete", "severity": "medium", "file": str(target_file), "evidence": "rm -f /swap.img", "issue": "Unsafe direct deletion.", "recommendation": "Validate path before deletion."})
    elif agent == "CODER":
        if "set -euo pipefail" not in source:
            findings.append({"id": "missing-euo-pipefail", "severity": "high", "file": str(target_file), "evidence": "set -e", "issue": "Incomplete strict mode.", "recommendation": "Use set -euo pipefail."})
    elif agent == "ARCHITECT":
        if "agent_runtime.py" not in source:
            findings.append({"id": "missing-control-gate", "severity": "high", "file": str(target_file), "evidence": "agent", "issue": "No explicit runtime routing.", "recommendation": "Use agent_runtime.py."})

    return json.dumps({"agent": agent, "status": "fail" if findings else "pass", "findings": findings}, ensure_ascii=False)

def main() -> None:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("agent")
    parser.add_argument("target_file")
    parser.add_argument("--fallback", action="store_true")
    args = parser.parse_args()

    agent = args.agent.upper().strip()
    target_file = Path(args.target_file)

    if agent not in VALID_AGENTS or not target_file.exists():
        sys.exit(1)

    try:
        contract = load_contract(agent)
        source = read_text(target_file)
        if args.fallback:
            print(deterministic_fallback(agent, target_file, source))
            return
        
        prompt = build_prompt(agent, contract, target_file, source)
        external = call_external_provider(prompt)
        if external:
            print(external.strip())
            return
            
        print(deterministic_fallback(agent, target_file, source))

    except Exception as exc:
        import traceback
        sys.stderr.write(f"ADAPTER_CRITICAL_EXCEPTION: {str(exc)}\n")
        sys.stderr.write(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
