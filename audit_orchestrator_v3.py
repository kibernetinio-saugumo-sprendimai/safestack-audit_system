#!/usr/bin/env python3
"""
SafeStack Audit Orchestrator v3
Connected to Physical Enforcement Layer (agent_runtime).
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
from agent_runtime import run_agent  # FIZINIS PRIJUNGIMAS

AGENTS = ["ARCHITECT", "CODER", "SECURITY", "DOCUMENTER"]
BLOCKING_SEVERITIES = {"critical", "high"}

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def supervisor(valid_results: list[dict[str, Any]], invalid_outputs: list[dict[str, Any]]) -> dict[str, Any]:
    findings = []
    for result in valid_results:
        findings.extend(result.get("output", {}).get("findings", []))

    if invalid_outputs:
        return {
            "agent": "CHIEF_SUPERVISOR",
            "status": "blocked",
            "reason": "Protocol breach detected in one or more agents.",
            "invalid_details": invalid_outputs,
            "approved_findings": findings,
        }

    blocking = [f for f in findings if f["severity"] in BLOCKING_SEVERITIES]
    status = "fail" if blocking else "pass"
    
    return {
        "agent": "CHIEF_SUPERVISOR",
        "status": status,
        "reason": "Blocking findings detected." if blocking else "All checks passed.",
        "approved_findings": findings,
    }

def run_pipeline(target_file: Path) -> dict[str, Any]:
    valid_results = []
    invalid_outputs = []

    for agent in AGENTS:
        print(f"[*] Executing {agent} through Enforcement Layer...")
        
        # FIZINIS PRIJUNGIMAS: ČIA NUSTATOME, KAIP PALEIDŽIAMAS AGENTAS
        # Pavyzdžiui, naudojame pagalbinį skriptą, kuris imituoja LLM arba tikrą LLM adapterį
        command = [sys.executable, "llm_adapter.py", agent, str(target_file)]
        
        # Agentas bėga per runtime, kuris daro FIREWALL ir VALIDATION
        result = run_agent(agent, command)

        if result["status"] == "valid":
            valid_results.append(result)
            print(f" [+] {agent}: VALID")
        else:
            invalid_outputs.append(result)
            print(f" [!] {agent}: BLOCKED - {result['reason']}")

    decision = supervisor(valid_results, invalid_outputs)

    return {
        "schema": "safestack.audit.report.v3.enforced",
        "generated_at": utc_now(),
        "target": str(target_file),
        "supervisor": decision,
        "details": {
            "valid_count": len(valid_results),
            "invalid_count": len(invalid_outputs)
        }
    }

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 audit_orchestrator_v3.py <target_file>")
        sys.exit(2)

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"Target not found: {target}")
        sys.exit(2)

    report = run_pipeline(target)
    
    out_dir = Path("reports")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "audit_report_v3.json"
    out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "="*40)
    print(f"SUPERVISOR: {report['supervisor']['status'].upper()}")
    print(f"REASON: {report['supervisor']['reason']}")
    print("="*40)

    sys.exit(0 if report["supervisor"]["status"] == "pass" else 1)

if __name__ == "__main__":
    main()
