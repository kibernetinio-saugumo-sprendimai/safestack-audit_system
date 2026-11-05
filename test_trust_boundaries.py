"""Regressions for independent signing roots, bounded API input and truthful checks."""
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
import audit_tool
import key_registry as keys
import server


class RootTrustTests(unittest.TestCase):
    def setUp(self):
        self.root = keys.Ed25519PrivateKey.generate()
        self.pin = keys._public_bytes(self.root.public_key())
        self.registry = keys.sign_registry(keys.new_registry(self.pin), self.root)
        self.registry, self.project = keys.add_project(self.registry, self.root, "project")
        self.artifact = b"release-content"

    def test_attacker_cannot_replace_registry_and_its_embedded_root(self):
        attacker = keys.Ed25519PrivateKey.generate()
        attacker_pin = keys._public_bytes(attacker.public_key())
        forged = keys.sign_registry(keys.new_registry(attacker_pin), attacker)
        forged, project = keys.add_project(forged, attacker, "project")
        signature = keys.sign_artifact(forged, "project", self.artifact, project, attacker_pin)
        with self.assertRaises(ValueError):
            keys.verify_registry(forged, self.pin)
        with self.assertRaises(ValueError):
            keys.verify_artifact(forged, signature, self.artifact, self.pin)
        with self.assertRaises(TypeError):
            keys.verify_registry(forged)

    def test_signatures_bind_artifact_schema_project_and_registry(self):
        signature = keys.sign_artifact(self.registry, "project", self.artifact, self.project, self.pin)
        keys.verify_artifact(self.registry, signature, self.artifact, self.pin)
        with self.assertRaises(keys.InvalidSignature):
            keys.verify_artifact(self.registry, signature, b"different", self.pin)
        another = keys.sign_registry(keys.new_registry(self.pin), self.root)
        another, _ = keys.add_project(another, self.root, "project", self.project)
        altered = {**signature, "registry_id": another["registry_id"]}
        with self.assertRaises(keys.InvalidSignature):
            keys.verify_artifact(another, altered, self.artifact, self.pin)
        other_project, _ = keys.add_project(self.registry, self.root, "other-project", self.project)
        with self.assertRaises(keys.InvalidSignature):
            keys.verify_artifact(other_project, {**signature, "project_id": "other-project"}, self.artifact, self.pin)
        with self.assertRaises(ValueError):
            keys.verify_artifact(self.registry, {**signature, "schema": "safestack.project-signature.v1"}, self.artifact, self.pin)

    def test_root_initialization_refuses_existing_or_overlapping_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry, private, public = root / "registry.json", root / "root.key", root / "root.pub"
            registry.write_text("previous registry")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(keys.main(["init-root", "--registry", str(registry), "--private-out", str(private), "--public-out", str(public)]), 1)
            self.assertEqual(registry.read_text(), "previous registry")
            self.assertFalse(private.exists())
            self.assertFalse(public.exists())
            registry.unlink()
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(keys.main(["init-root", "--registry", str(registry), "--private-out", str(registry), "--public-out", str(public)]), 1)
            self.assertFalse(registry.exists())

    def test_existing_root_can_export_pin_without_regenerating_or_overwriting_it(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            private, public = root / "root.key", root / "root.pub"
            keys._write_secret(private, keys._private_bytes(self.root))
            arguments = ["export-root-public", "--root-private", str(private), "--public-out", str(public)]
            self.assertEqual(keys.main(arguments), 0)
            self.assertEqual(public.read_bytes(), self.pin)
            keys.verify_registry(self.registry, public.read_bytes())
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(keys.main(arguments), 1)
            self.assertEqual(public.read_bytes(), self.pin)

    def test_invalid_registry_signature_has_clean_cli_failure_and_preserves_parent_permissions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            os.chmod(root, 0o755)
            keys._write_secret(root / "private.key", b"x" * 32)
            self.assertEqual(root.stat().st_mode & 0o777, 0o755)
            registry = {**self.registry, "signature": keys._b64(b"x" * 64)}
            (root / "registry.json").write_text(json.dumps(registry))
            (root / "root.pub").write_bytes(self.pin)
            errors = io.StringIO()
            with contextlib.redirect_stderr(errors):
                self.assertEqual(keys.main(["verify", "--registry", str(root / "registry.json"), "--root-public", str(root / "root.pub")]), 1)
            self.assertNotIn("Traceback", errors.getvalue())


class ApiInputTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(server.server, raise_server_exceptions=False)
        self.key = patch.dict(os.environ, {"SAFESTACK_API_KEY": "fixture-key"})
        self.key.start()
        self.addCleanup(self.key.stop)

    def test_non_ascii_untrusted_header_returns_unauthorized(self):
        result = self.client.post("/ask", json={"task": "audit x"}, headers=[(b"x-api-key", b"\xff")])
        self.assertEqual(result.status_code, 401)

    def test_oversized_body_never_reaches_the_graph(self):
        with patch.object(server, "_stream_audit") as graph:
            result = self.client.post("/ask", json={"task": "audit x", "ignored": "x" * server.MAX_REQUEST_BYTES}, headers={"X-API-Key": "fixture-key"})
            self.assertEqual(result.status_code, 413)
            graph.assert_not_called()

    def test_chunked_and_misdeclared_body_lengths_cannot_bypass_limit(self):
        raw = json.dumps({"task": "audit x", "ignored": "x" * server.MAX_REQUEST_BYTES}).encode()
        for headers in ({}, {"Content-Length": "1"}):
            with self.subTest(headers=headers), patch.object(server, "_stream_audit") as graph:
                chunks = (raw[i:i + 1024] for i in range(0, len(raw), 1024))
                response = self.client.post("/ask", content=chunks, headers={"Content-Type": "application/json", "X-API-Key": "fixture-key", **headers})
                self.assertEqual(response.status_code, 413)
                graph.assert_not_called()

    def test_normal_and_maximum_unicode_task_keep_working(self):
        for task in ("audit x", "\U0001f512" * 4000):
            raw = json.dumps({"task": task, "thread_id": "\U0001f512" * 128})
            self.assertLess(len(raw.encode()), server.MAX_REQUEST_BYTES)
            with patch.object(server, "_stream_audit", return_value=([], {"current_state": "COMPLETE"})) as graph:
                result = self.client.post("/ask", content=raw, headers={"Content-Type": "application/json", "X-API-Key": "fixture-key"})
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result.json()["status"], "success")
                graph.assert_called_once()


