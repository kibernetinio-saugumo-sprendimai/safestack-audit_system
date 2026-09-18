#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import shlex
from datetime import datetime, timezone
from typing import Optional, Tuple

def load_canon(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_command(command: str) -> Tuple[str, int]:
    # Canon commands are operator-trusted configuration. Never invoke a shell.
    try:
        argv = shlex.split(command)
    except ValueError as e:
        return "", 2
    if not argv or any(re.search(r"[;&|<>`$()]", token) for token in argv):
        return "", 2
    try:
        result = subprocess.run(
            argv,
            shell=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10
        )
        return result.stdout.strip(), result.returncode
    except (OSError, subprocess.SubprocessError):
        return "", 2

def check_file_exists(rule: dict) -> bool:
    return os.path.exists(rule["path"])

def check_file_regex(rule: dict) -> bool:
    path = rule["path"]
    pattern = rule["pattern"]
    if not os.path.exists(path): return False
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return re.search(pattern, content, re.MULTILINE) is not None

def check_command_contains(rule: dict) -> Optional[bool]:
    output, returncode = run_command(rule["command"])
    if returncode != 0:
        # A failed command is an execution error, never an observed false value.
        return None
    return rule["contains"] in output

def check_disk_free_mb(rule: dict) -> bool:
    usage = shutil.disk_usage(rule["path"])
    free_mb = usage.free // (1024 * 1024)
    return free_mb >= rule["minimum_mb"]

def run_check(rule: dict) -> bool:
    try:
        check_type = rule["type"]
        if check_type == "file_exists": result = check_file_exists(rule)
        elif check_type == "file_regex": result = check_file_regex(rule)
        elif check_type == "command_contains": result = check_command_contains(rule)
        elif check_type == "disk_free_mb": result = check_disk_free_mb(rule)
        else: return False
        if result is None:
            return False
        return result is rule.get("expected", True)
    except (OSError, KeyError, TypeError, ValueError, re.error):
        return False


def validate_canon(canon: object) -> list:
    if not isinstance(canon, dict) or not isinstance(canon.get("checks"), list) or not canon["checks"]:
        raise ValueError("canon must contain a nonempty checks list")
    supported = {"file_exists", "file_regex", "command_contains", "disk_free_mb"}
    for rule in canon["checks"]:
        if not isinstance(rule, dict) or not isinstance(rule.get("id"), str) or not rule["id"].strip():
            raise ValueError("each check requires a nonempty id")
        if rule.get("type") not in supported or rule.get("severity") not in {"critical", "high", "medium", "low", "info"}:
            raise ValueError("check uses an unsupported type or severity")
        if not isinstance(rule.get("expected", True), bool):
            raise ValueError("check expected value must be boolean")
    return canon["checks"]

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 audit_tool.py SAFESTACK_CANON_DEPLOYMENT.json")
        sys.exit(2)
    canon_path = sys.argv[1]
    try:
        canon = load_canon(canon_path)
        checks = validate_canon(canon)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Invalid deployment canon: {error}", file=sys.stderr)
        sys.exit(2)
    results = []
    failed_checks = False
    print(f"# SafeStack Deployment Audit")
    print(f"Time: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")
    print(f"Canon: {canon.get('schema')} / {canon.get('version')}\n")
    for rule in checks:
        passed = run_check(rule)
        status = "PASS" if passed else "FAIL"
        severity = rule.get("severity", "unknown").upper()
        print(f"[{status}] [{severity}] {rule['id']}")
        results.append({"id": rule["id"], "severity": rule.get("severity"), "passed": passed})
        if not passed: failed_checks = True
    print("\nSummary:")
    print(json.dumps(results, indent=2))
    if failed_checks:
        print("\nRESULT: FAILED — one or more configured deployment checks did not pass.")
        sys.exit(1)
    print("\nRESULT: PASSED — all configured deployment checks passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
