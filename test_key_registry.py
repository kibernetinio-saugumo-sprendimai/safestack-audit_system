import os
import tempfile
import unittest
from pathlib import Path

import key_registry


class KeyRegistryTests(unittest.TestCase):
    def test_each_project_isolated_and_revocation_is_scoped(self):
        root = key_registry.Ed25519PrivateKey.generate()
        registry = key_registry.sign_registry(
            key_registry.new_registry(key_registry._public_bytes(root.public_key())), root)
        registry, first = key_registry.add_project(registry, root, "project-001")
        registry, second = key_registry.add_project(registry, root, "project-002")
        artifact = b"release bytes"
        signature = key_registry.sign_artifact(registry, "project-001", artifact, first)
        key_registry.verify_artifact(registry, signature, artifact)
        revoked = key_registry.revoke_project(registry, root, "project-001")
        with self.assertRaises(ValueError):
            key_registry.verify_artifact(revoked, signature, artifact)
        second_signature = key_registry.sign_artifact(revoked, "project-002", artifact, second)
        key_registry.verify_artifact(revoked, second_signature, artifact)

    def test_registry_tampering_is_rejected(self):
        root = key_registry.Ed25519PrivateKey.generate()
        registry = key_registry.sign_registry(
            key_registry.new_registry(key_registry._public_bytes(root.public_key())), root)
        registry["projects"]["rogue"] = {"public_key": "AA==", "status": "active"}
        with self.assertRaises(Exception):
            key_registry.verify_registry(registry)

    def test_secret_files_are_private_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "root.key"
            key_registry._write_secret(path, b"x" * 32)
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                key_registry._write_secret(path, b"y" * 32)

    def test_cli_sign_and_verify_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root.key"
            registry_path = Path(tmp) / "registry.json"
            project = Path(tmp) / "project.key"
            artifact = Path(tmp) / "artifact.bin"
            signature = Path(tmp) / "artifact.sig.json"
            self.assertEqual(key_registry.main(["init-root", "--registry", str(registry_path), "--private-out", str(root)]), 0)
            self.assertEqual(key_registry.main(["add-project", "--registry", str(registry_path), "--root-private", str(root), "--project-id", "p1", "--private-out", str(project)]), 0)
            artifact.write_bytes(b"artifact")
            self.assertEqual(key_registry.main(["sign-artifact", "--registry", str(registry_path), "--project-private", str(project), "--project-id", "p1", "--artifact", str(artifact), "--signature-out", str(signature)]), 0)
            self.assertEqual(key_registry.main(["verify-artifact", "--registry", str(registry_path), "--artifact", str(artifact), "--signature", str(signature)]), 0)


if __name__ == "__main__":
    unittest.main()
