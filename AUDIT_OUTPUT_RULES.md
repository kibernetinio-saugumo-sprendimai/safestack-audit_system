# AUDIT_OUTPUT_RULES.md

1. The agent may greet only professionally and briefly (maximum one sentence).
2. Conversational text may not exceed 15% of the total response.
3. The agent must not apologize.
4. The agent must not create content that is not present in the file.
4. Every finding must include:
   - file
   - line or snippet
   - severity
   - issue
   - evidence
   - recommendation
5. If there is no evidence, the finding is prohibited.
6. QA must not write PASSED while any critical/high finding remains unresolved.
7. FIXER returns only a unified diff or a complete file.
