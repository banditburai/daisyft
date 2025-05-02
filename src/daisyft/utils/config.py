"""
Configuration data models for DaisyFT.
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Literal, Optional, Union, Any

@dataclass
class InitOptions:
    """Options captured during the init process."""
    style: Literal["daisy", "vanilla"] = "daisy"
    theme: Literal["dark", "light", "default"] = "dark"
    app_path: Path = Path("main.py")
    static_dir: Path = Path("static")

@dataclass
class BinaryMetadata:
    """Metadata about the Tailwind binary."""
    version: str
    downloaded_at: datetime
    app_path: Union[str, Path] = "main.py"
    
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
class ProjectConfig:
    """Main configuration for a DaisyFT project."""
    # Project settings
    style: str = "daisy"
    theme: str = "dark"
    app_path: Union[str, Path] = "main.py"
    
    # For tracking style changes during reinitialization
    previous_style: Optional[str] = None
    
    # Server settings
    host: str = "localhost"
    port: int = 5000
    live: bool = True
    
    # Paths
    paths: Dict[str, Path] = field(default_factory=lambda: {
        "static": Path("static"),
        "css": Path("static/css"),
        "js": Path("static/js"),
    })
    
    # Metadata
    binary_metadata: Optional[BinaryMetadata] = None
    
    @property
    def is_initialized(self) -> bool:
        """Check if the project is initialized."""
        return self.binary_metadata is not None
    
    def update_from_options(self, options: InitOptions) -> None:
        """Update configuration from options object."""
        self.style = options.style
        self.theme = options.theme
        self.app_path = options.app_path
        
        # Update paths
        self.paths["static"] = options.static_dir
        self.paths["css"] = options.static_dir / "css"
        self.paths["js"] = options.static_dir / "js"
    
    def update_binary_metadata(self, release_info: Dict[str, Any]) -> None:
        """Update binary metadata from release info."""
        self.binary_metadata = BinaryMetadata(
            version=release_info.get("tag_name", "unknown"),
            downloaded_at=datetime.now()
        ) 