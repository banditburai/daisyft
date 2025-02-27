import typer
from pathlib import Path
from typing import Optional
from ..utils.config import ProjectConfig
from ..utils.toml_config import load_config, save_config
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
        
        # Create CSS content based on style and theme
        if config.style == "daisy":
            # For DaisyUI, include proper theme configuration
            css_content = [
                '@import "tailwindcss";',
                '@plugin "daisyui" {',
                f'  themes: {config.theme} --default;',
                '  logs: false;',
                '}'
            ]
            
            # Add a comment to help users customize themes
            css_content.extend([
                '',
                '/* To customize themes or add more themes, see:',
                ' * https://daisyui.com/docs/themes/',
                ' * ',
                ' * Example:',
                ' * @plugin "daisyui" {',
                ' *   themes: light --default, dark --prefersdark, cupcake, corporate;',
                ' * }',
                ' *',
                ' * Or add a custom theme:',
                ' * @plugin "daisyui/theme" {',
                ' *   name: "mytheme";',
                ' *   --color-primary: #1EA1F1;',
                ' *   --color-secondary: #0070BA;',
                ' * }',
                ' */',
            ])
        else:
            # For vanilla Tailwind, just import Tailwind
            css_content = [
                '@import "tailwindcss";'
            ]
        
        # Write the CSS file
        css_file.write_text("\n".join(css_content) + "\n")
        console.print(f"[green]✓[/green] Updated CSS file at {css_file}")
    
    # Save any changes to the config
    save_config(config)
    
    # Provide helpful information about next steps
    console.print("\n[bold]Project files synced successfully![/bold]")
    console.print("Run [bold]daisyft build[/bold] to rebuild your CSS with the updated settings.")
    
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
    
    config = load_config(Path("daisyft.toml"))
    sync_with_config(config, force) 