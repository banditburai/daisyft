"""
Utilities for downloading Tailwind binaries.
"""
import platform
import requests
from pathlib import Path
from typing import Optional, Callable
from rich.progress import Progress, BarColumn, DownloadColumn, TimeRemainingColumn, TextColumn
import typer

from .config import ProjectConfig
from .platform import get_bin_dir, get_tailwind_binary_name, get_tailwind_remote_asset_name
from .release_info import TailwindReleaseInfo
from .console import console
from .toml_config import save_config

def check_for_binary_update(config: ProjectConfig) -> bool:    
    try:        
        release_info = get_release_info(config.style)
        latest_version = release_info.get("tag_name", "unknown")
                
        if not config.binary_metadata:
            console.print("[yellow]No binary metadata found. Download required.[/yellow]")
            return True
            
        if (hasattr(config, 'previous_style') and 
            config.previous_style is not None and 
            config.previous_style != config.style):
            console.print(f"[yellow]Style changed from {config.previous_style} to {config.style}.[/yellow]")
            return True
                    
        current_version = config.binary_metadata.version
                
        if current_version != latest_version:
            console.print(f"[yellow]New version available: {latest_version} (current: {current_version})[/yellow]")
            return True
        else:
            console.print(f"[green]Already on latest version: {current_version}[/green]")
            return False
        
    except requests.RequestException:        
        console.print("[yellow]Warning:[/yellow] Could not check for updates. Network issue?")
        return False

def download_tailwind_binary(
    config: ProjectConfig,
    force: bool = False,
    show_progress: bool = True
) -> Path:
    try:            
        release_info = get_release_info(config.style)
        dest = get_bin_dir() / get_tailwind_binary_name()

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

        remote_asset_name = get_tailwind_remote_asset_name(config.style)
        url = f"{TailwindReleaseInfo.get_download_url(config.style)}{remote_asset_name}"
        
        if not show_progress:
            console.print(f"Downloading from: {url}")
        
        _core_download(url, dest, show_progress)

        if platform.system() != "Windows":
            dest.chmod(0o755)
        
        config.update_binary_metadata(release_info)
        save_config(config)
        return dest

    except requests.RequestException as e:
        console.print(f"[red]Download request failed:[/red] {e}")
        raise typer.Exit(1) from e
    except IOError as e:
        console.print(f"[red]Failed to save or finalize downloaded file:[/red] {e}")
        raise typer.Exit(1) from e
    except Exception as e:        
        console.print(f"[red]An unexpected error occurred during binary download:[/red] {e}")
        dest = get_bin_dir() / get_tailwind_binary_name()
        dest.unlink(missing_ok=True)
        temp_dest = dest.with_suffix(dest.suffix + ".tmp")
        temp_dest.unlink(missing_ok=True)
        raise typer.Exit(1) from e

def _core_download(url: str, dest: Path, show_progress: bool) -> None:
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
    temp_dest = dest.with_suffix(dest.suffix + ".tmp")
    
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    download_successful = False
    try:
        with temp_dest.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk: # Handle potential empty chunks
                    continue
                f.write(chunk)
                if callback:
                    callback(len(chunk))
        download_successful = True
        
    except Exception as e:
        console.print(f"[red]Error during download write:[/red] {e}")
        download_successful = False
        raise

    finally:
        if download_successful:
            try:
                if platform.system() == "Windows" and dest.exists():
                    dest.unlink() # Explicitly remove destination on Windows first
                temp_dest.rename(dest)
            except OSError as e:
                console.print(f"[red]Error renaming temporary file {temp_dest} to {dest}:[/red] {e}")
                temp_dest.unlink(missing_ok=True)
                raise IOError(f"Failed to finalize downloaded file: {e}") from e
        else:
            temp_dest.unlink(missing_ok=True)

def get_release_info(style: str = "daisy") -> dict:
    url = TailwindReleaseInfo.get_api_url(style)
    
    try:
        response = requests.get(url, timeout=(3.05, 30))
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        console.print(f"[red]Failed to fetch release info:[/red] {e}")
        raise typer.Exit(1) from e