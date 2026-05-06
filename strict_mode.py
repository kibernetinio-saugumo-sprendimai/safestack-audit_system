#!/usr/bin/env python3
"""
strict_mode.py

SafeStack Strict Mode Engine

Purpose:
- central hard policy gate
- block non-JSON agent output
- block prose / markdown / greetings / roleplay
- enforce agent schema
- enforce FIXER patch-only mode
- terminate pipeline on protocol breach

Rule:
If strict_mode rejects output, pipeline must STOP.
"""

import json
import sys
from pathlib import Path
from typing import Any


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

VALID_STATUSES = {"pass", "fail"}
VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}

FORBIDDEN_PHRASES = [
    "hello",
    "i'm",
    "i am",
    "sorry",
    "as an ai",
    "here is",
    "analysis",
    "congratulations",
    "well done",
    "please let me know",
    "senior developer",
    "cyber security expert",
    "system architect",
    "technical writer",
    "a script for",
    "let's",
    "recommendations",
    "audit output",
    "suggested fix",
    "rewrite file",
    "strict mode:",
    "```",
    "**",
    "##",
    "# ",
    "- ",
]

FORBIDDEN_CONTEXT_LEAKS = [
    "tensorflow",
    "cnn",
    "azure",
    "textbook",
    "openai",
    "chatgpt",
]

FORBIDDEN_PATCH_PATHS = [
    "/etc/passwd",
    "/etc/shadow",
    "/etc/sudoers",
    "/root/",
    "/boot/",
]


class StrictModeError(Exception):
    pass


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def fail(message: str) -> None:
    raise StrictModeError(message)


def check_forbidden_text(raw: str, agent: str) -> None:
    lower = raw.lower()

    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            fail(f"{agent}: forbidden phrase detected: {phrase}")

    for phrase in FORBIDDEN_CONTEXT_LEAKS:
        if phrase in lower:
            fail(f"{agent}: context leak detected: {phrase}")


def enforce_json_only(raw: str, agent: str) -> dict[str, Any]:
    text = raw.strip()

    if not text:
        fail(f"{agent}: empty output")

    if not text.startswith("{") or not text.endswith("}"):
        fail(f"{agent}: non-json output blocked")

    check_forbidden_text(text, agent)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        fail(f"{agent}: invalid json: {exc}")

    return data


def validate_json_agent(data: dict[str, Any], agent: str) -> None:
    if data.get("agent") != agent:
        fail(f"{agent}: agent mismatch")

    if data.get("status") not in VALID_STATUSES:
        fail(f"{agent}: invalid status")

    findings = data.get("findings")

    if not isinstance(findings, list):
        fail(f"{agent}: findings must be list")

    if data["status"] == "pass" and findings:
        fail(f"{agent}: pass cannot contain findings")

    if data["status"] == "fail" and not findings:
        fail(f"{agent}: fail must contain findings")

    for finding in findings:
        validate_finding(finding, agent)


def validate_finding(finding: Any, agent: str) -> None:
    if not isinstance(finding, dict):
        fail(f"{agent}: finding must be object")

    required = [
        "id",
        "severity",
        "file",
        "evidence",
        "issue",
        "recommendation",
    ]

    for key in required:
        if key not in finding:
            fail(f"{agent}: finding missing key: {key}")

        if not isinstance(finding[key], str):
            fail(f"{agent}: finding field must be string: {key}")

        if not finding[key].strip():
            fail(f"{agent}: finding field empty: {key}")

    if finding["severity"] not in VALID_SEVERITIES:
        fail(f"{agent}: invalid severity: {finding['severity']}")


def enforce_fixer_patch(raw: str, agent: str) -> None:
    text = raw.strip()
    lower = text.lower()

    if not text:
        fail(f"{agent}: empty patch")

    check_forbidden_text(text, agent)

    if not text.startswith("--- "):
        fail(f"{agent}: fixer output must start with unified diff header")

    if "+++ " not in text:
        fail(f"{agent}: fixer patch missing +++ header")

    if "@@" not in text:
        fail(f"{agent}: fixer patch missing hunk marker")

    for path in FORBIDDEN_PATCH_PATHS:
        if path in text:
            fail(f"{agent}: forbidden patch path detected: {path}")

    if len(text.splitlines()) > 500:
        fail(f"{agent}: patch too large")

    for line in text.splitlines():
        if line.startswith("```"):
            fail(f"{agent}: markdown fence in patch")

        if line.lower().startswith(("hello", "here is", "analysis", "recommendation")):
            fail(f"{agent}: prose detected inside patch")


def enforce(raw: str, agent: str) -> dict[str, Any]:
    agent = agent.upper().strip()

    if agent in VALID_PATCH_AGENTS:
        enforce_fixer_patch(raw, agent)
        return {
            "agent": agent,
            "status": "pass",
            "type": "patch",
        }

    if agent not in VALID_JSON_AGENTS:
        fail(f"{agent}: unknown agent")

    data = enforce_json_only(raw, agent)
    validate_json_agent(data, agent)

    return {
        "agent": agent,
        "status": "pass",
        "type": "json",
        "output": data,
    }


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage:")
        print("  python3 strict_mode.py <AGENT> <output_file>")
        sys.exit(2)

    agent = sys.argv[1]
    output_file = Path(sys.argv[2])

    if not output_file.exists():
        print(f"STRICT_MODE: FAIL — output file not found: {output_file}")
        sys.exit(2)

    raw = read_text(output_file)

    try:
        result = enforce(raw, agent)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)
    except StrictModeError as exc:
        print(json.dumps({
            "agent": agent.upper(),
            "status": "blocked",
            "reason": str(exc),
        }, indent=2, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
