import typer
from pathlib import Path
from rich.console import Console
from ...utils.config import ProjectConfig

registry_app = typer.Typer(
    name="registry",
    help="Registry management commands",
    no_args_is_help=True
)

console = Console()

@registry_app.command()
def build(
    output_dir: str = typer.Option("registry", "--output", "-o", help="Output directory for registry"),
    force: bool = typer.Option(False, "--force", "-f", help="Force rebuild registry")
) -> None:
    """Build the component registry"""
    console.print("[bold]Building registry...[/bold]")
    # Registry building logic here
    console.print("[green]✓[/green] Registry built successfully!")

@registry_app.command()
def add(
    component: str = typer.Argument(..., help="Component to add to registry"),
    style: str = typer.Option("daisy", "--style", "-s", help="Component style"),
) -> None:
    """Add a component to the registry"""
    console.print(f"[bold]Adding {component} to registry...[/bold]")
    # Component addition logic here
    console.print("[green]✓[/green] Component added successfully!")

@registry_app.command()
def list():
    """List all components in the registry"""
    console.print("[bold]Available components:[/bold]")
    # List components logic here 