import typer
from pathlib import Path
import subprocess
import os
import sys
import time
from ..utils.toml_config import load_config
from ..utils.process import ProcessManager
from ..utils.console import console
from ..utils.command_utils import (
    validate_binary,
    build_css_command,
    resolve_css_paths
)

def dev(
    host: str = typer.Option(None, "--host", "-h", help="Override host from config"),
    port: int = typer.Option(None, "--port", "-p", help="Override port from config"),
    input_css: str = typer.Option(None, "--input", "-i", help="Input CSS file path"),
    output_css: str = typer.Option(None, "--output", "-o", help="Output CSS file path"),
) -> None:
    """Start development server with CSS watching"""
    config = load_config(Path("daisyft.toml"))
    
    # Resolve paths using shared utility
    input_css_path, output_css_path = resolve_css_paths(config, input_css, output_css)
    
    # Validate binary using shared utility
    binary_path = validate_binary(config)
    
    # Use config values unless overridden
    host = host or config.host
    port = port or config.port
    
    # Clean existing CSS
    if output_css_path.exists():
        output_css_path.unlink()
        console.print("[bold]Cleaning existing CSS...[/bold]")
    
    with ProcessManager().manage() as pm:
        # Start Tailwind watcher
        css_process = subprocess.Popen(
            build_css_command(binary_path, input_css_path, output_css_path, watch=True),
            preexec_fn=pm.preexec_fn,
            creationflags=pm.creationflags
        )
        pm.add_process(css_process)
        
        # Start FastHTML dev server
        server_process = subprocess.Popen([
            "uvicorn",
            f"{config.app_path.stem}:app",
            "--host", host,
            "--port", str(port),
            "--reload"
        ], preexec_fn=pm.preexec_fn, creationflags=pm.creationflags)
        pm.add_process(server_process)
        
        # Status check
        time.sleep(0.5)
        if server_process.poll() is None:
            console.print(f"\n[green]Server running at[/green] http://{host}:{port}")
        
        try:
            server_process.wait()
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down...[/yellow]")
            raise typer.Exit(0) 