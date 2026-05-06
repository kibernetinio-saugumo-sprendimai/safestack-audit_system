import hashlib
import json
import hmac
import sys
from pathlib import Path

# Šis skriptas prašo įvesti raktą patikrai (saugumo sumetimais jis čia neįrašytas)
def verify_registry(key_hex):
    registry_path = Path("POLICY_HASH_REGISTRY.json")
    if not registry_path.exists():
        return False, "Missing registry file"

    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        signature = data.pop("signature_v1", None)
        signer = data.pop("signer", None)

        if not signature:
            return False, "No signature found in registry"

        # Sukuriame kanoninę JSON formą patikrai
        canonical_json = json.dumps(data, sort_keys=True)
        
        # Perskaičiuojame parašą su pateiktu raktu
        key_bytes = bytes.fromhex(key_hex)
        expected_signature = hmac.new(key_bytes, canonical_json.encode('utf-8'), hashlib.sha256).hexdigest()

        if hmac.compare_digest(signature, expected_signature):
            return True, f"VALID SIGNATURE (Signed by {signer})"
        else:
            return False, "INVALID SIGNATURE (Tampering detected or wrong key)"

    except Exception as e:
        return False, f"Verification error: {str(e)}"

if __name__ == "__main__":
    key = input("Enter ROOT PRIVATE KEY for verification: ").strip()
    success, msg = verify_registry(key)
    print(f"[*] Result: {msg}")
    sys.exit(0 if success else 1)
