# ============================================================================
#  Project Configuration and binary management
# ============================================================================

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Literal, Optional
from platform import system, machine
from .templates import render_template
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
    version: str
    path: Path

    def __post_init__(self):
        """Ensure path is a Path object"""
        if isinstance(self.path, str):
            self.path = Path(self.path)

    @classmethod
    def from_release_info(cls, release_info: dict, style: str) -> "BinaryMetadata":
        return cls(
            version=release_info.get("tag_name", "unknown"),
            path=Path(release_info.get("url", "unknown").split("/")[-1])
        )

@dataclass
class ComponentMetadata:
    """Metadata for installed components"""
    name: str
    type: str  # RegistryType
    path: Path

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
    binary_path: Path = field(default_factory=lambda: Path(
        sys.prefix) / "bin" / ProjectConfig.get_tailwind_binary_name()
    )
    
    def __post_init__(self):
        """Post-initialization checks"""
        # Only validate binary path if metadata exists
        if self.binary_metadata and not self.binary_path.exists():
            raise ValueError(f"Binary path {self.binary_path} does not exist")
        
        """Ensure all paths are absolute"""
        self.binary_path = self.binary_path.absolute()
        
        # Make all stored paths absolute
        self.app_path = self.app_path.absolute()
        for key in self.paths:
            if isinstance(self.paths[key], Path):
                self.paths[key] = self.paths[key].absolute()

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
        """Save config to a Python file"""
        context = {
            "binary_metadata": self.binary_metadata,
            "style": self.style,
            "theme": self.theme,
            "app_path": self.app_path,
            "paths": self.paths,
            "port": self.port,
            "live": self.live,
            "host": self.host,
            "include_icons": self.include_icons,
            "verbose": self.verbose,
            "components": self.components,
            "sys": sys,
            "Path": Path,
            "ProjectConfig": ProjectConfig
        }
        render_template("daisyft.conf.py.jinja2", path, **context)

    def update_binary_metadata(self, release_info: dict) -> None:
        """Update binary metadata from release info"""
        self.binary_metadata = BinaryMetadata(
            version=release_info['tag_name'],
            path=self.binary_path  # Use configured path
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
        
        # Update paths
        self.paths = {
            "components": options.components_dir,
            "ui": options.components_dir / "ui",
            "static": options.static_dir,
            "css": options.static_dir / "css",
            "js": options.static_dir / "js",
            "icons": options.static_dir / "icons" if options.include_icons else Path("_disabled")
        }

PlatformName = Literal["macos", "linux", "windows"]
Architecture = Literal["x64", "arm64"]

def detect_platform() -> tuple[PlatformName, Architecture]:
    """Detect current platform and architecture in a normalized way."""
    sys_name = system().lower()
    arch = machine().lower()
    
    # Determine platform
    platform_name: PlatformName = "windows"
    if sys_name == "darwin":
        platform_name = "macos"
    elif sys_name == "linux":
        platform_name = "linux"

    # Determine architecture
    architecture: Architecture = "x64"
    if arch in ("arm64", "aarch64"):
        architecture = "arm64"
    elif arch in ("x86_64", "amd64"):
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