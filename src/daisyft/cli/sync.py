import typer
from pathlib import Path
from typing import Optional
from ..utils.config import ProjectConfig
from ..utils.toml_config import load_config, save_config
from ..utils.downloader import download_tailwind_binary, check_for_binary_update
import logging
from ..utils.console import console
logger = logging.getLogger(__name__)

def sync_with_config(config: ProjectConfig, force: bool = False) -> None:
    """Internal sync function that works with ProjectConfig object
    
    Checks for updates to the Tailwind binary and downloads if available.
    """
    logger.debug("Starting sync...")
    
    # Check for binary updates
    console.print("[bold]Checking for Tailwind binary updates...[/bold]")
    
    update_available = check_for_binary_update(config)
    
    if update_available or force:
        console.print(f"[yellow]Update available for Tailwind binary.[/yellow]")
        console.print(f"Downloading latest {config.style} binary...")
        
        # Download the latest binary
        download_tailwind_binary(config, force=True)
        
        # Save config with updated binary metadata
        save_config(config)
        
        console.print("[green]✓[/green] Tailwind binary updated successfully!")
    else:
        console.print("[green]✓[/green] Tailwind binary is up to date.")
    
    logger.debug("Sync completed successfully")
    return True

def sync(
    force: bool = typer.Option(False, "--force", "-f", help="Force download even if no update is available"),
) -> None:
    """Sync Tailwind binary with the latest version
    
    This command checks for updates to the Tailwind binary and downloads
    the latest version if available.
    """
    
    if not Path("daisyft.toml").exists():
        console.print("[red]Error:[/red] Not in a daisyft project.")
        console.print("\nTo create a new project, run:")
        console.print("  [bold]daisyft init[/bold]")
        console.print("\nOr cd into an existing daisyft project directory.")
        raise typer.Exit(1)
    
    config = load_config(Path("daisyft.toml"))
    sync_with_config(config, force) 