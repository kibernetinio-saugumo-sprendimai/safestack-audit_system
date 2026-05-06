import os
from pathlib import Path

PROTECTED_ZONES = [
    "governance/",
    "strict_mode.py",
    "app.py",
    "quarantine_engine.py",
    "canonical_serializer.py",
    "path_guard.py",
    "server.py"
]

def is_protected(file_path: str) -> bool:
    """Checks if the target file path is in a protected zone."""
    abs_target = Path(file_path).resolve()
    
    # Root of the project for resolve context
    project_root = Path(".").resolve()
    
    try:
        relative_target = abs_target.relative_to(project_root)
    except ValueError:
        # Outside project root is also forbidden for agents
        return True

    path_str = str(relative_target).replace("\\", "/")
    
    for zone in PROTECTED_ZONES:
        if path_str.startswith(zone) or path_str == zone.rstrip("/"):
            return True
            
    return False

def validate_write_attempt(target_file: str):
    """Hard enforcement for write attempts."""
    if is_protected(target_file):
        raise PermissionError(f"IMMUTABILITY VIOLATION: Attempted to write to protected zone: {target_file}")
    return True
