# 2. RUNTIME_STATE_MACHINE.md
Version: 1.0
Status: ENFORCED

States: INIT -> VALIDATING -> EXECUTING -> AUDITING -> PATCH_PROPOSED -> DRY_RUN -> REVIEW -> APPROVED -> APPLIED -> COMPLETE.

Recovery: LOCKDOWN, FORENSIC, RECOVERY.
Illegal transitions halt execution and trigger supervisor notification.
