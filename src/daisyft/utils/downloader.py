"""
Utilities for downloading Tailwind binaries.
"""
import platform
import requests
from pathlib import Path
from typing import Literal, Optional, Callable
from rich.progress import Progress, BarColumn, DownloadColumn, TimeRemainingColumn, TextColumn
import typer

from .config import ProjectConfig
from .platform import get_bin_dir, get_tailwind_binary_name
from .release_info import TailwindReleaseInfo
from .console import console
from .toml_config import save_config

def check_for_binary_update(config: ProjectConfig) -> bool:
    """
    Check if a newer version of the Tailwind binary is available.
    
    Args:
        config: ProjectConfig object with configuration settings
        
    Returns:
        True if an update is available, False otherwise
    """
    try:
        # Get release info
        release_info = get_release_info(config.style)
        latest_version = release_info.get("tag_name", "unknown")
        
        # If no binary metadata exists, an update is needed
        if not config.binary_metadata:
            console.print("[yellow]No binary metadata found. Download required.[/yellow]")
            return True
            
        # Check if style has changed - but only if previous_style is not None
        # and it's different from the current style
        if (hasattr(config, 'previous_style') and 
            config.previous_style is not None and 
            config.previous_style != config.style):
            console.print(f"[yellow]Style changed from {config.previous_style} to {config.style}.[/yellow]")
            return True
            
        # Compare versions
        current_version = config.binary_metadata.version
        
        # Log the versions for debugging
        console.print(f"Current version: {current_version}")
        console.print(f"Latest version: {latest_version}")
        
        # Simple string comparison (assumes semantic versioning format)
        if current_version != latest_version:
            console.print(f"[yellow]New version available: {latest_version} (current: {current_version})[/yellow]")
            return True
        else:
            console.print(f"[green]Already on latest version: {current_version}[/green]")
            return False
        
    except requests.RequestException:
        # If we can't check, assume no update is needed
        console.print("[yellow]Warning:[/yellow] Could not check for updates. Network issue?")
        return False

def download_tailwind_binary(
    config: ProjectConfig,
    force: bool = False,
    show_progress: bool = True,
    existing_progress = None
) -> Path:
    """
    Unified download handler with version checks and progress control.
    
    Args:
        config: ProjectConfig object with configuration settings
        force: Whether to force download even if already up to date
        show_progress: Whether to show download progress
        existing_progress: An existing Progress object to use instead of creating a new one
        
    Returns:
        Path to the downloaded binary
    """
    try:
        # Remove redundant debug output
        release_info = get_release_info(config.style)
        dest = get_bin_dir() / get_tailwind_binary_name()

        # Version check
        if not force and config.binary_metadata:
            current = config.binary_metadata.version
            latest = release_info.get("tag_name", "unknown")
            
            # Force download if style has changed
            style_changed = False
            if (hasattr(config, 'previous_style') and 
                config.previous_style is not None and 
                config.previous_style != config.style):
                style_changed = True
                force = True
                console.print(f"[yellow]Style changed from {config.previous_style} to {config.style}, downloading new binary...[/yellow]")
            
            if current == latest and not style_changed:
                console.print(f"[green]✓[/green] Already on latest version {latest}")
                return dest
            
            if not force and not typer.confirm(f"Update from {current} to {latest}?"):
                return dest

        # Perform download
        url = f"{TailwindReleaseInfo.get_download_url(config.style)}{dest.name}"
        
        # Only show URL in verbose mode or when no progress bar
        if not existing_progress and not show_progress:
            console.print(f"Downloading from: {url}")
        
        if existing_progress:
            # Use the existing progress bar
            _download_with_existing_progress(url, dest, existing_progress)
        else:
            # Create a new progress bar
            _core_download(url, dest, show_progress)

        # Post-download setup
        if platform.system() != "Windows":
            dest.chmod(0o755)
        
        config.update_binary_metadata(release_info)
        save_config(config)
        return dest

    except requests.RequestException as e:
        dest.unlink(missing_ok=True)
        console.print(f"[red]Download failed:[/red] {e}")
        raise typer.Exit(1) from e

def _core_download(url: str, dest: Path, show_progress: bool) -> None:
    """
    Base download implementation with progress optional.
    
    Args:
        url: URL to download from
        dest: Destination path to save the file
        show_progress: Whether to show download progress
    """
    response = requests.get(url, stream=True, timeout=(3.05, 30))
    response.raise_for_status()

    if show_progress:
        with Progress(
            BarColumn(complete_style="success"),
            TextColumn("[progress.description]{task.description}", style="info"),
            "[progress.percentage]{task.percentage:>3.0f}%",
            DownloadColumn(),
            TimeRemainingColumn(),
            console=console,
            refresh_per_second=30,
        ) as progress:
            task = progress.add_task("Downloading", total=int(response.headers.get("content-length", 0)))
            _write_content(response, dest, lambda len: progress.update(task, advance=len))
    else:
        _write_content(response, dest)

def _write_content(response: requests.Response, dest: Path, callback: Optional[Callable[[int], None]] = None) -> None:
    """
    Stream response to file with optional progress callback.
    
    Args:
        response: HTTP response object
        dest: Destination path to save the file
        callback: Optional callback function to report progress
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            if callback:
                callback(len(chunk))

def get_release_info(style: str = "daisy") -> dict:
    """
    Fetch GitHub release info with timeout.
    
    Args:
        style: Either "daisy" or "vanilla" to determine which repository to use
        
    Returns:
        Dictionary with release information
    """
    url = TailwindReleaseInfo.get_api_url(style)
    
    try:
        response = requests.get(url, timeout=(3.05, 30))
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        console.print(f"[red]Failed to fetch release info:[/red] {e}")
        raise typer.Exit(1) from e

def download_binary(style: Literal["daisy", "vanilla"]) -> Path:
    """
    Download platform-specific Tailwind binary.
    
    Args:
        style: Either "daisy" or "vanilla" to determine which repository to use
        
    Returns:
        Path to the downloaded binary
    """
    # Get binary name
    binary_name = get_tailwind_binary_name()
    
    # Final destination path
    dest = get_bin_dir() / binary_name
    
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
    if platform.system().lower() != "windows":
        dest.chmod(0o755)
    
    console.print(f"  Binary installed at: [green]{dest}[/green]")
    
    # Return absolute path
    return dest.absolute()

def _download_with_existing_progress(url: str, dest: Path, progress: Progress) -> None:
    """
    Download with an existing progress object.
    
    Args:
        url: URL to download from
        dest: Destination path to save the file
        progress: Existing Progress object
    """
    response = requests.get(url, stream=True, timeout=(3.05, 30))
    response.raise_for_status()
    
    # Create a task in the existing progress - but with a more specific message
    # that doesn't duplicate the parent message
    task = progress.add_task("Fetching file...", total=int(response.headers.get("content-length", 0)))
    
    # Stream the content
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            progress.update(task, advance=len(chunk)) 