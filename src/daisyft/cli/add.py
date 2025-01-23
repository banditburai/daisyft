import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import questionary
from pathlib import Path
from typing import Optional, Type
from ..registry.base import RegistryBase
from ..registry.decorators import Registry
from ..utils.config import ProjectConfig

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

        selected = questionary.select(
            f"Select a {'component' if component_type == 'UI Component' else 'block'}:",
            choices=choices
        ).ask()        
        
        if not selected:
            console.print("[red]No component selected[/red]")
            raise typer.Exit(1)
            
        # Extract just the component name from the selection string
        component = str(selected).split(":", 1)[0].strip().lower()

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
        
        try:
            # Check and install dependencies
            if component_class._registry_meta.dependencies:
                progress.update(task, description="Checking dependencies...")
                for dep in component_class._registry_meta.dependencies:
                    if not config.has_component(dep):
                        dep_class = Registry.get_component(dep)
                        if dep_class:
                            install_with_confirmation(dep_class, config, force)
            
            progress.update(task, advance=30)
            
            # Install the component files
            progress.update(task, description="Installing component files...")
            if install_with_confirmation(component_class, config, force):
                # Track the component in config
                component_path = config.paths["ui"] / f"{component}.py"
                config.add_component(
                    name=component,
                    type=component_class._registry_meta.type,
                    path=component_path
                )
                
                # Update project through sync command
                progress.update(task, description="Syncing project...")
                from .sync import sync_with_config
                sync_with_config(config, force)
                
            progress.update(task, advance=70)
            
            console.print(f"[green]✓[/green] Added {component} successfully!")
            
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            raise typer.Exit(1)

def install_with_confirmation(component_class: Type[RegistryBase], config: ProjectConfig, force: bool) -> bool:
    """Handle component installation with user confirmation. Returns True if installed."""
    if not force and config.has_component(component_class._registry_meta.name):
        if not typer.confirm(f"{component_class._registry_meta.name} is already installed. Overwrite?"):
            return False
    
    return component_class.install(config, force=True)
