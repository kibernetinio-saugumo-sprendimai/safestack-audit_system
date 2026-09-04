#!/usr/bin/env python3
"""Fail-closed deployment checks driven by the repository-owned canon."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent
CANON_PATH = PROJECT_ROOT / "SAFESTACK_CANON_DEPLOYMENT.json"
MAX_CANON_BYTES = 256 * 1024
ALLOWED_COMMANDS = {
    ("ufw", "status"),
    ("systemctl", "is-active", "auditd"),
}


class CanonError(ValueError):
    pass


def load_canon(path: str) -> dict[str, Any]:
    requested = Path(path).resolve(strict=True)
    if requested != CANON_PATH or requested.is_symlink():
        raise CanonError("only the repository-owned deployment canon is accepted")
    if requested.stat().st_size > MAX_CANON_BYTES:
        raise CanonError("canon exceeds size limit")
    with requested.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    validate_canon(data)
    return data


def validate_canon(canon: Any) -> None:
    if not isinstance(canon, dict) or not isinstance(canon.get("checks"), list):
        raise CanonError("canon must contain a checks array")
    seen: set[str] = set()
    allowed_types = {"file_exists", "file_regex", "argv_contains", "disk_free_mb"}
    allowed_severities = {"critical", "high", "medium", "low"}
    for rule in canon["checks"]:
        if not isinstance(rule, dict):
            raise CanonError("each check must be an object")
        rule_id = rule.get("id")
        if not isinstance(rule_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", rule_id):
            raise CanonError("invalid check id")
        if rule_id in seen:
            raise CanonError(f"duplicate check id: {rule_id}")
        seen.add(rule_id)
        if rule.get("type") not in allowed_types:
            raise CanonError(f"unsupported check type: {rule.get('type')}")
        if rule.get("severity") not in allowed_severities:
            raise CanonError(f"invalid severity for {rule_id}")
        if rule["type"] == "argv_contains":
            argv = rule.get("argv")
            if not isinstance(argv, list) or not all(isinstance(arg, str) and arg for arg in argv):
                raise CanonError(f"invalid argv for {rule_id}")
            if tuple(argv) not in ALLOWED_COMMANDS:
                raise CanonError(f"command not allowlisted for {rule_id}")


def run_argv(argv: list[str]) -> str:
    if tuple(argv) not in ALLOWED_COMMANDS:
        raise CanonError("command is not allowlisted")
    result = subprocess.run(
        argv,
        shell=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=10,
        cwd="/",
        env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"},
        check=False,
    )
    return result.stdout.strip()


def check_file_exists(rule: dict[str, Any]) -> bool:
    return Path(rule["path"]).exists()


def check_file_regex(rule: dict[str, Any]) -> bool:
    path = Path(rule["path"])
    pattern = rule["pattern"]
    if not path.is_file() or path.is_symlink():
        return False
    if path.stat().st_size > 4 * 1024 * 1024:
        return False
    content = path.read_text(encoding="utf-8", errors="ignore")
    return re.search(pattern, content, re.MULTILINE) is not None


def check_argv_contains(rule: dict[str, Any]) -> bool:
    return rule["contains"] in run_argv(rule["argv"])


def check_disk_free_mb(rule: dict[str, Any]) -> bool:
    usage = shutil.disk_usage(rule["path"])
    return usage.free // (1024 * 1024) >= int(rule["minimum_mb"])


def run_check(rule: dict[str, Any]) -> bool:
    handlers = {
        "file_exists": check_file_exists,
        "file_regex": check_file_regex,
        "argv_contains": check_argv_contains,
        "disk_free_mb": check_disk_free_mb,
    }
    return handlers[rule["type"]](rule)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 audit_tool.py SAFESTACK_CANON_DEPLOYMENT.json", file=sys.stderr)
        return 2
    try:
        canon = load_canon(sys.argv[1])
    except (OSError, json.JSONDecodeError, CanonError) as exc:
        print(f"CANON REJECTED: {exc}", file=sys.stderr)
        return 2

    results = []
    failed_critical = False
    print("# SafeStack Deployment Audit")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print(f"Canon: {canon.get('schema')} / {canon.get('version')}\n")
    for rule in canon["checks"]:
        try:
            passed = run_check(rule)
        except (OSError, subprocess.SubprocessError, CanonError, ValueError) as exc:
            passed = False
            print(f"[ERROR] {rule['id']}: {exc}")
        status = "PASS" if passed else "FAIL"
        severity = rule["severity"].upper()
        print(f"[{status}] [{severity}] {rule['id']}")
        results.append({"id": rule["id"], "severity": rule["severity"], "passed": passed})
        if not passed and rule["severity"] == "critical":
            failed_critical = True

    print("\nSummary:")
    print(json.dumps(results, indent=2))
    if failed_critical:
        print("\nRESULT: FAILED — critical deployment rule violated.")
        return 1
    print("\nRESULT: PASSED — no critical deployment rule violated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
