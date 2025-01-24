from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, ClassVar, Type
from pathlib import Path
from ..utils.config import ProjectConfig
import inspect
import jinja2
import os

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
    def get_template_path(cls) -> Path:
        """Get the template path for this component"""
        # Use generic component template
        default_path = Path(__file__).parent.parent / "templates" / "component.py.jinja2"
        if default_path.exists():
            return default_path
        
        raise FileNotFoundError("Component template not found")

    @classmethod
    def install(cls, config: ProjectConfig, force: bool = False, verbose: bool = True) -> bool:
        """Install this component into the project"""
        meta = cls._registry_meta
        target_dir = Path(cls.get_install_path(config))
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Get template
        template_path = cls.get_template_path()
        template = jinja2.Template(template_path.read_text())
        
        # Extract component parts
        module = inspect.getmodule(cls)
        module_source = inspect.getsource(module)
        class_source = inspect.getsource(cls)
        
        # Get class body (skip decorator and get actual class content)
        class_lines = class_source.split('\n')
        in_class = False
        class_body_lines = []
        
        for line in class_lines:
            if line.strip().startswith('class '):
                in_class = True
                continue
            if in_class and not line.strip().startswith('@'):
                class_body_lines.append(line)
        
        class_body = '\n'.join(class_body_lines)
        
        # Get variants section if it exists
        variants_marker = f"#  {cls.__name__} Variants"
        variants_source = module_source.split(variants_marker)[1].strip() if variants_marker in module_source else ""
        
        # Prepare template context
        context = {
            'meta': meta,
            'verbose': verbose,
            'imports': meta.imports,
            'class_name': cls.__name__,
            'class_body': class_body,
            'variants_source': variants_source,
            'docs': meta.detailed_docs if verbose else None
        }
        
        # Render template
        content = template.render(**context)
        
        # Write file
        target_path = target_dir / f"{meta.name}.py"
        target_path.write_text(content)
        
        return True 