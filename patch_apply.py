#!/usr/bin/env python3
"""
patch_apply.py

Controlled patch apply tool.

Modes:
- --dry-run : test only
- --apply   : apply patch

Never applies without explicit --apply.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> int:
    result = subprocess.run(cmd, text=True)
    return result.returncode


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        print(f"Required tool not found: {name}")
        sys.exit(2)


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage:")
        print("  python3 patch_apply.py --dry-run <patch.diff>")
        print("  python3 patch_apply.py --apply <patch.diff>")
        sys.exit(2)

    mode = sys.argv[1]
    patch_path = Path(sys.argv[2])

    if mode not in {"--dry-run", "--apply"}:
        print("Invalid mode. Use --dry-run or --apply.")
        sys.exit(2)

    if not patch_path.exists():
        print(f"Patch not found: {patch_path}")
        sys.exit(2)

    require_tool("patch")

    if mode == "--dry-run":
        # -p1 assumption for current structure
        code = run(["patch", "--dry-run", "-p1", "-i", str(patch_path)])
        if code == 0:
            print("PATCH_DRY_RUN: PASS")
        else:
            print("PATCH_DRY_RUN: FAIL")
        sys.exit(code)

    if mode == "--apply":
        code = run(["patch", "-p1", "-i", str(patch_path)])
        if code == 0:
            print("PATCH_APPLY: PASS")
        else:
            print("PATCH_APPLY: FAIL")
        sys.exit(code)


if __name__ == "__main__":
    main()
