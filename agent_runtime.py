#!/usr/bin/env python3
"""
agent_runtime.py

SafeStack Canonical Agent Runtime

Purpose:
- run one agent command
- capture stdout as raw agent output only
- capture stderr separately
- validate stdout through strict_mode.py
- save valid or invalid runtime record
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUNTIME_DIR = Path("runtime")
RAW_DIR = RUNTIME_DIR / "raw"
VALID_DIR = RUNTIME_DIR / "valid"
INVALID_DIR = RUNTIME_DIR / "invalid"
STDERR_DIR = RUNTIME_DIR / "stderr"

VALID_AGENTS = {
    "ARCHITECT",
    "CODER",
    "SECURITY",
    "DOCUMENTER",
    "FIXER",
    "REVIEWER",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs() -> None:
    for path in [RAW_DIR, VALID_DIR, INVALID_DIR, STDERR_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", errors="ignore")


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def run_strict_mode(agent: str, raw_path: Path) -> tuple[bool, dict[str, Any]]:
    result = subprocess.run(
        [sys.executable, "strict_mode.py", agent, str(raw_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        parsed = {
            "agent": agent,
            "status": "blocked",
            "reason": "strict_mode returned non-json output",
            "strict_stdout": result.stdout[:500],
            "strict_stderr": result.stderr[:500],
        }

    return result.returncode == 0, parsed


def run_agent(agent: str, command: list[str]) -> dict[str, Any]:
    ensure_dirs()

    agent = agent.upper().strip()

    if agent not in VALID_AGENTS:
        record = {
            "agent": agent,
            "status": "invalid",
            "reason": "invalid agent name",
            "timestamp": utc_now(),
        }
        return record

    result = run_command(command)

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    raw_path = RAW_DIR / f"{agent}.raw.txt"
    stderr_path = STDERR_DIR / f"{agent}.stderr.txt"

    write_text(raw_path, stdout)
    write_text(stderr_path, stderr)

    # MANDATORY VALIDATION
    strict_ok, strict_result = run_strict_mode(agent, raw_path)

    if strict_ok:
        output = strict_result.get("output")

        valid_record = {
            "agent": agent,
            "status": "valid",
            "timestamp": utc_now(),
            "raw_path": str(raw_path),
            "stderr_path": str(stderr_path),
            "valid_path": str(VALID_DIR / f"{agent}.json"),
            "output": output,
            "command_exit_code": result.returncode,
        }

        write_text(
            VALID_DIR / f"{agent}.json",
            json.dumps(valid_record, indent=2, ensure_ascii=False),
        )

        return valid_record

    invalid_record = {
        "agent": agent,
        "status": "invalid",
        "reason": strict_result.get("reason", "strict_mode blocked output"),
        "timestamp": utc_now(),
        "raw_path": str(raw_path),
        "stderr_path": str(stderr_path),
        "strict_result": strict_result,
        "command_exit_code": result.returncode,
    }

    write_text(
        INVALID_DIR / f"{agent}.invalid.json",
        json.dumps(invalid_record, indent=2, ensure_ascii=False),
    )

    return invalid_record


def main() -> None:
    if len(sys.argv) < 3:
        print(json.dumps({
            "agent": "UNKNOWN",
            "status": "invalid",
            "reason": "Usage: python agent_runtime.py <AGENT> <command...>"
        }, ensure_ascii=False))
        sys.exit(7)

    agent = sys.argv[1]
    command = sys.argv[2:]

    result = run_agent(agent, command)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result["status"] != "valid":
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
