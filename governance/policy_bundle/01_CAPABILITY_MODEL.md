# 1. CAPABILITY_MODEL.md
Version: 1.0
Status: ENFORCED
Mode: ZERO TRUST

Default policy: DENY ALL.

Capabilities must be explicitly granted.
Filesystem write access: restricted to /sandbox/ and /runtime/quarantine/.
Network access: false.
Subprocess execution: false.
Protected zones (IMMUTABLE): /governance/, /canon/, /keys/.
