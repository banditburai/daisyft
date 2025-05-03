from pathlib import Path
from typing import Optional, Dict, Any, List
import questionary
import typer
from jinja2 import TemplateError
from rich.progress import Progress, SpinnerColumn, TextColumn
from ..utils.config import InitOptions
from ..utils.toml_config import load_config, save_config
from ..utils.console import console
from ..utils.downloader import download_tailwind_binary
from ..utils.template import render_template, TemplateContext
from ..utils.platform import get_tailwind_binary_name, get_bin_dir

# Simplified question handlers with progressive disclosure
def handle_basic_options(answers: Dict[str, Any]) -> None:
    """Handle the basic, most important configuration options"""
    # Define style choices
    style_choices = [
        {"value": "daisy", "name": "DaisyUI components (recommended)"},
        {"value": "vanilla", "name": "Vanilla Tailwind CSS"}
    ]
    
    # Find default choice
    default_choice = 0
    for i, choice in enumerate(style_choices):
        if choice["value"] == answers["style"]:
            default_choice = i
            break
    
    selected = questionary.select(
        "Style framework:",
        choices=style_choices,
        default=style_choices[default_choice]
    ).ask()
    
    # Update the style
    answers["style"] = selected
    
    if answers["style"] == "daisy":        
        theme_choices = [
            {"value": "dark", "name": "Dark mode (default)"},
            {"value": "light", "name": "Light mode"}
        ]
        
        # Find default choice
        default_choice = 0
        for i, choice in enumerate(theme_choices):
            if choice["value"] == answers["theme"]:
                default_choice = i
                break
                
        selected_theme = questionary.select(
            "Theme:",
            choices=theme_choices,
            default=theme_choices[default_choice]
        ).ask()
                
        answers["theme"] = selected_theme
    else:
        answers["theme"] = "default"

def handle_advanced_options(answers: Dict[str, Any]) -> None:
    """Handle more advanced configuration options"""
    answers["app_path"] = questionary.text(
        "FastHTML app entry point:", 
        default=answers["app_path"]
    ).ask()
    
    answers["static_dir"] = questionary.text(
        "Static assets directory:", 
        default=answers["static_dir"]
    ).ask()

