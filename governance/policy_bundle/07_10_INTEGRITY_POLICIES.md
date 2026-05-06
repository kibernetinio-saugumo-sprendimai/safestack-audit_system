# 7. HASH_CHAIN_SPEC.md
Version: 1.0
Status: ENFORCED
Artifact hash-chain integrity enforcement. Hash mismatch MUST halt execution and trigger lockdown.

# 8. REPRODUCIBILITY_POLICY.md
Version: 1.0
Status: ENFORCED
Identical inputs MUST produce identical outputs. No hidden state persistence.

# 9. FAILSAFE_LOCKDOWN_PROTOCOL.md
Version: 1.0
Status: ENFORCED
Runtime MUST enter LOCKDOWN if corruption or inconsistency is detected. Safety has priority over availability.

# 10. CANONICAL_SERIALIZATION_SPEC.md
Version: 1.0
Status: ENFORCED
Logically identical data MUST produce identical hashes. Enforce stable key ordering and normalized whitespace.
