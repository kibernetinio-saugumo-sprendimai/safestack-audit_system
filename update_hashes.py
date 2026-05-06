import hashlib
import json
import hmac
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Raktas imamas iš aplinkos kintamojo SAFESTACK_ROOT_KEY
ROOT_PRIVATE_KEY = os.environ.get("SAFESTACK_ROOT_KEY")

FILES = [
    "GLOBAL_POLICY.md",
    "PRIORITY_MODEL.md",
    "THREAT_MODEL.md",
    "STATE_MODEL.md",
    "EXIT_CODE_POLICY.md",
    "CHAIN_OF_TRUST.md",
    "IMMUTABILITY_POLICY.md",
    "FORENSICS_POLICY.md",
    "ENFORCEMENT_MATRIX.md",
    "SAFE_RECOVERY_POLICY.md"
]

def get_hash(filename):
    path = Path(filename)
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()

def sign_data(data_str, key_hex):
    key_bytes = bytes.fromhex(key_hex)
    data_bytes = data_str.encode('utf-8')
    return hmac.new(key_bytes, data_bytes, hashlib.sha256).hexdigest()

def update_and_sign_registry():
    if not ROOT_PRIVATE_KEY:
        print("[!] ERROR: SAFESTACK_ROOT_KEY environment variable not set.")
        sys.exit(1)

    hashes = {f: get_hash(f) for f in FILES}
    registry_data = {
        "registry_name": "SafeStack Governance Hash Registry",
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "hashes": hashes
    }
    
    canonical_json = json.dumps(registry_data, sort_keys=True)
    signature = sign_data(canonical_json, ROOT_PRIVATE_KEY)
    
    registry_data["signature_v1"] = signature
    registry_data["signer"] = "CHIEF_SUPERVISOR_ROOT"
    
    with open("POLICY_HASH_REGISTRY.json", "w", encoding="utf-8") as f:
        json.dump(registry_data, f, indent=2, ensure_ascii=False)
    
    print("[+] POLICY_HASH_REGISTRY.json successfully updated and SIGNED.")

if __name__ == "__main__":
    update_and_sign_registry()
