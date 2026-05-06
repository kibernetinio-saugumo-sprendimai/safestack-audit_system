# SAFESTACK CHAIN OF TRUST

Version: 1.0
Mode: LOCKDOWN

---

# Purpose
Defines how trust is created, limited, validated, and revoked inside the SafeStack audit runtime. Trust is granted only by validation, never by generation.

---

# Trust Levels
- Level 0 (Untrusted): LLM agent output. Allowed: capture only.
- Level 1 (Captured): Output stored in runtime/raw/. Trust: existence only.
- Level 2 (Strict Validated): Passed strict_mode.py. Trust: protocol compliance.
- Level 3 (Schema Validated): Passed JSON schema & consistency. Trust: structural validity.
- Level 4 (Evidence Accepted): Finding has valid source code evidence. Trust: may enter supervisor review.
- Level 5 (Supervisor Approved): Accepted by CHIEF_SUPERVISOR. Trust: may enter final report.
- Level 6 (Patch Guarded): Passed fixer_guard.py. Trust: may enter dry-run.
- Level 7 (Dry-Run Verified): Passed patch_apply.py --dry-run. Trust: manual apply eligible.
- Level 8 (Applied): Patch applied explicitly. Trust: modified file exists.
- Level 9 (Re-Audited): Post-patch audit complete. Trust: final operational confidence.

---

# Trust Flow
Required: agent output -> raw capture -> strict validation -> schema validation -> evidence check -> supervisor approval -> report.
Patch flow: fixer output -> raw capture -> strict patch validation -> fixer_guard -> dry-run -> explicit apply -> re-audit.

---

# Revocation Rules
Trust is revoked if: later validation fails, evidence is false, schema inconsistency found, patch modifies forbidden path, policy violation detected.

---

# Agent Trust Rule
Agents are never trusted. They only generate candidate output.

---

# Final Rule
If trust cannot be traced, trust does not exist.
