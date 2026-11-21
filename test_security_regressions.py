"""Local, dependency-backed regressions for previously uncovered audit boundaries."""
import asyncio
import contextlib
import hashlib
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as runtime
import secure_io
from canonical_serializer import canonical_json
from strict_mode import validate_output, verify_chain


class ProtocolTests(unittest.TestCase):
    def test_requires_object_and_rejects_duplicate_and_nonfinite_json(self):
        for raw in (
            '[]', 'null',
            '{"agent":"x","agent":"y","status":"pass","findings":[]}',
            '{"agent":"x","status":"pass","findings":[],"extra":NaN}',
        ):
            with self.subTest(raw=raw):
                self.assertNotEqual(validate_output(raw)["status"], "valid")
        with self.assertRaises(ValueError):
            canonical_json({"value": float("nan")})

    def test_role_contract_and_top_level_failure(self):
        self.assertEqual(validate_output('{"agent":"DOCUMENTER","status":"pass","findings":[],"summary":"ok"}', "DOCUMENTER")["status"], "valid")
        self.assertEqual(validate_output('{"agent":"DOCUMENTER","status":"pass","findings":[]}', "DOCUMENTER")["status"], "invalid")
        value = {"agent": "REVIEWER", "status": "fail", "findings": [], "meta": {"status": "pass"}}
        self.assertEqual(runtime.should_lockdown({"messages": [("ai", canonical_json(value))]}), "lockdown")
        self.assertEqual(runtime.should_lockdown({"current_state": "LOCKDOWN", "messages": [("ai", "anything")]}), "lockdown")
        self.assertEqual(runtime.should_lockdown({"lifecycle_stage": "HALTED", "messages": [("ai", "anything")]}), "lockdown")

    def test_chain_uses_the_same_exact_bytes_for_create_and_verify(self):
        content = "trailing whitespace stays bound  \n"
        digest = hashlib.sha256(("0" * 64 + "|" + content).encode()).hexdigest()
        self.assertTrue(verify_chain([{"content": content, "hash": digest}])["trusted_chain_valid"])


class FilesystemBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.project = self.root / "project"
        self.project.mkdir()
        self.runtime = self.root / "runtime"
        self.runtime.mkdir(mode=0o700)
        self.root_scope = patch.object(runtime, "PROJECT_ROOT", self.root)
        self.runtime_scope = patch.object(secure_io, "RUNTIME_ROOT", self.runtime)
        self.root_scope.start()
        self.runtime_scope.start()

    def tearDown(self):
        self.runtime_scope.stop()
        self.root_scope.stop()
        self.temp.cleanup()

    def test_reads_every_supported_script_in_stable_order(self):
        (self.project / "z_last.py").write_text("last = True\n")
        (self.project / "a_first.py").write_text("first = True\n")
        (self.project / "skip.txt").write_text("unsupported\n")
        text, sources = runtime.read_project_files(str(self.project))
        self.assertEqual(list(sources), ["a_first.py", "z_last.py"])
        self.assertIn("last = True", text)

    def test_rejects_a_fifo_without_waiting_for_a_writer(self):
        os.mkfifo(self.project / "blocked.py")
        text, sources = runtime.read_project_files(str(self.project))
        self.assertFalse(sources)
        self.assertEqual(text, "ERROR: INCOMPLETE_OR_UNSAFE_SOURCE")

    def test_rejects_source_symlinks_and_hardlinks(self):
        victim = self.project / "victim.py"
        victim.write_text("safe = True\n")
        (self.project / "link.py").symlink_to(victim)
        text, sources = runtime.read_project_files(str(self.project))
        self.assertFalse(sources)
        (self.project / "link.py").unlink()
        os.link(victim, self.project / "alias.py")
        text, sources = runtime.read_project_files(str(self.project))
        self.assertFalse(sources)

    def test_atomic_output_does_not_mutate_a_hardlink_target(self):
        victim = self.root / "victim.txt"
        victim.write_text("preserve\n")
        os.link(victim, self.runtime / "alias.txt")
        secure_io.write_private("alias.txt", "replace\n")
        self.assertEqual(victim.read_text(), "preserve\n")
        self.assertEqual((self.runtime / "alias.txt").read_text(), "replace\n")
        self.assertEqual(stat.S_IMODE((self.runtime / "alias.txt").stat().st_mode), 0o600)

    def test_report_replaces_a_symlink_without_writing_its_target(self):
        victim = self.root / "victim.txt"
        victim.write_text("preserve\n")
        (self.runtime / "LATEST_AUDIT_REPORT.md").symlink_to(victim)
        decisions = {role: {"status": "pass", "findings": []} for role in runtime.ROLE_FIELDS}
        decisions["DOCUMENTER"]["summary"] = "Reviewed"
        decisions["SUPERVISOR"].update(approved_findings=[], rejected_findings=[])
        decisions["FIXER"]["patches"] = []
        decisions["VALIDATOR"]["issue"] = "Valid"
        decisions["REVIEWER"]["reasoning"] = "Complete"
        decisions["DRY_RUN"] = {"status": "pass", "findings": []}
        content = "start|audit"
        digest = runtime.update_chain({}, content)
        state = {"current_state": "APPROVED", "trust_level": "LIMITED", "source_files": {"demo.py": "ok = True\n"},
                 "project_path": str(self.project), "runtime_id": "a" * 32, "decisions": decisions,
                 "patches": [], "artifact_paths": {}, "evidence_chain": [{"content": content, "hash": digest}], "chain_hash": digest}
        result = runtime.reporter(state)
        self.assertEqual(victim.read_text(), "preserve\n")
        self.assertFalse((self.runtime / "LATEST_AUDIT_REPORT.md").is_symlink())
        self.assertIn("unsigned", (self.runtime / "LATEST_AUDIT_REPORT.md").read_text())
        self.assertEqual(result["trust_level"], "UNTRUSTED")
        self.assertEqual(result["lifecycle_stage"], "VALIDATED")
        self.assertEqual(result["report_path"], str(self.runtime / "sessions" / ("a" * 32) / "report.md"))

    def test_lockdown_symlink_failure_still_stops_safely(self):
        victim = self.root / "victim.txt"
        victim.write_text("preserve\n")
        (self.runtime / "LOCKDOWN_FORENSICS.log").symlink_to(victim)
        result = runtime.lockdown({"current_state": "AUDITING"})
        self.assertEqual(victim.read_text(), "preserve\n")
        self.assertEqual(result["current_state"], "LOCKDOWN")
        self.assertIn("Forensic storage failed", result["messages"][0][1])


