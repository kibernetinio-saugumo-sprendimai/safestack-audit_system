"""API authentication, overload rejection and workflow status propagation."""
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import server


class ApiSecurityTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(server.server)

    def test_missing_or_wrong_api_key_is_rejected(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SAFESTACK_API_KEY", None)
            self.assertEqual(self.client.post("/ask", json={"task": "audit x"}).status_code, 503)
        with patch.dict(os.environ, {"SAFESTACK_API_KEY": "real-secret"}):
            response = self.client.post("/ask", json={"task": "audit x"}, headers={"X-API-Key": "wrong"})
            self.assertEqual(response.status_code, 401)

    def test_checkpoint_namespace_is_server_generated_and_failure_reaches_client(self):
        def fail_audit(inputs, config):
            self.assertIn("messages", inputs)
            self.assertNotEqual(config["configurable"]["thread_id"], "guessed-thread")
            return ([{"agent": "LOCKDOWN"}], {"current_state": "LOCKDOWN", "trust_level": "UNTRUSTED"})
        with patch.dict(os.environ, {"SAFESTACK_API_KEY": "real-secret"}), \
             patch.object(server, "_stream_audit", side_effect=fail_audit):
            response = self.client.post("/ask", json={"task": "audit x", "thread_id": "guessed-thread"},
                                        headers={"X-API-Key": "real-secret"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "failed")
        self.assertEqual(response.json()["state"], "LOCKDOWN")

    def test_overload_is_rejected_without_waiting(self):
        with patch.dict(os.environ, {"SAFESTACK_API_KEY": "real-secret"}):
            self.assertTrue(server._audit_slot.acquire(blocking=False))
            try:
                response = self.client.post("/ask", json={"task": "audit x"},
                                            headers={"X-API-Key": "real-secret"})
            finally:
                server._audit_slot.release()
        self.assertEqual(response.status_code, 429)


if __name__ == "__main__":
    unittest.main()
