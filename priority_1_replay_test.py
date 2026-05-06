import requests
import json
import time
import hashlib

API_URL = "http://localhost:8000/ask"

def run_iteration(i):
    print(f"\n--- REPLAY ITERATION {i} ---")
    payload = {
        "task": "audit C:/Users/greit/.gemini/antigravity/scratch/test_project",
        "thread_id": f"replay_test_session_{i}" 
    }
    
    start_time = time.time()
    response = requests.post(API_URL, json=payload)
    duration = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        # Find Architect result (which we expect to be quarantined)
        architect_res = next((r for r in data["results"] if r["agent"] == "ARCHITECT"), None)
        
        if architect_res:
            print(f"Agent: {architect_res['agent']}")
            print(f"State: {architect_res['state']}")
            print(f"Hash:  {architect_res['integrity_hash']}")
            return architect_res['integrity_hash'], architect_res['content']
    else:
        print(f"Error: {response.status_code}")
    return None, None

def main():
    hashes = []
    contents = []
    
    for i in range(1, 4):
        h, c = run_iteration(i)
        if h:
            hashes.append(h)
            contents.append(c)
        time.sleep(2) # Stability pause

    print("\n=== REPLAY PROOF VERDICT ===")
    if len(set(hashes)) == 1:
        print(f"SUCCESS: All iterations produced identical Hash Chain: {hashes[0]}")
    else:
        print(f"FAILURE: Non-deterministic hashes detected!")
        for i, h in enumerate(hashes):
            print(f"Run {i+1}: {h}")

    if len(set(contents)) == 1:
        print("SUCCESS: All iterations produced identical quarantined content markers.")
    else:
        print("FAILURE: Quarantined markers differ!")

if __name__ == "__main__":
    main()