class ObservationTests(unittest.TestCase):
    def test_invalid_or_unreadable_path_never_passes_expected_absence(self):
        rule = {"type": "file_exists", "path": "\0", "expected": False}
        self.assertFalse(audit_tool.run_check(rule))
        with patch.object(audit_tool.os, "stat", side_effect=PermissionError):
            self.assertFalse(audit_tool.run_check({**rule, "path": "/protected"}))
        with tempfile.TemporaryDirectory() as temp:
            self.assertTrue(audit_tool.run_check({**rule, "path": str(Path(temp) / "missing")}))
            self.assertFalse(audit_tool.run_check({"type": "file_regex", "path": str(Path(temp) / "missing"), "pattern": "unsafe", "expected": False}))
            parent_file = Path(temp) / "not-a-directory"
            parent_file.write_text("ordinary file")
            self.assertFalse(audit_tool.run_check({**rule, "path": str(parent_file / "child")}))
            bad = Path(temp) / "invalid.txt"
            bad.write_bytes(b"\xff")
            self.assertFalse(audit_tool.run_check({"type": "file_regex", "path": str(bad), "pattern": "unsafe", "expected": False}))

    def test_malformed_rules_and_duplicate_identifiers_are_rejected(self):
        valid = {"id": "present", "type": "file_exists", "path": "/valid", "severity": "high"}
        invalid = [{**valid, "path": "\0"}, {**valid, "path": 123},
                   {**valid, "type": "file_regex", "pattern": "["},
                   {**valid, "type": "disk_free_mb", "minimum_mb": True},
                   {**valid, "type": "command_contains", "command": "true"}]
        for rule in invalid:
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                audit_tool.validate_canon({"checks": [rule]})
        with self.assertRaises(ValueError):
            audit_tool.validate_canon({"checks": [valid, valid]})

    def test_ssh_checks_use_effective_settings_with_exact_lines_and_fail_on_errors(self):
        canon = json.loads(Path(__file__).with_name("SAFESTACK_CANON_DEPLOYMENT.json").read_text())
        ssh_rules = [r for r in canon["checks"] if r["id"] in {"root-login-disabled", "ssh-password-disabled"}]
        for rule in ssh_rules:
            self.assertEqual(rule["command"], "sshd -T")
            with patch.object(audit_tool, "run_command", return_value=("permitrootlogin no\npasswordauthentication no", 0)):
                self.assertTrue(audit_tool.run_check(rule))
            with patch.object(audit_tool, "run_command", return_value=("permitrootlogin yes\npasswordauthentication yes\nforcecommand echo permitrootlogin no passwordauthentication no", 0)):
                self.assertFalse(audit_tool.run_check(rule))
            with patch.object(audit_tool, "run_command", return_value=("permitrootlogin no\npasswordauthentication no", 1)):
                self.assertFalse(audit_tool.run_check(rule))


