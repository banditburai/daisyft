import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
import questionary
from pathlib import Path
from typing import Optional, Type
from ..registry.base import RegistryBase
from ..registry.decorators import Registry
from ..utils.toml_config import ProjectConfig
from ..utils.console import console
from rich.panel import Panel
from ..utils.package import PackageManager

def add(
    component: Optional[str] = typer.Argument(None, help="Component or block to add"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
    verbose: bool = typer.Option(True, "--verbose/--brief", help="Include detailed documentation"),
    package_manager: Optional[str] = typer.Option(None, "--pm", help="Package manager to use")
) -> None:
    """Add a component or block to your project
    
    This command is currently in preview mode with limited component availability.
    Only the Button component is fully implemented at this time.
    
    Examples:
        daisyft add button     # Add the Button component
    """
    
    # Ensure we're in a project
    if not Path("daisyft.toml").exists():
        console.print("[red]Error:[/red] Not in a daisyft project. Run 'daisyft init' first.")
        raise typer.Exit(1)
    
    config = ProjectConfig.load()
    
    # Show preview message
    console.print(Panel(
        "[yellow]This command is currently in preview mode.[/yellow]\n"
        "We're actively developing more components. Currently, only the Button component is available.\n"
        "Stay tuned for more components in future releases!",
        title="Component Registry Preview",
        expand=False
    ))
    
    # Simplified component selection - only Button for now
    available_components = ["button"]
    
    if not component:
        component = questionary.select(
            "Select a component to add:",
            choices=available_components,
            default="button"
        ).ask()
    
    if not component or component.lower() not in available_components:
        console.print(f"[red]Error:[/red] Component '{component}' not available yet.")
        console.print("Currently available components: " + ", ".join(available_components))
        raise typer.Exit(1)
    
    # Get and validate component
    component_class = Registry.get_any(component.lower())
    if not component_class:
        console.print(f"[red]Error:[/red] Component '{component}' not found in registry.")
        raise typer.Exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Installing component...", total=100)
        
        try:
            # Check for dependencies
            if hasattr(component_class, '_registry_meta') and component_class._registry_meta.dependencies:
                progress.update(task, description="Checking dependencies...", advance=20)
                for dependency in component_class._registry_meta.dependencies:
                    # If it's a Python package dependency
                    if dependency.startswith("pip:"):
                        pkg_name = dependency[4:]  # Remove 'pip:' prefix
                        console.print(f"Installing dependency: {pkg_name}")
                        
                        # Use our new PackageManager to install the dependency
                        success = PackageManager.install(
                            pkg_name,
                            manager=package_manager,
                            quiet=True
                        )
                        
                        if not success:
                            console.print(f"[yellow]Warning:[/yellow] Could not install dependency: {pkg_name}")
                            if not typer.confirm("Continue anyway?", default=False):
                                console.print("[yellow]Installation cancelled.[/yellow]")
                                return
            
            # Install the component
            progress.update(task, description="Installing component files...", advance=30)
            
            if config.has_component(component) and not force:
                if not typer.confirm(f"{component} is already installed. Overwrite?"):
                    console.print("[yellow]Installation cancelled.[/yellow]")
                    return
            
            # Install component
            component_class.install(config, force=True, verbose=verbose)
            
            # Track in config
            component_path = config.paths["ui"] / f"{component}.py"
            config.add_component(
                name=component,
                type=component_class._registry_meta.type,
                path=component_path
            )
            
            # Save the updated configuration
            config.save()
            
            # Sync project
            progress.update(task, description="Syncing project...", advance=50)
            from .sync import sync_with_config
            sync_with_config(config, force)
            
            console.print(f"\n[green]✓[/green] Added {component} successfully!")
            console.print("\nTo use this component, add the following import:")
            console.print(f"[bold]from components.ui.{component} import {component.title()}[/bold]")
            
            # Show example usage
            console.print("\n[bold]Example usage:[/bold]")
            if component == "button":
                console.print("""
Button("Click me")                      # Basic button
Button("Submit", var="primary")         # DaisyUI variant
Button("Custom", var="fancy-gradient")  # Custom variant
Button([Icon.check, "Submit"])          # With icon (requires ft-icons)
                """)
            
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            raise typer.Exit(1)
