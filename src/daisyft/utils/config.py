# ============================================================================
#  Project Configuration and binary management
# ============================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Literal, Optional
from platform import system, machine
from datetime import datetime
from functools import cached_property
from .templates import render_template
import typer

@dataclass(frozen=True)
class TailwindReleaseInfo:
    """Release information for Tailwind binaries"""
    DAISY_REPO = "banditburai/fastwindcss"
    VANILLA_REPO = "tailwindlabs/tailwindcss"
    VANILLA_VERSION = "v4.0.0-beta.9"  # Will change to "latest" when stable

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
    style: Literal["daisy", "vanilla"]
    version: str
    downloaded_at: datetime
    sha: str
    release_id: int

    @classmethod
    def from_release_info(cls, release_info: dict, style: str) -> "BinaryMetadata":
        return cls(
            style=style,
            version=release_info.get("tag_name", "unknown"),
            downloaded_at=datetime.now(),
            sha=release_info.get("sha", "unknown"),
            release_id=release_info.get("id", 0)
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
    verbose_docs: bool = True 
    host: str = "localhost"
    port: int = 5001
    live: bool = True 
    paths: Dict[str, Path] = field(default_factory=lambda: {
        "components": Path("components"),
        "ui": Path("components/ui"),
        "static": Path("static"),
        "css": Path("static/css"),
        "js": Path("static/js"),
        "icons": Path("static/icons")
    })
    binary_metadata: Optional[BinaryMetadata] = None
    components: Dict[str, ComponentMetadata] = field(default_factory=dict)
    
    def __post_init__(self):
        """Convert any string paths to Path objects"""
        if isinstance(self.app_path, str):
            self.app_path = Path(self.app_path)
        self.paths = {k: Path(v) if isinstance(v, str) else v 
                     for k, v in self.paths.items()}

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
        """Save config as a Python file using template"""
        render_template(
            "daisyft.conf.py.jinja2",
            path,
            style=self.style,
            theme=self.theme,
            app_path=self.app_path,
            paths=self.paths,
            binary_metadata=self.binary_metadata,
            port=self.port,
            live=self.live,
            host=self.host,
            include_icons=self.include_icons,
            verbose_docs=self.verbose_docs, 
            components=self.components
        )

    def update_binary_metadata(self, release_info: dict) -> None:
        """Update binary metadata from release info"""
        self.binary_metadata = BinaryMetadata.from_release_info(release_info, self.style)
        self.save()

    @cached_property
    def tailwind_binary_name(self) -> str:
        """Get the appropriate Tailwind binary name for the current system"""
        os_name = system().lower()
        arch = machine().lower()
        
        if os_name == "darwin":
            return f"tailwindcss-macos-{'arm64' if arch == 'arm64' else 'x64'}"
        elif os_name == "linux":
            return f"tailwindcss-linux-{'arm64' if arch == 'aarch64' else 'x64'}"
        else:
            return "tailwindcss-windows-x64.exe"

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