# SAFESTACK FORENSICS POLICY

Version: 1.0
Mode: STABILIZATION

---

# Purpose
Defines evidence preservation requirements for all pipeline executions, failures, and protocol breaches. Every important execution event must be reconstructable.

---

# Mandatory Evidence Collection
Always preserve:
- raw outputs, invalid outputs, validated findings.
- supervisor decisions, patch metadata, runtime state.
- timestamps, exit codes, execution path.

---

# Required Directories
runtime/raw/
runtime/invalid/
runtime/valid/
reports/
logs/
forensics/

---

# Incident Triggers
Generate forensic record if: BLOCKED, INTERNAL_ERROR, PATCH_REJECTED, schema failure, strict_mode failure, enforcement bypass attempt, immutable mutation attempt.

---

# Required Metadata
Every forensic record must contain: timestamp, pipeline state, triggering agent, reason, affected files, exit code, runtime version.

---

# Forbidden Actions
Forbidden: deleting invalid outputs, overwriting raw evidence, mutating timestamps, silent log removal.

---

# Retention Policy
Minimum retention: 90 days for forensic logs, invalid outputs, and supervisor decisions.

---

# Final Rule
If evidence cannot be reconstructed, the audit is incomplete.
