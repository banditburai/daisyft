from dataclasses import dataclass
from pathlib import Path
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import questionary
from typing import Optional
import subprocess
import requests
import stat
from platform import system
from questionary import Choice

from ..utils.config import ProjectConfig, TailwindReleaseInfo
from ..utils.templates import render_template
from ..utils.package import PackageManager
from ..registry.decorators import Registry, RegistryType

console = Console()

def get_release_info(style: str = "daisy") -> dict:
    """Get latest release info from GitHub"""
    url = TailwindReleaseInfo.get_api_url(style)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def download_tailwind_binary(config: ProjectConfig, force: bool = False) -> Path:
    """Download the appropriate Tailwind binary"""
    binary_path = Path("tailwindcss" + (".exe" if system().lower() == "windows" else ""))
    
    try:
        release_info = get_release_info(config.style)
        
        if binary_path.exists() and not force and config.binary_metadata:
            # Check if we need to update
            if config.binary_metadata.style == config.style:
                current_version = config.binary_metadata.version
                latest_version = release_info.get('tag_name')
                
                if current_version == latest_version:
                    console.print(f"[green]✓[/green] Tailwind binary is up to date ({current_version})")
                    return binary_path
                
                if not typer.confirm(
                    f"\nNew version available: {latest_version} (current: {current_version})\nDownload update?",
                    default=True
                ):
                    return binary_path
            else:
                if not typer.confirm(
                    f"\nExisting binary is for {config.binary_metadata.style} style, "
                    f"but {config.style} style is requested. Download new version?",
                    default=True
                ):
                    return binary_path
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not check for updates: {e}")
        if binary_path.exists() and not force:
            return binary_path
    
    base_url = TailwindReleaseInfo.get_download_url(config.style)
    url = f"{base_url}{config.tailwind_binary_name}"
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    # Download to original name first
    temp_path = Path(config.tailwind_binary_name)
    temp_path.write_bytes(response.content)
    
    # Rename to tailwindcss
    if binary_path.exists():
        binary_path.unlink()
    temp_path.rename(binary_path)
    
    # Make binary executable (skip on Windows)
    if system().lower() != "windows":
        binary_path.chmod(binary_path.stat().st_mode | stat.S_IEXEC)
    
    # Update config with new binary metadata
    config.update_binary_metadata(release_info)
    
    return binary_path

@dataclass
class InitOptions:
    """Initialization options for project setup"""
    style: str = "daisy"
    theme: str = "dark"
    app_path: Path = Path("main.py")
    include_icons: bool = True
    components_dir: Path = Path("components")
    static_dir: Path = Path("static")

def get_user_options(defaults: bool = False) -> InitOptions:
    """Get project options either from user input or defaults"""
    if defaults:
        return InitOptions()
    
    default_options = {
        "style": ("daisy", "Choose between DaisyUI components or vanilla Tailwind"),
        "theme": ("dark", "Select a theme for your application"),
        "app_path": ("main.py", "Entry point for your FastHTML application"),
        "include_icons": (True, "Include ft-icons package for SVG icon components"),
        "components_dir": ("components", "Directory where your UI components will be stored"),
        "static_dir": ("static", "Directory for CSS, JavaScript, and other static assets")
    }
    
    # Show current configuration
    console.print("\n[bold]Default configuration:[/bold]")
    for key, (value, desc) in default_options.items():
        if key != "theme" or default_options["style"][0] == "daisy":
            console.print(f"  [green]{key}:[/green] {value}")
            console.print(f"    [dim]{desc}[/dim]")
    
    console.print("\n[dim]Use arrow keys to move, space to select options to customize[/dim]")
    
    # Start with defaults
    answers = {k: v for k, (v, _) in default_options.items()}
    
    to_change = questionary.checkbox(
        "Which options would you like to customize?",
        choices=[
            Choice(
                title=f"{key}",
                value=key,
                disabled=key == "theme" and default_options["style"][0] != "daisy"
            )
            for key, (_, _) in default_options.items()
        ]
    ).ask()
    
    # Only prompt for selected options
    if "style" in to_change:
        answers["style"] = questionary.select(
            "Style:",
            choices=[
                Choice("daisy", "Use DaisyUI components (recommended)"),
                Choice("vanilla", "Use vanilla Tailwind CSS")
            ],
            default="daisy"
        ).ask()
    
    if "theme" in to_change:
        theme_question = questionary.select(
            "Theme:",
            choices=[
                Choice("dark", "Dark mode (default)"),
                Choice("light", "Light mode"),
                Choice("cupcake", "Light and playful"),
                Choice("corporate", "Professional and clean"),
                # ... other themes with descriptions ...
            ],
            default="dark"
        ).skip_if(lambda x: answers["style"] != "daisy", default="dark")
        answers["theme"] = theme_question.ask()
    
    if "app_path" in to_change:
        answers["app_path"] = questionary.text(
            "FastHTML app entry point:",
            default="main.py"
        ).ask()
    
    if "include_icons" in to_change:
        answers["include_icons"] = questionary.confirm(
            "Include ft-icons package?",
            default=True
        ).ask()
    
    if "components_dir" in to_change:
        answers["components_dir"] = questionary.text(
            "Components directory:",
            default="components"
        ).ask()
    
    if "static_dir" in to_change:
        answers["static_dir"] = questionary.text(
            "Static assets directory:",
            default="static"
        ).ask()
    
    return InitOptions(
        style=answers["style"],
        theme=answers["theme"],
        app_path=Path(answers["app_path"]),
        include_icons=answers["include_icons"],
        components_dir=Path(answers["components_dir"]),
        static_dir=Path(answers["static_dir"])
    )

