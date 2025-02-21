import subprocess
from pathlib import Path
from typing import Optional, List
import os
from ..utils.console import console
import re

class PackageManager:
    """Handle different Python package managers"""
    
    @staticmethod
    def detect() -> str:
        """Detect package manager with priority sorting and validation"""
        checks = [
            # Highest priority first
            ("uv", lambda: (
                Path(".uv").exists() and 
                (Path("requirements.txt").exists() or Path("pyproject.toml").exists())
            )),
            ("poetry", lambda: (
                Path("poetry.lock").exists() and 
                "[tool.poetry]" in Path("pyproject.toml").read_text()
            )),
            ("conda", lambda: (
                Path(os.environ.get("CONDA_PREFIX", "")).joinpath("conda-meta").exists() and 
                (Path("environment.yml").exists() or Path("conda-lock.yml").exists())
            )),
            ("pip-compile", lambda: (
                Path("requirements.in").exists() or
                (Path("requirements.txt").exists() and 
                 any(re.match(r"^#.*pip-compile", line) for line in open("requirements.txt")))
            )),
            ("pip", lambda: True)  # Final fallback
        ]
        
        for name, check in checks:
            if check():
                console.print(f"  Detected package manager: [bold]{name}[/bold]", style="info")
                return name
        return "pip"  # Ultimate fallback
    
    @staticmethod
    def install_command(package: str, manager: Optional[str] = None) -> List[str]:
        manager = manager or PackageManager.detect()
        
        commands = {
            "poetry": ["poetry", "add", "--lock"],
            "conda": ["conda", "install", "-c", "conda-forge", "--yes"],
            "uv": ["uv", "pip", "install", "--quiet"],
            "pip": ["pip", "install", "--quiet"],
            "pip-compile": ["pip-compile", "--quiet", "requirements.in"]
        }
        
        # Handle VCS URLs differently for some managers
        if any(s in package for s in ("@git+", "@http", "@svn+")):
            if manager == "poetry":
                return ["poetry", "add", package]
            if manager == "conda":
                console.print("[yellow]Conda doesn't support direct VCS installs[/yellow]")
                return ["pip", "install", package]
        
        return commands.get(manager, commands["pip"]) + [package]

    @staticmethod
    def install(package: str, manager: Optional[str] = None) -> subprocess.CompletedProcess:
        manager = manager or PackageManager.detect()
        cmd = PackageManager.install_command(package, manager)
        console.print(f"  Installing with [bold]{manager}[/bold]: {package}", style="info")
        try:
            return subprocess.run(
                cmd, 
                check=True,
                capture_output=True,
                text=True,
                env={**os.environ, "PIP_PROGRESS_BAR": "off"}  # Quieter output
            )
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Install failed with {manager}:[/red] {e.stderr}")
            # Fallback to pip if manager-specific install failed
            if manager != "pip":
                console.print("[yellow]Attempting fallback to pip...[/yellow]")
                return PackageManager.install(package, "pip")
            raise 
