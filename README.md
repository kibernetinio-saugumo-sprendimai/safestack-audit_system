# SafeStack Audit Governance Kernel

[![Version](https://img.shields.io/badge/version-1.0.0--lockdown-blue.svg)](https://github.com/SafeStack)
[![Mode](https://img.shields.io/badge/mode-deterministic-red.svg)](https://github.com/SafeStack)
[![Governance](https://img.shields.io/badge/governance-strict-black.svg)](https://github.com/SafeStack)

## Overview

The **SafeStack Audit Governance Kernel** is a production-grade, deterministic framework for autonomous security auditing. Unlike traditional AI wrappers, SafeStack implements a strict **Execution Governance** layer that isolates, validates, and enforces protocols on LLM outputs before they enter the trust chain.

## Documentation

To get the most out of SafeStack, please refer to the following guides:

- **[Installation Guide](INSTALL.md)**: Detailed technical setup instructions.
- **[Operator Guide](GUIDE.md)**: How to run audits and analyze forensic results.
- **[VS Code Setup](VSCODE_SETUP.md)**: Beginner-friendly guide for Visual Studio Code users.

## Key Features

- **Hardened V2 Runtime**: Strict separation of concern (Stdout for data, Stderr for diagnostics).
- **Agent Containment (V3)**: Brutal conditioning of LLM agents via role suppression and token limits.
- **Zero-Trust Validation**: Every agent output must pass through `strict_mode.py` and `json_repair_guard.py`.
- **Forensics First**: Automated capture of raw outputs, invalid records, and execution paths for audit reconstruction.
- **Deterministic Fallback**: Built-in logic for consistent auditing even without active LLM providers.

## Getting Started

### Prerequisites
- Python 3.10+
- Ollama (optional, for LLM-powered auditing)

### Installation
```bash
git clone https://github.com/<USER>/safestack-audit-core.git
cd safestack-audit-core
```

### Running an Audit
To execute a full hardened audit on a target script:
```bash
python pipeline_controller.py /path/to/target_script.sh
```

## Security & Compliance

SafeStack operates in **FAIL-CLOSED** mode. Any protocol violation, prose injection, or markdown leakage results in immediate pipeline termination with a `BLOCKED` status.

---
**SafeStack: Dehumanizing AI for High-Integrity Infrastructure.**
