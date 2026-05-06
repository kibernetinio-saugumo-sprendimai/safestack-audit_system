# 11. VALIDATION_PIPELINE_SPEC.md
Layers: raw_output -> transport -> schema -> protocol -> evidence -> integrity -> determinism -> supervisor review.

# 12. SUPERVISOR_PROTOCOL.md
Supervisor governance is the final authority layer. Supervisor MAY: approve, reject, freeze, revoke trust, trigger lockdown.

# 13. REPORT_SPEC.md
Canonical structure: report_id, runtime_id, timestamp, findings, evidence_chain, artifact_hash, signature.

# 14. TRANSPORT_PROTOCOL.md
Stdout purity, UTF-8, deterministic framing. Forbidden: mixed stdout/stderr, markdown leakage.

# 15. EXECUTION_POLICY.md
Limits: timeout, memory, retry, recursion, payload size. Execution safety has priority over runtime persistence.