def init(
    path: str = typer.Option(".", help="Project path"),
    defaults: bool = typer.Option(False, "--defaults", "-d", help="Use default settings"),
    template: str = typer.Option("basic", help="Project template to use"),
    force: bool = typer.Option(False, "--force", "-f", help="Force download new Tailwind binary"),
    package_manager: Optional[str] = typer.Option(None, "--pm", help="Package manager to use")
) -> None:
    """Initialize a new ft-daisy project"""
    project_path = Path(path).absolute()
    project_path.mkdir(parents=True, exist_ok=True)
    
    # Load or create config
    config = ProjectConfig.load(project_path / "daisyft.conf.py")
    config_exists = config.is_initialized
    
    # Get project settings
    if not config_exists and not defaults:
        options = get_user_options()
        config.style = options.style
        config.theme = options.theme
        config.app_path = options.app_path
        config.include_icons = options.include_icons
        config.paths.update({
            "components": options.components_dir,
            "ui": options.components_dir / "ui",
            "static": options.static_dir,
            "css": options.static_dir / "css",
            "js": options.static_dir / "js",
            "icons": options.static_dir / "icons",
        })
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("", total=100)
        
        # Create project structure
        if not config_exists:
            progress.update(task, description="Creating project structure...")
            for path in config.paths.values():
                (project_path / path).mkdir(parents=True, exist_ok=True)
            
            # Generate initial files
            render_template(
                "input.css.jinja2",
                project_path / config.paths["css"] / "input.css",
                style=config.style
            )
            
            # Install base components
            if template == "basic":
                button = Registry.get_component("button")
                if button:
                    button.install(config, force)
            
            # Generate main app
            render_template(
                "main.py.jinja2",
                project_path / config.app_path,
                style=config.style,
                theme=config.theme,
                paths=config.paths,
                port=config.port,
                live=config.live,
                host=config.host
            )
            
            progress.update(task, advance=50)
        
        # Always check/update Tailwind binary
        progress.update(task, description="Checking Tailwind binary...")
        try:
            download_tailwind_binary(config, force=force)
            progress.update(task, advance=25)
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not download Tailwind binary: {e}")
        
        # Save config
        config.save(project_path / "daisyft.conf.py")
        
        # Install ft-icons if requested
        if config.include_icons and not config_exists:
            progress.update(task, description="Installing ft-icons...")
            try:
                PackageManager.install(
                    "git+https://github.com/banditburai/ft-icon.git",
                    manager=package_manager
                )
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Could not install ft-icons: {e}")
                console.print("You can install it manually later with your package manager of choice.")
            
            progress.update(task, advance=25)

    if config_exists:
        console.print("\n[green]✓[/green] Tailwind binary updated successfully!")
    else:
        console.print("\n[green]✓[/green] Project initialized successfully!")
        console.print("\nNext steps:")
        console.print("  1. Add components with [bold]daisyft add[/bold]")
        console.print("  2. Configure Tailwind in [bold]daisyft.conf.py[/bold]")
        console.print("  3. Run [bold]daisyft dev[/bold] to start development server") 