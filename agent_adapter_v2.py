#!/usr/bin/env python3
"""
agent_adapter_v2.py

Deterministic SafeStack agent adapter.

Purpose:
- load agent contract
- inject strict execution rules
- enforce deterministic generation settings
- produce JSON-only output
"""

import json
import sys
from pathlib import Path


CONTRACTS_DIR = Path("agent_contracts")

VALID_AGENTS = {
    "ARCHITECT",
    "CODER",
    "SECURITY",
    "DOCUMENTER",
    "FIXER",
    "REVIEWER",
}


class AdapterError(Exception):
    pass


def load_contract(agent: str) -> str:
    path = CONTRACTS_DIR / f"{agent.lower()}.contract.md"

    if not path.exists():
        raise AdapterError(f"Missing contract: {path}")

    return path.read_text(encoding="utf-8", errors="ignore")


def build_system_prompt(agent: str, contract: str) -> str:
    return f"""
SYSTEM MODE: STRICT LOCKDOWN

You must obey the contract exactly.

Violation results in termination.

CONTRACT:
{contract}

STRICT RULES:
- output only allowed format
- no prose
- no markdown
- no explanations
- no roleplay
- deterministic mode
- exact schema only
"""


def build_payload(agent: str, source: str) -> dict:
    contract = load_contract(agent)

    return {
        "agent": agent,
        "mode": "deterministic",
        "temperature": 0.0,
        "top_p": 0.0,
        "max_tokens": 4096,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "stop": [
            "```",
            "Hello",
            "I'm",
            "Analysis",
            "Recommendations",
        ],
        "system_prompt": build_system_prompt(agent, contract),
        "input": source,
    }


def main() -> None:
    if len(sys.argv) != 3:
        print(json.dumps({
            "status": "error",
            "reason": "Usage: python3 agent_adapter_v2.py <AGENT> <target_file>"
        }))
        sys.exit(7)

    agent = sys.argv[1].upper()
    target_file = Path(sys.argv[2])

    if agent not in VALID_AGENTS:
        print(json.dumps({
            "status": "error",
            "reason": "Invalid agent"
        }))
        sys.exit(7)

    if not target_file.exists():
        print(json.dumps({
            "status": "error",
            "reason": "Missing target file"
        }))
        sys.exit(8)

    source = target_file.read_text(encoding="utf-8", errors="ignore")

    payload = build_payload(agent, source)

    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
