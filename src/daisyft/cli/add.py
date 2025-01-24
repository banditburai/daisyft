import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import questionary
from pathlib import Path
from typing import Optional, Type
from ..registry.base import RegistryBase
from ..registry.decorators import Registry
from ..utils.config import ProjectConfig
from ..utils.console import console

def add(
    component: Optional[str] = typer.Argument(None, help="Component or block to add"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
    verbose: bool = typer.Option(True, "--verbose/--brief", help="Include detailed documentation")
) -> None:
    """Add a component or block to your project"""
    
    # Ensure we're in a project
    if not Path("daisyft.conf.py").exists():
        console.print("[red]Error:[/red] Not in a daisyft project. Run 'daisyft init' first.")
        raise typer.Exit(1)
    
    config = ProjectConfig.load()
    
    # Get component selection
    component_name = component or _select_component_interactively()
    if not component_name:
        console.print("[red]No component selected[/red]")
        raise typer.Exit(1)
    
    # Get and validate component
    component_class = Registry.get_any(component_name)
    if not component_class:
        console.print(f"[red]Error:[/red] Component '{component_name}' not found")
        raise typer.Exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Installing component...", total=100)
        
        try:
            # Install dependencies first
            if component_class._registry_meta.dependencies:
                progress.update(task, description="Checking dependencies...")
                _install_dependencies(component_class, config, force, verbose)
            progress.update(task, advance=30)
            
            # Install the component
            progress.update(task, description="Installing component files...")
            if _should_install(component_class, config, force):
                component_class.install(config, force=True, verbose=verbose)
                
                # Track in config
                _track_component(component_class, config)
                
                # Sync project
                progress.update(task, description="Syncing project...")
                from .sync import sync_with_config
                sync_with_config(config, force)
                
            progress.update(task, advance=70)
            console.print(f"[green]✓[/green] Added {component_name} successfully!")
            
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            raise typer.Exit(1)

def _select_component_interactively() -> Optional[str]:
    """Handle interactive component selection"""
    component_type = questionary.select(
        "What would you like to add?",
        choices=["UI Component", "Block"]
    ).ask()
    
    if not component_type:
        return None
        
    choices = (Registry.get_available_components() 
              if component_type == "UI Component" 
              else Registry.get_available_blocks())
    
    selected = questionary.select(
        f"Select a {'component' if component_type == 'UI Component' else 'block'}:",
        choices=choices
    ).ask()
    
    return selected.split(":", 1)[0].strip().lower() if selected else None

def _should_install(component_class, config: ProjectConfig, force: bool) -> bool:
    """Check if component should be installed"""
    name = component_class._registry_meta.name
    if not force and config.has_component(name):
        return typer.confirm(f"{name} is already installed. Overwrite?")
    return True

def _install_dependencies(component_class, config: ProjectConfig, force: bool, verbose: bool) -> None:
    """Install component dependencies"""
    deps = component_class._registry_meta.dependencies
    if not deps:
        return
        
    for dep in deps:
        if not config.has_component(dep):
            dep_class = Registry.get_component(dep)
            if dep_class and _should_install(dep_class, config, force):
                dep_class.install(config, force=True, verbose=verbose)

def _track_component(component_class, config: ProjectConfig) -> None:
    """Track component in project config"""
    meta = component_class._registry_meta
    component_path = config.paths["ui"] / f"{meta.name}.py"
    config.add_component(
        name=meta.name,
        type=meta.type,
        path=component_path
    )
