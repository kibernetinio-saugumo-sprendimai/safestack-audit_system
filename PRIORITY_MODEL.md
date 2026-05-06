# SAFESTACK PRIORITY MODEL

Version: 1.0
Mode: LOCKDOWN

---

# Purpose
Defines mandatory authority and execution priorities across the SafeStack control plane. If conflict occurs, higher priority always overrides lower priority. No exception.

---

# Priority Hierarchy
1. GLOBAL POLICY (Absolute)
2. STRICT MODE (Hard Enforcement)
3. SCHEMA VALIDATION (Structural)
4. CHIEF_SUPERVISOR (Final Decision)
5. RUNTIME CONTROLLER (Execution)
6. REVIEWER (Compliance Review)
7. FIXER (Patch Generation)
8. SECURITY (Security Findings)
9. ARCHITECT (Architecture Findings)
10. CODER (Code Quality Findings)
11. DOCUMENTER (Lowest Authority)

---

# Enforcement Priority
GLOBAL POLICY -> STRICT MODE -> SCHEMA VALIDATION -> SUPERVISOR -> RUNTIME -> AGENTS. Never inverse.

---

# Conflict Resolution Rules
If conflict occurs: Higher priority wins automatically.
STRICT MODE vs REVIEWER -> STRICT MODE wins.
SUPERVISOR vs FIXER -> SUPERVISOR wins.
GLOBAL POLICY vs ANYTHING -> GLOBAL POLICY wins.

---

# Trust Rules
Trusted: strict_mode, schema validation, supervisor decisions.
Semi-trusted: runtime controller.
Untrusted: all LLM agents.

---

# Pipeline Termination Rules
Immediate termination if: strict_mode fail, schema fail, invalid patch, prose leakage, raw output bypass, malformed findings, unknown agent, hallucinated evidence.

---

# Determinism Rule
Higher priority layers MUST be deterministic. Forbidden: personality, creativity, conversational logic, motivational text.

---

# Canonical Rule
Authority is determined by validation level, not by agent confidence.
