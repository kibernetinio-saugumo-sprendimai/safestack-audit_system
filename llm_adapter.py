#!/usr/bin/env python3
"""
llm_adapter.py
Connects one specific agent to Ollama.
Executed by agent_runtime.py.
"""

import json
import requests
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 llm_adapter.py <AGENT_NAME> <TARGET_FILE>")
        sys.exit(2)

    agent_name = sys.argv[1]
    target_path = Path(sys.argv[2])
    
    if not target_path.exists():
        print(f"Target file {target_path} not found.")
        sys.exit(2)

    code_content = target_path.read_text(encoding="utf-8", errors="ignore")
    
    # Load agent prompt
    instruction_path = Path(f"agents/{agent_name.lower()}.md")
    system_prompt = instruction_path.read_text(encoding="utf-8") if instruction_path.exists() else "Output JSON only."

    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": system_prompt + "\nSTRICT: OUTPUT JSON ONLY. NO PROSE."},
            {"role": "user", "content": f"AUDIT THIS CODE:\n{code_content}"}
        ],
        "stream": False,
        "options": {"temperature": 0.0}
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        print(response.json()['message']['content'].strip())
    except Exception as e:
        print(f"LLM_ADAPTER_ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
