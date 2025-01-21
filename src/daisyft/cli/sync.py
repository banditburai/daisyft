import typer
from rich.console import Console
from pathlib import Path
from ..utils.config import ProjectConfig
from ..utils.templates import render_template

console = Console()

def sync(
    config_path: str = typer.Option("daisyft.conf.py", "--config", "-c", help="Path to config file"),
    force: bool = typer.Option(False, "--force", "-f", help="Force overwrite without confirmation")
) -> None:
    """Sync main.py with current config values"""
    try:
        config = ProjectConfig.load(Path(config_path))
        config.ensure_initialized()
        
        if config.app_path.exists() and not force:
            if not typer.confirm(
                f"\n{config.app_path} already exists. Overwrite?",
                default=False
            ):
                raise typer.Exit()
        
        render_template(
            "main.py.jinja2",
            config.app_path,
            style=config.style,
            theme=config.theme,
            paths=config.paths,
            port=config.port,
            live=config.live,
            host=config.host
        )
        
        console.print(f"[green]✓[/green] Synchronized {config.app_path} with current config")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) 