#!/usr/bin/env python3
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime

ALLOWED_AUDIT_COMMANDS = {
    "findmnt",
    "lsblk",
    "ss",
    "sysctl",
    "systemctl",
    "ufw",
}


def load_canon(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_command(command: str) -> str:
    try:
        argv = shlex.split(command)
        if not argv:
            return "ERROR: empty command"

        executable = os.path.basename(argv[0])
        if executable not in ALLOWED_AUDIT_COMMANDS:
            return f"ERROR: command not allowlisted: {executable}"

        result = subprocess.run(
            argv,
            shell=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
            check=False,
            env={
                "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
                "LANG": "C",
                "LC_ALL": "C",
            },
        )
        return result.stdout.strip()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return f"ERROR: {exc}"


def check_file_exists(rule: dict) -> bool:
    return os.path.exists(rule["path"])


def check_file_regex(rule: dict) -> bool:
    path = rule["path"]
    pattern = rule["pattern"]
    if not os.path.exists(path):
        return False
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return re.search(pattern, content, re.MULTILINE) is not None


def check_command_contains(rule: dict) -> bool:
    output = run_command(rule["command"])
    return rule["contains"] in output


def check_disk_free_mb(rule: dict) -> bool:
    usage = shutil.disk_usage(rule["path"])
    free_mb = usage.free // (1024 * 1024)
    return free_mb >= rule["minimum_mb"]


def run_check(rule: dict) -> bool:
    check_type = rule["type"]
    if check_type == "file_exists":
        return check_file_exists(rule)
    if check_type == "file_regex":
        return check_file_regex(rule)
    if check_type == "command_contains":
        return check_command_contains(rule)
    if check_type == "disk_free_mb":
        return check_disk_free_mb(rule)
    return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 audit_tool.py SAFESTACK_CANON_DEPLOYMENT.json")
        sys.exit(2)

    canon_path = sys.argv[1]
    canon = load_canon(canon_path)
    results = []
    failed_critical = False

    print("# SafeStack Deployment Audit")
    print(f"Time: {datetime.now().astimezone().isoformat()}")
    print(f"Canon: {canon.get('schema')} / {canon.get('version')}\n")

    for rule in canon.get("checks", []):
        passed = run_check(rule)
        status = "PASS" if passed else "FAIL"
        severity = rule.get("severity", "unknown").upper()
        print(f"[{status}] [{severity}] {rule['id']}")
        results.append({
            "id": rule["id"],
            "severity": rule.get("severity"),
            "passed": passed,
        })
        if not passed and rule.get("severity") == "critical":
            failed_critical = True

    print("\nSummary:")
    print(json.dumps(results, indent=2))

    if failed_critical:
        print("\nRESULT: FAILED — critical deployment rule violated.")
        sys.exit(1)

    print("\nRESULT: PASSED — no critical deployment rule violated.")
    sys.exit(0)


if __name__ == "__main__":
    main()
