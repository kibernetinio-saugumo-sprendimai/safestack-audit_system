import os
from app import app

def run_isolated_test():
    print(f"=== SafeStack ISO-CLEAN REBUILD TEST | CWD: {os.getcwd()} ===")
    config = {"configurable": {"thread_id": "final_proof_v1000"}}
    # Explicitly audit the test_project directory to avoid environment noise
    inputs = {"messages": [("user", "audit test_project")]}
    
    for event in app.stream(inputs, config=config):
        for node, value in event.items():
            chash = value.get("chain_hash")
            print(f"NODE: {node:15} | HASH: {chash}")

if __name__ == "__main__":
    run_isolated_test()
