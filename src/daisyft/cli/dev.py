import typer
from pathlib import Path
import subprocess
import signal
import sys
from rich.console import Console
from ..utils.config import ProjectConfig

console = Console()

def dev(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to run the server on"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to run the server on"),
    input_css: str = typer.Option(None, "--input", "-i", help="Input CSS file path"),
    output_css: str = typer.Option(None, "--output", "-o", help="Output CSS file path"),
) -> None:
    """Start development server with CSS watching"""
    config = ProjectConfig.load(Path("daisyft.conf.py"))
    
    input_css_path = Path(input_css) if input_css else Path(config.paths["css"]) / "input.css"
    output_css_path = Path(output_css) if output_css else Path(config.paths["css"]) / "output.css"
    
    # Start Tailwind CSS watcher
    css_process = subprocess.Popen([
        "./tailwindcss",
        "-i", str(input_css_path),
        "-o", str(output_css_path),
        "--watch"
    ])
    
    # Start FastHTML dev server
    server_process = subprocess.Popen([
        "uvicorn",
        f"{config.app_path.stem}:app",
        "--host", host,
        "--port", str(port),
        "--reload"
    ])
    
    def cleanup(signum, frame):
        """Clean up processes on exit"""
        console.print("\n[yellow]Shutting down...[/yellow]")
        css_process.terminate()
        server_process.terminate()
        sys.exit(0)
    
    # Handle interrupts gracefully
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    try:
        # Wait for either process to finish
        css_process.wait()
        server_process.wait()
    except KeyboardInterrupt:
        cleanup(None, None)
    finally:
        cleanup(None, None) 