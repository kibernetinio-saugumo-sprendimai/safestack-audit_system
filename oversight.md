# 🧐 Agent Oversight & Quality Control (Reviewer Guide)

## Review Criteria:
1. **Safety:** Did the FIXER include `set -euo pipefail`?
2. **Standardization:** Are `[[ ... ]]` used correctly as per skill.md?
3. **Logic Integrity:** Does the fixed code still perform the original intended task? 
4. **No Hallucinations:** Did the FIXER add any unnecessary or fake commands?
5. **Cleanliness:** Is the output only the code, without chatty explanations?

## Approval Process:
- If the code meets ALL criteria, output: `PASSED: The code is hardened and safe.`
- If there are issues, output: `FAILED: [List issues]`.
