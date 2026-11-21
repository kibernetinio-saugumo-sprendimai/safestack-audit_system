"""Signed per-project Ed25519 key registry.

The registry is public data.  Root and project private keys are deliberately
kept outside the repository and are written with restrictive permissions.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from canonical_serializer import canonical_json
from strict_mode import parse_json

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
except ImportError as exc:  # pragma: no cover - exercised in missing-dependency installs
    raise RuntimeError("key registry requires cryptography; install requirements.txt") from exc

SCHEMA = "safestack.project-key-registry.v1"
SIGNATURE_SCHEMA = "safestack.project-signature.v2"
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
    raw = path.expanduser().read_bytes()
    if len(raw) != 32:
        raise ValueError(f"private key must be exactly 32 raw bytes: {path}")
    return Ed25519PrivateKey.from_private_bytes(raw)


def _write_secret(path: Path, data: bytes) -> None:
    path = path.expanduser()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
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


def _write_public(path: Path, data: dict[str, Any], *, exclusive: bool = False) -> None:
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
        if exclusive:
            os.link(temporary, path)
            os.unlink(temporary)
        else:
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


def _read_public(path: Path) -> bytes:
    raw = path.expanduser().read_bytes()
    if len(raw) != 32:
        raise ValueError("trusted root must be exactly 32 raw public-key bytes")
    return raw


def _write_root_public(path: Path, data: bytes) -> None:
    path = path.expanduser()
    path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


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


def verify_registry(registry: dict[str, Any], trusted_root_public: bytes) -> None:
    if not isinstance(registry, dict):
        raise ValueError("registry must be an object")
    if not isinstance(trusted_root_public, bytes) or len(trusted_root_public) != 32:
        raise ValueError("an independent 32-byte trusted root is required")
    if registry.get("schema") != SCHEMA or not isinstance(registry.get("projects"), dict):
        raise ValueError("invalid registry schema")
    if _unb64(registry.get("root_public_key")) != trusted_root_public:
        raise ValueError("registry root does not match the independently trusted root")
    if not isinstance(registry.get("registry_id"), str) or not re.fullmatch(r"[a-f0-9]{32}", registry["registry_id"]):
        raise ValueError("invalid registry identifier")
    root = Ed25519PublicKey.from_public_bytes(trusted_root_public)
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
    verify_registry(registry, _public_bytes(root.public_key()))
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
    verify_registry(registry, _public_bytes(root.public_key()))
    if project_id not in registry["projects"]:
        raise ValueError("unknown project id")
    updated = json.loads(json.dumps(registry))
    updated["projects"][project_id]["status"] = REVOKED
    updated["projects"][project_id]["revoked_at"] = _now()
    return sign_registry(updated, root)


def _artifact_message(registry_id: str, project_id: str, artifact: bytes) -> bytes:
    # Bind attribution as well as content; envelope fields must not be transferable.
    context = {"schema": SIGNATURE_SCHEMA, "registry_id": registry_id, "project_id": project_id,
               "artifact_sha256": hashlib.sha256(artifact).hexdigest()}
    return b"SafeStack artifact signature v2\0" + canonical_json(context).encode("utf-8")


def sign_artifact(registry: dict[str, Any], project_id: str, artifact: bytes,
                  project_key: Ed25519PrivateKey, trusted_root_public: bytes) -> dict[str, str]:
    verify_registry(registry, trusted_root_public)
    entry = registry["projects"].get(project_id)
    if not entry or entry.get("status") != ACTIVE:
        raise ValueError("project key is missing or revoked")
    if _public_bytes(project_key.public_key()) != _unb64(entry["public_key"]):
        raise ValueError("project private key does not match registry")
    return {"schema": SIGNATURE_SCHEMA, "project_id": project_id,
            "registry_id": registry["registry_id"],
            "signature": _b64(project_key.sign(_artifact_message(registry["registry_id"], project_id, artifact)))}


def verify_artifact(registry: dict[str, Any], signature: dict[str, str], artifact: bytes,
                    trusted_root_public: bytes) -> None:
    verify_registry(registry, trusted_root_public)
    if not isinstance(signature, dict) or signature.get("schema") != SIGNATURE_SCHEMA:
        raise ValueError("invalid artifact signature schema")
    if signature.get("registry_id") != registry.get("registry_id"):
        raise ValueError("signature belongs to another registry")
    entry = registry["projects"].get(signature.get("project_id"))
    if not entry or entry.get("status") != ACTIVE:
        raise ValueError("project key is missing or revoked")
    Ed25519PublicKey.from_public_bytes(_unb64(entry["public_key"])).verify(
        _unb64(signature.get("signature")), _artifact_message(registry["registry_id"], signature["project_id"], artifact))


def _load(path: Path) -> dict[str, Any]:
    return parse_json(path.expanduser().read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage the signed SafeStack project-key registry")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init-root"); init.add_argument("--registry", type=Path, required=True); init.add_argument("--private-out", type=Path, required=True); init.add_argument("--public-out", type=Path, required=True)
    add = sub.add_parser("add-project"); add.add_argument("--registry", type=Path, required=True); add.add_argument("--root-private", type=Path, required=True); add.add_argument("--project-id", required=True); add.add_argument("--private-out", type=Path, required=True)
    revoke = sub.add_parser("revoke-project"); revoke.add_argument("--registry", type=Path, required=True); revoke.add_argument("--root-private", type=Path, required=True); revoke.add_argument("--project-id", required=True)
    verify = sub.add_parser("verify"); verify.add_argument("--registry", type=Path, required=True)
    sign = sub.add_parser("sign-artifact"); sign.add_argument("--registry", type=Path, required=True); sign.add_argument("--project-private", type=Path, required=True); sign.add_argument("--project-id", required=True); sign.add_argument("--artifact", type=Path, required=True); sign.add_argument("--signature-out", type=Path, required=True)
    verify_art = sub.add_parser("verify-artifact"); verify_art.add_argument("--registry", type=Path, required=True); verify_art.add_argument("--artifact", type=Path, required=True); verify_art.add_argument("--signature", type=Path, required=True)
    for command in (verify, sign, verify_art):
        command.add_argument("--root-public", type=Path, required=True, help="independently trusted 32-byte raw root public key")
    export_root = sub.add_parser("export-root-public")
    export_root.add_argument("--root-private", type=Path, required=True)
    export_root.add_argument("--public-out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init-root":
            paths = [p.expanduser().resolve() for p in (args.private_out, args.public_out, args.registry)]
            if len(set(paths)) != 3 or any(os.path.lexists(p.expanduser()) for p in (args.private_out, args.public_out, args.registry)):
                raise ValueError("root initialization requires three distinct, new output paths")
            root = Ed25519PrivateKey.generate()
            _write_secret(args.private_out, _private_bytes(root))
            public = _public_bytes(root.public_key())
            _write_root_public(args.public_out, public)
            _write_public(args.registry, sign_registry(new_registry(public), root), exclusive=True)
            print(f"created registry {args.registry}; distribute {args.public_out} through a trusted channel")
        elif args.command == "export-root-public":
            _write_root_public(args.public_out, _public_bytes(_read_private(args.root_private).public_key()))
            print(f"exported trusted root public key to {args.public_out}")
        elif args.command == "add-project":
            root = _read_private(args.root_private); registry = _load(args.registry); updated, project = add_project(registry, root, args.project_id)
            _write_secret(args.private_out, _private_bytes(project)); _write_public(args.registry, updated); print(f"added project {args.project_id}")
        elif args.command == "revoke-project":
            _write_public(args.registry, revoke_project(_load(args.registry), _read_private(args.root_private), args.project_id)); print(f"revoked project {args.project_id}")
        elif args.command == "sign-artifact":
            signature = sign_artifact(_load(args.registry), args.project_id, args.artifact.read_bytes(), _read_private(args.project_private), _read_public(args.root_public))
            _write_public(args.signature_out, signature); print(f"signed {args.artifact} as {args.project_id}")
        elif args.command == "verify-artifact":
            verify_artifact(_load(args.registry), _load(args.signature), args.artifact.read_bytes(), _read_public(args.root_public)); print("artifact signature valid")
        else:
            verify_registry(_load(args.registry), _read_public(args.root_public)); print("registry signature valid")
        return 0
    except (OSError, ValueError, TypeError, InvalidSignature):
        print("key registry operation failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
