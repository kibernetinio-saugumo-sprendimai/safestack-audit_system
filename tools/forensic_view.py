"""Display the newest private quarantine records to the local operator."""
import json
import os
from pathlib import Path

import secure_io
from secure_io import read_regular


def view_latest_evidence():
    root = secure_io.RUNTIME_ROOT / "quarantine"
    if not root.exists():
        print("No quarantine evidence found.")
        return
    candidates = []
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if not (Path(directory) / name).is_symlink()]
        candidates.extend(Path(directory) / name for name in files if name.endswith(".json"))
    candidates.sort(key=lambda path: path.name, reverse=True)
    count = 0
    for path in candidates[:3]:
        try:
            relative = path.relative_to(secure_io.RUNTIME_ROOT).as_posix()
            data = json.loads(read_regular(secure_io.RUNTIME_ROOT, relative, 2_100_000))
            if not isinstance(data, dict):
                continue
            count += 1
            print(f"--- ARTIFACT: {path.name} ---")
            print(f"CATEGORY: {data.get('category')}")
            print(f"REASON:   {data.get('reason')}")
            print(f"HASH:     {data.get('artifact_hash')}")
            print("\nRAW CONTENT FROM AGENT:\n" + "-" * 40)
            print(data.get("raw_content"))
            print("-" * 40)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    if not count:
        print("Quarantine is empty.")


if __name__ == "__main__":
    view_latest_evidence()
