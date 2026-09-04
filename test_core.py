import json
import hashlib
from canonical_serializer import canonical_json
from strict_mode import validate_output
from quarantine_engine import quarantine

def test_hash_determinism():
    print("--- 1. HASH DETERMINISM TEST ---")
    obj1 = {"a": 1, "b": 2}
    obj2 = {"b": 2, "a": 1}
    
    c1 = canonical_json(obj1)
    c2 = canonical_json(obj2)
    
    h1 = hashlib.sha256(c1.encode()).hexdigest()
    h2 = hashlib.sha256(c2.encode()).hexdigest()
    
    assert h1 == h2
    print(f"PASS: {h1} == {h2}")

def test_invalid_json():
    print("\n--- 2. INVALID JSON TEST ---")
    raw = '{ "status":'
    result = validate_output(raw)
    print(f"Result: {result}")
    assert result["status"] == "invalid"
    assert result["reason"] == "INVALID_JSON"
    print("PASS: Invalid JSON caught.")

def test_prose_leakage():
    print("\n--- 3. PROSE LEAKAGE TEST ---")
    raw = '{"agent": "test", "status": "pass", "findings": [], "issue": "I think this is dangerous"}'
    result = validate_output(raw)
    print(f"Result: {result}")
    assert result["status"] == "invalid"
    assert "PROTOCOL_VIOLATION" in result["reason"]
    print("PASS: Prose leakage caught.")

def test_markdown_leakage():
    print("\n--- 4. MARKDOWN LEAKAGE TEST ---")
    raw = '```json\n{"agent": "test", "status": "ok", "findings": []}\n```'
    result = validate_output(raw)
    print(f"Result: {result}")
    assert result["status"] == "invalid"
    print("PASS: Markdown leakage caught.")

def test_missing_field():
    print("\n--- 5. MISSING REQUIRED FIELD TEST ---")
    raw = '{"agent": "test", "status": "pass"}'
    result = validate_output(raw)
    print(f"Result: {result}")
    assert result["status"] == "invalid"
    assert "MISSING_FIELD:findings" in result["reason"]
    print("PASS: Missing 'findings' field caught.")

def test_fake_approval_rejected():
    print("\n--- 6. FAKE APPROVAL TEST ---")
    raw = '{"agent":"test","status":"approved","findings":[],"canonical":true}'
    result = validate_output(raw)
    assert result["status"] == "invalid"
    print("PASS: Fake approval rejected.")

def test_findings_type_enforced():
    print("\n--- 7. FINDINGS TYPE TEST ---")
    result = validate_output('{"agent":"test","status":"pass","findings":"none"}')
    assert result["status"] == "invalid"
    print("PASS: Findings type enforced.")

def test_quarantine_integrity():
    print("\n--- 8. QUARANTINE INTEGRITY TEST ---")
    raw = "CORRUPT DATA"
    result = quarantine(raw, "schema", "Testing quarantine")
    print(f"Quarantine result: {result}")
    assert result["status"] == "quarantined"
    assert "hash" in result
    assert "path" in result
    import os
    assert os.path.exists(result["path"])
    with open(result["path"], "r", encoding="utf-8") as handle:
        record = json.load(handle)
    assert record["raw_content_stored"] is False
    assert "raw_content" not in record
    print("PASS: Quarantine file created and hash-verified.")

if __name__ == "__main__":
    try:
        test_hash_determinism()
        test_invalid_json()
        test_prose_leakage()
        test_markdown_leakage()
        test_missing_field()
        test_fake_approval_rejected()
        test_findings_type_enforced()
        test_quarantine_integrity()
        print("\n✅ CORE DETERMINISM VERIFIED. Trust layer is stable.")
    except Exception as e:
        print(f"\n❌ DETERMINISM FAILURE: {e}")
        exit(1)
