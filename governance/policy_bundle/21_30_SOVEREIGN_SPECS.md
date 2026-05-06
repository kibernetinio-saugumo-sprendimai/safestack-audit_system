# 21. RUNTIME_MEMORY_POLICY.md
Memory MUST be bounded, auditable, and deterministic. No hidden persistent memory.

# 22. AGENT_ISOLATION_SPEC.md
Zero trust between agents. No shared hidden state. Each agent is an untrusted execution domain.

# 23. CANON_INTEGRITY_SPEC.md
Canon artifacts remain immutable, signed, and hash-verified.

# 24. VALIDATOR_AUTHORITY_SPEC.md
Validators reduce uncertainty but do not create authority.

# 25. RUNTIME_RECOVERY_PROTOCOL.md
Recovery must preserve forensic evidence and verify trust chains.

# 26. CHAIN_OF_CUSTODY_SPEC.md
Uninterrupted forensic traceability: origin, timestamps, handlers, validation stages.

# 27. SESSION_INTEGRITY_SPEC.md
Unique session IDs, isolated execution, event ordering.

# 28. ARTIFACT_LIFECYCLE_SPEC.md
Stages: CREATED -> VALIDATED -> TRUSTED -> SIGNED -> ARCHIVED -> REVOKED -> QUARANTINED.

# 29. RUNTIME_OBSERVABILITY_SPEC.md
Full visibility: execution, transport, integrity, forensic logs.

# 30. GOVERNANCE_TERMINATION_PROTOCOL.md
Safe termination has priority over uncontrolled continuation.
