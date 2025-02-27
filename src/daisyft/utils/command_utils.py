from pathlib import Path
from typing import List, Tuple, Protocol
from .config import ProjectConfig
from .console import console
from .platform import get_bin_dir, get_tailwind_binary_name

import typer

class CSSCommandBuilder(Protocol):
    """Protocol defining the CSS command builder interface"""
    def __call__(
        self,
        binary_path: Path,
        input_path: Path,
        output_path: Path,
        *,
        minify: bool = False,
        watch: bool = False
    ) -> List[str]: ...

def validate_binary(config: ProjectConfig) -> Path:
    """Validate Tailwind binary exists and return its path"""
    # Use platform utilities to determine binary path
    binary_path = get_bin_dir() / get_tailwind_binary_name()
    
    if not binary_path.exists():
        console.print(f"[red]Error:[/red] Tailwind binary missing at {binary_path}")
        console.print("Please run [bold]daisyft init --force[/bold] to download it")
        raise typer.Exit(1)
    return binary_path

def build_css_command(
    binary_path: Path,
    input_path: Path,
    output_path: Path,
    minify: bool = False,
    watch: bool = False
) -> List[str]:
    """Construct Tailwind CSS command with common options"""
    cmd = [
        str(binary_path.absolute()),
        "-i", str(input_path),
        "-o", str(output_path)
    ]
    
    # Conditional flag handling using list extension
    cmd.extend(["--minify"] if minify else [])
    cmd.extend(["--watch"] if watch else [])
    
    return cmd

def resolve_css_paths(
    config: ProjectConfig,
    input_override: str,
    output_override: str
) -> Tuple[Path, Path]:
    """Resolve input/output CSS paths from config and overrides"""
    input_path = Path(input_override) if input_override \
        else Path(config.paths["css"]) / "input.css"
    output_path = Path(output_override) if output_override \
        else Path(config.paths["css"]) / "output.css"
    return input_path, output_path 