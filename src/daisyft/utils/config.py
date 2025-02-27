"""
Configuration data models for DaisyFT.
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Literal, Optional, Union, Any

@dataclass
class InitOptions:
    """Initialization options for project setup."""
    style: str = "daisy"
    theme: str = "dark"
    app_path: Path = Path("main.py")
    include_icons: bool = False
    include_datastar: bool = False
    components_dir: Path = Path("components")
    static_dir: Path = Path("static")
    verbose: bool = True
    template: str = "standard"

@dataclass
class BinaryMetadata:
    """Metadata about the Tailwind binary."""
    version: str
    downloaded_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for serialization."""
        return {
            "version": self.version,
            "downloaded_at": self.downloaded_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BinaryMetadata':
        """Create a BinaryMetadata instance from a dictionary."""
        if not data:
            return None
        
        # Filter to only include the fields we care about
        filtered_data = {
            "version": data.get("version", "unknown"),
            "downloaded_at": data.get("downloaded_at")
        }
        
        # Convert ISO format string to datetime
        if isinstance(filtered_data['downloaded_at'], str):
            filtered_data['downloaded_at'] = datetime.fromisoformat(filtered_data['downloaded_at'])
            
        return cls(**filtered_data)

@dataclass
class ComponentMetadata:
    """Metadata about an installed component."""
    name: str
    type: str
    path: Union[str, Path]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for serialization."""
        return {
            "name": self.name,
            "type": self.type,
            "path": str(self.path) if isinstance(self.path, Path) else self.path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComponentMetadata':
        """Create a ComponentMetadata instance from a dictionary."""
        if isinstance(data.get('path'), str):
            data['path'] = Path(data['path'])
        return cls(**data)

@dataclass
class ProjectConfig:
    """Main configuration for a DaisyFT project."""
    # Project settings
    style: str = "daisy"
    theme: str = "dark"
    app_path: Union[str, Path] = "main.py"
    include_icons: bool = False
    include_datastar: bool = False
    verbose: bool = True
    
    # For tracking style changes during reinitialization
    previous_style: Optional[str] = None
    
    # Server settings
    host: str = "127.0.0.1"
    port: int = 8000
    live: bool = True
    template: str = "standard"
    
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
    
    def update_from_options(self, options: InitOptions) -> None:
        """Update configuration from options object."""
        self.style = options.style
        self.theme = options.theme
        self.app_path = options.app_path
        self.include_icons = options.include_icons
        self.include_datastar = options.include_datastar
        self.verbose = options.verbose
        self.template = options.template
        
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
    
    def add_component(self, name: str, type_: str, path: Path) -> None:
        """Add a component to the configuration."""
        self.components[name] = ComponentMetadata(
            name=name,
            type=type_,
            path=path
        )
    
    def remove_component(self, name: str) -> bool:
        """Remove a component from the configuration."""
        if name in self.components:
            del self.components[name]
            return True
        return False
    
    def update_binary_metadata(self, release_info: dict) -> None:
        """Update binary metadata from release info."""
        self.binary_metadata = BinaryMetadata(
            version=release_info.get("tag_name", "unknown"),
            downloaded_at=datetime.now()
        ) 