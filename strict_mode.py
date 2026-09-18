"""Validate model envelopes; these content rules are not a network sandbox."""
import ipaddress
import json
import re
from urllib.parse import urlsplit

FORBIDDEN_TOKENS = ["```", "# ", "Certainly", "I think", "maybe", "I apologize",
                    "Here is the", "Please find", "Note:", "**"]
REQUIRED_FIELDS = ["agent", "status", "findings"]
SEVERITIES = {"critical", "high", "medium", "low", "info"}
ROLE_FIELDS = {
    "ARCHITECT": {}, "CODER": {}, "SECURITY": {},
    "DOCUMENTER": {"summary": str},
    "SUPERVISOR": {"approved_findings": list, "rejected_findings": list},
    "FIXER": {"patches": list},
    "VALIDATOR": {"issue": str}, "REVIEWER": {"reasoning": str},
}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError("nonfinite JSON number")


def parse_json(raw):
    return json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)


def check_airgap_violation(raw: str) -> bool:
    """Check exact destinations in decoded text, never URL substrings."""
    for match in re.findall(r"[a-z][a-z0-9+.-]*://[^\s\"'<>]+", raw, re.I):
        try:
            parsed = urlsplit(match.rstrip(".,;)}"))
            host = parsed.hostname
            if parsed.username is not None or parsed.password is not None:
                return True
            if host == "localhost":
                continue
            if host is None or not ipaddress.ip_address(host).is_loopback:
                return True
        except ValueError:
            return True
    for value in re.findall(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])|\[[0-9a-f:]+\]", raw, re.I):
        try:
            if not ipaddress.ip_address(value.strip("[]")).is_loopback:
                return True
        except ValueError:
            return True
    return False


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            # Quoted source and proposed code are inert data, not narrative.
            if key not in {"evidence", "content"}:
                yield from _strings(item)


def valid_finding(finding):
    required = {"id", "issue", "evidence", "severity"}
    return (isinstance(finding, dict) and required.issubset(finding)
            and all(isinstance(finding[k], str) and finding[k].strip() for k in required)
            and finding["severity"] in SEVERITIES)


def validate_output(raw: str, expected_agent=None):
    if not isinstance(raw, str):
        return reject("INVALID_OUTPUT_TYPE")
    try:
        if len(raw.encode("utf-8")) > 250_000:
            return reject("OUTPUT_TOO_LARGE")
        data = parse_json(raw)
    except (ValueError, TypeError, RecursionError):
        return reject("INVALID_JSON")
    if not isinstance(data, dict):
        return reject("ROOT_NOT_OBJECT")
    for field in REQUIRED_FIELDS:
        if field not in data:
            return reject(f"MISSING_FIELD:{field}")
    if not isinstance(data["agent"], str) or not isinstance(data["status"], str) or not isinstance(data["findings"], list):
        return reject("INVALID_FIELD_TYPES")
    if data["status"] not in {"pass", "fail", "ok", "quarantined", "error"}:
        return reject("INVALID_STATUS")
    if len(data["findings"]) > 500:
        return reject("TOO_MANY_FINDINGS")
    if not all(valid_finding(f) for f in data["findings"]):
        return reject("INVALID_FINDING_SCHEMA")
    if expected_agent is not None:
        if data["agent"] != expected_agent or expected_agent not in ROLE_FIELDS:
            return reject("UNEXPECTED_AGENT")
        if data["status"] not in {"pass", "fail"}:
            return reject("INVALID_ROLE_STATUS")
        for key, kind in ROLE_FIELDS[expected_agent].items():
            if not isinstance(data.get(key), kind):
                return reject(f"INVALID_ROLE_FIELD:{key}")
        if expected_agent == "SUPERVISOR":
            for key in ("approved_findings", "rejected_findings"):
                if len(data[key]) > 500 or not all(valid_finding(f) for f in data[key]):
                    return reject(f"INVALID_ROLE_FIELD:{key}")
        if expected_agent == "FIXER":
            if len(data["patches"]) > 100:
                return reject("TOO_MANY_PATCHES")
            for patch in data["patches"]:
                if (not isinstance(patch, dict) or set(patch) != {"path", "content"}
                        or not isinstance(patch["path"], str) or not patch["path"]
                        or not isinstance(patch["content"], str)):
                    return reject("INVALID_PATCH")
    try:
        for text in _strings(data):
            if check_airgap_violation(text):
                return reject("AIRGAP_VIOLATION: External URL detected")
            for token in FORBIDDEN_TOKENS:
                if token in text:
                    return reject(f"PROTOCOL_VIOLATION:{token}")
    except RecursionError:
        return reject("INVALID_JSON")
    return accept(data)


def reject(reason):
    return {"status": "invalid", "reason": reason, "quarantine_required": True}


def accept(data):
    return {"status": "valid", "validated": True, "artifact": data}


def verify_chain(history: list) -> dict:
    import hashlib
    previous = "0" * 64
    for i, record in enumerate(history):
        if not isinstance(record, dict) or not isinstance(record.get("content"), str):
            return {"trusted_chain_valid": False, "reason": "INVALID_RECORD", "position": i}
        expected = hashlib.sha256(f"{previous}|{record['content']}".encode()).hexdigest()
        if record.get("hash") != expected:
            return {"trusted_chain_valid": False, "reason": f"HASH_MISMATCH at position {i}", "position": i}
        previous = expected
    return {"trusted_chain_valid": True, "reason": "CHAIN_VERIFIED"}