class GraphIntegrationTests(unittest.TestCase):
    def test_success_requires_all_stages_and_covers_all_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            project = root / "project"
            project.mkdir()
            (project / "a.py").write_text("value = 1\n")
            (project / "b.sh").write_text("#!/bin/sh\ntrue\n")
            runtime_root = root / "private-runtime"
            original_root, original_runtime = runtime.PROJECT_ROOT, secure_io.RUNTIME_ROOT
            runtime.PROJECT_ROOT = root
            secure_io.RUNTIME_ROOT = runtime_root
            def respond(role, _code, _prompt):
                response = {"agent": role, "status": "pass", "findings": []}
                if role == "DOCUMENTER": response["summary"] = "Reviewed source."
                if role == "SUPERVISOR": response.update(approved_findings=[], rejected_findings=[])
                if role == "FIXER": response["patches"] = []
                if role == "VALIDATOR": response["issue"] = "Valid."
                if role == "REVIEWER": response["reasoning"] = "No high-risk issues."
                return canonical_json(response)
            graph = runtime.workflow.compile()
            with patch.object(runtime, "call_ollama", side_effect=respond):
                # Run after patch is active; model requests stay fully offline.
                runtime.PROJECT_ROOT = root
                secure_io.RUNTIME_ROOT = runtime_root
                try:
                    events = list(graph.stream({"messages": [("user", "audit " + str(project))]},
                                               {"configurable": {"thread_id": "regression-" + os.urandom(8).hex()}}))
                finally:
                    runtime.PROJECT_ROOT = original_root
                    secure_io.RUNTIME_ROOT = original_runtime
            final = events[-1].get("reporter", events[-1].get("lockdown", {}))
            self.assertEqual(final["current_state"], "COMPLETE")
            self.assertEqual(final["lifecycle_stage"], "VALIDATED")
            self.assertIn("report_path", final)
            self.assertTrue(Path(final["report_path"]).is_file())
            report = Path(final["report_path"]).read_text()
            self.assertIn('"covered_files": [\n        "a.py",\n        "b.sh"', report)
            self.assertIn("Untrusted model-assisted draft", report)
            self.assertNotIn("AUTHORITATIVE", report)


if __name__ == "__main__":
    unittest.main()
