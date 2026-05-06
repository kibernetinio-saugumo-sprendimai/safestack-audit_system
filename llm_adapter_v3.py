#!/usr/bin/env python3
"""
llm_adapter_v3.py
SafeStack High-Integrity LLM Executor.
"""

import json
import requests
import subprocess
import sys

def main():
    if len(sys.argv) < 3: sys.exit(7)
    agent = sys.argv[1]
    target = sys.argv[2]

    # 1. Suformuojame brutalų paketą
    adapter_res = subprocess.run(
        ["python", "agent_adapter_v3.py", agent, target],
        capture_output=True, text=True
    )
    payload_raw = json.loads(adapter_res.stdout)

    # 2. Siunčiame į Ollama (Ollama API naudoja 'num_predict' vietoje 'max_tokens')
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3",
        "prompt": payload_raw["prompt"],
        "system": payload_raw["system"],
        "stream": False,
        "options": {
            "temperature": 0.0,
            "top_p": 0.0,
            "num_predict": payload_raw["num_predict"],
            "stop": payload_raw["stop"]
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=180)
        raw_content = response.json()['response'].strip()
        
        # Tikriname per naująjį Firewall
        firewall_process = subprocess.Popen(
            ["python", "output_firewall_v2.py"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
        )
        fw_out, _ = firewall_process.communicate(input=raw_content)
        fw_res = json.loads(fw_out)

        if fw_res["status"] == "pass":
            print(raw_content)
        else:
            # Jei Firewall užblokavo, išvedame blokavimo priežastį kaip invalid JSON
            # Kad agent_runtime suprastų, jog tai yra pažeidimas
            print(f"FIREWALL_BLOCKED: {fw_res['reason']}")
            sys.exit(2)

    except Exception as e:
        print(f"LLM_CRITICAL_ERROR: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()
