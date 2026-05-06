#!/bin/bash
# SafeStack Autonomous Audit Pipeline v3
# Usage: ./run_pipeline.sh <target_file>

set -e

TARGET=$1

if [ -z "$TARGET" ]; then
    echo "Usage: ./run_pipeline.sh <target_file>"
    exit 2
fi

echo "[*] INITIATING STAGE 1: HARDENED AUDIT"
python3 audit_orchestrator_v3.py "$TARGET"
AUDIT_STATUS=$?

if [ $AUDIT_STATUS -ne 0 ]; then
    echo "[!] STAGE 1 FAILED: Audit findings or Protocol breach detected."
    echo "[*] Check reports/audit_report_v3.json for details."
    
    # STAGE 2: FIXING (Optional/Future)
    # echo "[*] INITIATING STAGE 2: CONTROLLED FIX"
    # if [ -f "generated_code/${TARGET}.patch" ]; then
    #     python3 fixer_guard.py "generated_code/${TARGET}.patch"
    #     python3 patch_apply.py --dry-run "generated_code/${TARGET}.patch"
    #     echo "[?] Apply patch? (y/n)"
    #     read confirm
    #     if [ "$confirm" == "y" ]; then
    #         python3 patch_apply.py --apply "generated_code/${TARGET}.patch"
    #         echo "[*] RE-AUDITING..."
    #         python3 audit_orchestrator_v3.py "$TARGET"
    #     fi
    # fi
    
    exit 1
fi

echo "[++] STAGE 1 SUCCESS: System is compliant and verified."
exit 0
