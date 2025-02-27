from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List
import questionary
from questionary import Choice
import typer
from jinja2 import TemplateError
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from ..utils.toml_config import ProjectConfig, InitOptions
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
        "files": ["input.css", "main.py", "tailwind.config.js"]
    },
    "standard": {
        "name": "Standard",
        "description": "Complete setup with example components",
        "files": ["input.css", "main.py", "tailwind.config.js", "example.py"]
    },
}

# Simplified question handlers with progressive disclosure
def handle_basic_options(answers: Dict[str, Any]) -> None:
    """Handle the basic, most important configuration options"""
    answers["style"] = questionary.select(
        "Style framework:",
        choices=[
            Choice("daisy", "DaisyUI components (recommended)"),
            Choice("vanilla", "Vanilla Tailwind CSS")
        ],
        default="daisy"
    ).ask()
    
    if answers["style"] == "daisy":
        answers["theme"] = questionary.select(
            "Theme:",
            choices=[
                Choice("dark", "Dark mode (default)"),
                Choice("light", "Light mode"),
                Choice("cupcake", "Light and playful"),
                Choice("corporate", "Professional and clean"),
            ],
            default="dark"
        ).ask()
    else:
        answers["theme"] = "default"

def handle_advanced_options(answers: Dict[str, Any]) -> None:
    """Handle more advanced configuration options"""
    answers["app_path"] = questionary.text(
        "FastHTML app entry point:", 
        default="main.py"
    ).ask()
    
    answers["components_dir"] = questionary.text(
        "Components directory:", 
        default="components"
    ).ask()
    
    answers["static_dir"] = questionary.text(
        "Static assets directory:", 
        default="static"
    ).ask()
    
    answers["include_icons"] = questionary.confirm(
        "Include ft-icons package?", 
        default=True
    ).ask()
    
    answers["verbose"] = questionary.confirm(
        "Include detailed documentation?", 
        default=True
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
        style = "daisy"
        theme = "dark"
        
        # Just ask the most essential questions
        style = questionary.select(
            "Style framework:",
            choices=[
                Choice("daisy", "DaisyUI components (recommended)"),
                Choice("vanilla", "Vanilla Tailwind CSS")
            ],
            default="daisy"
        ).ask()
        
        if style == "daisy":
            theme = questionary.select(
                "Theme:",
                choices=[
                    Choice("dark", "Dark mode (default)"),
                    Choice("light", "Light mode"),
                    Choice("cupcake", "Light and playful"),
                    Choice("corporate", "Professional and clean"),
                ],
                default="dark"
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
            template="standard"
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
        answers["template"] = questionary.select(
            "Select a template:",
            choices=[
                Choice(name, info["description"]) 
                for name, info in TEMPLATES.items()
            ],
            default="standard"
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
        config = ProjectConfig.load(config_path)
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
            progress.update(task, description="Downloading Tailwind CSS...", advance=10)
            download_tailwind_binary(config, force=force)
            
            # Save config with valid binary path
            config.save(config_path)

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
                
                # Tailwind config
                render_template_safe(
                    "tailwind.config.js.jinja2",
                    project_path / "tailwind.config.js",
                    {"style": config.style}
                )
                
                # Add example component if using standard template
                if config.template == "standard":
                    render_template_safe(
                        "example.py.jinja2",
                        project_path / "example.py",
                        {"style": config.style}
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