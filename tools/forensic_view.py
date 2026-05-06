import json
import os
from pathlib import Path

QUARANTINE_ROOT = Path("runtime/quarantine")

def view_latest_evidence():
    print("=== SafeStack Forensic Evidence Viewer ===")
    if not QUARANTINE_ROOT.exists():
        print("No quarantine evidence found.")
        return

    # Find all quarantined files
    files = list(QUARANTINE_ROOT.glob("**/*.json"))
    if not files:
        print("Quarantine is empty.")
        return

    # Sort by timestamp (prefix of filename)
    files.sort(key=lambda x: x.name, reverse=True)

    print(f"Found {len(files)} forensic artifacts. Showing latest 3:\n")

    for f in files[:3]:
        try:
            with open(f, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                print(f"--- ARTIFACT: {f.name} ---")
                print(f"CATEGORY: {data.get('category')}")
                print(f"REASON:   {data.get('reason')}")
                print(f"HASH:     {data.get('artifact_hash')}")
                print("\nRAW CONTENT FROM AGENT:")
                print("-" * 40)
                print(data.get('raw_content'))
                print("-" * 40 + "\n")
        except Exception as e:
            print(f"Error reading {f}: {e}")

if __name__ == "__main__":
    view_latest_evidence()
