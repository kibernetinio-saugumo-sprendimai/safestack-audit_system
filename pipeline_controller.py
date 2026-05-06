#!/usr/bin/env python3
"""
pipeline_controller.py (V3 - Hardened)
SafeStack Pipeline Controller powered by Runtime v2 and Strict Mode.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AGENTS = ["ARCHITECT", "CODER", "SECURITY", "DOCUMENTER"]
REPORTS_DIR = Path("reports")
RUNTIME_VALID_DIR = Path("runtime/valid")

def run_agent_runtime(agent: str, target_file: Path) -> dict[str, Any]:
    # TIESIOGINIS KVIETIMAS: Runtime -> Adapter v3 su --fallback
    cmd = [
        sys.executable, "agent_runtime.py", agent,
        sys.executable, "agent_adapter_v3.py", agent, str(target_file), "--fallback"
    ]
    
    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "agent": agent,
            "status": "invalid",
            "reason": f"Runtime V2 return non-json: {result.stdout[:200]}"
        }

def generate_final_report(target_file: Path, results: list[dict]):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).isoformat()
    report = {
        "target_file": str(target_file),
        "timestamp": timestamp,
        "summary": {
            "total_agents": len(results),
            "valid_agents": len([r for r in results if r["status"] == "valid"]),
            "blocked_agents": len([r for r in results if r["status"] == "invalid"])
        },
        "results": results
    }
    
    report_path = REPORTS_DIR / "pipeline_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report_path

def main():
    if len(sys.argv) < 2: sys.exit(7)
    target_file = Path(sys.argv[1])
    
    all_results = []
    print(f"[*] STARTING HARDENED AUDIT: {target_file}")
    
    for agent in AGENTS:
        print(f"[*] Executing {agent}...")
        res = run_agent_runtime(agent, target_file)
        all_results.append(res)
        
        if res["status"] == "valid":
            print(f"    [+] {agent}: VALID (Findings: {len(res.get('output', {}).get('findings', []))})")
        else:
            print(f"    [!] {agent}: BLOCKED - {res.get('reason')}")

    report_path = generate_final_report(target_file, all_results)
    print(f"[*] AUDIT COMPLETE. Report: {report_path}")

if __name__ == "__main__":
    main()
