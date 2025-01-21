import subprocess
from pathlib import Path
from typing import Optional, List
import shutil
import os

class PackageManager:
    """Handle different Python package managers"""
    
    @staticmethod
    def detect() -> str:
        """Detect which package manager is being used"""
        # Check for uv
        if (Path("requirements.txt").exists() and Path(".uv").exists()) or \
           (Path("pyproject.toml").exists() and Path(".uv").exists()):
            return "uv"
        
        # Check for Poetry (look for poetry.lock and poetry section in pyproject.toml)
        if Path("poetry.lock").exists() or \
           (Path("pyproject.toml").exists() and "[tool.poetry]" in Path("pyproject.toml").read_text()):
            return "poetry"
        
        # Check for Conda
        if Path("environment.yml").exists() or \
           (shutil.which("conda") and "CONDA_PREFIX" in os.environ):
            return "conda"
        
        # Check for pip-tools
        if Path("requirements.in").exists() or \
           (Path("requirements.txt").exists() and "# via pip-compile" in Path("requirements.txt").read_text()):
            return "pip-compile"
            
        # Default to pip
        return "pip"
    
    @staticmethod
    def install_command(package: str, manager: Optional[str] = None) -> List[str]:
        """Get the appropriate install command for the package manager"""
        manager = manager or PackageManager.detect()
        
        commands = {
            "poetry": ["poetry", "add"],
            "conda": ["conda", "install", "-c", "conda-forge"],
            "uv": ["uv", "pip", "install"],
            "pip": ["pip", "install"]
        }
        
        return commands.get(manager, commands["pip"]) + [package]

    @staticmethod
    def install(package: str, manager: Optional[str] = None) -> subprocess.CompletedProcess:
        """Install a package using the appropriate package manager"""
        cmd = PackageManager.install_command(package, manager)
        return subprocess.run(cmd, check=True, capture_output=True, text=True) 