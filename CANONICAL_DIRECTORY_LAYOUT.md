# SAFESTACK CANONICAL DIRECTORY LAYOUT

Version: 1.0
Mode: LOCKDOWN

---

# Purpose
Defines the mandatory directory structure for the SafeStack audit system. Any deviation from this layout results in an INTERNAL_ERROR (Code 3).

---

# Mandatory Layout

audit_system/
├── GLOBAL_POLICY.md        # The Supreme Law
├── PRIORITY_MODEL.md       # Hierarchy
├── THREAT_MODEL.md         # Risks
├── STATE_MODEL.md          # Flow
├── EXIT_CODE_POLICY.md     # Communication
├── CHAIN_OF_TRUST.md       # Validation
├── IMMUTABILITY_POLICY.md   # Mutation Guard
├── FORENSICS_POLICY.md      # Traceability
├── CANONICAL_DIRECTORY_LAYOUT.md # This file
│
├── agent_contracts/        # Mandatory .contract.md files
├── agents/                 # Legacy/Instruction files (Read-only)
├── rules/                  # JSON Schemas
│
├── pipeline_controller.py  # Orchestration Core
├── agent_runtime.py        # Enforcement Jailer
├── strict_mode.py          # Policy Gate
├── fixer_guard.py          # Patch Guard
├── patch_apply.py          # Execution Tool
├── single_agent_adapter.py # Execution Bridge
│
├── reports/                # Final validated reports
├── runtime/                # Forensic trail
│   ├── raw/                # Untrusted raw captures
│   ├── valid/              # Enforced valid JSON
│   └── invalid/            # Enforced breach records
│
└── fixes/                  # Generated .patch files (Staging area)

---

# Enforcement Rule
The `pipeline_controller` MUST verify the existence of this directory structure during the `INIT` state.
