"""
TOML configuration utilities for DaisyFT projects.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, Union
import tomli
import tomli_w
import typer
from jinja2 import Environment, FileSystemLoader, Template
from ..utils.console import console

@dataclass
class BinaryMetadata:
    """Metadata about the Tailwind binary."""
    version: str
    downloaded_at: datetime
    sha: str
    release_id: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BinaryMetadata':
        """Create a BinaryMetadata instance from a dictionary."""
        if not data:
            return None
        
        # Convert ISO format string to datetime
        if isinstance(data.get('downloaded_at'), str):
            data['downloaded_at'] = datetime.fromisoformat(data['downloaded_at'])
            
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for serialization."""
        result = asdict(self)
        # Convert datetime to ISO format string
        if isinstance(result.get('downloaded_at'), datetime):
            result['downloaded_at'] = result['downloaded_at'].isoformat()
        return result

@dataclass
class ComponentMetadata:
    """Metadata about an installed component."""
    name: str
    type: str
    path: Union[str, Path]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComponentMetadata':
        """Create a ComponentMetadata instance from a dictionary."""
        if isinstance(data.get('path'), str):
            data['path'] = Path(data['path'])
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for serialization."""
        result = asdict(self)
        if isinstance(result.get('path'), Path):
            result['path'] = str(result['path'])
        return result

@dataclass
class ProjectConfig:
    """Main configuration for a DaisyFT project."""
    # Project settings
    style: str = "daisy"
    theme: str = "dark"
    app_path: Union[str, Path] = "main.py"
    include_icons: bool = True
    verbose: bool = True
    
    # Server settings
    host: str = "127.0.0.1"
    port: int = 8000
    live: bool = True
    
    # Paths
    paths: Dict[str, Union[str, Path]] = field(default_factory=lambda: {
        "components": "components",
        "ui": "components/ui",
        "static": "static",
        "css": "static/css",
        "js": "static/js",
        "icons": "static/icons",
    })
    
    # Metadata
    binary_metadata: Optional[BinaryMetadata] = None
    components: Dict[str, ComponentMetadata] = field(default_factory=dict)
    
    @property
    def is_initialized(self) -> bool:
        """Check if the project is initialized."""
        return self.binary_metadata is not None
    
    @classmethod
    def load(cls, config_path: Path = None) -> 'ProjectConfig':
        """Load configuration from a TOML file."""
        if config_path is None:
            config_path = Path("daisyft.toml")
            
        if not config_path.exists():
            return cls()  # Return default config if file doesn't exist
        
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
            config = cls(
                style=project_data.get('style', cls.style),
                theme=project_data.get('theme', cls.theme),
                app_path=project_data.get('app_path', cls.app_path),
                include_icons=project_data.get('include_icons', cls.include_icons),
                verbose=project_data.get('verbose', cls.verbose),
                host=server_data.get('host', cls.host),
                port=server_data.get('port', cls.port),
                live=server_data.get('live', cls.live),
                paths=paths or cls.paths,
                binary_metadata=binary_metadata,
                components=components
            )
            
            return config
            
        except Exception as e:
            console.print(f"[red]Error loading configuration:[/red] {e}")
            return cls()  # Return default config on error
    
    def save(self, config_path: Path = None) -> None:
        """Save configuration to a TOML file."""
        if config_path is None:
            config_path = Path("daisyft.toml")
            
        try:
            # Convert to nested dictionary structure
            data = {
                'project': {
                    'style': self.style,
                    'theme': self.theme,
                    'app_path': str(self.app_path),
                    'include_icons': self.include_icons,
                    'verbose': self.verbose,
                },
                'server': {
                    'host': self.host,
                    'port': self.port,
                    'live': self.live,
                },
                'paths': {
                    key: str(value) for key, value in self.paths.items()
                },
            }
            
            # Add binary metadata if available
            if self.binary_metadata:
                data['binary'] = self.binary_metadata.to_dict()
            
            # Add components if available
            if self.components:
                data['components'] = {}
                for name, component in self.components.items():
                    data['components'][name] = component.to_dict()
            
            # Write to file
            with open(config_path, "wb") as f:
                tomli_w.dump(data, f)
                
        except Exception as e:
            console.print(f"[red]Error saving configuration:[/red] {e}")
            raise typer.Exit(1)
    
    def update_from_options(self, options: Any) -> None:
        """Update configuration from options object."""
        self.style = options.style
        self.theme = options.theme
        self.app_path = options.app_path
        self.include_icons = options.include_icons
        self.verbose = options.verbose
        
        # Update paths
        self.paths["components"] = options.components_dir
        self.paths["ui"] = options.components_dir / "ui"
        self.paths["static"] = options.static_dir
        self.paths["css"] = options.static_dir / "css"
        self.paths["js"] = options.static_dir / "js"
        self.paths["icons"] = options.static_dir / "icons"
    
    def has_component(self, name: str) -> bool:
        """Check if a component is installed."""
        return name in self.components
    
    def add_component(self, name: str, type: str, path: Path) -> None:
        """Add a component to the configuration."""
        self.components[name] = ComponentMetadata(
            name=name,
            type=type,
            path=path
        )
    
    def remove_component(self, name: str) -> bool:
        """Remove a component from the configuration."""
        if name in self.components:
            del self.components[name]
            return True
        return False
    
    def render_template(self, template_path: Path, output_path: Path, context: Dict[str, Any] = None) -> None:
        """Render a template with configuration values."""
        # Create context with config values
        ctx = {
            'config': self,
            'now': datetime.now(),
        }
        
        # Add additional context if provided
        if context:
            ctx.update(context)
            
        # Load template
        env = Environment(loader=FileSystemLoader(template_path.parent))
        template = env.get_template(template_path.name)
        
        # Render and write to file
        content = template.render(**ctx)
        output_path.write_text(content)

# For backward compatibility with existing code
from ..utils.config import InitOptions 