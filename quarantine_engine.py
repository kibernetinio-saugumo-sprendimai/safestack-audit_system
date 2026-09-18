from pathlib import Path
import hashlib
import time
import json
import os

QUARANTINE_ROOT = Path("runtime/quarantine")
ALLOWED_CATEGORIES = {"schema", "protocol", "security", "runtime", "determinism"}

def quarantine(raw: str, category: str, reason: str = "unknown"):
    """Preserves invalid runtime artifacts in isolated storage."""
    if category not in ALLOWED_CATEGORIES:
        raise ValueError("invalid quarantine category")
    if len(raw) > 2_000_000:
        raise ValueError("quarantine artifact is too large")
    ts = time.time_ns()
    digest = hashlib.sha256(raw.encode()).hexdigest()

    target = QUARANTINE_ROOT / category
    target.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        raise ValueError("quarantine category must not be a symlink")
    target = target.resolve(strict=True)
    target.relative_to(Path.cwd().resolve())

    filename = f"{ts}_{digest[:8]}.json"
    path = target / filename

    record = {
        "timestamp": ts,
        "category": category,
        "reason": reason,
        "artifact_hash": f"sha256:{digest}",
        "raw_content": raw
    }

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
    except Exception:
        try: os.close(fd)
        except OSError: pass
        raise

    return {
        "status": "quarantined",
        "hash": digest,
        "path": str(path)
    }
