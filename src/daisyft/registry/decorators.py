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
    # Core types
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
    name: str
    type: RegistryType
    description: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    dev_dependencies: List[str] = field(default_factory=list)
    registry_dependencies: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    tailwind: Optional[dict] = None
    css_vars: Optional[CSSVars] = None
    meta: dict = None
    docs: Optional[str] = None

    def __post_init__(self):
        self.dependencies = self.dependencies or []
        self.dev_dependencies = self.dev_dependencies or []
        self.registry_dependencies = self.registry_dependencies or []
        self.categories = self.categories or []
        self.files = self.files or []
        self.meta = self.meta or {}

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
        # Install dependencies first
        for dep in meta.dependencies:
            dep_class = Registry.get_component(dep)
            if dep_class and not (config.paths["ui"] / f"{dep}.py").exists():
                dep_class.install(config, force)

        # Install component files
        for file in meta.files:
            target_path = target_dir / file
            if target_path.exists() and not force:
                return False  # Signal that we need user confirmation
            
            render_template(
                f"components/{file}.jinja2",
                target_path,
                component=cls,
                meta=meta,
                config=config
            )
            files_written = True

        # Track the component installation with simplified metadata
        if files_written:
            config.add_component(
                name=meta.name,
                type=meta.type.value,
                path=target_dir / meta.files[0] if meta.files else target_dir
            )

        return files_written

T = TypeVar('T', bound=RegistryBase)

class Registry:
    _components: ClassVar[Dict[str, Type[RegistryBase]]] = {}
    _blocks: ClassVar[Dict[str, Type[RegistryBase]]] = {}

    @classmethod
    def register(cls, type: RegistryType, *, name: Optional[str] = None, **kwargs):
        def decorator(component_class: Type[RegistryBase]) -> Type[RegistryBase]:
            registry_name = name or component_class.__name__.lower()
            # Only use docstring if description not provided in kwargs
            if 'description' not in kwargs and component_class.__doc__:
                kwargs['description'] = component_class.__doc__
            meta = RegistryMeta(
                name=registry_name,
                type=type,
                **kwargs
            )
            component_class._registry_meta = meta
            
            if type == RegistryType.BLOCK:
                cls._blocks[registry_name] = component_class
            else:
                cls._components[registry_name] = component_class
            return component_class
        return decorator

    @classmethod
    def get_any(cls, name: str) -> Optional[Type[RegistryBase]]:
        """Get component or block by name"""
        return cls._components.get(name) or cls._blocks.get(name)

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
    def component(cls, **kwargs) -> Callable[[Type[T]], Type[T]]:
        return cls.register(type=RegistryType.COMPONENT, **kwargs)
        
    @classmethod
    def block(cls, **kwargs) -> Callable[[Type[T]], Type[T]]:
        return cls.register(type=RegistryType.BLOCK, **kwargs)

    @classmethod
    def get_component(cls, name: str) -> Optional[Type[RegistryBase]]:
        return cls._components.get(name)

    @classmethod
    def get_block(cls, name: str) -> Optional[Type[RegistryBase]]:
        return cls._blocks.get(name)

    @classmethod
    def get_by_category(cls, category: str) -> List[Type[RegistryBase]]:
        return [
            item for items in [cls._components.values(), cls._blocks.values()]
            for item in items 
            if hasattr(item, '_registry_meta') 
            and category in item._registry_meta.categories
        ]
