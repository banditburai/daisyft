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
    logger.debug("Starting sync...")        
    console.print("[bold]Checking for Tailwind binary updates...[/bold]")
    
    update_available = check_for_binary_update(config)
    
    if update_available or force:
        console.print(f"[yellow]Update available for Tailwind binary.[/yellow]")
        console.print(f"Downloading latest {config.style} binary...")        
        download_tailwind_binary(config, force=True)                
        save_config(config)
        
        console.print("[green]✓[/green] Tailwind binary updated successfully!")
    else:
        console.print("[green]✓[/green] Tailwind binary is up to date.")
    
    logger.debug("Sync completed successfully")
    return True

def sync(
    force: bool = typer.Option(False, "--force", "-f", help="Force download even if no update is available"),
) -> None:
        
    config_path = Path(".daisyft") / "daisyft.toml"
    if not config_path.exists():
        console.print("[red]Error:[/red] daisyft.toml not found. Please run [bold]daisyft init[/bold].")
        raise typer.Exit(1)
    
    config = load_config() # Use default path
    
    sync_with_config(config, force) 