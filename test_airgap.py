from strict_mode import validate_output

payload = '{"agent": "test", "status": "pass", "findings": [], "leak": "http://google.com"}'
result = validate_output(payload)
print(f"Result: {result}")

if result["reason"] == "AIRGAP_VIOLATION: External URL detected":
    print("SUCCESS: The listed external URL text was rejected.")
else:
    print("FAILURE: Air-Gap violation bypassed!")
