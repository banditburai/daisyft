import typer
from pathlib import Path
import subprocess
import platform
import sys
import time
from rich.console import Console
from ..utils.config import ProjectConfig
from ..utils.process import ProcessManager

console = Console()

def run(
    host: str = typer.Option(None, "--host", "-h", help="Override host from config"),
    port: int = typer.Option(None, "--port", "-p", help="Override port from config"),
) -> None:
    """Build CSS and run the FastHTML application"""
    config = ProjectConfig.load(Path("daisyft.conf.py"))
    
    # Use config values unless overridden by command line
    host = host or config.host
    port = port or config.port
    
    pm = ProcessManager()
    
    # Build CSS first
    console.print("[bold]Building CSS...[/bold]")
    try:
        subprocess.run([
            "./tailwindcss",
            "-i", str(Path(config.paths["css"]) / "input.css"),
            "-o", str(Path(config.paths["css"]) / "output.css"),
            "--minify"
        ], check=True)
        console.print("[green]✓[/green] CSS built successfully!")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error:[/red] Failed to build CSS: {e}")
        raise typer.Exit(1)
    
    # Start FastHTML server
    server_process = subprocess.Popen([
        sys.executable,
        str(config.app_path),
        "--host", host,
        "--port", str(port)
    ])
    pm.add_process(server_process)
    
    # Brief pause to check if server started successfully
    time.sleep(0.5)
    if server_process.poll() is None:
        console.print(f"\n[green]Server running at[/green] http://{host}:{port}")
    
    try:
        server_process.wait()
    except KeyboardInterrupt:
        pass
    finally:
        pm.cleanup() 