# Operator Guide

## Core Concept
SafeStack is a **containment runtime**. It runs LLM agents in a controlled environment where every output is validated against a strict protocol.

## Execution Modes

### 1. Fallback Mode (Deterministic)
Use this for testing or when LLM access is unavailable. It uses pre-defined security logic.
```bash
python pipeline_controller.py <target_script>
```

### 2. LLM Mode (Ollama)
To use local LLMs (e.g., Llama3), configure the agent command environment variable:
```bash
# Windows PowerShell
$env:SAFESTACK_AGENT_COMMAND = "python llm_adapter_v3.py"
# Linux/macOS
export SAFESTACK_AGENT_COMMAND="python llm_adapter_v3.py"

python pipeline_controller.py <target_script>
```

## Forensic Analysis
After every run, check the `runtime/` directory:
- `runtime/raw/`: Original agent output (untrusted).
- `runtime/valid/`: Successfully validated findings.
- `runtime/invalid/`: Blocked protocol violations.
- `runtime/stderr/`: Diagnostic logs from agents.

## Handling BLOCKED Status
If an agent is blocked, check `runtime/invalid/<AGENT>.invalid.json`. The `reason` field will specify if it was a prose injection, markdown leakage, or schema violation.
