import typer
from pathlib import Path
import subprocess
import os
import sys
import time
from rich.console import Console
from ..utils.config import ProjectConfig
from ..utils.process import ProcessManager
from ..utils.console import console

def dev(
    host: str = typer.Option(None, "--host", "-h", help="Override host from config"),
    port: int = typer.Option(None, "--port", "-p", help="Override port from config"),
    input_css: str = typer.Option(None, "--input", "-i", help="Input CSS file path"),
    output_css: str = typer.Option(None, "--output", "-o", help="Output CSS file path"),
) -> None:
    """Start development server with CSS watching"""
    config = ProjectConfig.load(Path("daisyft.conf.py"))
    
    # Use config values unless overridden by command line
    host = host or config.host
    port = port or config.port
    
    input_css_path = Path(input_css) if input_css else Path(config.paths["css"]) / "input.css"
    output_css_path = Path(output_css) if output_css else Path(config.paths["css"]) / "output.css"
    
    pm = ProcessManager()
    
    # Start Tailwind CSS watcher with process group
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    preexec_fn = os.setsid if os.name != 'nt' else None
    
    css_process = subprocess.Popen([
        "./tailwindcss",
        "-i", str(input_css_path),
        "-o", str(output_css_path),
        "--watch"
    ], preexec_fn=preexec_fn, creationflags=creationflags)
    pm.add_process(css_process)
    
    # Brief pause to let Tailwind start
    time.sleep(0.5)
    
    # Start FastHTML dev server with process group
    server_process = subprocess.Popen([
        "uvicorn",
        f"{config.app_path.stem}:app",
        "--host", host,
        "--port", str(port),
        "--reload"
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