# 4. FORENSIC_LOG_SPEC.md
Version: 1.0
Status: ENFORCED
Required Fields: event_id, runtime_id, session_id, timestamp, event_type, severity, artifact_hash.
Logs MUST be: append-only, immutable, hash-verifiable.

# 5. PATCH_TRUST_MODEL.md
Version: 1.0
Status: ENFORCED
Patch flow: proposal -> validation -> dry-run -> re-audit -> supervisor approval -> controlled apply.
No patch may be applied without deterministic validation and supervisor approval.

# 6. SANDBOX_POLICY.md
Version: 1.0
Status: ENFORCED
Immutable Zones: /immutable/, /canon/, /contracts/, /governance/, /keys/.
No runtime component may escape sandbox boundaries.
