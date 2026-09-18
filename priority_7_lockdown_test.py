"""Regression test: unsafe inputs end in a terminal LOCKDOWN state."""
import os
import tempfile
from pathlib import Path

import secure_io
from app import workflow


def test_lockdown_enforcement():
    with tempfile.TemporaryDirectory() as temporary:
        old_runtime = secure_io.RUNTIME_ROOT
        secure_io.RUNTIME_ROOT = Path(temporary).resolve() / "runtime"
        try:
            graph = workflow.compile()
            events = list(graph.stream(
                {"messages": [("user", "audit INVALID_PATH_THAT_DOES_NOT_EXIST")]},
                {"configurable": {"thread_id": "lockdown-test-" + os.urandom(8).hex()}},
            ))
            last_node, result = next(iter(events[-1].items()))
            assert last_node in {"discoverer", "lockdown"}, f"unexpected terminal node: {last_node}"
            assert result.get("current_state") == "LOCKDOWN"
            assert result.get("lifecycle_stage") == "HALTED"
            assert result.get("trust_level") == "UNTRUSTED"
            evidence = secure_io.RUNTIME_ROOT / "LOCKDOWN_FORENSICS.log"
            assert evidence.is_file()
            assert "LOCKDOWN TRIGGERED" in evidence.read_text()
        finally:
            secure_io.RUNTIME_ROOT = old_runtime


if __name__ == "__main__":
    test_lockdown_enforcement()
    print("LOCKDOWN TERMINAL-STATE TEST PASSED")
