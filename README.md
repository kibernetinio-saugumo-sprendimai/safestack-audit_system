# 🛡️ SafeStack: Sovereign Governance Kernel

**Version: v2.0.0 security-hardening candidate**

SafeStack is a deterministic, zero-trust security auditing framework designed for autonomous infrastructure. It enforces a strict **Verification Era** protocol where every action is cryptographically linked, audited, and reproducible.

## 💎 Core Doctrine
1. **Determinism**: Identical inputs ALWAYS yield identical cryptographic hashes. No environmental drift.
2. **Zero-Trust Runtime**: Agents are contained within a strict protocol. No magic, no unverified memory.
3. **Network isolation prerequisite**: Execution fails closed unless the Linux runtime has no non-loopback default route. Output URL filtering is only an additional policy check.
4. **Protected write paths**: Application-level guards block writes to governance files. OS-level permissions or immutable mounts remain deployment responsibilities.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Ollama (running `llama3` model)
- LangGraph

### Installation
```bash
git clone <your-repo-url>
cd my-langgraph-app
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Running an Audit
```bash
python server.py
# In a separate terminal or via the graph:
audit <project_path>
```

## 🔒 Verification & Compliance
This repository contains a candidate baseline. A release is eligible for approval only after the test suite, isolated-runtime checks and an independent cryptographic signature pass.

- **Governance Stack Hash**: generated and verified by CI; see `GOLDEN_HASH_REGISTRY.json`
- **Baseline Discoverer**: `e4af70e71d50e0e0a20a2507cae815ad650fddd44e33d47bcbcc0be360b9ac75`

## 📜 Doctrine
*No hash or model verdict makes an artifact authoritative by itself. Authority requires an independently controlled signing key and release approval.*

---
**Status: CANDIDATE | License: Sovereign SafeStack Protocol**
