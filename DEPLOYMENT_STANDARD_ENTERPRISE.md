# 📘 DEPLOYMENT_STANDARD_ENTERPRISE.md

**Deployment Governance Standard (v1.0)**
Aligned with principles of ISO/IEC 27001, NIST, and secure engineering practices

---

# 1. Scope
Taikoma visiems deployment procesams infrastruktūrai, aplikacijoms, tinklo komponentams.

# 2. Objectives
- Integrity (Vientisumas)
- Availability (Prieinamumas)
- Confidentiality (Konfidencialumas)
- Accountability (Audituojamumas)

# 3. Roles & Responsibilities
- Deployment Engineer: vykdo diegimą
- Security Officer: vertina saugumą
- System Owner: tvirtina pakeitimus
- Auditor: tikrina atitiktį

# 4. Pre-Deployment Controls
Privaloma: change request, priklausomybių patikra, konfigūracijos validacija, rizikos vertinimas.

# 5. Deployment Controls
- Execution by authorized persons only.
- All actions MUST be logged.
- Configuration versioned, no manual production changes.

# 6. Security Requirements
- Least Privilege, Secure defaults, Network segmentation, Encryption.

# 7. Logging & Monitoring
- Centralized logs, Real-time monitoring, Alerting.

# 8. Incident Handling
- Identification, Isolation, Analysis, Recovery, Documentation.

# 11. Rollback Strategy
- Backup, Rollback plan, Recovery procedures required.

# 13. Definition of Done
- Controls met, stable system, no critical incidents.
