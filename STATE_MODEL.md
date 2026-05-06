# SAFESTACK PIPELINE STATE MODEL

Version: 1.0
Mode: LOCKDOWN

---

# Purpose
Defines the official state machine for SafeStack audit runtime execution. All pipeline components must use these states consistently.

---

# State List
- INIT: Created but not started.
- RUNNING: Execution started.
- AGENT_EXECUTING: Agent command running.
- RAW_CAPTURED: Raw output stored in runtime/raw/.
- STRICT_VALIDATING: strict_mode.py evaluating.
- STRICT_VALID / STRICT_INVALID: Result of strict mode.
- SCHEMA_VALIDATING: JSON/Consistency check.
- SCHEMA_VALID / SCHEMA_INVALID: Result of schema check.
- PATCH_VALIDATING / PATCH_REJECTED: Result of fixer_guard.
- PATCH_DRY_RUN / PASS / FAIL: Result of patch -n.
- PATCH_READY / PATCH_APPLIED: Fix execution states.
- RE_AUDIT_REQUIRED: State after patch application.
- SUPERVISOR_REVIEW: Final evaluation stage.
- PASSED, FAILED, BLOCKED, INTERNAL_ERROR, TERMINATED: Terminal states.

---

# Forbidden Transitions
- RAW_CAPTURED -> REPORT
- AGENT_EXECUTING -> REPORT
- STRICT_INVALID -> SUPERVISOR_PASS
- SCHEMA_INVALID -> SUPERVISOR_PASS
- PATCH_REJECTED -> PATCH_APPLIED
- BLOCKED -> PASSED
- FAILED -> PASSED

---

# State Priority
1. INTERNAL_ERROR
2. BLOCKED
3. FAILED
4. PASSED

---

# Final Rule
A report is valid only if its state path passed through strict validation and supervisor review.
