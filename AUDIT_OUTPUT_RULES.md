# AUDIT_OUTPUT_RULES.md

1. Agentas gali pasisveikinti tik profesionaliai ir trumpai (maks. 1 sakinys).
2. Pokalbinis tekstas negali sudaryti daugiau nei 15% viso atsakymo.
3. Agentas negali atsiprašinėti.
3. Agentas negali kurti turinio, kurio nėra faile.
4. Kiekvienas finding turi turėti:
   - file
   - line arba snippet
   - severity
   - issue
   - evidence
   - recommendation
5. Jei įrodymo nėra → finding draudžiamas.
6. QA negali rašyti PASSED, jei bent vienas critical/high finding neišspręstas.
7. FIXER grąžina tik unified diff arba pilną failą.
