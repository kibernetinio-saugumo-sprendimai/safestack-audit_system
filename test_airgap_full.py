from strict_mode import validate_output

test_payloads = [
    ('{"agent": "test", "status": "pass", "findings": [], "ip": "192.168.1.1"}', "LITERAL_IP"),
    ('{"agent": "test", "status": "pass", "findings": [], "ftp": "ftp://fileserver.com"}', "FTP_PROTOCOL"),
    ('{"agent": "test", "status": "pass", "findings": [], "ssh": "ssh://root@10.0.0.1"}', "SSH_PROTOCOL"),
    ('{"agent": "test", "status": "pass", "findings": [], "safe": "http://localhost:11434"}', "SAFE_LOCAL"),
]

failures = 0
for payload, name in test_payloads:
    result = validate_output(payload)
    is_blocked = result["status"] == "invalid" and "AIRGAP" in result.get("reason", "")
    
    if name == "SAFE_LOCAL":
        if not is_blocked:
            print(f"PASS: {name} allowed as expected.")
        else:
            print(f"FAIL: {name} was blocked but should be allowed!")
            failures += 1
    else:
        if is_blocked:
            print(f"PASS: {name} blocked successfully.")
        else:
            print(f"FAIL: {name} bypassed the Air-Gap filter!")
            failures += 1

if failures == 0:
    print("\nListed output-text filter cases passed; this is not network isolation.")
else:
    print(f"\nAIR-GAP BREACH: {failures} test cases failed!")
    exit(1)