def get_user_options(defaults: bool = False) -> InitOptions:
    """Get project options through interactive prompts or defaults
    
    Args:
        defaults: Use default values without prompting
    """
    if defaults:
        return InitOptions()

    console.print("\n[bold blue]DaisyFT Project Setup[/bold blue]")
    
    # Start with default answers
    answers = {
        "style": "daisy",
        "theme": "dark",
        "app_path": "main.py",
        "static_dir": "static",
    }

    try:
        handle_basic_options(answers)
        handle_advanced_options(answers)

        return InitOptions(
            style=answers["style"],
            theme=answers["theme"],
            app_path=Path(answers["app_path"]),
            static_dir=Path(answers["static_dir"]),
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Initialization cancelled[/yellow]")
        raise typer.Exit(1)

def safe_create_directories(path: Path) -> None:
    """Create directories safely with proper error handling"""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        console.print(f"[red]Error creating directory {path}:[/red] {e}")
        raise typer.Exit(1)

def render_template_safe(template_name: str, output_path: Path, context: TemplateContext) -> None:
    """Render a template with proper error handling"""
    try:
        render_template(template_name, output_path, context)
    except (TemplateError, OSError) as e:
        console.print(f"[red]Error rendering {template_name}:[/red] {e}")
        raise typer.Exit(1)

def init(
    path: str = typer.Option(".", help="Project path"),
    defaults: bool = typer.Option(False, "--defaults", "-d", help="Use default settings without prompting"),
    force: bool = typer.Option(False, "--force", "-f", help="Force download new Tailwind binary"),
    binaries: bool = typer.Option(False, "--binaries", "-b", help="Download Tailwind binaries only without modifying project files")
) -> None:
    """Initialize a new DaisyFT project
    
    This command sets up a new project with Tailwind CSS and FastHTML integration.
    It creates the necessary directory structure, configuration files, and downloads
    the Tailwind CSS binary.
    
    Examples:
        daisyft init                # Interactive setup
        daisyft init --defaults     # Use default settings without prompting
        daisyft init --binaries     # Download Tailwind binaries only without modifying project files
    """
    project_path = Path(path).absolute()
    daisyft_dir = project_path / ".daisyft"
    config_path = daisyft_dir / "daisyft.toml"

    try:
        project_path.mkdir(parents=True, exist_ok=True)
        daisyft_dir.mkdir(exist_ok=True)
        
        config = load_config()
        config_exists = config.is_initialized

        if config_exists and not force and not binaries:
            console.print("[yellow]Project already initialized.[/yellow]")
            if not typer.confirm(
                "Do you want to reinitialize?",
                default=False
            ):
                console.print("[yellow]Initialization cancelled.[/yellow]")
                return
        
        if not defaults or not config_exists:
            previous_style = config.style if config_exists else None            
            options = get_user_options(defaults=defaults)            
            config.update_from_options(options)
            
            if previous_style:
                config.previous_style = previous_style
                
        binary_type = "DaisyUI-enhanced Tailwind CSS" if config.style == "daisy" else "Vanilla Tailwind CSS"
        
        # List to store messages about skipped files
        skipped_files = []
        
        local_binary_path = get_bin_dir() / get_tailwind_binary_name()
        needs_download = force or not (config.binary_metadata and local_binary_path.exists())
        if not needs_download and hasattr(config, 'previous_style') and config.previous_style != config.style:
             needs_download = True # Force download if style changed
                
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            if binaries:
                task = progress.add_task("Preparing binary setup...", total=None) # Indeterminate task
                if not config_exists:
                    options = InitOptions()
                    config.update_from_options(options)                             
            else: # Regular init 
                task = progress.add_task("Setting up project...", total=None) # Indeterminate task
                
                # Check if we need to update template files due to style change
                style_changed = hasattr(config, 'previous_style') and config.previous_style != config.style
            
                if not config_exists:                    
                    progress.update(task, description="Creating directories...")
                    for dir_path in config.paths.values():
                        safe_create_directories(project_path / dir_path)

                    # Generate template files
                    progress.update(task, description="Generating files...")                    
                    
                    css_input_path = project_path / config.paths["css"] / "input.css"
                    app_file_path = project_path / config.app_path
                                        
                    if not css_input_path.exists():
                        render_template_safe(
                            "input.css.jinja2",
                            css_input_path,
                            {"style": config.style}
                        )
                    else:
                        skipped_files.append(f"Skipped creating existing file: {css_input_path.relative_to(project_path)}")
                        
                    if not app_file_path.exists():
                        render_template_safe(
                            "main.py.jinja2",
                            app_file_path,
                            {
                                "style": config.style,
                                "theme": config.theme,
                                "paths": config.paths,
                                "port": config.port,
                                "live": config.live,
                                "host": config.host
                            }
                        )
                    else:
                        skipped_files.append(f"Skipped creating existing file: {app_file_path.relative_to(project_path)}")
                
                progress.update(task, description="Finalizing setup...")
        
        download_performed = False
        if needs_download:
             console.print(f"Downloading {binary_type} binary...")
             try:
                 download_tailwind_binary(config, force=force, show_progress=True)
                 download_performed = True
             except typer.Exit:
                 raise # Re-raise the exit exception
             except Exception as e:
                 console.print(f"[red]Unexpected error during download:[/red] {e}")
                 raise typer.Exit(1)

        save_config(config, config_path)

        for msg in skipped_files:
            console.print(f"[yellow]Note:[/yellow] {msg}")
            
        if binaries:
            if download_performed:
                 console.print("\n[green bold]✓ Tailwind binaries installed successfully![/green bold]")
            else:
                 console.print("\n[green bold]✓ Tailwind binaries already up-to-date.[/green bold]")
            console.print("\n[bold]The binaries are now available for use with your existing project.[/bold]")
        else: # Regular init
            if not config_exists:
                 console.print("\n[green bold]✓ Project initialized successfully![/green bold]")
                 console.print("\n[bold]Next steps:[/bold]")
                 console.print("  1. Run [bold]daisyft dev[/bold] to start development server")
                 console.print(f"  2. Edit [bold]{config_path.relative_to(project_path)}[/bold] to customize your project")
                 console.print("\n[bold]Example commands:[/bold]")
                 console.print("  daisyft dev      # Start development server (with live CSS watch)")
                 console.print("  daisyft build    # Build production CSS")
                 console.print("  daisyft run      # Builds CSS and Runs FastHTML app")
            else: # Reinitialization messages
                 console.print("\n[bold]Project configuration updated in .daisyft/daisyft.toml.[/bold]")
                 style_changed = hasattr(config, 'previous_style') and config.previous_style != config.style
                 if style_changed:
                      console.print(f"\n[yellow]Note:[/yellow] Style changed from '{config.previous_style}' to '{config.style}'.")
                      css_input_path = project_path / config.paths["css"] / "input.css"
                      console.print(f"  - Your existing '{css_input_path.relative_to(project_path)}' was [bold]not[/bold] modified.")
                      console.print(f"  - You may need to manually update it to use the correct `@plugin` directive.")
                      console.print(f"  - You may also need to update your app file ('{config.app_path}') if it uses style-specific features.")
                      
                 if download_performed:
                     console.print("\n[bold]Tailwind binary was updated.[/bold]")
                 else:
                      console.print("\n[bold]Tailwind binary is already up-to-date.[/bold]")
                 console.print("\n[bold]Run [green]daisyft sync[/green] to check for future Tailwind binary updates.[/bold]")

    except (OSError, PermissionError) as e:
        console.print(f"[red]Fatal error:[/red] {e}")
        raise typer.Exit(1)