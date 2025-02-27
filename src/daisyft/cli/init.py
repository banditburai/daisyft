from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List
import questionary
from questionary import Choice
import typer
from jinja2 import TemplateError
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from ..utils.config import ProjectConfig, InitOptions
from ..utils.toml_config import load_config, save_config
from ..utils.console import console
from ..utils.downloader import download_tailwind_binary
from ..utils.template import render_template, TemplateContext
from ..utils.package import PackageManager
from datetime import datetime

# Templates available for project initialization
TEMPLATES = {
    "minimal": {
        "name": "Minimal",
        "description": "Basic setup with essential files only",
        "files": ["input.css", "main.py"]
    },
    "standard": {
        "name": "Standard",
        "description": "Complete setup with example components",
        "files": ["input.css", "main.py"]
    },
}

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
    
    # Use dictionary-based choices instead of Choice objects
    selected = questionary.select(
        "Style framework:",
        choices=style_choices,
        default=style_choices[default_choice]
    ).ask()
    
    # Update the style
    answers["style"] = selected
    
    if answers["style"] == "daisy":
        # Define theme choices
        theme_choices = [
            {"value": "dark", "name": "Dark mode (default)"},
            {"value": "light", "name": "Light mode"},
            {"value": "cupcake", "name": "Light and playful"},
            {"value": "corporate", "name": "Professional and clean"}
        ]
        
        # Find default choice
        default_choice = 0
        for i, choice in enumerate(theme_choices):
            if choice["value"] == answers["theme"]:
                default_choice = i
                break
        
        # Use dictionary-based choices
        selected_theme = questionary.select(
            "Theme:",
            choices=theme_choices,
            default=theme_choices[default_choice]
        ).ask()
        
        # Update the theme
        answers["theme"] = selected_theme
    else:
        answers["theme"] = "default"

def handle_advanced_options(answers: Dict[str, Any]) -> None:
    """Handle more advanced configuration options"""
    answers["app_path"] = questionary.text(
        "FastHTML app entry point:", 
        default=answers["app_path"]
    ).ask()
    
    answers["components_dir"] = questionary.text(
        "Components directory:", 
        default=answers["components_dir"]
    ).ask()
    
    answers["static_dir"] = questionary.text(
        "Static assets directory:", 
        default=answers["static_dir"]
    ).ask()
    
    answers["include_icons"] = questionary.confirm(
        "Include ft-icons package?", 
        default=answers["include_icons"]
    ).ask()
    
    answers["verbose"] = questionary.confirm(
        "Include detailed documentation?", 
        default=answers["verbose"]
    ).ask()

