import typer
from pathlib import Path
import subprocess
import os
import sys
import time
from ..utils.config import ProjectConfig
from ..utils.process import ProcessManager
from ..utils.console import console

def run(
    host: str = typer.Option(None, "--host", "-h", help="Override host from config"),
    port: int = typer.Option(None, "--port", "-p", help="Override port from config"),
    input_css: str = typer.Option(None, "--input", "-i", help="Input CSS file path"),
    output_css: str = typer.Option(None, "--output", "-o", help="Output CSS file path"),
) -> None:
    """Build CSS and run the FastHTML application"""
    config = ProjectConfig.load(Path("daisyft.conf.py"))
    
    # Use config values unless overridden by command line
    host = host or config.host
    port = port or config.port
    
    pm = ProcessManager()

    input_css_path = Path(input_css) if input_css else Path(config.paths["css"]) / "input.css"
    output_css_path = Path(output_css) if output_css else Path(config.paths["css"]) / "output.css"
    
    # Delete existing output.css if it exists
    if output_css_path.exists():
        output_css_path.unlink()
        console.print("[bold]Cleaning existing CSS...[/bold]")
    
    # Build CSS first
    console.print("[bold]Building CSS...[/bold]")
    binary_path = config.binary_path
    if not binary_path.exists():
        console.print(f"[red]Error:[/red] Tailwind binary missing at {binary_path}")
        console.print("Please run [bold]daisyft init --force[/bold] to download it")
        raise typer.Exit(1)
            
    try:
        console.print(f"Resolved binary path: [dim]{binary_path}[/dim] (exists: {binary_path.exists()})")
        subprocess.run([
            str(binary_path.absolute()),
            "-i", str(input_css_path),
            "-o", str(output_css_path),
            "--minify"
        ], check=True)
        console.print("[green]✓[/green] CSS built successfully!")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error:[/red] Failed to build CSS: {e}")
        raise typer.Exit(1)
    
    # Start FastHTML server with process group
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    preexec_fn = os.setsid if os.name != 'nt' else None
    
    server_process = subprocess.Popen([
        sys.executable,
        str(config.app_path),
        "--host", host,
        "--port", str(port)
    ], preexec_fn=preexec_fn, creationflags=creationflags)
    
    pm.add_process(server_process)
    
    # Brief pause to check if server started successfully
    time.sleep(0.5)
    if server_process.poll() is None:
        console.print(f"\n[green]Server running at[/green] http://{host}:{port}")
    
    try:
        server_process.wait()
    except KeyboardInterrupt:
        pm.cleanup()
        sys.exit(0) 