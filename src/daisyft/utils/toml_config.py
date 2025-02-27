"""
TOML configuration utilities for DaisyFT projects.
"""
from pathlib import Path
import tomli
import tomli_w
import typer
from typing import Dict, Any, Optional

from .config import ProjectConfig, BinaryMetadata, ComponentMetadata
from .console import console

def load_config(config_path: Optional[Path] = None) -> ProjectConfig:
    """
    Load configuration from a TOML file.
    
    Args:
        config_path: Path to the configuration file (defaults to daisyft.toml in current directory)
        
    Returns:
        ProjectConfig object with loaded configuration
    """
    if config_path is None:
        config_path = Path("daisyft.toml")
        
    if not config_path.exists():
        return ProjectConfig()  # Return default config if file doesn't exist
    
    try:
        with open(config_path, "rb") as f:
            data = tomli.load(f)
        
        # Extract nested sections
        project_data = data.get('project', {})
        server_data = data.get('server', {})
        paths_data = data.get('paths', {})
        binary_data = data.get('binary')
        components_data = data.get('components', {})
        
        # Convert paths to Path objects
        paths = {}
        for key, value in paths_data.items():
            paths[key] = Path(value)
            
        # Convert app_path to Path
        if 'app_path' in project_data and isinstance(project_data['app_path'], str):
            project_data['app_path'] = Path(project_data['app_path'])
        
        # Process binary metadata
        binary_metadata = None
        if binary_data:
            binary_metadata = BinaryMetadata.from_dict(binary_data)
        
        # Process components
        components = {}
        for name, comp_data in components_data.items():
            if isinstance(comp_data, dict):  # Skip the empty table marker
                components[name] = ComponentMetadata.from_dict(comp_data)
        
        # Create config object
        config = ProjectConfig(
            style=project_data.get('style', ProjectConfig.style),
            theme=project_data.get('theme', ProjectConfig.theme),
            app_path=project_data.get('app_path', ProjectConfig.app_path),
            include_icons=project_data.get('include_icons', ProjectConfig.include_icons),
            include_datastar=project_data.get('include_datastar', ProjectConfig.include_datastar),
            verbose=project_data.get('verbose', ProjectConfig.verbose),
            host=server_data.get('host', ProjectConfig.host),
            port=server_data.get('port', ProjectConfig.port),
            live=server_data.get('live', ProjectConfig.live),
            template=project_data.get('template', ProjectConfig.template),
            paths=paths or ProjectConfig.paths,
            binary_metadata=binary_metadata,
            components=components
        )
        
        # Set previous_style if it exists in the data
        if 'previous_style' in project_data:
            config.previous_style = project_data['previous_style']
        
        return config
        
    except Exception as e:
        console.print(f"[red]Error loading configuration:[/red] {e}")
        return ProjectConfig()  # Return default config on error

def save_config(config: ProjectConfig, config_path: Optional[Path] = None) -> None:
    """
    Save configuration to a TOML file.
    
    Args:
        config: ProjectConfig object to save
        config_path: Path to save the configuration file (defaults to daisyft.toml in current directory)
    """
    if config_path is None:
        config_path = Path("daisyft.toml")
        
    try:
        # Convert to nested dictionary structure
        data = {
            'project': {
                'style': config.style,
                'theme': config.theme,
                'app_path': str(config.app_path),
                'include_icons': config.include_icons,
                'include_datastar': config.include_datastar,
                'verbose': config.verbose,
                'template': config.template,
            },
            'server': {
                'host': config.host,
                'port': config.port,
                'live': config.live,
            },
            'paths': {
                key: str(value) for key, value in config.paths.items()
            },
        }
        
        # Add previous_style if it exists
        if hasattr(config, 'previous_style') and config.previous_style is not None:
            data['project']['previous_style'] = config.previous_style
        
        # Add binary metadata if available
        if config.binary_metadata:
            data['binary'] = config.binary_metadata.to_dict()
        
        # Add components if available
        if config.components:
            data['components'] = {}
            for name, component in config.components.items():
                data['components'][name] = component.to_dict()
        
        # Write to file
        with open(config_path, "wb") as f:
            tomli_w.dump(data, f)
            
    except Exception as e:
        console.print(f"[red]Error saving configuration:[/red] {e}")
        raise typer.Exit(1) 