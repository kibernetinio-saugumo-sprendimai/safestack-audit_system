"""Signed per-project Ed25519 key registry.

The registry is public data.  Root and project private keys are deliberately
kept outside the repository and are written with restrictive permissions.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import secrets
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from canonical_serializer import canonical_json

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
except ImportError as exc:  # pragma: no cover - exercised in missing-dependency installs
    raise RuntimeError("key registry requires cryptography; install requirements.txt") from exc

SCHEMA = "safestack.project-key-registry.v1"
ACTIVE = "active"
REVOKED = "revoked"


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _unb64(value: Any) -> bytes:
    if not isinstance(value, str):
        raise ValueError("encoded key must be a string")
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError) as exc:
        raise ValueError("invalid base64 key") from exc


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def unsigned_registry(registry: dict[str, Any]) -> dict[str, Any]:
    """Return the exact object covered by the root signature."""
    if not isinstance(registry, dict):
        raise ValueError("registry must be an object")
    result = dict(registry)
    result.pop("signature", None)
    return result


def _registry_bytes(registry: dict[str, Any]) -> bytes:
    return canonical_json(unsigned_registry(registry)).encode("utf-8")


def _private_bytes(key: Ed25519PrivateKey) -> bytes:
    return key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                             serialization.NoEncryption())


def _public_bytes(key: Ed25519PublicKey) -> bytes:
    return key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def _read_private(path: Path) -> Ed25519PrivateKey:
    raw = path.read_bytes()
    if len(raw) != 32:
        raise ValueError(f"private key must be exactly 32 raw bytes: {path}")
    return Ed25519PrivateKey.from_private_bytes(raw)


def _write_secret(path: Path, data: bytes) -> None:
    path = path.expanduser()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def _write_public(path: Path, data: dict[str, Any]) -> None:
    path = path.expanduser()
    path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    payload = (canonical_json(data) + "\n").encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def new_registry(root_public: bytes) -> dict[str, Any]:
    if len(root_public) != 32:
        raise ValueError("Ed25519 public key must be 32 bytes")
    return {"schema": SCHEMA, "registry_id": secrets.token_hex(16),
            "root_public_key": _b64(root_public), "projects": {}}


def sign_registry(registry: dict[str, Any], root: Ed25519PrivateKey) -> dict[str, Any]:
    expected = _unb64(registry.get("root_public_key"))
    if _public_bytes(root.public_key()) != expected:
        raise ValueError("root private key does not match registry root public key")
    result = dict(registry)
    result["signature"] = _b64(root.sign(_registry_bytes(registry)))
    return result


def verify_registry(registry: dict[str, Any]) -> None:
    if registry.get("schema") != SCHEMA or not isinstance(registry.get("projects"), dict):
        raise ValueError("invalid registry schema")
    root = Ed25519PublicKey.from_public_bytes(_unb64(registry.get("root_public_key")))
    signature = _unb64(registry.get("signature"))
    if len(signature) != 64:
        raise ValueError("invalid registry signature")
    root.verify(signature, _registry_bytes(registry))
    for project_id, entry in registry["projects"].items():
        if not isinstance(project_id, str) or not project_id or not isinstance(entry, dict):
            raise ValueError("invalid project entry")
        if entry.get("status") not in {ACTIVE, REVOKED}:
            raise ValueError("invalid project status")
        if len(_unb64(entry.get("public_key"))) != 32:
            raise ValueError("invalid project public key")


def add_project(registry: dict[str, Any], root: Ed25519PrivateKey, project_id: str,
                project_key: Ed25519PrivateKey | None = None) -> tuple[dict[str, Any], Ed25519PrivateKey]:
    verify_registry(registry)
    if not project_id or project_id in registry["projects"]:
        raise ValueError("project id must be new and nonempty")
    project_key = project_key or Ed25519PrivateKey.generate()
    updated = dict(registry)
    projects = dict(registry["projects"])
    projects[project_id] = {"public_key": _b64(_public_bytes(project_key.public_key())),
                            "status": ACTIVE, "created_at": _now()}
    updated["projects"] = projects
    return sign_registry(updated, root), project_key


def revoke_project(registry: dict[str, Any], root: Ed25519PrivateKey, project_id: str) -> dict[str, Any]:
    verify_registry(registry)
    if project_id not in registry["projects"]:
        raise ValueError("unknown project id")
    updated = json.loads(json.dumps(registry))
    updated["projects"][project_id]["status"] = REVOKED
    updated["projects"][project_id]["revoked_at"] = _now()
    return sign_registry(updated, root)


def sign_artifact(registry: dict[str, Any], project_id: str, artifact: bytes,
                  project_key: Ed25519PrivateKey) -> dict[str, str]:
    verify_registry(registry)
    entry = registry["projects"].get(project_id)
    if not entry or entry.get("status") != ACTIVE:
        raise ValueError("project key is missing or revoked")
    if _public_bytes(project_key.public_key()) != _unb64(entry["public_key"]):
        raise ValueError("project private key does not match registry")
    return {"schema": "safestack.project-signature.v1", "project_id": project_id,
            "registry_id": registry["registry_id"], "signature": _b64(project_key.sign(artifact))}


def verify_artifact(registry: dict[str, Any], signature: dict[str, str], artifact: bytes) -> None:
    verify_registry(registry)
    if signature.get("registry_id") != registry.get("registry_id"):
        raise ValueError("signature belongs to another registry")
    entry = registry["projects"].get(signature.get("project_id"))
    if not entry or entry.get("status") != ACTIVE:
        raise ValueError("project key is missing or revoked")
    Ed25519PublicKey.from_public_bytes(_unb64(entry["public_key"])).verify(
        _unb64(signature.get("signature")), artifact)


def _load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage the signed SafeStack project-key registry")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init-root"); init.add_argument("--registry", type=Path, required=True); init.add_argument("--private-out", type=Path, required=True)
    add = sub.add_parser("add-project"); add.add_argument("--registry", type=Path, required=True); add.add_argument("--root-private", type=Path, required=True); add.add_argument("--project-id", required=True); add.add_argument("--private-out", type=Path, required=True)
    revoke = sub.add_parser("revoke-project"); revoke.add_argument("--registry", type=Path, required=True); revoke.add_argument("--root-private", type=Path, required=True); revoke.add_argument("--project-id", required=True)
    verify = sub.add_parser("verify"); verify.add_argument("--registry", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init-root":
            root = Ed25519PrivateKey.generate(); _write_secret(args.private_out, _private_bytes(root))
            _write_public(args.registry, sign_registry(new_registry(_public_bytes(root.public_key())), root)); print(f"created registry {args.registry}")
        elif args.command == "add-project":
            root = _read_private(args.root_private); registry = _load(args.registry); updated, project = add_project(registry, root, args.project_id)
            _write_secret(args.private_out, _private_bytes(project)); _write_public(args.registry, updated); print(f"added project {args.project_id}")
        elif args.command == "revoke-project":
            _write_public(args.registry, revoke_project(_load(args.registry), _read_private(args.root_private), args.project_id)); print(f"revoked project {args.project_id}")
        else:
            verify_registry(_load(args.registry)); print("registry signature valid")
        return 0
    except (OSError, ValueError, TypeError):
        print("key registry operation failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
