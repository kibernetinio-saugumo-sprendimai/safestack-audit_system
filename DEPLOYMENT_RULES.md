# 📐 DEPLOYMENT_RULES.md

**Universal Deployment Rules (v1.0)**
*General-purpose standard for secure, controlled system deployment*

---

# 0. 🎯 Tikslas
Apibrėžti bendras taisykles, kurios taikomos bet kokiai sistemai:
Tikslas – užtikrinti: stabilumą, saugumą, pakartojamumą, kontrolę.

# 1. 🧠 Pagrindiniai principai
## 1.1 Minimalizmas
- Diegti tik tai, kas būtina. Kiekvienas komponentas turi turėti aiškią funkciją.
## 1.2 Pakartojamumas (Repeatability)
- Deployment turi būti atkuriamas 1:1. Jokio rankinio „spėjimo“.
## 1.3 Determinizmas
- Tas pats procesas → tas pats rezultatas. Vengti “random behavior”.
## 1.4 Skaidrumas
- Visi veiksmai turi būti matomi, loginami, suprantami.
## 1.5 Kontrolė
- Nėra „black box“ sprendimų. Kiekvienas žingsnis turi būti paaiškinamas.

# 2. 🧱 Deployment struktūra
## 2.1 Paruošimas (Preparation)
- Patikrinti aplinką, priklausomybes, prieigas, resursus (CPU, RAM, disk).
## 2.2 Diegimas (Installation)
- Visi komponentai diegiami iš patikimų šaltinių su versijų kontrole.
## 2.3 Konfigūracija (Configuration)
- Aiškiai apibrėžta, atskirta nuo kodo, versijuojama.
## 2.4 Verifikacija (Verification)
- Po kiekvieno žingsnio: VERIFY → APPLY → VERIFY.
## 2.5 Paleidimas (Execution)
- Sistema paleidžiama tik po pilnos verifikacijos.

# 3. 🔒 Saugumo taisyklės
## 3.1 Least Privilege
- Vartotojai ir procesai turi tik būtinas teises.
## 3.2 Input kontrolė
- Visi input’ai validuojami. Jokio nepatikrinto duomenų naudojimo.
## 3.3 Autentifikacija
- Naudoti stiprius identifikacijos metodus.
## 3.4 Tinklo kontrolė
- Atidaryti tik būtini portai. Default: deny all.
## 3.5 Atnaujinimai
- Naudoti stabilias, palaikomas versijas. Vengti „latest“ be kontrolės.

# 4. 📜 Log’ai ir stebėjimas
## 4.1 Logging
- Visi svarbūs veiksmai loginami formatu: [TIME] ACTION → RESULT.
## 4.2 Monitoring
- Stebėti servisų būseną, resursus, klaidas.

# 5. ⚙️ Automatizacija
## 5.1 Scriptai
- Deployment turi būti automatizuotas. Rankiniai veiksmai minimalūs.
## 5.3 Idempotency
- Scriptas gali būti paleistas kelis kartus be žalos.

# 6. 🔄 Klaidos valdymas
## 6.1 Kritinės klaidos
- STOP execution. Neleisti dalinio deployment.

# 7. 🧪 Testavimas
## 7.1 Prieš deployment
- Testuoti izoliuotoje aplinkoje.
## 7.3 Edge case’ai
- Testuoti: network failure, disk full, service crash.

# 8. 📦 Dokumentacija
## 8.1 Privaloma turėti
- Kaip diegti, kaip konfigūruoti, kaip atstatyti.

# 9. 🧠 Finalinė taisyklė
- Jei deployment negali būti pakartotas identiškai → jis laikomas nepatikimu.
