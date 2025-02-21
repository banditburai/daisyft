import sysconfig
from pathlib import Path
import platform
import sys

def get_bin_dir() -> Path:
    """Get platform-appropriate binary directory with venv awareness"""
    # Try to use sysconfig first (respects virtual environments)
    if scripts_path := sysconfig.get_path("scripts"):
        return Path(scripts_path)
    
    # Fallback for non-standard environments
    system = platform.system().lower()
    return Path(sys.prefix) / ("Scripts" if system == "windows" else "bin") 