from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import questionary
from questionary import Choice
import typer
from jinja2 import TemplateError
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils.config import ProjectConfig
from ..utils.console import console
from ..utils.downloader import download_tailwind_binary
from ..utils.template import render_template, TemplateContext

@dataclass
class InitOptions:
    """Initialization options for project setup"""
    style: str = "daisy"
    theme: str = "dark"
    app_path: Path = Path("main.py")
    include_icons: bool = True
    components_dir: Path = Path("components")
    static_dir: Path = Path("static")
    verbose: bool = True

def handle_style_prompt(answers: Dict[str, Any]) -> None:
    answers["style"] = questionary.select(
        "Style:",
        choices=[
            Choice("daisy", "Use DaisyUI components (recommended)"),
            Choice("vanilla", "Use vanilla Tailwind CSS")
        ],
        default="daisy"
    ).ask()

def handle_theme_prompt(answers: Dict[str, Any]) -> None:
    if answers["style"] != "daisy":
        return
    
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

QUESTION_HANDLERS = {
    "style": handle_style_prompt,
    "theme": handle_theme_prompt,
    "app_path": lambda a: a.update({"app_path": 
        questionary.text("FastHTML app entry point:", default="main.py").ask()
    }),
    "include_icons": lambda a: a.update({"include_icons": 
        questionary.confirm("Include ft-icons package?", default=True).ask()
    }),
    "components_dir": lambda a: a.update({"components_dir": 
        questionary.text("Components directory:", default="components").ask()
    }),
    "static_dir": lambda a: a.update({"static_dir": 
        questionary.text("Static assets directory:", default="static").ask()
    }),
    "verbose": lambda a: a.update({"verbose": 
        questionary.confirm("Include detailed documentation?", default=True).ask()
    })
}

def get_user_options(defaults: bool = False) -> InitOptions:
    """Get project options through interactive prompts or defaults"""
    if defaults:
        return InitOptions()

    console.print("\n[bold]Project Configuration:[/bold]")
    console.print("[dim]Use arrow keys to navigate, space to select options to customize[/dim]\n")

    answers = {
        "style": "daisy",
        "theme": "dark",
        "app_path": "main.py",
        "include_icons": True,
        "components_dir": "components",
        "static_dir": "static",
        "verbose": True
    }

    try:
        selected = questionary.checkbox(
            "Which options would you like to customize?",
            choices=[
                Choice(
                    title=key,
                    value=key,
                    disabled=key == "theme" and answers["style"] != "daisy"
                ) for key in QUESTION_HANDLERS.keys()
            ]
        ).ask()

        for key in selected:
            QUESTION_HANDLERS[key](answers)

        return InitOptions(
            style=answers["style"],
            theme=answers["theme"],
            app_path=Path(answers["app_path"]),
            include_icons=answers["include_icons"],
            components_dir=Path(answers["components_dir"]),
            static_dir=Path(answers["static_dir"]),
            verbose=answers["verbose"]
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Initialization cancelled[/yellow]")
        raise typer.Exit(1)

def safe_create_directories(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        console.print(f"[red]Error creating directory {path}:[/red] {e}")
        raise typer.Exit(1)

def render_template_safe(template_name: str, output_path: Path, context: TemplateContext) -> None:
    try:
        render_template(template_name, output_path, context)
    except (TemplateError, OSError) as e:
        console.print(f"[red]Error rendering {template_name}:[/red] {e}")
        raise typer.Exit(1)

def init(
    path: str = typer.Option(".", help="Project path"),
    defaults: bool = typer.Option(False, "--defaults", "-d", help="Use default settings"),
    template: str = typer.Option("basic", help="Project template to use"),
    force: bool = typer.Option(False, "--force", "-f", help="Force download new Tailwind binary"),
    package_manager: Optional[str] = typer.Option(None, "--pm", help="Package manager to use")
) -> None:
    """Initialize a new ft-daisy project"""
    project_path = Path(path).absolute()
    config_path = project_path / "daisyft.conf.py"

    try:
        project_path.mkdir(parents=True, exist_ok=True)
        config = ProjectConfig.load(config_path)
        config_exists = config.is_initialized

        if not config_exists and not defaults:
            options = get_user_options()
            config.update_from_options(options)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing project...", total=100)

            if not config_exists:
                progress.update(task, description="Creating directories...")
                for path in config.paths.values():
                    safe_create_directories(project_path / path)

                progress.update(task, advance=30, description="Generating files...")
                render_template_safe(
                    "input.css.jinja2",
                    project_path / config.paths["css"] / "input.css",
                    {"style": config.style, "components": {}}
                )

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
                progress.update(task, advance=40)

            progress.update(task, description="Downloading Tailwind...")
            try:
                binary_path = download_tailwind_binary(config, force=force)
                if not binary_path.exists():
                    raise typer.Exit(1)
                progress.update(task, advance=20)
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Binary download failed - {e}")
                progress.update(task, advance=20)

            config.save(config_path)
            progress.update(task, advance=10)

        console.print("\n[green]✓ Project initialized successfully![/green]")
        if not config_exists:
            console.print("\nNext steps:")
            console.print("  1. Add components with [bold]daisyft add[/bold]")
            console.print("  2. Configure Tailwind in [bold]daisyft.conf.py[/bold]")
            console.print("  3. Run [bold]daisyft dev[/bold] to start development server")

    except (OSError, PermissionError) as e:
        console.print(f"[red]Fatal error:[/red] {e}")
        raise typer.Exit(1)