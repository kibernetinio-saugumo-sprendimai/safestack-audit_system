# SAFESTACK ENFORCEMENT MATRIX

Version: 1.0
Mode: STABILIZATION

---

# Purpose
Defines which components can enforce, block, validate, or terminate other components.

---

# Enforcement Hierarchy
1. GLOBAL POLICY (Highest)
2. STRICT MODE
3. SCHEMA VALIDATION
4. CHIEF_SUPERVISOR
5. RUNTIME CONTROLLER
6. REVIEWER
7. AGENTS (Lowest)

---

# Enforcement Table
| Component | Can Validate | Can Block | Can Override |
|---|---|---|---|
| GLOBAL_POLICY | ALL | ALL | NONE |
| strict_mode | ALL AGENTS | ALL AGENTS | NONE |
| schema validation | JSON AGENTS | JSON AGENTS | NONE |
| CHIEF_SUPERVISOR | VALID OUTPUTS | PIPELINE | NONE |
| runtime controller | EXECUTION FLOW | EXECUTION FLOW | NONE |
| REVIEWER | CONTRACT COMPLIANCE | INVALID OUTPUTS | NONE |
| AGENTS | NONE | NONE | NONE |

---

# Hard Rules

## strict_mode
Can: terminate pipeline, reject output, reject prose, reject markdown, reject malformed patches. Cannot be overridden.

## schema validation
Can: reject malformed JSON, reject invalid findings, reject logic inconsistency. Cannot approve prose.

## CHIEF_SUPERVISOR
Can: PASS, FAIL, BLOCK. Cannot override: strict_mode, schema validation, immutable policy.

## REVIEWER
Can: detect and report violations. Cannot: approve invalid output, override strict_mode, or override supervisor.

---

# Final Rule
Authority exists only through enforced validation.
