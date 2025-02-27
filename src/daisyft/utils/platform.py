"""
Platform detection and binary naming utilities.
"""
from pathlib import Path
import platform
import sys
import sysconfig
from typing import Literal, Tuple

# Type definitions
PlatformName = Literal["macos", "linux", "windows"]
Architecture = Literal["x64", "arm64"]

def detect_platform() -> Tuple[PlatformName, Architecture]:
    """
    Detect current platform and architecture in a normalized way.
    
    Returns:
        Tuple containing (platform_name, architecture)
    """
    # Platform detection
    system = platform.system().lower()
    if system == "darwin":
        platform_name: PlatformName = "macos"
    elif system == "linux":
        platform_name = "linux"
    else:
        platform_name = "windows"

    # Architecture detection
    arch = platform.machine().lower()
    if arch in ("arm64", "aarch64"):
        architecture: Architecture = "arm64"
    elif arch in ("x86_64", "amd64"):
        architecture = "x64"
    else:
        architecture = "x64"  # Default to x64 for unknown architectures

    return platform_name, architecture

def get_tailwind_binary_name() -> str:
    """
    Get the platform-specific Tailwind binary name.
    
    Returns:
        String with the appropriate binary name for the current platform
    """
    platform_name, architecture = detect_platform()
    
    # Determine file extension
    ext = ".exe" if platform_name == "windows" else ""
    
    return f"tailwindcss-{platform_name}-{architecture}{ext}"

def get_bin_dir() -> Path:
    """
    Get platform-appropriate binary directory with venv awareness.
    
    Returns:
        Path to the appropriate binary directory
    """
    # Try to use sysconfig first (respects virtual environments)
    if scripts_path := sysconfig.get_path("scripts"):
        return Path(scripts_path)
    
    # Fallback for non-standard environments
    system = platform.system().lower()
    return Path(sys.prefix) / ("Scripts" if system == "windows" else "bin") 