from pathlib import Path
import hashlib
import time
import json

QUARANTINE_ROOT = Path("runtime/quarantine")

def quarantine(raw: str, category: str, reason: str = "unknown"):
    """Preserves invalid runtime artifacts in isolated storage."""
    ts = int(time.time())
    digest = hashlib.sha256(raw.encode()).hexdigest()

    target = QUARANTINE_ROOT / category
    target.mkdir(parents=True, exist_ok=True)

    filename = f"{ts}_{digest[:8]}.json"
    path = target / filename

    record = {
        "timestamp": ts,
        "category": category,
        "reason": reason,
        "artifact_hash": f"sha256:{digest}",
        "raw_content": raw
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    return {
        "status": "quarantined",
        "hash": digest,
        "path": str(path)
    }
