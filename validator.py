#!/usr/bin/env python3
import json
from typing import Any

FORBIDDEN_PHRASES = [
    "hello",
    "i'm",
    "i am",
    "senior developer",
    "cyber security",
    "expert",
    "specialist",
    "assistant",
    "ai model",
    "analysis",
    "here is",
    "i hope",
    "as an ai",
    "tensorflow",
    "cnn",
    "congratulations",
]

REQUIRED_AGENT_VALUES = {
    "ARCHITECT",
    "CODER",
    "SECURITY",
    "DOCUMENTER",
    "FIXER",
    "REVIEWER",
}

REQUIRED_SEVERITIES = {
    "critical",
    "high",
    "medium",
    "low",
    "info",
}

class ValidationError(Exception):
    pass

def parse_json_only(raw: str) -> dict[str, Any]:
    raw_stripped = raw.strip()
    
    if not raw_stripped.startswith("{"):
        raise ValidationError("NON-JSON OUTPUT: Output must start with '{'")

    lower = raw_stripped.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            raise ValidationError(f"FORBIDDEN PHRASE DETECTED: {phrase}")

    try:
        return json.loads(raw_stripped)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON: {exc}") from exc

def validate_agent_output(data: dict[str, Any]) -> None:
    if data.get("agent") not in REQUIRED_AGENT_VALUES:
        raise ValidationError("Invalid or missing agent.")
    if data.get("status") not in {"pass", "fail"}:
        raise ValidationError("Invalid or missing status.")
    findings = data.get("findings")
    if not isinstance(findings, list):
        raise ValidationError("findings must be a list.")
    for finding in findings:
        for key in ["id", "severity", "file", "evidence", "issue", "recommendation"]:
            if key not in finding:
                raise ValidationError(f"Finding missing key: {key}")
            if not isinstance(finding[key], str):
                raise ValidationError(f"Finding key must be string: {key}")
            if key == "evidence" and not finding[key].strip():
                raise ValidationError("Finding evidence cannot be empty.")
        if finding["severity"] not in REQUIRED_SEVERITIES:
            raise ValidationError(f"Invalid severity: {finding['severity']}")
    if data["status"] == "pass" and findings:
        raise ValidationError("status=pass cannot contain findings.")
    if data["status"] == "fail" and not findings:
        raise ValidationError("status=fail must contain findings.")

def validate(raw: str) -> dict[str, Any]:
    data = parse_json_only(raw)
    validate_agent_output(data)
    return data
