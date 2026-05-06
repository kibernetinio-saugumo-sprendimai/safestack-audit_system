import hashlib
import json
import copy
from strict_mode import verify_chain

def calculate_linked_hash(content, prev_hash):
    combined = f"{prev_hash}|{content}"
    return hashlib.sha256(combined.encode()).hexdigest()

def build_valid_chain():
    prev_hash = "0" * 64
    history = []
    messages = ["DISCOVERER: Started", "ARCHITECT: Analyzed", "REVIEWER: Approved"]
    
    for msg in messages:
        h = calculate_linked_hash(msg, prev_hash)
        history.append({"content": msg, "hash": h})
        prev_hash = h
    return history

def run_test(name, tampered_history):
    print(f"--- TESTING: {name} ---")
    result = verify_chain(tampered_history)
    print(f"Result: {result}")
    
    if not result["trusted_chain_valid"]:
        print(f"SUCCESS: Tampering detected. Reason: {result['reason']}")
        return True
    else:
        print(f"FAILURE: Tampering BYPASSED verification!")
        return False

def audit_suite():
    valid_history = build_valid_chain()
    failures = 0
    
    # 1. Change artifact content, leave old hash
    case1 = copy.deepcopy(valid_history)
    case1[1]["content"] = "ARCHITECT: Malicious edit"
    if not run_test("CONTENT_TAMPER", case1): failures += 1

    # 2. Change hash, leave old content
    case2 = copy.deepcopy(valid_history)
    case2[1]["hash"] = "0" * 64
    if not run_test("HASH_TAMPER", case2): failures += 1

    # 3. Delete middle chain record
    case3 = copy.deepcopy(valid_history)
    del case3[1]
    if not run_test("MIDDLE_RECORD_DELETION", case3): failures += 1

    # 4. Swap chain_position
    case4 = [valid_history[0], valid_history[2], valid_history[1]]
    if not run_test("POSITION_SWAP", case4): failures += 1

    # 5. Re-insert old valid record (Duplicate)
    case5 = copy.deepcopy(valid_history)
    case5.insert(1, valid_history[1])
    if not run_test("RECORD_DUPLICATION", case5): failures += 1

    # 6. Change previous_hash dependency (indirectly tested by any linkage break)
    case6 = copy.deepcopy(valid_history)
    case6[2]["hash"] = calculate_linked_hash(case6[2]["content"], "WRONG_PREV")
    if not run_test("PREV_HASH_TAMPER", case6): failures += 1

    # 7. Add rogue record into the end
    case7 = copy.deepcopy(valid_history)
    case7.append({"content": "HACKER: Injected", "hash": "random_hash"})
    if not run_test("ROGUE_RECORD_APPEND", case7): failures += 1

    print(f"\n=== HASH-CHAIN AUDIT SUMMARY ===")
    if failures == 0:
        print("ALL TAMPERING ATTEMPTS DETECTED. CHAIN IS SECURE.")
    else:
        print(f"FAILED: {failures} tampering attempts bypassed verification!")
        exit(1)

if __name__ == "__main__":
    audit_suite()
