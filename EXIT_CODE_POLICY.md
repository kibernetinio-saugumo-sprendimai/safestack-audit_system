# SAFESTACK EXIT CODE POLICY

Version: 1.0
Mode: LOCKDOWN

---

# Purpose
Defines standard exit codes for all SafeStack audit runtime tools. All tools must use these codes consistently.

---

# Exit Code Table
| Code | Meaning |
|---:|---|
| 0 | PASS |
| 1 | FAIL |
| 2 | BLOCKED |
| 3 | INTERNAL_ERROR |
| 4 | VALIDATION_ERROR |
| 5 | PATCH_REJECTED |
| 6 | PATCH_DRY_RUN_FAILED |
| 7 | INVALID_USAGE |
| 8 | MISSING_FILE |
| 9 | POLICY_VIOLATION |

---

# Tool Mapping

## strict_mode.py
Allowed: 0 (PASS), 2 (BLOCKED), 4 (VALIDATION_ERROR), 7 (INVALID_USAGE), 8 (MISSING_FILE).

## agent_runtime.py
Allowed: 0 (PASS), 2 (BLOCKED), 3 (INTERNAL_ERROR), 7 (INVALID_USAGE).

## pipeline_controller.py
Allowed: 0 (PASS), 1 (FAIL), 2 (BLOCKED), 3 (INTERNAL_ERROR), 8 (MISSING_FILE).

## fixer_guard.py
Allowed: 0 (PASS), 5 (PATCH_REJECTED), 7 (INVALID_USAGE), 8 (MISSING_FILE).

## patch_apply.py
Allowed: 0 (PASS), 6 (PATCH_DRY_RUN_FAILED), 7 (INVALID_USAGE), 8 (MISSING_FILE).

---

# Definitions
- Code 0: All checks passed.
- Code 1: High/Critical findings or dry-run fail.
- Code 2: Protocol breach (prose, markdown, etc.).
- Code 3: Python crash or environment fail.
- Code 4: Schema/Logic inconsistency.
- Code 5: Guard reject (unsafe patch/forbidden path).
- Code 6: Technically valid patch but won't apply cleanly.
- Code 9: Violation of GLOBAL_POLICY or PRIORITY_MODEL.
