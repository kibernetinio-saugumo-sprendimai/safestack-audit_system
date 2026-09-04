import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import audit_tool


class AuditToolSecurityTests(unittest.TestCase):
    def test_untrusted_canon_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "canon.json"
            path.write_text(json.dumps({"checks": []}), encoding="utf-8")
            with self.assertRaises(audit_tool.CanonError):
                audit_tool.load_canon(str(path))

    def test_command_must_be_allowlisted(self):
        canon = {
            "checks": [
                {
                    "id": "injection",
                    "severity": "critical",
                    "type": "argv_contains",
                    "argv": ["sh", "-c", "touch /tmp/pwned"],
                    "contains": "anything",
                }
            ]
        }
        with self.assertRaises(audit_tool.CanonError):
            audit_tool.validate_canon(canon)

    @patch("audit_tool.subprocess.run")
    def test_shell_is_never_used(self, run):
        run.return_value.stdout = "Status: active"
        output = audit_tool.run_argv(["ufw", "status"])
        self.assertIn("active", output)
        self.assertIs(run.call_args.kwargs["shell"], False)


if __name__ == "__main__":
    unittest.main()
