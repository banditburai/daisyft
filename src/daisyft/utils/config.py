# ============================================================================
#  Project Configuration and binary management
# ============================================================================

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Literal, Optional
from platform import system, machine
from .template import render_template
import typer
import sys
import platform
import sysconfig

@dataclass
class InitOptions:
    """Initialization options for project setup"""
    style: str = "daisy"
    theme: str = "dark"
    app_path: Path = Path("main.py")
    include_icons: bool = True
    components_dir: Path = Path("components")
    static_dir: Path = Path("static")
    verbose: bool = True
    template: str = "standard"  # New field for template selection

@dataclass(frozen=True)
class TailwindReleaseInfo:
    """Release information for Tailwind binaries"""
    DAISY_REPO = "banditburai/fastwindcss"
    VANILLA_REPO = "tailwindlabs/tailwindcss"
    VANILLA_VERSION = "latest"  # Will change to "latest" when stable

    @classmethod
    def get_api_url(cls, style: Literal["daisy", "vanilla"]) -> str:
        """Get GitHub API URL for release info"""
        if style == "daisy":
            return f"https://api.github.com/repos/{cls.DAISY_REPO}/releases/latest"
        return f"https://api.github.com/repos/{cls.VANILLA_REPO}/releases/tags/{cls.VANILLA_VERSION}"

    @classmethod
    def get_download_url(cls, style: Literal["daisy", "vanilla"]) -> str:
        """Get base URL for binary downloads"""
        if style == "daisy":
            return f"https://github.com/{cls.DAISY_REPO}/releases/latest/download/"
        return f"https://github.com/{cls.VANILLA_REPO}/releases/download/{cls.VANILLA_VERSION}/"

@dataclass
class BinaryMetadata:
    """Metadata for Tailwind binary"""
    version: str  # Only store version

    @classmethod
    def from_release_info(cls, release_info: dict, style: str) -> "BinaryMetadata":
        return cls(
            version=release_info.get("tag_name", "unknown"),
        )

@dataclass
class ComponentMetadata:
    """Metadata for installed components"""
    name: str
    type: str  # RegistryType
    path: Path

    def __json__(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "path": str(self.path)
        }

