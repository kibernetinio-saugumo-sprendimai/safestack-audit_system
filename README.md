# 🛡️ SafeStack: Sovereign Governance Kernel

**Version: v2.0.0**

SafeStack is a model-assisted audit tool for Python and Bash projects on POSIX systems with directory-relative, no-follow filesystem operations. It reads source under a configured audit root, sends that source to a local Ollama service, and stores findings and proposed replacement files for human review. It does not apply or deploy proposed changes.

## 💎 Core Doctrine
1. The API requires an operator configured `SAFESTACK_API_KEY`.
2. The default listener is `127.0.0.1:8000`.
3. Reports include an unsigned integrity digest. This digest does not authenticate an author.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Ollama (running `llama3` model)
- LangGraph

### Installation
```bash
git clone https://github.com/kibernetinio-saugumo-sprendimai/safestack-audit_system.git
cd safestack-audit_system
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export SAFESTACK_API_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

### Running an Audit
```bash
# The path must be inside SAFESTACK_AUDIT_ROOT (defaults to the repository directory).
curl -H "X-API-Key: $SAFESTACK_API_KEY" -H 'Content-Type: application/json' \
  -d '{"task":"audit path/to/project"}' http://127.0.0.1:8000/ask
```

Start the server once in a terminal with `python server.py`, then run the `curl` command from another terminal. Ollama must already be running locally on port 11434 with the `llama3` model available. Set `SAFESTACK_AUDIT_ROOT` before startup to choose the allowed source tree.

Audits include at most 100 `.py` and `.sh` files, 24 KB per file and 24 KB total, and at most 10,000 directory entries. Requests exceeding the configured model-input limit stop without a report. The service stops if it encounters an unsafe, changing, or oversized source tree. It omits `.git`, virtual environments, caches, `node_modules`, runtime data, and generated files. These bounds constrain input handling; they do not guarantee that a language model notices every defect.

Runtime databases and outputs are stored below `runtime/`, which the service restricts to the current OS user. Reports are written to a per-audit directory and `runtime/LATEST_AUDIT_REPORT.md`. Proposed files are under that audit's `generated/` directory. Nothing is copied over the audited project. A `failed` API result means the workflow stopped; a `success` result means a report was generated, not that the project is secure.

## 🔒 Verification & Compliance
This repository contains legacy governance and test documents. Their stated checks are not a claim that all attack paths, environments, or deployments are formally verified.

The runtime's trust labels are workflow metadata. Agent functions share one process, and source text filters are not operating-system network isolation.

## 📜 Doctrine
*Model-generated findings and proposed replacements require independent review before use.*

---
**License: Sovereign SafeStack Protocol**
