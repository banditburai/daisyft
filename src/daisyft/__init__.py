"""DaisyFT: Fast Tailwind Components"""
from .utils.config import ProjectConfig, BinaryMetadata, ComponentMetadata
from .registry.components import *  # This will register all components

__all__ = ['ProjectConfig', 'BinaryMetadata', 'ComponentMetadata']
__version__ = "0.1.0"
