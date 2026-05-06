import os
from app import app

def test_lockdown_enforcement():
    print("=== SafeStack Lockdown Formalization Test ===")
    
    # Simulate a state that should trigger lockdown (e.g. invalid path)
    inputs = {
        "messages": [("user", "audit INVALID_PATH_THAT_DOES_NOT_EXIST")],
        "project_path": "INVALID",
        "project_context": "ERROR: PATH_NOT_FOUND" # This triggers lockdown in discoverer
    }
    
    config = {"configurable": {"thread_id": "lockdown_test_session"}}
    
    # Clean old forensics
    if os.path.exists("LOCKDOWN_FORENSICS.log"):
        os.remove("LOCKDOWN_FORENSICS.log")

    print("Executing audit with invalid input...")
    final_state = None
    for event in app.stream(inputs, config=config):
        for node, value in event.items():
            print(f"Node reached: {node}")
            final_state = value

    # Verification
    print("\n--- Verification ---")
    
    # 1. Check state
    if final_state.get("current_state") == "LOCKDOWN":
        print("PASS: System entered LOCKDOWN state.")
    else:
        print(f"FAIL: System in wrong state: {final_state.get('current_state')}")

    # 2. Check lifecycle
    if final_state.get("lifecycle_stage") == "HALTED":
        print("PASS: Lifecycle stage set to HALTED.")
    else:
        print("FAIL: Lifecycle stage not HALTED.")

    # 3. Check forensics
    if os.path.exists("LOCKDOWN_FORENSICS.log"):
        with open("LOCKDOWN_FORENSICS.log", "r") as f:
            log = f.read()
            if "LOCKDOWN TRIGGERED" in log:
                print("PASS: Forensic evidence preserved in LOCKDOWN_FORENSICS.log")
            else:
                print("FAIL: Forensics log is empty or incorrect.")
    else:
        print("FAIL: Forensic log not created.")

    if final_state.get("trust_level") == "UNTRUSTED":
        print("PASS: Trust level reset to UNTRUSTED.")
    else:
        print("FAIL: Trust level not reset.")

if __name__ == "__main__":
    test_lockdown_enforcement()
