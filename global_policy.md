# SAFESTACK GLOBAL POLICY

Version: 1.0
Mode: LOCKDOWN
Authority: CHIEF_SUPERVISOR

---

# Purpose
This document defines mandatory global rules for all agents, orchestrators, validators, reviewers, patch engines, runtime controllers, and enforcement layers. No component may override this policy.

---

# Core Philosophy
All AI output is UNTRUSTED until validated. Validation is mandatory. No AI component has authority by default. Authority exists only through strict validation, schema compliance, enforcement approval, and supervisor acceptance.

---

# Primary Security Principle
FAIL CLOSED. If uncertainty exists: BLOCK. If validation fails: BLOCK. If schema fails: BLOCK. If prose appears in strict mode: BLOCK.

---

# Mandatory Execution Flow
Required pipeline: agent -> runtime -> raw capture -> strict_mode -> schema validation -> valid/invalid state -> supervisor -> final report.
Forbidden pipeline: agent -> final report.

---

# Trust Model
LLM agents are generators only. They are NOT authorities, validators, reviewers, or policy engines. Enforcement layers are authoritative.

---

# Single Entry Point Rule
All agents MUST execute only through: agent_runtime.py. Direct agent execution is forbidden.

---

# Strict Mode Rule
All agent output MUST pass strict_mode.py. No bypass allowed.

---

# Output Rules
Allowed: strict JSON, unified diff (FIXER only).
Forbidden: prose, markdown, greetings, explanations, roleplay, summaries, hallucinated technologies, unsupported claims.

---

# JSON Rule
All JSON agents MUST follow schema exactly. 
Forbidden: missing keys, invalid severity, empty evidence, malformed findings, pass with findings, fail without findings.

---

# FIXER Rule
FIXER may output ONLY: unified diff patch. 
Forbidden: markdown, prose, rewrite explanations, full file rewrites, unrelated changes.

---

# REVIEWER Rule
REVIEWER cannot override: strict_mode, schema validation, firewall, supervisor. If invalid output exists: REVIEWER MUST FAIL.

---

# Supervisor Authority
CHIEF_SUPERVISOR is final authority. Only supervisor may: approve, fail, block pipeline. No other component has override rights.

---

# Blocking Conditions
Pipeline MUST terminate if: invalid JSON, forbidden prose, markdown leakage, invalid patch, schema violation, enforcement bypass, raw output bypass, unknown agent, malformed findings.

---

# Raw Output Policy
All raw outputs MUST be stored in: runtime/raw/. No raw output may directly enter reports.

---

# Logic Consistency Rules
Forbidden: status=pass with findings, status=fail with empty findings, missing evidence, hallucinated evidence.

---

# Hallucination Policy
Hallucinated files, commands, technologies, vulnerabilities, dependencies, architectures are critical violations.

---

# Patch Safety Policy
Forbidden targets: /etc/passwd, /etc/shadow, /boot/, /root/, secrets, private keys.
Forbidden behaviors: chmod 777, curl | bash, eval, unsafe rm -rf, unquoted variables, unsafe temp files.

---

# Determinism Policy
All agents must behave deterministically. No personality, personality, conversational tone, motivational language, scoring language, or emotional language.

---

# Isolation Policy
Agents cannot: call each other directly, override findings, edit runtime state, bypass orchestrator.

---

# Auditability Policy
Every decision must be traceable. Required: evidence, source file, validation state, timestamp.

---

# Canonical Rule
If output is not validated, it does not exist.