@dataclass
class ProjectConfig:
    """Project configuration for daisyft"""
    style: Literal["daisy", "vanilla"] = "daisy"
    theme: str = "dark"
    app_path: Path = Path("main.py")
    include_icons: bool = True
    verbose: bool = True 
    host: str = "localhost"
    port: int = 5001
    live: bool = True 
    template: str = "standard"  # New field for template selection
    paths: Dict[str, Path] = field(default_factory=lambda: {
        "components": Path("components"),
        "ui": Path("components/ui"),
        "static": Path("static"),
        "css": Path("static/css"),
        "js": Path("static/js"),
        "icons": Path("icons")
    })
    binary_metadata: Optional[BinaryMetadata] = None
    components: Dict[str, ComponentMetadata] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization checks"""
        # Only validate binary path if metadata exists
        if self.binary_metadata and not self.binary_path.exists():
            raise ValueError(f"Binary path {self.binary_path} does not exist")
        
        """Ensure all paths are absolute"""
        for key in self.paths:
            if isinstance(self.paths[key], Path):
                self.paths[key] = self.paths[key].absolute()
    
    @property
    def binary_path(self) -> Path:
        """Dynamically resolve binary path relative to current environment"""
        return (Path(sys.prefix) / "bin" / self.get_tailwind_binary_name()).resolve()
    
    @classmethod
    def load(cls, path: Path = Path("daisyft.conf.py")) -> "ProjectConfig":
        """Load config from a Python file"""
        if not path.exists():
            return cls()  # Return defaults
                    
        from importlib.util import spec_from_file_location, module_from_spec
        spec = spec_from_file_location("daisyft_conf", path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, "config", cls())

    def save(self, path: Path = Path("daisyft.conf.py")) -> None:
        """Save configuration to file"""
        from json import dumps
        
        context = {
            "config": self,
            "config_json": dumps(self.__json__(), indent=2)
        }
        render_template("daisyft.conf.py.jinja2", path, context=context)

    def update_binary_metadata(self, release_info: dict) -> None:
        """Update binary metadata from release info"""
        self.binary_metadata = BinaryMetadata(
            version=release_info['tag_name'],            
        )
        self.save()

    @property
    def is_initialized(self) -> bool:
        """Check if this is an initialized project"""
        return Path("daisyft.conf.py").exists()

    def ensure_initialized(self) -> None:
        """Raise error if not in a project directory"""
        if not self.is_initialized:
            raise typer.Exit("Not in a daisyft project. Run 'daisyft init' first.")

    def add_component(self, name: str, type: str, path: Path) -> None:
        """Track an installed component"""
        self.components[name] = ComponentMetadata(
            name=name,
            type=type,
            path=path
        )
        self.save()
    
    def remove_component(self, name: str) -> None:
        """Remove a component from tracking"""
        if name in self.components:
            del self.components[name]
            self.save()
    
    def has_component(self, name: str) -> bool:
        """Check if a component is installed"""
        return name in self.components
    
    def get_component_path(self, name: str) -> Optional[Path]:
        """Get the installation path of a component"""
        if comp := self.components.get(name):
            return comp.path
        return None 

    @staticmethod
    def get_tailwind_binary_name() -> str:
        platform_name, architecture = detect_platform()
        if platform_name == "macos":
            return f"tailwindcss-macos-{architecture}"
        elif platform_name == "linux":
            return f"tailwindcss-linux-{architecture}"
        return "tailwindcss-windows-x64.exe" 
    
    def update_from_options(self, options: InitOptions) -> None:
        """Update config from initialization options"""
        self.style = options.style
        self.theme = options.theme
        self.app_path = options.app_path
        self.include_icons = options.include_icons
        self.verbose = options.verbose
        self.template = options.template  # Add template field
        
        # Update paths
        self.paths = {
            "components": options.components_dir,
            "ui": options.components_dir / "ui",
            "static": options.static_dir,
            "css": options.static_dir / "css",
            "js": options.static_dir / "js",
            "icons": options.static_dir / "icons" if options.include_icons else Path("_disabled")
        }

    def __json__(self) -> dict:
        """Custom serialization for template rendering"""
        return {
            "style": self.style,
            "theme": self.theme,
            "app_path": str(self.app_path),
            "include_icons": bool(self.include_icons),
            "verbose": bool(self.verbose),
            "host": self.host,
            "port": int(self.port),
            "live": bool(self.live),
            "template": self.template,  # Add template field
            "paths": {k: str(v) for k, v in self.paths.items()},
            "binary_metadata": {
                "version": self.binary_metadata.version if self.binary_metadata else "unknown"
            } if self.binary_metadata else None,
            "components": {
                name: {
                    "name": comp.name,
                    "type": comp.type,
                    "path": str(comp.path)
                }
                for name, comp in self.components.items()
            }
        }

PlatformName = Literal["macos", "linux", "windows"]
Architecture = Literal["x64", "arm64"]

def detect_platform() -> tuple[PlatformName, Architecture]:
    """Detect current platform and architecture in a normalized way."""
    # Platform detection with structural pattern matching
    match platform.system().lower():
        case "darwin":
            platform_name: PlatformName = "macos"
        case "linux":
            platform_name = "linux"
        case _:  # default case
            platform_name = "windows"

    # Architecture detection with pattern matching
    match machine().lower():
        case arch if arch in ("arm64", "aarch64"):
            architecture: Architecture = "arm64"
        case arch if arch in ("x86_64", "amd64"):
            architecture = "x64"
        case _:  # default case
            architecture = "x64"

    return platform_name, architecture

def get_bin_dir() -> Path:
    """Get platform-appropriate binary directory with venv awareness"""
    # Try to use sysconfig first (respects virtual environments)
    if scripts_path := sysconfig.get_path("scripts"):
        return Path(scripts_path)
    
    # Fallback for non-standard environments
    system = platform.system().lower()
    return Path(sys.prefix) / ("Scripts" if system == "windows" else "bin") 