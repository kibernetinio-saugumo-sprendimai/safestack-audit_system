"""Strict, typed validation for agent-produced audit JSON."""

from __future__ import annotations

import ipaddress
import json
import re
from typing import Any
from urllib.parse import urlparse

MAX_OUTPUT_BYTES = 256 * 1024
MAX_FINDINGS = 100
ALLOWED_AGENTS = {
    "architect",
    "coder",
    "developer",
    "security",
    "documenter",
    "writer",
    "supervisor",
    "validator",
    "reviewer",
    "test",
}
ALLOWED_STATUSES = {"pass", "fail"}
ALLOWED_FIELDS = {
    "agent",
    "status",
    "findings",
    "approved_findings",
    "rejected_findings",
    "summary",
    "reasoning",
    "issue",
}
ALLOWED_SEVERITIES = {"critical", "high", "medium", "low", "info"}
FORBIDDEN_TOKENS = ["```", "# ", "Certainly", "I think", "maybe", "I apologize", "Here is the", "Please find", "Note:", "**"]
URL_PATTERN = re.compile(r"(?:https?|ftp|ssh|ws|wss|telnet)://[^\s\"'\}]+", re.IGNORECASE)
IP_PATTERN = re.compile(r"(?<![A-Za-z0-9])(?:\d{1,3}\.){3}\d{1,3}(?![A-Za-z0-9])")


def check_external_reference(raw: str) -> bool:
    """Reject non-loopback network references in model output.

    This is an output policy, not a substitute for OS-level network isolation.
    """
    for value in URL_PATTERN.findall(raw):
        host = urlparse(value).hostname
        if host not in {"localhost", "127.0.0.1", "::1"}:
            return True
    for value in IP_PATTERN.findall(raw):
        try:
            if not ipaddress.ip_address(value).is_loopback:
                return True
        except ValueError:
            return True
    return False


def validate_finding(finding: Any, index: int) -> str | None:
    if not isinstance(finding, dict):
        return f"FINDING_NOT_OBJECT:{index}"
    required = {"id", "issue", "evidence", "severity"}
    if not required.issubset(finding):
        return f"FINDING_MISSING_FIELDS:{index}"
    if not all(isinstance(finding[key], str) and finding[key].strip() for key in required):
        return f"FINDING_INVALID_VALUE:{index}"
    if finding["severity"].lower() not in ALLOWED_SEVERITIES:
        return f"FINDING_INVALID_SEVERITY:{index}"
    return None


def validate_output(raw: str) -> dict[str, Any]:
    if not isinstance(raw, str) or len(raw.encode("utf-8", errors="replace")) > MAX_OUTPUT_BYTES:
        return reject("OUTPUT_SIZE_LIMIT")
    if any(ord(char) < 32 and char not in "\r\n\t" for char in raw):
        return reject("CONTROL_CHARACTER")
    try:
        data = json.loads(raw)
    except Exception:
        return reject("INVALID_JSON")
    if not isinstance(data, dict):
        return reject("ROOT_NOT_OBJECT")
    unknown = set(data) - ALLOWED_FIELDS
    if unknown:
        return reject("UNKNOWN_FIELDS:" + ",".join(sorted(unknown)))

    for field in ("agent", "status", "findings"):
        if field not in data:
            return reject(f"MISSING_FIELD:{field}")

    agent = data.get("agent")
    status = data.get("status")
    findings = data.get("findings")
    if not isinstance(agent, str) or agent.lower() not in ALLOWED_AGENTS:
        return reject("INVALID_AGENT")
    if not isinstance(status, str) or status.lower() not in ALLOWED_STATUSES:
        return reject("INVALID_STATUS")
    if not isinstance(findings, list) or len(findings) > MAX_FINDINGS:
        return reject("INVALID_FINDINGS")

    for index, finding in enumerate(findings):
        reason = validate_finding(finding, index)
        if reason:
            return reject(reason)
    for field in ("approved_findings", "rejected_findings"):
        if field in data and not isinstance(data[field], list):
            return reject(f"INVALID_FIELD:{field}")
    for field in ("summary", "reasoning", "issue"):
        if field in data and not isinstance(data[field], str):
            return reject(f"INVALID_FIELD:{field}")

    if check_external_reference(raw):
        return reject("EXTERNAL_REFERENCE")
    for token in FORBIDDEN_TOKENS:
        if token in raw:
            return reject(f"PROTOCOL_VIOLATION:{token}")
    return accept(data)


def reject(reason: str) -> dict[str, Any]:
    return {"status": "invalid", "reason": reason, "quarantine_required": True}


def accept(data: dict[str, Any]) -> dict[str, Any]:
    return {"status": "valid", "validated": True, "artifact": data}


def verify_chain(history: list[dict[str, Any]]) -> dict[str, Any]:
    import hashlib

    prev_hash = "0" * 64
    for index, record in enumerate(history):
        content = str(record.get("content", ""))
        claimed_hash = record.get("hash", "")
        expected_hash = hashlib.sha256(f"{prev_hash}|{content}".encode()).hexdigest()
        if claimed_hash != expected_hash:
            return {"trusted_chain_valid": False, "reason": f"HASH_MISMATCH at position {index}", "position": index}
        prev_hash = claimed_hash
    return {"trusted_chain_valid": True, "reason": "CHAIN_VERIFIED"}
