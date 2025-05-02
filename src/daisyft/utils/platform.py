"""
Platform detection and binary naming utilities.
"""
from pathlib import Path
import platform
from typing import Literal, Tuple

PlatformName = Literal["macos", "linux", "windows"]
Architecture = Literal["x64", "arm64"]

def detect_platform() -> Tuple[PlatformName, Architecture]:
    system = platform.system().lower()
    if system == "darwin":
        platform_name: PlatformName = "macos"
    elif system == "linux":
        platform_name = "linux"
    else:
        platform_name = "windows"

    arch = platform.machine().lower()
    if arch in ("arm64", "aarch64"):
        architecture: Architecture = "arm64"
    elif arch in ("x86_64", "amd64"):
        architecture = "x64"
    else:
        architecture = "x64"  # Default to x64 for unknown architectures

    return platform_name, architecture

def get_tailwind_binary_name() -> str:
    platform_name, architecture = detect_platform()
    
    ext = ".exe" if platform_name == "windows" else ""
    
    return f"tailwindcss-{platform_name}-{architecture}{ext}"

def get_tailwind_remote_asset_name(style: str) -> str:
    platform_name, architecture = detect_platform()
    ext = ".exe" if platform_name == "windows" else ""
    
    prefix = "tailwindcss-extra-" if style == "daisy" else "tailwindcss-"
        
    return f"{prefix}{platform_name}-{architecture}{ext}"

def get_bin_dir() -> Path:
    return Path(".daisyft") / "bin" 