class CiCoverageTests(unittest.TestCase):
    def test_regression_scripts_are_separate_ci_commands(self):
        import yaml
        workflow = yaml.safe_load(Path(__file__).with_name('.github').joinpath('workflows/ci.yml').read_text())
        commands = [line.strip() for step in workflow['jobs']['audit']['steps'] for line in step.get('run', '').splitlines()]
        for command in ('python -m unittest discover -v', 'python test_core.py', 'python test_airgap.py',
                        'python test_airgap_full.py', 'python priority_3_hash_chain_audit.py',
                        'python priority_4_immutability_test.py', 'python priority_7_lockdown_test.py',
                        'sha256sum --check SHA256SUMS'):
            self.assertIn(command, commands)


class ApiWorkflowTests(unittest.TestCase):
    def test_complete_graph_api_run_generates_report_and_cleans_checkpoints(self):
        import app as runtime
        import secure_io
        from canonical_serializer import canonical_json

        def model_reply(role, _context, _prompt):
            value = {"agent": role, "status": "pass", "findings": []}
            for field, kind in runtime.ROLE_FIELDS[role].items():
                value[field] = [] if kind is list else "Reviewed"
            return canonical_json(value)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            project = root / "project"
            project.mkdir()
            (project / "sample.py").write_text("value = 1\n")
            with patch.object(runtime, "PROJECT_ROOT", root), patch.object(secure_io, "RUNTIME_ROOT", root / "private-runtime"), \
                 patch.object(runtime, "call_ollama", side_effect=model_reply), \
                 patch.dict(os.environ, {"SAFESTACK_API_KEY": "fixture-key"}):
                response = TestClient(server.server).post("/ask", json={"task": "audit " + str(project)}, headers={"X-API-Key": "fixture-key"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["state"], "COMPLETE")
            self.assertTrue(Path(data["report_path"]).is_file())
            self.assertFalse(server._audit_slot.locked())
            config = {"configurable": {"thread_id": data["session_id"]}}
            self.assertEqual(list(runtime.memory.list(config)), [])

    def test_asgi_stream_stops_reading_after_limit_without_parsing(self):
        import asyncio
        events = []
        reads = 0
        called = False

        async def receive():
            nonlocal reads
            reads += 1
            return {"type": "http.request", "body": b"x" * 32768, "more_body": True}

        async def send(event):
            events.append(event)

        async def downstream(*_args):
            nonlocal called
            called = True

        scope = {"type": "http", "method": "POST", "path": "/ask"}
        asyncio.run(server.AuditBodyLimit(downstream)(scope, receive, send))
        self.assertFalse(called)
        self.assertEqual(reads, 3)
        self.assertEqual(events[0]["status"], 413)
