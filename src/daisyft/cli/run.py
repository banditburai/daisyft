import typer
from pathlib import Path
import subprocess
import platform
import sys
from rich.console import Console
from ..utils.config import ProjectConfig

console = Console()

def get_binary_name() -> str:
    """Get platform-specific Tailwind binary name"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "darwin":  # macOS
        arch = "arm64" if machine == "arm64" else "x64"
        return f"tailwindcss-macos-{arch}"
    elif system == "linux":
        arch = "arm64" if machine in ["aarch64", "arm64"] else "x64"
        return f"tailwindcss-linux-{arch}"
    else:  # Windows
        return "tailwindcss-windows-x64.exe"

def run(
    browser: bool = typer.Option(False, "--browser", "-b", help="Open in browser"),
    sound: bool = typer.Option(False, "--sound", "-s", help="Play sound on start"),
    port: int = typer.Option(None, "--port", "-p", help="Port to run on"),
    no_live: bool = typer.Option(False, "--no-live", help="Disable live reload"),
) -> None:
    """Build CSS and run the FastHTML application"""
    config = ProjectConfig.load(Path("daisyft.conf.py"))
    
    # Use config values if not overridden
    port = port or config.port
    
    if no_live:
        config.live = False
        config.save()
    
    # Build CSS first
    console.print("[bold]Building CSS...[/bold]")
    try:
        subprocess.run([
            "./tailwindcss",
            "-i", str(Path(config.paths["css"]) / "input.css"),
            "-o", str(Path(config.paths["css"]) / "output.css")
        ], check=True)
        console.print("[green]✓[/green] CSS built successfully!")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error:[/red] Failed to build CSS: {e}")
        raise typer.Exit(1)
    
    # Play sound if requested
    if sound:
        try:
            system = platform.system().lower()
            if system == "darwin":
                subprocess.run(["afplay", "/System/Library/Sounds/Purr.aiff"])
            elif system == "linux":
                subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"])
            elif system == "windows":
                subprocess.run(['powershell', '-c', '(New-Object Media.SoundPlayer "C:\Windows\Media\notify.wav").PlaySync();'])
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not play sound: {e}")
    
    # Open browser if requested
    if browser:
        import webbrowser
        url = f"http://{config.host}:{port}"
        webbrowser.open(url)
    
    # Run the application using Python
    console.print(f"[bold]Starting FastHTML application on port {port}...[/bold]")
    try:
        subprocess.run([
            sys.executable, str(config.app_path)
        ], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error:[/red] Failed to start application: {e}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]") 