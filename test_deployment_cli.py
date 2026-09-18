"""Deployment checks never treat command errors or missing canon rules as success."""
import unittest
import json
import sys
import tempfile
import contextlib
import io
from unittest.mock import patch

import audit_tool


class DeploymentCliTests(unittest.TestCase):
    def test_failed_command_cannot_satisfy_expected_output(self):
        output, status = audit_tool.run_command("python3 -m module_that_does_not_exist_safestack")
        self.assertNotEqual(status, 0)
        self.assertIn("No module named", output)
        self.assertFalse(audit_tool.check_command_contains({
            "command": "python3 -m module_that_does_not_exist_safestack",
            "contains": "No module named",
        }))

    def test_shell_metacharacters_remain_rejected(self):
        self.assertEqual(audit_tool.run_command("echo safe ; false"), ("", 2))

    def test_empty_or_malformed_canon_is_rejected(self):
        for canon in ({}, {"checks": []}, {"checks": [{}]},
                      {"checks": [{"id": "bad", "type": "command_contains", "severity": "high", "expected": "yes"}]}):
            with self.subTest(canon=canon), self.assertRaises(ValueError):
                audit_tool.validate_canon(canon)

    def test_all_configured_failures_matter_independent_of_severity(self):
        self.assertFalse(audit_tool.run_check({"id": "firewall", "type": "command_contains",
                                               "command": "python3 -m module_that_does_not_exist_safestack",
                                               "contains": "active", "severity": "high"}))

    def test_command_execution_error_never_passes_expected_false(self):
        self.assertFalse(audit_tool.run_check({"type": "command_contains",
                                               "command": "/no/such/safestack-command",
                                               "contains": "x", "expected": False}))

    def test_expected_false_is_supported(self):
        with patch.object(audit_tool.os.path, "exists", return_value=False):
            self.assertTrue(audit_tool.run_check({"type": "file_exists", "path": "/missing", "expected": False}))

    def test_main_reports_exit_status_and_canon_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            existing = temporary + "/present.txt"
            with open(existing, "w", encoding="utf-8") as stream:
                stream.write("present")
            canon_path = temporary + "/canon.json"
            with open(canon_path, "w", encoding="utf-8") as stream:
                json.dump({"schema": "test", "version": "1", "checks": [
                    {"id": "present", "type": "file_exists", "severity": "low", "path": existing},
                    {"id": "missing", "type": "file_exists", "severity": "high", "path": temporary + "/missing"},
                ]}, stream)
            stdout = io.StringIO()
            with patch.object(sys, "argv", ["audit_tool.py", canon_path]), contextlib.redirect_stdout(stdout):
                with self.assertRaises(SystemExit) as exit_code:
                    audit_tool.main()
            self.assertEqual(exit_code.exception.code, 1)
            self.assertIn("Canon: test / 1", stdout.getvalue())
            self.assertIn("FAILED", stdout.getvalue())

    def test_successful_main_reports_all_checks_passed(self):
        with tempfile.TemporaryDirectory() as temporary:
            canon_path = temporary + "/canon.json"
            with open(canon_path, "w", encoding="utf-8") as stream:
                json.dump({"schema": "test", "version": "1", "checks": [
                    {"id": "missing", "type": "file_exists", "severity": "low", "path": temporary + "/missing", "expected": False},
                ]}, stream)
            stdout = io.StringIO()
            with patch.object(sys, "argv", ["audit_tool.py", canon_path]), contextlib.redirect_stdout(stdout):
                with self.assertRaises(SystemExit) as exit_code:
                    audit_tool.main()
            self.assertEqual(exit_code.exception.code, 0)
            self.assertIn("all configured deployment checks passed", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
