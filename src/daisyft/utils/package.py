"""
Package manager utilities for cross-environment dependency management.
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union, Any
from ..utils.console import console

class PackageManager:
    """
    Unified package manager interface that works across different Python
    package management tools (pip, poetry, conda, etc.)
    """
    
    # Configuration for supported package managers
    MANAGERS = {
        "pip": {
            "install_cmd": ["pip", "install"],
            "uninstall_cmd": ["pip", "uninstall", "-y"],
            "detection_cmd": ["pip", "--version"],
            "dev_flag": None,  # pip doesn't have a dev dependency concept
            "priority": 1,  # Default fallback
        },
        "poetry": {
            "install_cmd": ["poetry", "add"],
            "uninstall_cmd": ["poetry", "remove"],
            "detection_cmd": ["poetry", "--version"],
            "dev_flag": "--group=dev",
            "priority": 2,  # Preferred if available
        },
        "conda": {
            "install_cmd": ["conda", "install", "-y"],
            "uninstall_cmd": ["conda", "remove", "-y"],
            "detection_cmd": ["conda", "--version"],
            "dev_flag": None,
            "priority": 1,
        },
        "pipenv": {
            "install_cmd": ["pipenv", "install"],
            "uninstall_cmd": ["pipenv", "uninstall"],
            "detection_cmd": ["pipenv", "--version"],
            "dev_flag": "--dev",
            "priority": 2,
        },
        "pdm": {
            "install_cmd": ["pdm", "add"],
            "uninstall_cmd": ["pdm", "remove"],
            "detection_cmd": ["pdm", "--version"],
            "dev_flag": "-d",
            "priority": 2,
        },
        "uv": {
            "install_cmd": ["uv", "pip", "install"],
            "uninstall_cmd": ["uv", "pip", "uninstall", "-y"],
            "detection_cmd": ["uv", "--version"],
            "dev_flag": None,
            "priority": 3,  # Highest priority if available (it's fast!)
        },
    }
    
    @classmethod
    def detect(cls, specified: Optional[str] = None) -> str:
        """
        Detect which package manager to use.
        
        Args:
            specified: Explicitly specified package manager name
            
        Returns:
            Name of the package manager to use
            
        Raises:
            RuntimeError: If no suitable package manager is found
        """
        # Use specified manager if available
        if specified:
            if specified not in cls.MANAGERS:
                raise ValueError(f"Unsupported package manager: {specified}")
                
            if cls._check_manager_available(specified):
                return specified
            else:
                console.print(f"[yellow]Warning:[/yellow] Specified package manager '{specified}' not found.")
        
        # Auto-detection based on environment and project files
        available_managers = cls._get_available_managers()
        if not available_managers:
            raise RuntimeError("No supported package managers found. Please install pip or another supported package manager.")
        
        # First check for active environments
        if os.environ.get("POETRY_ACTIVE"):
            if "poetry" in available_managers:
                return "poetry"
        
        if os.environ.get("CONDA_PREFIX"):
            if "conda" in available_managers:
                return "conda"
        
        if os.environ.get("VIRTUAL_ENV"):
            # Standard venv - prefer uv > pip
            if "uv" in available_managers:
                return "uv"
            if "pip" in available_managers:
                return "pip"
        
        # Then check for project files
        if Path("pyproject.toml").exists():
            content = Path("pyproject.toml").read_text()
            if "tool.poetry" in content and "poetry" in available_managers:
                return "poetry"
            if "tool.pdm" in content and "pdm" in available_managers:
                return "pdm"
        
        if Path("poetry.lock").exists() and "poetry" in available_managers:
            return "poetry"
            
        if Path("Pipfile").exists() and "pipenv" in available_managers:
            return "pipenv"
            
        if Path("pdm.lock").exists() and "pdm" in available_managers:
            return "pdm"
        
        # Sort by priority and return the highest priority available manager
        by_priority = sorted(
            available_managers, 
            key=lambda m: cls.MANAGERS[m]["priority"], 
            reverse=True
        )
        return by_priority[0]
    
    @classmethod
    def _get_available_managers(cls) -> List[str]:
        """Get a list of available package managers."""
        return [
            manager for manager in cls.MANAGERS 
            if cls._check_manager_available(manager)
        ]
    
    @classmethod
    def _check_manager_available(cls, manager: str) -> bool:
        """Check if a package manager is available on the system."""
        try:
            subprocess.run(
                cls.MANAGERS[manager]["detection_cmd"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    @classmethod
    def install(
        cls, 
        package: str, 
        manager: Optional[str] = None, 
        dev: bool = False,
        upgrade: bool = False,
        quiet: bool = False,
        fallback: bool = True
    ) -> bool:
        """
        Install a package using the specified or detected package manager.
        
        Args:
            package: Package name or URL to install
            manager: Specific package manager to use (auto-detected if None)
            dev: Whether to install as a development dependency
            upgrade: Whether to upgrade the package if already installed
            quiet: Whether to suppress output
            fallback: Whether to try alternative package managers if the first fails
            
        Returns:
            True if installation succeeded, False otherwise
        """
        try:
            # Get the package manager to use
            manager_name = cls.detect(manager)
            
            # Build the command
            cmd = list(cls.MANAGERS[manager_name]["install_cmd"])
            
            # Add dev flag if supported and requested
            if dev and cls.MANAGERS[manager_name]["dev_flag"]:
                cmd.append(cls.MANAGERS[manager_name]["dev_flag"])
            
            # Add upgrade flag if supported and requested
            if upgrade:
                if manager_name == "pip":
                    cmd.append("--upgrade")
                elif manager_name == "poetry":
                    cmd.append("--latest")
                elif manager_name == "uv":
                    cmd.append("--upgrade")
            
            # Add the package
            cmd.append(package)
            
            # Run the command
            if not quiet:
                console.print(f"Installing {package} with {manager_name}...")
                
            result = cls._run_command(cmd, quiet=quiet)
            
            if result:
                if not quiet:
                    console.print(f"[green]✓[/green] Successfully installed {package}")
                return True
            
            # If installation failed and fallback is enabled, try other managers
            if fallback:
                available_managers = cls._get_available_managers()
                for fallback_manager in available_managers:
                    if fallback_manager == manager_name:
                        continue  # Skip the one we already tried
                        
                    if not quiet:
                        console.print(f"Trying fallback installation with {fallback_manager}...")
                        
                    cmd = list(cls.MANAGERS[fallback_manager]["install_cmd"])
                    if dev and cls.MANAGERS[fallback_manager]["dev_flag"]:
                        cmd.append(cls.MANAGERS[fallback_manager]["dev_flag"])
                    if upgrade:
                        if fallback_manager == "pip":
                            cmd.append("--upgrade")
                        elif fallback_manager == "poetry":
                            cmd.append("--latest")
                        elif fallback_manager == "uv":
                            cmd.append("--upgrade")
                    cmd.append(package)
                    
                    result = cls._run_command(cmd, quiet=quiet)
                    if result:
                        if not quiet:
                            console.print(f"[green]✓[/green] Successfully installed {package} with {fallback_manager}")
                        return True
            
            # If we get here, all installation attempts failed
            cls._show_installation_instructions(package, dev)
            return False
            
        except Exception as e:
            console.print(f"[red]Error installing package:[/red] {str(e)}")
            cls._show_installation_instructions(package, dev)
            return False
    
    @classmethod
    def uninstall(
        cls, 
        package: str, 
        manager: Optional[str] = None,
        quiet: bool = False
    ) -> bool:
        """
        Uninstall a package using the specified or detected package manager.
        
        Args:
            package: Package name to uninstall
            manager: Specific package manager to use (auto-detected if None)
            quiet: Whether to suppress output
            
        Returns:
            True if uninstallation succeeded, False otherwise
        """
        try:
            manager_name = cls.detect(manager)
            cmd = list(cls.MANAGERS[manager_name]["uninstall_cmd"])
            cmd.append(package)
            
            if not quiet:
                console.print(f"Uninstalling {package} with {manager_name}...")
                
            result = cls._run_command(cmd, quiet=quiet)
            
            if result:
                if not quiet:
                    console.print(f"[green]✓[/green] Successfully uninstalled {package}")
                return True
            
            return False
            
        except Exception as e:
            console.print(f"[red]Error uninstalling package:[/red] {str(e)}")
            return False
    
    @classmethod
    def _run_command(cls, cmd: List[str], quiet: bool = False) -> bool:
        """Run a command and handle errors."""
        try:
            if quiet:
                # Suppress output
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
            else:
                # Show output
                result = subprocess.run(
                    cmd,
                    text=True,
                    check=False
                )
            
            if result.returncode != 0:
                if not quiet:
                    console.print(f"[red]Command failed:[/red] {' '.join(cmd)}")
                    if result.stderr:
                        console.print(f"[red]Error:[/red] {result.stderr}")
                return False
            
            return True
            
        except FileNotFoundError:
            if not quiet:
                console.print(f"[red]Command not found:[/red] {cmd[0]}")
            return False
            
        except Exception as e:
            if not quiet:
                console.print(f"[red]Error executing command:[/red] {str(e)}")
            return False
    
    @classmethod
    def _show_installation_instructions(cls, package: str, dev: bool = False) -> None:
        """Show manual installation instructions for different package managers."""
        console.print("\n[bold yellow]Installation failed. Please install manually:[/bold yellow]")
        
        for manager, config in cls.MANAGERS.items():
            cmd_parts = list(config["install_cmd"])
            if dev and config["dev_flag"]:
                cmd_parts.append(config["dev_flag"])
            cmd_parts.append(package)
            
            console.print(f"[bold]{manager}:[/bold] {' '.join(cmd_parts)}")
        
        console.print("\nAfter installing, run your daisyft command again.")

# Simplified interface for backward compatibility
def install(package: str, manager: Optional[str] = None, **kwargs) -> bool:
    """Install a package using the PackageManager class."""
    return PackageManager.install(package, manager, **kwargs)

def uninstall(package: str, manager: Optional[str] = None, **kwargs) -> bool:
    """Uninstall a package using the PackageManager class."""
    return PackageManager.uninstall(package, manager, **kwargs)

def detect_manager(specified: Optional[str] = None) -> str:
    """Detect which package manager to use."""
    return PackageManager.detect(specified)
