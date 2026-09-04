"""Metadata-only quarantine with bounded retention.

Untrusted model output may contain secrets, so raw content is never persisted.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

QUARANTINE_ROOT = Path("runtime/quarantine")
ALLOWED_CATEGORIES = {"schema", "protocol", "security", "runtime", "determinism"}
MAX_RECORDS_PER_CATEGORY = 100


def _enforce_retention(target: Path) -> None:
    records = sorted(
        (path for path in target.glob("*.json") if path.is_file() and not path.is_symlink()),
        key=lambda path: path.stat().st_mtime,
    )
    for old in records[: max(0, len(records) - MAX_RECORDS_PER_CATEGORY + 1)]:
        old.unlink(missing_ok=True)


def quarantine(raw: str, category: str, reason: str = "unknown") -> dict[str, str]:
    if category not in ALLOWED_CATEGORIES:
        category = "runtime"
    encoded = raw.encode("utf-8", errors="replace")
    digest = hashlib.sha256(encoded).hexdigest()
    timestamp = int(time.time())

    target = QUARANTINE_ROOT / category
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(target, 0o700)
    _enforce_retention(target)

    path = target / f"{time.time_ns()}_{digest[:8]}.json"
    record = {
        "timestamp": timestamp,
        "category": category,
        "reason": reason[:256],
        "artifact_hash": f"sha256:{digest}",
        "artifact_size_bytes": len(encoded),
        "raw_content_stored": False,
    }
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(record, handle, sort_keys=True, separators=(",", ":"))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())

    return {"status": "quarantined", "hash": digest, "path": str(path)}
