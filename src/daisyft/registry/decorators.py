# ============================================================================
#  Component Registry and Metadata
# ============================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Type, TypeVar, Callable, Any, Protocol, Dict, ClassVar
from pathlib import Path
from ..utils.config import ProjectConfig
from ..utils.templates import render_template

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
    tailwind: Optional[dict] = None

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
    def install(cls, config: ProjectConfig, force: bool = False) -> bool:
        """Install this component and its dependencies"""
        meta = cls._registry_meta
        target_dir = cls.get_install_path(config)
        target_dir.mkdir(parents=True, exist_ok=True)

        files_written = False
        for file in meta.files:
            target_path = target_dir / file
            if target_path.exists() and not force:
                return False
            
            # Determine template name based on file extension
            template_name = f"components/{file}.jinja2"
            if file.endswith('.css'):
                template_name = f"components/{file[:-4]}.css.jinja2"
            elif file.endswith('.py'):
                template_name = f"components/{file[:-3]}.py.jinja2"
            
            render_template(
                template_name,
                target_path,
                component=cls,
                meta=meta,
                config=config
            )
            files_written = True

        return files_written

T = TypeVar('T', bound=RegistryBase)

class Registry:
    """Component and block registry"""
    _components: Dict[str, Type[RegistryBase]] = {}
    _blocks: Dict[str, Type[RegistryBase]] = {}

    @classmethod
    def register(cls, type: RegistryType, **kwargs):
        """Register a component or block"""
        def decorator(component_class: Type[T]) -> Type[T]:
            name = kwargs.get('name', component_class.__name__.lower())
            meta = RegistryMeta(
                name=name,
                type=type,
                description=kwargs.get('description') or component_class.__doc__,
                author=kwargs.get('author'),
                dependencies=kwargs.get('dependencies', []),
                files=kwargs.get('files', []),
                categories=kwargs.get('categories', []),
                tailwind=kwargs.get('tailwind')
            )
            component_class._registry_meta = meta
            
            registry = cls._blocks if type == RegistryType.BLOCK else cls._components
            registry[name] = component_class
            return component_class
        return decorator

    @classmethod
    def component(cls, **kwargs):
        """Register a component"""
        return cls.register(type=RegistryType.COMPONENT, **kwargs)

    @classmethod
    def block(cls, **kwargs):
        """Register a block"""
        return cls.register(type=RegistryType.BLOCK, **kwargs)

    @classmethod
    def get_any(cls, name: str) -> Optional[Type[RegistryBase]]:
        """Get component or block by name"""
        return cls._components.get(name) or cls._blocks.get(name)

    @classmethod
    def get_component(cls, name: str) -> Optional[Type[RegistryBase]]:
        """Get component by name"""
        return cls._components.get(name)

    @classmethod
    def get_block(cls, name: str) -> Optional[Type[RegistryBase]]:
        """Get block by name"""
        return cls._blocks.get(name)

    @classmethod
    def get_available_components(cls) -> List[str]:
        """Get list of available component descriptions"""
        return [
            f"{comp._registry_meta.name}: {comp._registry_meta.description}"
            for comp in cls._components.values()
        ]

    @classmethod
    def get_available_blocks(cls) -> List[str]:
        """Get list of available block descriptions"""
        return [
            f"{block._registry_meta.name}: {block._registry_meta.description}"
            for block in cls._blocks.values()
        ]

    @classmethod
    def get_by_category(cls, category: str) -> List[Type[RegistryBase]]:
        """Get all components and blocks in a category"""
        return [
            item for items in [cls._components.values(), cls._blocks.values()]
            for item in items 
            if category in item._registry_meta.categories
        ]
