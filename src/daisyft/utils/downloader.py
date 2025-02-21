from __future__ import annotations
import platform
import requests
from pathlib import Path
from typing import Literal, Optional
from rich.progress import Progress, BarColumn, DownloadColumn, TimeRemainingColumn
from .config import TailwindReleaseInfo, ProjectConfig
from .console import console
from .paths import get_bin_dir
import typer
import sys

def download_tailwind_binary(
    config: ProjectConfig,
    force: bool = False,
    show_progress: bool = True
) -> Path:
    """Unified download handler with version checks and progress control"""
    try:
        release_info = get_release_info(config.style)
        dest = get_bin_dir() / ProjectConfig.get_tailwind_binary_name()

        # Version check
        if not force and config.binary_metadata:
            current = config.binary_metadata.version
            latest = release_info.get("tag_name", "unknown")
            
            if current == latest:
                console.print(f"[green]✓[/green] Already on latest version {latest}")
                return dest
            
            if not typer.confirm(f"Update from {current} to {latest}?"):
                return dest

        # Perform download
        url = f"{TailwindReleaseInfo.get_download_url(config.style)}{dest.name}"
        _core_download(url, dest, show_progress)

        # Post-download setup
        if platform.system() != "Windows":
            dest.chmod(0o755)
        
        config.update_binary_metadata(release_info)
        console.print(f"[green]✓[/green] Installed {dest.name} to {dest}")
        return dest

    except requests.RequestException as e:
        dest.unlink(missing_ok=True)
        console.print(f"[red]Download failed:[/red] {e}")
        raise typer.Exit(1) from e

def _core_download(url: str, dest: Path, show_progress: bool) -> None:
    """Base download implementation with progress optional"""
    response = requests.get(url, stream=True, timeout=(3.05, 30))
    response.raise_for_status()

    if show_progress:
        with Progress(
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            DownloadColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Downloading", total=int(response.headers.get("content-length", 0)))
            _write_content(response, dest, lambda len: progress.update(task, advance=len))
    else:
        _write_content(response, dest)

def _write_content(response: requests.Response, dest: Path, callback: Optional[callable] = None) -> None:
    """Stream response to file with optional progress callback"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            if callback:
                callback(len(chunk))

def get_release_info(style: str = "daisy") -> dict:
    """Fetch GitHub release info with timeout"""
    url = TailwindReleaseInfo.get_api_url(style)
    try:
        response = requests.get(url, timeout=(3.05, 30))
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        console.print(f"[red]Failed to fetch release info:[/red] {e}")
        raise typer.Exit(1) from e

def download_binary(style: Literal["daisy", "vanilla"]) -> Path:
    """Download platform-specific Tailwind binary using project config"""
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    # Get binary name from existing project logic
    binary_name = ProjectConfig.get_tailwind_binary_name()
    
    # Final destination path
    dest = Path(sys.prefix) / ("Scripts" if system == "windows" else "bin") / binary_name
    
    console.print(f"  Downloading binary to: [cyan]{dest}[/cyan]")
    
    # Use the project's URL construction
    base_url = TailwindReleaseInfo.get_download_url(style)
    url = f"{base_url}{binary_name}"
    
    # Existing download logic
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    # Direct download without temp file renaming
    with open(dest, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    # Set executable permissions
    if system != "windows":
        dest.chmod(0o755)
    
    console.print(f"  Binary installed at: [green]{dest}[/green]")
    
    # Return absolute path
    return dest.absolute() 