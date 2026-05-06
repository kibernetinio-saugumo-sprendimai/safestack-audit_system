# 🛡️ SafeStack Hardening Rules & Skills

## 1. Shell Scripting Standards (Bash)
- **Safety First:** Always use `set -euo pipefail`.
- **Logic:** Use `[[ ... ]]` instead of `[ ... ]` for tests.
- **Paths:** Always quote variables that contain paths or user input.
- **Checks:** Every script MUST check for root privileges (`EUID != 0`).

## 2. Security Protocols
- **Race Conditions:** Use `flock` or lockfiles for sensitive system operations.
- **Validation:** Sanitize all environment variables (like `TARGET_USER`).
- **Principle of Least Privilege:** Do not run commands as root if not necessary.

## 3. Storage Optimization (RPi 5)
- **ZRAM:** Prefer ZRAM over physical Swap to save SD card life.
- **fstrim:** Ensure fstrim is enabled for SSD longevity.

## 4. Documentation
- **Clear Output:** Use emojis for status checks (✅, ❌, 🔍, ⚠️).
- **Audit Trail:** Log timestamps for every major system change.
