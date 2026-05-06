# SAFESTACK SAFE RECOVERY POLICY

Version: 1.0
Mode: STABILIZATION

---

# Purpose
Defines safe recovery behavior after pipeline failure, blocking event, or protocol violation. Recovery must preserve integrity before restoring execution.

---

# Immediate Actions (On Trigger)
Upon any failure (BLOCKED, INTERNAL_ERROR, etc.):
1. Freeze runtime.
2. Stop all patch applications.
3. Preserve forensic evidence.
4. Store metadata & terminate execution.

---

# Forbidden Recovery Actions
Forbidden: silent restart, auto-continue after BLOCKED, deleting invalid evidence, bypassing supervisor, auto-applying rejected patch.

---

# Recovery States & Transitions
- BLOCKED -> FORENSIC_CAPTURE -> MANUAL_REVIEW -> REINITIALIZE -> RUNNING.
- FAILED -> REVIEW -> PATCH -> RE_AUDIT_REQUIRED.
- PATCH_REJECTED -> REVIEW -> FIXER_RETRY -> DRY_RUN.

---

# Manual Review Requirement
Required for: immutable policy violation, supervisor corruption, repeated schema failures, repeated invalid outputs, repeated patch rejection.

---

# Re-Audit Rule
Any applied patch requires RE_AUDIT_REQUIRED before a PASS state is allowed.

---

# Final Rule
Recovery without preserved evidence is forbidden.
