#!/usr/bin/env python3
"""
json_repair_guard.py

Safe minimal JSON repair.

Allowed:
- trailing commas
- whitespace cleanup

Forbidden:
- prose cleanup
- hallucination cleanup
- markdown stripping
"""

import json
import re
import sys
from pathlib import Path


class RepairError(Exception):
    pass


def repair_json(raw: str) -> str:
    text = raw.strip()

    if not text.startswith("{"):
        raise RepairError("Non-JSON content")

    if "```" in text:
        raise RepairError("Markdown detected")

    forbidden = [
        "Hello",
        "I'm",
        "Analysis",
        "Recommendations",
    ]

    lower = text.lower()

    for item in forbidden:
        if item.lower() in lower:
            raise RepairError(f"Forbidden prose: {item}")

    # Chirurginis taisymas: kableliai prieš užsidarančius skliaustus
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)

    return text


def validate(text: str) -> dict:
    return json.loads(text)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 json_repair_guard.py <file>")
        sys.exit(7)

    path = Path(sys.argv[1])

    if not path.exists():
        print("Missing file")
        sys.exit(8)

    raw = path.read_text(encoding="utf-8", errors="ignore")

    try:
        repaired = repair_json(raw)
        parsed = validate(repaired)

        print(json.dumps({
            "status": "pass",
            "output": parsed
        }, indent=2))

        sys.exit(0)

    except Exception as exc:
        print(json.dumps({
            "status": "blocked",
            "reason": str(exc)
        }, indent=2))

        sys.exit(2)


if __name__ == "__main__":
    main()
