#!/usr/bin/env python3
"""
deterministic_runner.py

Ensures repeated execution consistency.
"""

import hashlib
import json
import subprocess
import sys


def sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def run(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    return result.stdout.strip()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 deterministic_runner.py <command>")
        sys.exit(7)

    cmd = sys.argv[1:]

    # Paleidžiame du kartus ir lyginame
    out1 = run(cmd)
    out2 = run(cmd)

    h1 = sha256(out1)
    h2 = sha256(out2)

    result = {
        "deterministic": h1 == h2,
        "hash_1": h1,
        "hash_2": h2,
    }

    print(json.dumps(result, indent=2))

    if h1 != h2:
        # Jei nesutampa, laikome tai protokolo pažeidimu
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
