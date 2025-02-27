import typer
from pathlib import Path
import subprocess
import os
import sys
import time
from ..utils.config import ProjectConfig
from ..utils.toml_config import load_config
from ..utils.process import ProcessManager
from ..utils.console import console
from ..utils.command_utils import (
    validate_binary,
    build_css_command,
    resolve_css_paths
)

def run(
    host: str = typer.Option(None, "--host", "-h", help="Override host from config"),
    port: int = typer.Option(None, "--port", "-p", help="Override port from config"),
    input_css: str = typer.Option(None, "--input", "-i", help="Input CSS file path"),
    output_css: str = typer.Option(None, "--output", "-o", help="Output CSS file path"),
) -> None:
    """Build CSS and run the FastHTML application"""
    config = load_config(Path("daisyft.toml"))
    
    # Use config values unless overridden
    host = host or config.host
    port = port or config.port
    
    # Resolve paths using shared utility
    input_css_path, output_css_path = resolve_css_paths(config, input_css, output_css)
    
    # Validate binary using shared utility
    binary_path = validate_binary(config)
    
    # Delete existing output.css if it exists
    if output_css_path.exists():
        output_css_path.unlink()
        console.print("[bold]Cleaning existing CSS...[/bold]")
    
    # Build CSS using shared command builder
    try:
        console.print("[bold]Building CSS...[/bold]")
        subprocess.run(
            build_css_command(binary_path, input_css_path, output_css_path, minify=True),
            check=True
        )
        console.print("[green]✓[/green] CSS built successfully!")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error:[/red] Failed to build CSS: {e}")
        raise typer.Exit(1)
    
    with ProcessManager().manage() as pm:
        # Start server
        server_process = subprocess.Popen([
            sys.executable,
            str(config.app_path),
            "--host", host,
            "--port", str(port)
        ], preexec_fn=pm.preexec_fn, creationflags=pm.creationflags)
        pm.add_process(server_process)
        
        # Brief pause to check server status
        time.sleep(0.5)
        if server_process.poll() is None:
            console.print(f"\n[green]Server running at[/green] http://{host}:{port}")
        
        try:
            server_process.wait()
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down...[/yellow]")
            raise typer.Exit(0) 