def get_user_options(defaults: bool = False, advanced: bool = False) -> InitOptions:
    """Get project options through interactive prompts or defaults
    
    Args:
        defaults: Use default values without prompting
        advanced: Use advanced setup with more configuration options
    """
    if defaults:
        return InitOptions()

    console.print("\n[bold blue]DaisyFT Project Setup[/bold blue]")
    
    if not advanced:
        # Quick setup with minimal questions (default)
        # Just ask the most essential questions
        style_choices = [
            {"value": "daisy", "name": "DaisyUI components (recommended)"},
            {"value": "vanilla", "name": "Vanilla Tailwind CSS"}
        ]
        
        # Use dictionary-based choices
        style = questionary.select(
            "Style framework:",
            choices=style_choices,
            default=style_choices[0]
        ).ask()
        
        if style == "daisy":
            theme_choices = [
                {"value": "dark", "name": "Dark mode (default)"},
                {"value": "light", "name": "Light mode"},
                {"value": "cupcake", "name": "Light and playful"},
                {"value": "corporate", "name": "Professional and clean"}
            ]
            
            # Use dictionary-based choices
            theme = questionary.select(
                "Theme:",
                choices=theme_choices,
                default=theme_choices[0]
            ).ask()
        else:
            theme = "default"
            
        return InitOptions(
            style=style,
            theme=theme,
            app_path=Path("main.py"),
            include_icons=True,
            components_dir=Path("components"),
            static_dir=Path("static"),
            verbose=True,
            template="minimal"
        )
    
    # Advanced setup with all options
    # Show available templates
    console.print(Panel(
        "\n".join([f"[bold]{name}[/bold]: {info['description']}" 
                  for name, info in TEMPLATES.items()]),
        title="Available Templates",
        expand=False
    ))
    
    # Start with default answers
    answers = {
        "style": "daisy",
        "theme": "dark",
        "app_path": "main.py",
        "include_icons": True,
        "components_dir": "components",
        "static_dir": "static",
        "verbose": True,
        "template": "standard"
    }

    try:
        # Select template first
        template_choices = [
            {"value": name, "name": info["description"]} 
            for name, info in TEMPLATES.items()
        ]
        
        # Find default choice
        default_choice = 0
        for i, choice in enumerate(template_choices):
            if choice["value"] == "standard":
                default_choice = i
                break
        
        answers["template"] = questionary.select(
            "Select a template:",
            choices=template_choices,
            default=template_choices[default_choice]
        ).ask()
        
        # Always ask for basic options
        handle_basic_options(answers)
        
        # Always ask for advanced options in advanced mode
        handle_advanced_options(answers)

        return InitOptions(
            style=answers["style"],
            theme=answers["theme"],
            app_path=Path(answers["app_path"]),
            include_icons=answers["include_icons"],
            components_dir=Path(answers["components_dir"]),
            static_dir=Path(answers["static_dir"]),
            verbose=answers["verbose"],
            template=answers["template"]
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
    advanced: bool = typer.Option(False, "--advanced", "-a", help="Advanced setup with more configuration options"),
    template: Optional[str] = typer.Option(None, help="Project template to use"),
    force: bool = typer.Option(False, "--force", "-f", help="Force download new Tailwind binary"),
    package_manager: Optional[str] = typer.Option(None, "--pm", help="Package manager to use")
) -> None:
    """Initialize a new DaisyFT project
    
    This command sets up a new project with Tailwind CSS and FastHTML integration.
    It creates the necessary directory structure, configuration files, and downloads
    the Tailwind CSS binary.
    
    Examples:
        daisyft init                # Quick setup with minimal questions
        daisyft init --advanced     # Advanced setup with more configuration options
        daisyft init --defaults     # Use default settings without prompting
        daisyft init --template=minimal  # Use minimal template
    """
    project_path = Path(path).absolute()
    config_path = project_path / "daisyft.toml"

    try:
        # Create project directory if it doesn't exist
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Check if project is already initialized
        config = load_config(config_path)
        config_exists = config.is_initialized

        if config_exists and not force:
            if not typer.confirm(
                "[yellow]Project already initialized.[/yellow] Do you want to reinitialize?",
                default=False
            ):
                console.print("[yellow]Initialization cancelled.[/yellow]")
                return
        
        # Get configuration options
        if not config_exists:
            # Override template if specified in command line
            if template and template in TEMPLATES:
                options = get_user_options(defaults, advanced)
                options.template = template
            else:
                options = get_user_options(defaults, advanced)
                
            config.update_from_options(options)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Download Tailwind binary first
            task = progress.add_task("Setting up project...", total=100)
            
            # Clearer messaging about what's being downloaded
            binary_type = "DaisyUI-enhanced Tailwind CSS" if config.style == "daisy" else "Vanilla Tailwind CSS"
            progress.update(task, description=f"Downloading {binary_type} binary...", advance=10)
            
            download_tailwind_binary(config, force=force, existing_progress=progress)
            
            # Save config with valid binary path
            save_config(config, config_path)

            if not config_exists:
                # Create project structure
                progress.update(task, description="Creating directories...", advance=20)
                for dir_path in config.paths.values():
                    safe_create_directories(project_path / dir_path)

                # Generate template files
                progress.update(task, description="Generating files...", advance=30)
                
                # CSS input file
                render_template_safe(
                    "input.css.jinja2",
                    project_path / config.paths["css"] / "input.css",
                    {"style": config.style, "components": {}}
                )
                
                # Main app file
                render_template_safe(
                    "main.py.jinja2",
                    project_path / config.app_path,
                    {
                        "style": config.style,
                        "theme": config.theme,
                        "paths": config.paths,
                        "port": config.port,
                        "live": config.live,
                        "host": config.host
                    }
                )
                
                # Install required dependencies
                if config.include_icons:
                    progress.update(task, description="Installing dependencies...", advance=10)
                    try:
                        # Use our new PackageManager to install ft-icons
                        PackageManager.install(
                            "git+https://github.com/banditburai/ft-icon.git",
                            manager=package_manager,
                            quiet=True
                        )
                    except Exception as e:
                        console.print(f"[yellow]Warning:[/yellow] Could not install ft-icons: {e}")
                        console.print("You can install it manually later with your package manager of choice.")
                
            progress.update(task, description="Finalizing setup...", advance=40)
        
        # Show success message and next steps
        console.print("\n[green bold]✓ Project initialized successfully![/green bold]")
        if not config_exists:
            console.print("\n[bold]Next steps:[/bold]")
            console.print("  1. Run [bold]daisyft dev[/bold] to start development server")
            console.print("  2. Edit [bold]daisyft.toml[/bold] to customize your project")
            console.print("  3. Create your FastHTML components in the [bold]components/[/bold] directory")
            
            # Show command examples
            console.print("\n[bold]Example commands:[/bold]")
            console.print("  daisyft dev      # Start development server")
            console.print("  daisyft build    # Build production CSS")
            console.print("  daisyft run      # Run FastHTML app")
            
            if not advanced and not defaults:
                console.print("\n[dim]Note: You used the quick setup. For more configuration options, run:[/dim]")
                console.print("  daisyft init --advanced")

    except (OSError, PermissionError) as e:
        console.print(f"[red]Fatal error:[/red] {e}")
        raise typer.Exit(1)