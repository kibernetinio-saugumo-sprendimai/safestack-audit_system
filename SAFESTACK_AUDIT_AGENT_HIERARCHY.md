# 🧭 SAFESTACK_AUDIT_AGENT_HIERARCHY.md

**Agentų rolės, subordinacija ir pagrindinis prižiūrėtojas**
**Version:** 1.0

# 1. Pagrindinė taisyklė
> Kodas yra aukščiau už agento nuomonę.
> Evidencija yra aukščiau už interpretaciją.
> Prižiūrėtojas yra aukščiau už visus agentus.

# 2. Subordinacijos modelis
USER -> CHIEF SUPERVISOR -> REVIEWER -> (ARCHITECT, CODER, SECURITY, DOCUMENTER) -> FIXER -> VALIDATOR

# 3. CHIEF SUPERVISOR
- Kontroliuoja agentų darbą. Tikrina, ar visi laikosi taisyklių.
- Gali: atmesti radinį, reikalauti per-audito, sustabdyti FIXER jei nėra evidencijos.

# 4.7 VALIDATOR
- Tikrina: ar JSON validus, ar nėra draudžiamų frazių, ar schema atitinka canon.

# 7. Sprendimų kelias
1. DISCOVERY -> 2. ARCHITECT -> 3. CODER -> 4. SECURITY -> 5. DOCUMENTER -> 6. CHIEF SUPERVISOR -> 7. FIXER -> 8. VALIDATOR -> 9. REVIEWER -> 10. FINAL RESULT

# 10. Finalinė taisyklė
> Agentas yra tik instrumentas. Prižiūrėtojas valdo procesą. Kodas ir evidencija sprendžia tiesą.
