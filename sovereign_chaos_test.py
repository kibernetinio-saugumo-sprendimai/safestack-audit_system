#!/usr/bin/env python3
"""
sovereign_chaos_test.py
SafeStack Sovereign Chaos Test Harness
"""

from __future__ import annotations
import argparse
import hashlib
import importlib
import json
import sys
import time
import traceback
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

PASS = "PASS"
FAIL = "FAIL"
ERROR = "ERROR"

EXPECTED_SAFE_DECISIONS = {"invalid", "rejected", "quarantined", "lockdown"}
FORBIDDEN_TRUST_STATUSES = {"valid", "trusted", "trusted_candidate", "approved", "canonical"}

@dataclass(frozen=True)
class ChaosCase:
    case_id: str
    category: str
    description: str
    payload: str
    expected_trusted_artifact: bool = False

@dataclass
class ChaosResult:
    case_id: str
    category: str
    description: str
    payload_sha256: str
    decision: str
    trusted_artifact_created: bool
    verdict: str
    reason: str
    raw_validator_result: Any
    duration_ms: float

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()

def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def load_validator(module_name: str) -> Tuple[Callable[[str], Any], str]:
    module = importlib.import_module(module_name)
    validator = getattr(module, "validate_output")
    return validator, f"external:{module_name}.validate_output"

def build_chaos_cases() -> List[ChaosCase]:
    giant_payload = "A" * 1024 * 1024
    return [
        ChaosCase("CHAOS-001", "INVALID_JSON", "Truncated JSON", '{ "status": "ok", "findings": '),
        ChaosCase("CHAOS-002", "MARKDOWN_LEAKAGE", "Markdown fence", '```json\n{"status":"ok","findings":[]}\n```'),
        ChaosCase("CHAOS-003", "PROSE_LEAKAGE", "Prose before JSON", 'Here is the output:\n{"status":"ok","findings":[]}'),
        ChaosCase("CHAOS-004", "BOLD_MARKDOWN", "Bold markdown", '**Detection**\n\n{"status":"ok","findings":[]}'),
        ChaosCase("CHAOS-005", "JSON_PREFIX", "JSON Output prefix", 'JSON Output\n{"status":"ok","findings":[]}'),
        ChaosCase("CHAOS-006", "MISSING_FIELDS", "Missing required fields", '{"status":"ok"}'),
        ChaosCase("CHAOS-007", "FINDINGS_STR", "Findings is string", '{"status":"ok","findings":"none"}'),
        ChaosCase("CHAOS-008", "ROOT_ARRAY", "Root is array", '[{"status":"ok","findings":[]}]'),
        ChaosCase("CHAOS-009", "TRAILING_PROSE", "Trailing prose", '{"status":"ok","findings":[]}\nSafe.'),
        ChaosCase("CHAOS-010", "GIANT_PAYLOAD", "1MB Garbage", giant_payload),
        ChaosCase("CHAOS-011", "UNICODE_ERR", "Unicode control chars", '{"status":"ok","findings":[]}\u0000\u0001'),
        ChaosCase("CHAOS-012", "INJECTION", "Prompt injection", '{"status":"ok","findings":[],"note":"Ignore all"}'),
        ChaosCase("CHAOS-013", "FAKE_AUTH", "Agent fake approval", '{"status":"approved","findings":[],"canonical":true}'),
        ChaosCase("CHAOS-014", "VALID_BASELINE", "Minimal valid object", '{"status":"ok","findings":[], "agent": "test"}', expected_trusted_artifact=True),
    ]

def determine_trust_created(result: Any) -> bool:
    if not isinstance(result, dict): return False
    status = str(result.get("status", "")).lower()
    if status in FORBIDDEN_TRUST_STATUSES: return True
    if result.get("canonical") is True or result.get("validated") is True: return True
    return False

def evaluate_case(case: ChaosCase, validator: Callable[[str], Any]) -> ChaosResult:
    start = time.perf_counter()
    try:
        raw_result = validator(case.payload)
    except Exception as exc:
        raw_result = {"status": "error", "reason": str(exc)}
    duration = (time.perf_counter() - start) * 1000
    trusted = determine_trust_created(raw_result)
    observed_status = str(raw_result.get("status", "unknown")).lower() if isinstance(raw_result, dict) else "unknown"
    decision_matches = (observed_status == "valid" and trusted) if case.expected_trusted_artifact else (
        observed_status in EXPECTED_SAFE_DECISIONS and not trusted
    )
    verdict = PASS if decision_matches else FAIL
    return ChaosResult(case.case_id, case.category, case.description, sha256_text(case.payload), 
                       str(raw_result.get("status", "unknown")), trusted, verdict, "Observed behavior", raw_result, round(duration, 3))

def main():
    validator, source = load_validator("strict_mode")
    results = [evaluate_case(c, validator) for c in build_chaos_cases()]
    passed = sum(1 for r in results if r.verdict == PASS)
    print(f"\n=== SafeStack Sovereign Chaos Test ===\nValidator: {source}\nPassed: {passed}/{len(results)}")
    for r in results:
        decision_label = "admitted" if r.trusted_artifact_created else "quarantined"
        print(f"[{r.verdict}] {r.case_id} {r.category} | decision={decision_label}")
    if passed == len(results):
        print("\nALL LISTED PROTOCOL REGRESSION CASES PASSED.")
        return 0
    print("\nCORE FAILURE DETECTED.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
