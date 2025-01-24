from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, ClassVar, Type
from pathlib import Path
from ..utils.config import ProjectConfig
import inspect

@dataclass
class TailwindConfig:
    content: List[str] = field(default_factory=list)
    theme: dict = field(default_factory=dict)
    plugins: List[str] = field(default_factory=list)

@dataclass
class CSSVars:
    light: dict = None
    dark: dict = None

    def __post_init__(self):
        self.light = self.light or {}
        self.dark = self.dark or {}

@dataclass
class RegistryFile:
    path: str
    type: RegistryType
    content: Optional[str] = None
    target: Optional[str] = None

class RegistryType(str, Enum):
    COMPONENT = "component"
    BLOCK = "block"
    UI = "ui"
    
    # Framework types
    LIB = "lib"
    HOOK = "hook"
    THEME = "theme"
    
    # Content types
    PAGE = "page"
    FILE = "file"

    @property
    def is_core(self) -> bool:
        return self in {self.COMPONENT, self.BLOCK, self.UI}

    @property
    def is_framework(self) -> bool:
        return self in {self.LIB, self.HOOK, self.THEME}

    @property
    def is_content(self) -> bool:
        return self in {self.PAGE, self.FILE}

@dataclass
class RegistryMeta:
    """Metadata for registry items"""
    name: str
    type: RegistryType
    description: Optional[str] = None
    author: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    tailwind: Optional[dict] = None
    detailed_docs: Optional[str] = None  # New field for detailed documentation

class RegistryBase:
    """Base class for registry components"""
    _registry_meta: ClassVar[RegistryMeta]

    @classmethod
    def get_install_path(cls, config: ProjectConfig) -> Path:
        """Get the installation path for this component"""
        meta = cls._registry_meta
        if meta.type == RegistryType.BLOCK:
            return (config.paths["components"] / meta.name 
                   if len(meta.files) > 1 
                   else config.paths["components"])
        return config.paths["ui"]

    @classmethod
    def install(cls, config: ProjectConfig, force: bool = False, verbose: bool = True) -> bool:
        """Install this component into the project"""
        meta = cls._registry_meta
        target_dir = Path(cls.get_install_path(config))
        target_dir.mkdir(parents=True, exist_ok=True)
        
        clean_source = []
        
        # Add detailed docs if verbose mode is on
        if verbose and meta.detailed_docs:
            # Format as a docstring
            clean_source.append('"""')
            clean_source.append(meta.detailed_docs.strip())
            clean_source.append('"""')
            clean_source.append("")  # Empty line after docs
        
        # Add imports
        if meta.imports:
            clean_source.extend(meta.imports)
            clean_source.append("")  # Empty line after imports
        
        # Get the class source
        source = inspect.getsource(cls)
        lines = source.split('\n')
        
        # Find the class definition
        for i, line in enumerate(lines):
            if line.startswith('class '):
                # Remove RegistryBase inheritance
                class_def = line.replace('(RegistryBase)', '')
                clean_source.append(class_def)
                # Add everything after the class definition
                clean_source.extend(lines[i+1:])
                break
        
        # Write the file
        target_path = target_dir / f"{meta.name}.py"
        target_path.write_text('\n'.join(clean_source))
        
        return True 