# 🛡️ SafeStack: Sovereign Governance Kernel

**Version: v2.0.0**

SafeStack is a model-assisted audit tool for Python and Bash projects on POSIX systems with directory-relative, no-follow filesystem operations. It reads source under a configured audit root, sends that source to a local Ollama service, and stores findings and proposed replacement files for human review. It does not apply or deploy proposed changes.

## 💎 Core Doctrine
1. The API requires an operator configured `SAFESTACK_API_KEY` and limits `/ask` request bodies to 64 KiB before JSON parsing, including streamed requests.
2. The default listener is `127.0.0.1:8000`.
3. Reports include an unsigned integrity digest. This digest does not authenticate an author.

### Per-project signing keys

The repository includes `key_registry.py` for isolated Ed25519 project keys. The
public registry may be published, but the root private key and every project
private key must remain offline and outside Git. The root key signs the registry;
revoking one project key does not revoke any other project.

```bash
python3 key_registry.py init-root --registry public-project-keys.json --private-out /offline/root.key --public-out /trusted/root.pub
python3 key_registry.py add-project --registry public-project-keys.json --root-private /offline/root.key --project-id project-001 --private-out /offline/project-001.key
python3 key_registry.py verify --registry public-project-keys.json --root-public /trusted/root.pub
python3 key_registry.py sign-artifact --registry public-project-keys.json --project-private /offline/project-001.key --project-id project-001 --artifact release.tar --signature-out release.tar.sig.json --root-public /trusted/root.pub
python3 key_registry.py verify-artifact --registry public-project-keys.json --artifact release.tar --signature release.tar.sig.json --root-public /trusted/root.pub
python3 key_registry.py revoke-project --registry public-project-keys.json --root-private /offline/root.key --project-id project-001
```

Keep offline root-key recovery material on paper or another physically separate
backup, but use an offline device or hardware token for signing. Do not paste
private key bytes into the repository, issue tracker, logs, or chat. The public
registry is not trusted until its signature verifies against an **independently trusted** root public key. Distribute the 32-byte raw `root.pub` through a separate trusted channel and keep the verifier's copy protected from replacement. Never extract a trust pin from the registry you are trying to verify. Existing root private keys can export their public half on the offline signing device; do not regenerate or replace a deployed root merely to create its public pin.

For an existing installation, export the public half from the existing private root on the offline signing device, instead of running `init-root` again:

```bash
python3 key_registry.py export-root-public --root-private /offline/root.key --public-out /trusted/root.pub
```

The example revokes the project after demonstrating signature verification; later verification with the updated registry rejects that project's signatures.

Artifact signatures now use `safestack.project-signature.v2`, binding the artifact hash, registry ID, and project ID. Legacy v1 artifact signatures must be regenerated; registry v1 remains supported when its root is independently pinned. A pinned root does not prove registry freshness: distribute the latest trusted signed registry so revocations cannot be bypassed with an older signed snapshot. Root initialization refuses existing or overlapping output paths.

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

## Local verification and development

```bash
pip install -r requirements-dev.txt
pip check
python -m unittest discover -v
python sovereign_chaos_test.py
python test_core.py
python test_airgap.py
python test_airgap_full.py
python priority_3_hash_chain_audit.py
python priority_4_immutability_test.py
python priority_7_lockdown_test.py
pip-audit
shasum -a 256 -c SHA256SUMS  # Linux: sha256sum --check SHA256SUMS
```

The automated regressions use temporary source trees, generated test keys and mocked model replies. They do not audit real projects through Ollama, deploy generated changes, or reuse operator private keys. `constraints.txt` sets patched minimum versions for vulnerable transitive dependencies; runtime installation applies it through `requirements.txt`.

The deployment canon now checks OpenSSH global effective settings using `sshd -T`, including its loaded configuration files. It requires sufficient access to query that configuration. Per-user/per-host `Match` contexts need separate context-specific checks. Failed commands, inaccessible files, invalid text, malformed paths and malformed canon rules cannot satisfy an expected-negative check. The canon is trusted operator configuration and can execute configured commands without a shell.

`GOLDEN_HASH_REGISTRY.json` remains an archived historical baseline. `SHA256SUMS` describes the current source; neither is a signature or an independent source of author trust. Legacy `AUDIT_REPORT*.md` documents describe earlier checks and do not certify subsequent changes.
