import json

FORBIDDEN_TOKENS = [
    "```",
    "# ",
    "Certainly",
    "I think",
    "maybe",
    "I apologize",
    "Here is the",
    "Please find",
    "Note:",
    "**"
]

def check_airgap_violation(raw: str) -> bool:
    """Blocks any external URLs, literal IPs, and non-local protocols."""
    import re
    # Catch http, https, ftp, ssh, ws, telnet (using non-capturing groups)
    patterns = [
        r'(?:https?|ftp|ssh|ws|telnet)://[^\s\"\'\}]+',
        r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b' # Literal IPv4
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, raw)
        for match in matches:
            # If it's a URL, check if it's local
            if "localhost" not in match and "127.0.0.1" not in match:
                return True
    return False

REQUIRED_FIELDS = [
    "agent",
    "status",
    "findings"
]

def validate_output(raw: str):
    """Primary protocol enforcement gate."""
    try:
        data = json.loads(raw)
    except Exception:
        return reject("INVALID_JSON")

    for field in REQUIRED_FIELDS:
        if field not in data:
            return reject(f"MISSING_FIELD:{field}")

    if check_airgap_violation(raw):
        return reject("AIRGAP_VIOLATION: External URL detected")

    for token in FORBIDDEN_TOKENS:
        if token in raw:
            return reject(f"PROTOCOL_VIOLATION:{token}")

    return accept(data)

def reject(reason: str):
    return {
        "status": "invalid",
        "reason": reason,
        "quarantine_required": True
    }

def accept(data: dict):
    return {
        "status": "valid",
        "validated": True,
        "artifact": data
    }

def verify_chain(history: list) -> dict:
    """Verifies the integrity of a linked hash chain history."""
    import hashlib
    prev_hash = "0" * 64
    for i, record in enumerate(history):
        content = str(record.get("content", ""))
        claimed_hash = record.get("hash", "")
        
        # Recalculate hash based on linked rule: H(prev_hash | current_content)
        combined = f"{prev_hash}|{content}"
        expected_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        if claimed_hash != expected_hash:
            return {
                "trusted_chain_valid": False,
                "reason": f"HASH_MISMATCH at position {i}",
                "position": i
            }
        prev_hash = claimed_hash
        
    return {"trusted_chain_valid": True, "reason": "CHAIN_VERIFIED"}
