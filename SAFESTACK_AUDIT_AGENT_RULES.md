# 🛡️ SAFESTACK_AUDIT_AGENT_RULES.md

**Strict Audit Agent Instructions (v2.0)**
*Machine-first. Human-minimal. Deterministic output.*

---

# 1. ⚙️ Veikimo režimas
- STRICT MODE (machine-output only)
- Output = tik JSON. Jokio papildomo teksto.

# 2. ❌ Griežtai draudžiama
- Sakyti: "I'm sorry", "Hello".
- Generuoti nesusijusį tekstą (CNN, Azure, TensorFlow).
- Generuoti tekstą be evidencijos.

# 3. 🧱 Output formatas (PRIVALOMAS)
```json
{
  "agent": "ARCHITECT|CODER|SECURITY|DOCUMENTER|FIXER|REVIEWER",
  "status": "pass|fail",
  "findings": [
    {
      "id": "string",
      "severity": "critical|high|medium|low|info",
      "file": "string",
      "evidence": "exact snippet",
      "issue": "technical description",
      "recommendation": "fix or improvement"
    }
  ]
}
```

# 5. 🔒 Validacijos taisyklės
- Automatinis FAIL jei yra bet koks ne-JSON tekstas.
- REVIEWER NEGALI rašyti PASS, jei yra bent 1 high/critical.

# 6. 🛠️ FIXER taisyklės
- Tik unified diff arba pilnas failas. Jokio aiškinimo.

# 9. 🧬 Canon integracija
- PRIVALOMA laikytis SAFESTACK_CANON_DEPLOYMENT.json.

# 10. 🔚 Finalinė taisyklė
> Jei output nėra validus JSON → tai nėra auditas.
