import typer
from pathlib import Path
import subprocess
from ..utils.config import ProjectConfig
from ..utils.console import console  
from ..utils.command_utils import validate_binary, build_css_command, resolve_css_paths

def build(
    input_path: str = typer.Option(None, "--input", "-i", help="Input CSS file path"),
    output_path: str = typer.Option(None, "--output", "-o", help="Output CSS file path"),
    minify: bool = typer.Option(False, "--minify", "-m", help="Minify output CSS")
) -> None:
    """Build Tailwind CSS"""
    config = ProjectConfig.load(Path("daisyft.conf.py"))
    input_path, output_path = resolve_css_paths(config, input_path, output_path)
    binary_path = validate_binary(config)
    
    console.print(f"[bold]Building CSS...[/bold]")
    try:
        cmd = build_css_command(binary_path, input_path, output_path, minify=minify)
        subprocess.run(cmd, check=True)
        console.print(f"[green]✓[/green] CSS built successfully!")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error:[/red] Failed to build CSS: {e}")
        raise typer.Exit(1) 