import hashlib
import json
import secrets
import time
from secure_io import write_private

ALLOWED_CATEGORIES = {"schema", "protocol", "security", "runtime", "determinism"}


def quarantine(raw: str, category: str, reason: str = "unknown"):
    """Preserve invalid artifacts without following output-path links."""
    if category not in ALLOWED_CATEGORIES:
        raise ValueError("invalid quarantine category")
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > 2_000_000:
        raise ValueError("quarantine artifact is too large")
    timestamp = time.time_ns()
    digest = hashlib.sha256(raw.encode()).hexdigest()
    record = {"timestamp": timestamp, "category": category, "reason": reason,
              "artifact_hash": f"sha256:{digest}", "raw_content": raw}
    name = f"quarantine/{category}/{timestamp}_{secrets.token_hex(8)}.json"
    path = write_private(name, json.dumps(record, indent=2, allow_nan=False), exclusive=True)
    return {"status": "quarantined", "hash": digest, "path": path}
