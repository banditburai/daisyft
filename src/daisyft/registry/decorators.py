# ============================================================================
#  Component Registry and Metadata
# ============================================================================
from __future__ import annotations
from typing import List, Optional, Type, TypeVar, Dict
from .base import (
    RegistryBase, 
    RegistryType, 
    RegistryMeta
)

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
                imports=kwargs.get('imports', []),
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
