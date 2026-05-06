#!/usr/bin/env python3
"""
output_firewall_v2.py

SafeStack High-Integrity Output Firewall.

Purpose:
- immediate rejection of human prose
- immediate rejection of roleplay identities
- immediate rejection of markdown formatting
- zero-tolerance policy
"""

import json
import sys

# Mirtinas sąrašas (Terminal list)
FORBIDDEN_PATTERNS = [
    "hello", "i'm", "i am", "as an ai", "senior", "engineer", "architect",
    "review", "analysis", "recommendation", "here is", "here's", "analysis of",
    "thank you", "sorry", "apologize", "understand", "please", "let's",
    "congratulations", "well done", "good work", "enterprise", "hardened",
    "```", "##", "###", "**", " - ", "   - "
]

def check_raw_output(raw: str) -> dict:
    lower = raw.lower().strip()
    
    if not lower:
        return {"status": "blocked", "reason": "Empty output"}
        
    # Patikra dėl uždraustų frazių
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in lower:
            return {
                "status": "blocked", 
                "reason": f"PROSE_INJECTION_DETECTED: Forbidden pattern '{pattern}'"
            }
            
    # Patikra dėl JSON/Diff pradžios
    if not (raw.startswith("{") or raw.startswith("--- a/")):
        return {
            "status": "blocked", 
            "reason": "PROTOCOL_VIOLATION: Output must start with '{' or '--- a/'"
        }
        
    return {"status": "pass"}

def main():
    if len(sys.argv) < 2:
        sys.exit(7)
        
    raw_input = sys.stdin.read()
    result = check_raw_output(raw_input)
    
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "pass" else 2)

if __name__ == "__main__":
    main()
