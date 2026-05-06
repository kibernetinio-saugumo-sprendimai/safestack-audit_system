#!/usr/bin/env python3
"""
fixer_guard.py

Validates FIXER output before any patch can be applied.

Rules:
- unified diff only
- no prose
- no greetings
- no markdown fences
- no dangerous path edits
"""

import sys
from pathlib import Path


FORBIDDEN_PHRASES = [
    "hello",
    "i'm",
    "i am",
    "sorry",
    "here is",
    "analysis",
    "congratulations",
    "please let me know",
    "well done",
    "senior",
    "expert",
]

FORBIDDEN_PATHS = [
    "/etc/passwd",
    "/etc/shadow",
    "/etc/sudoers",
    "/root/",
    "/boot/",
]


class FixerGuardError(Exception):
    pass


def read_patch(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def validate_patch(text: str) -> None:
    stripped = text.strip()
    lower = stripped.lower()

    if not stripped:
        raise FixerGuardError("Patch is empty.")

    if "```" in stripped:
        raise FixerGuardError("Markdown code fence detected.")

    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            raise FixerGuardError(f"Forbidden phrase detected: {phrase}")

    if not stripped.startswith("--- "):
        raise FixerGuardError("Patch must start with unified diff header: ---")

    if "+++ " not in stripped:
        raise FixerGuardError("Patch missing +++ header.")

    if "@@" not in stripped:
        raise FixerGuardError("Patch missing hunk marker @@.")

    for path in FORBIDDEN_PATHS:
        if path in stripped:
            raise FixerGuardError(f"Forbidden path modification detected: {path}")

    if len(stripped.splitlines()) > 500:
        raise FixerGuardError("Patch too large for controlled FIXER output.")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 fixer_guard.py <patch.diff>")
        sys.exit(2)

    patch_path = Path(sys.argv[1])

    if not patch_path.exists():
        print(f"Patch not found: {patch_path}")
        sys.exit(2)

    try:
        validate_patch(read_patch(patch_path))
        print("FIXER_GUARD: PASS")
        sys.exit(0)
    except FixerGuardError as exc:
        print(f"FIXER_GUARD: FAIL — {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
