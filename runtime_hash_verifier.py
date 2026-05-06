#!/usr/bin/env python3
"""
runtime_hash_verifier.py

Verifies governance integrity before execution.
"""

import hashlib
import json
import sys
from pathlib import Path


# Pagrindiniai valdymo dokumentai (DNR)
FILES = [
    "GLOBAL_POLICY.md",
    "PRIORITY_MODEL.md",
    "THREAT_MODEL.md",
    "STATE_MODEL.md",
    "EXIT_CODE_POLICY.md",
    "CHAIN_OF_TRUST.md",
]


def sha256_file(path: Path) -> str:
    # Apskaičiuojame failo SHA256 atspaudą
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    results = {}
    missing = []

    for item in FILES:
        path = Path(item)

        if not path.exists():
            missing.append(item)
            continue

        results[item] = sha256_file(path)

    if missing:
        # Jei trūksta nors vieno failo – blokuojame visą sistemą
        print(json.dumps({
            "status": "blocked",
            "missing": missing
        }, indent=2))

        sys.exit(8)

    # Grąžiname esamus atspaudus palyginimui
    print(json.dumps({
        "status": "pass",
        "hashes": results
    }, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()
