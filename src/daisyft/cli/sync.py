import typer
from rich.console import Console
from pathlib import Path
from ..utils.config import ProjectConfig
from ..utils.templates import render_template
from jinja2 import Environment, PackageLoader
from ..registry.decorators import Registry
import re

console = Console()

def sync(
    config_path: str = typer.Option("daisyft.conf.py", "--config", "-c", help="Path to config file"),
    force: bool = typer.Option(False, "--force", "-f", help="Force overwrite without confirmation")
) -> None:
    """Sync main.py and input.css with current config values"""
    try:
        config = ProjectConfig.load(Path(config_path))
        config.ensure_initialized()
        
        # Sync main.py
        if config.app_path.exists() and not force:
            if not typer.confirm(
                f"\n{config.app_path} already exists. Overwrite?",
                default=False
            ):
                raise typer.Exit()
        
        render_template(
            "main.py.jinja2",
            config.app_path,
            style=config.style,
            theme=config.theme,
            paths=config.paths,
            port=config.port,
            live=config.live,
            host=config.host
        )
        
        # Generate CSS for all registered components
        css_content = generate_component_css(config)
        
        css_path = config.paths["css"] / "input.css"
        if css_path.exists() and not force:
            if not typer.confirm(
                f"\n{css_path} already exists. Update component styles?",
                default=False
            ):
                raise typer.Exit()
                
        update_css_file(css_path, css_content)
        
        console.print(f"[green]✓[/green] Synchronized {config.app_path} and {css_path} with current config")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

def generate_component_css(config: ProjectConfig) -> str:
    """Generate CSS for all registered components."""
    env = Environment(
        loader=PackageLoader('daisyft', 'templates'),
        trim_blocks=True,
        lstrip_blocks=True
    )
    template = env.get_template('input.css.jinja2')
    
    # Collect CSS configurations from registered components
    component_styles = {}
    for component in Registry._components.values():
        if hasattr(component, '_registry_meta'):
            meta = component._registry_meta
            if 'tailwind' in meta.__dict__:
                # Use the component's name as the key for template lookup
                component_name = meta.name.lower()  # e.g., "button" for template lookup
                component_styles[component_name] = meta.tailwind
    
    return template.render(
        components=component_styles,
        theme=config.theme,
        style=config.style
    )

def update_css_file(css_path: Path, new_content: str):
    """Update input.css while preserving custom styles."""
    if css_path.exists():
        with open(css_path) as f:
            existing_content = f.read()
            
        custom_sections = re.findall(
            r'/\* BEGIN CUSTOM STYLES \*/\n(.*?)/\* END CUSTOM STYLES \*/',
            existing_content,
            re.DOTALL
        )
        
        final_content = new_content
        if custom_sections:
            final_content += "\n\n/* BEGIN CUSTOM STYLES */\n"
            final_content += "\n".join(custom_sections)
            final_content += "\n/* END CUSTOM STYLES */\n"
    else:
        final_content = new_content
        
    css_path.write_text(final_content) 