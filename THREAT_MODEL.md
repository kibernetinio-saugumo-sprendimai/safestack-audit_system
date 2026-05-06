# SAFESTACK AUDIT RUNTIME THREAT MODEL

Version: 1.0
Mode: LOCKDOWN

---

# Purpose
Defines threats against the SafeStack audit runtime, agent pipeline, validation flow, patching process, and final report integrity. Primary assumption: All agent output is untrusted.

---

# Protected Assets
Source code, audit reports, raw agent output, validated findings, patch files, global policies, schemas, contracts, supervisor decisions, runtime state, logs, chain of trust.

---

# Trust Boundaries
- Untrusted: LLM agents, raw output, proposed fixes, generated patches, reviewer text.
- Semi-trusted: runtime controller, agent adapter, report writer.
- Trusted: strict_mode.py, schema validation, fixer_guard.py, patch_apply.py (dry-run), CHIEF_SUPERVISOR decision layer.
- Canonical: GLOBAL_POLICY.md, PRIORITY_MODEL.md.

---

# Threat Categories

## T1 — Prose Injection
Agent outputs human text instead of protocol. 
Response: BLOCK.

## T2 — Markdown Leakage
Agent outputs markdown, code fences, headings, or bullets.
Response: BLOCK.

## T3 — Schema Poisoning
Agent outputs JSON-like data that violates schema (missing keys, invalid severity, etc.).
Response: BLOCK.

## T4 — Hallucinated Evidence
Agent reports evidence that does not exist in source.
Response: BLOCK or REJECT FINDING.

## T5 — Reviewer Override Attack
Reviewer claims PASS despite invalid output.
Response: BLOCK. Rule: Reviewer cannot override strict_mode, schema, or supervisor.

## T6 — FIXER Escalation
FIXER generates prose, full rewrites, unsafe patches, or unrelated changes.
Response: BLOCK.

## T7 — Raw Output Bypass
Raw agent output enters final report without validation.
Response: BLOCK PIPELINE.

## T8 — Contract Bypass
Agent ignores its contract (e.g., SECURITY writes architecture review).
Response: BLOCK.

## T9 — Role Confusion
Agent performs another agent’s function.
Response: BLOCK or REJECT.

## T10 — Unicode / Obfuscation Attack
Agent hides forbidden content using homoglyphs, encoded markdown, or whitespace tricks.
Response: BLOCK.

## T11 — Report Poisoning
Invalid data is written into final report.
Response: BLOCK REPORT GENERATION.

## T12 — Patch Poisoning
Patch appears valid but changes unrelated logic or unsafe files.
Response: REJECT PATCH.

## T13 — Policy Mutation
Agent attempts to modify GLOBAL_POLICY.md, PRIORITY_MODEL.md, strict_mode.py, or contracts.
Response: BLOCK.

## T14 — Silent Failure
Pipeline continues after validation failure.
Response: TERMINATE.

---

# Mandatory Defensive Controls
Required: raw capture, strict mode, schema validation, logic consistency check, supervisor decision, fixer guard, patch dry-run, immutable policies, traceable reports.
