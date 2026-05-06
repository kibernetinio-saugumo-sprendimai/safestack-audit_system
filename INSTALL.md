# Installation Guide

## System Requirements
- **OS**: Linux (recommended), macOS, or Windows 10/11 (PowerShell/WSL).
- **Python**: version 3.10 or higher.
- **Git**: for version control.

## Step-by-Step Installation

### 1. Clone the Repository
```bash
git clone https://github.com/<USER>/safestack-audit-core.git
cd safestack-audit-core
```

### 2. Prepare Python Environment (Optional but Recommended)
```bash
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
.\venv\Scripts\activate
```

### 3. Install Dependencies
SafeStack is designed to be lightweight. Most core tools use standard Python libraries.
```bash
pip install requests
```

### 4. Verify Installation
Run the integrity verifier to ensure all governance files are present:
```bash
python runtime_hash_verifier.py
```
If you see `status: pass`, your installation is successful.
