#!/usr/bin/env python3
"""
output_firewall.py

Blocks non-machine-safe agent output before JSON parsing.
"""

import sys
from pathlib import Path


FORBIDDEN_PHRASES = [
    "hello",
    "i'm",
    "i am",
    "sorry",
    "as an ai",
    "here is",
    "analysis",
    "congratulations",
    "well done",
    "please let me know",
    "senior developer",
    "cyber security expert",
    "system architect",
    "textbook",
    "cnn",
    "tensorflow",
    "azure",
    "```",
]


class OutputFirewallError(Exception):
    pass


def check_output(raw: str) -> None:
    text = raw.strip()
    lower = text.lower()

    if not text:
        raise OutputFirewallError("Empty output.")

    if not text.startswith("{") or not text.endswith("}"):
        raise OutputFirewallError("Non-JSON output blocked.")

    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            raise OutputFirewallError(f"Forbidden phrase detected: {phrase}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 output_firewall.py <agent_output.txt>")
        sys.exit(2)

    path = Path(sys.argv[1])

    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(2)

    raw = path.read_text(encoding="utf-8", errors="ignore")

    try:
        check_output(raw)
        print("OUTPUT_FIREWALL: PASS")
        sys.exit(0)
    except OutputFirewallError as exc:
        print(f"OUTPUT_FIREWALL: FAIL — {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
