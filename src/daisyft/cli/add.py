import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import questionary
from pathlib import Path
from typing import Optional, Type
from daisyft.registry.decorators import Registry, RegistryType, RegistryBase
from daisyft.utils.config import ProjectConfig
from daisyft.utils.templates import render_template

console = Console()

def add(
    component: Optional[str] = typer.Argument(None, help="Component or block to add"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
) -> None:
    """Add a component or block to your project"""
    
    # Verify we're in a daisyft project
    if not Path("daisyft.conf.py").exists():
        console.print("[red]Error:[/red] Not in a daisyft project.")
        console.print("\nTo create a new project, run:")
        console.print("  [bold]daisyft init[/bold]")
        console.print("\nOr cd into an existing daisyft project directory.")
        raise typer.Exit(1)
    
    # Load project configuration
    config = ProjectConfig.load()
    
    if not component:
        # Interactive component selection
        component_type = questionary.select(
            "What would you like to add?",
            choices=["UI Component", "Block"]
        ).ask()

        if component_type == "UI Component":
            choices = Registry.get_available_components()
        else:
            choices = Registry.get_available_blocks()

        if not choices:
            console.print(f"[yellow]No {'components' if component_type == 'UI Component' else 'blocks'} available[/yellow]")
            raise typer.Exit(1)

        selected = questionary.select(
            f"Select a {'component' if component_type == 'UI Component' else 'block'}:",
            choices=choices
        ).ask()
        component = selected.split(":")[0].lower()

    # Get component from registry
    component_class = Registry.get_any(component)
    if not component_class:
        console.print(f"[red]Error:[/red] Component '{component}' not found")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Installing component...", total=100)
        
        # Check and install dependencies
        if component_class._registry_meta.dependencies:
            progress.update(task, description="Checking dependencies...")
            for dep in component_class._registry_meta.dependencies:
                dep_class = Registry.get_component(dep)
                if dep_class and not (config.paths["ui"] / f"{dep}.py").exists():
                    # Install dependency component
                    install_with_confirmation(dep_class, config, force)
        
        progress.update(task, advance=50)
        
        # Install the component
        install_with_confirmation(component_class, config, force)
        progress.update(task, advance=50)

    console.print(f"[green]✓[/green] Added {component} successfully!")

def install_with_confirmation(component_class: Type[RegistryBase], config: ProjectConfig, force: bool) -> None:
    """Handle component installation with user confirmation"""
    if not component_class.install(config, force):
        if typer.confirm("Files already exist. Overwrite?"):
            component_class.install(config, force=True)

def update_tailwind_config(config: ProjectConfig, tailwind_config) -> None:
    """Update Tailwind configuration with component-specific settings"""
    input_css = config.paths["css"] / "input.css"
    if input_css.exists():
        # TODO: Implement Tailwind config merging
        pass 