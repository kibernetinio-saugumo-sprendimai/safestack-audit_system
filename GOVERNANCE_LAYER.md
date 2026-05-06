# 🏛️ GOVERNANCE_LAYER.md

**SafeStack System Governance Policy (v1.0)**
*The framework for agent accountability and integrity control*

---

# 1. Pagrindiniai principai

## 1.1 Integrity of Findings
Kiekvienas agento radinys (finding) yra laikomas negaliojančiu, jei jis negali būti 100% susietas su specifine taisykle iš **SAFESTACK_CANON_DEPLOYMENT.json** arba **skill.md**.

## 1.2 No Silent Decisions
Visi sprendimai (atmetimas, patvirtinimas, severity keitimas) privalo būti dokumentuoti agento JSON output'e. Draudžiama keisti kito agento duomenis be paaiškinimo.

## 1.3 Audit Trail
Visi agentų tarpusavio komunikacijos etapai yra saugomi ir gali būti peržiūrėti auditoriaus. Tai užtikrina **Accountability** (atsakomybę).

---

# 2. Sprendimų hierarchija (Conflict Resolution)

Jei taisyklės prieštarauja viena kitai:
1. **Governance Policy** (Šis dokumentas) > Visas technines taisykles.
2. **Standard Compliance** > Patogumą ar greitį.
3. **Safety** > Funkcionalumą.

---

# 3. Agentų etika ir ribos

- Agentas privalo pranešti apie trūkstamą informaciją (Insufficient Evidence), o ne spėlioti.
- Agentas privalo laikytis „Least Privilege“ principo net ir siūlydamas pataisymus.
- Agentas privalo užtikrinti, kad jo siūlomas pataisymas nesugriaus sistemos stabilumo (Idempotency).

---

# 4. Finalinis patvirtinimas

Joks kodas negali būti laikomas „Hardened“, kol jis nepraėjo viso **GOVERNANCE** ciklo:
`AUDIT -> SUPERVISE -> FIX -> VALIDATE -> REVIEW`.

---
