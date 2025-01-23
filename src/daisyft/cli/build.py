import typer
from pathlib import Path
import subprocess
from rich.console import Console
from ..utils.config import ProjectConfig
from ..utils.console import console  

def build(
    input_path: str = typer.Option(None, "--input", "-i", help="Input CSS file path"),
    output_path: str = typer.Option(None, "--output", "-o", help="Output CSS file path"),
    minify: bool = typer.Option(False, "--minify", "-m", help="Minify output CSS")
) -> None:
    """Build Tailwind CSS"""
    config = ProjectConfig.load(Path("daisyft.conf.py"))
    
    input_css = Path(input_path) if input_path else Path(config.paths["css"]) / "input.css"
    output_css = Path(output_path) if output_path else Path(config.paths["css"]) / "output.css"
    
    console.print(f"[bold]Building CSS...[/bold]")
    try:
        cmd = [
            "./tailwindcss",
            "-i", str(input_css),
            "-o", str(output_css)
        ]
        if minify:
            cmd.append("--minify")
        
        subprocess.run(cmd, check=True)
        console.print(f"[green]✓[/green] CSS built successfully!")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error:[/red] Failed to build CSS: {e}")
        raise typer.Exit(1) 