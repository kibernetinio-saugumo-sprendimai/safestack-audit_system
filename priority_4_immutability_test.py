from path_guard import is_protected, validate_write_attempt

def run_immutability_test():
    print("=== SafeStack Immutability Audit ===")
    
    test_cases = [
        ("generated_code/safe_script.sh", False), # SAFE
        ("governance/policy_bundle/32_CORE.md", True), # PROTECTED
        ("strict_mode.py", True), # PROTECTED
        ("app.py", True), # PROTECTED
        ("../outside_root.txt", True), # PROTECTED (Escaping root)
        ("quarantine_engine.py", True), # PROTECTED
        ("random_file.py", False), # SAFE (if not in root list)
    ]
    
    failures = 0
    for path, expected in test_cases:
        result = is_protected(path)
        marker = "[PASS]" if result == expected else "[FAIL]"
        print(f"{marker} Path: {path:40} | Protected: {result}")
        if result != expected: failures += 1
        
    # Test physical enforcement
    print("\n--- Testing Physical Enforcement ---")
    try:
        validate_write_attempt("governance/hacked.md")
        print("FAILURE: System allowed write to governance!")
        failures += 1
    except PermissionError as e:
        print(f"SUCCESS: Write blocked. Message: {e}")

    print("\n=== IMMUTABILITY SUMMARY ===")
    if failures == 0:
        print("CORE IMMUTABILITY CONFIRMED. PROTECTED ZONES ARE INVIOLABLE.")
    else:
        print(f"FAILED: {failures} immutability bypasses detected!")
        exit(1)

if __name__ == "__main__":
    run_immutability_test()
