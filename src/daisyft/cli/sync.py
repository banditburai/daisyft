import typer
from pathlib import Path
from typing import Optional
from ..utils.toml_config import ProjectConfig
import logging
from ..utils.console import console
logger = logging.getLogger(__name__)

def sync_with_config(config: ProjectConfig, force: bool = False) -> None:
    """Internal sync function that works with ProjectConfig object"""
    logger.debug("Starting sync...")
    
    # Ensure directories exist
    for path in config.paths.values():
        path = Path(path)  # Ensure Path object
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {path}")

    # Update CSS
    css_file = Path(config.paths["css"]) / "input.css"
    logger.debug(f"CSS file path: {css_file}")
    
    if not css_file.exists() or force:
        logger.debug("Creating/updating CSS file")
        css_content = [
            "@tailwind base;",
            "@tailwind components;",
            "@tailwind utilities;"
        ]
        css_file.write_text("\n".join(css_content) + "\n")
    
    # Save any changes to the config
    config.save()
    
    logger.debug("Sync completed successfully")
    return True

def sync(
    force: bool = typer.Option(False, "--force", "-f", help="Force sync even if no changes"),
) -> None:
    """Sync project files and rebuild CSS"""
    
    if not Path("daisyft.toml").exists():
        console.print("[red]Error:[/red] Not in a daisyft project.")
        console.print("\nTo create a new project, run:")
        console.print("  [bold]daisyft init[/bold]")
        console.print("\nOr cd into an existing daisyft project directory.")
        raise typer.Exit(1)
    
    config = ProjectConfig.load()
    sync_with_config(config, force) 