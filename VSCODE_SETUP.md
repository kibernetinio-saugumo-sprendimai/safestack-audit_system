# Getting Started with VS Code

This guide will help you set up the SafeStack Audit core using Visual Studio Code.

## 1. Open the Project
1. Open **Visual Studio Code**.
2. Go to `File` > `Open Folder...`
3. Select the `audit_system` directory.

## 2. Open the Integrated Terminal
You don't need an external terminal.
1. Press `` Ctrl + ` `` (backtick) or go to `Terminal` > `New Terminal`.
2. This will open a terminal window at the bottom of your VS Code.

## 3. Configure Python
1. Ensure the **Python Extension** (by Microsoft) is installed in VS Code.
2. Click on the Python version in the bottom-right corner (or press `Ctrl+Shift+P` and type `Python: Select Interpreter`).
3. Select your Python 3.10+ installation.

## 4. Running the Audit
In the VS Code terminal, simply type:
```powershell
python pipeline_controller.py C:\path\to\your\script.sh
```

## 5. Viewing Forensic Results
The VS Code explorer on the left is the best way to inspect results:
- Open the `runtime/` folder to see raw and valid outputs.
- VS Code will automatically format the `.json` files, making them easy to read.

## 6. Pro Tip: Multi-root Workspace
If you are auditing scripts in a different directory (e.g., `pi5VPN`), you can add that folder to your workspace (`File` > `Add Folder to Workspace...`). This allows you to edit the scripts and run the audit from a single window.
