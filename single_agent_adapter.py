#!/usr/bin/env python3
"""
single_agent_adapter.py
Bridge between a single agent contract and Ollama API.
Mandatory use of .contract.md files.
"""

import json
import requests
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 single_agent_adapter.py <AGENT_NAME> <TARGET_FILE>")
        sys.exit(2)

    agent_name = sys.argv[1].lower()
    target_path = Path(sys.argv[2])
    
    if not target_path.exists():
        sys.exit(2)

    code_content = target_path.read_text(encoding="utf-8", errors="ignore")
    
    # FIZINIS HIERARCHIJOS IR KONTRAKTO ĮKROVIMAS
    policy_path = Path("GLOBAL_POLICY.md")
    contract_path = Path(f"agent_contracts/{agent_name}.contract.md")
    
    if not policy_path.exists() or not contract_path.exists():
        print(f"CRITICAL: Policy or Contract missing for {agent_name}")
        sys.exit(1)
        
    global_policy = policy_path.read_text(encoding="utf-8")
    agent_contract = contract_path.read_text(encoding="utf-8")
    
    system_prompt = f"{global_policy}\n\n{agent_contract}"

    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"AUDIT THIS SOURCE CODE:\n\n{code_content}"}
        ],
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_ctx": 8192
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=180)
        # Tik raw output, kurį vėliau perims agent_runtime -> strict_mode
        print(response.json()['message']['content'].strip())
    except Exception as e:
        print(f"LLM_ADAPTER_ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
