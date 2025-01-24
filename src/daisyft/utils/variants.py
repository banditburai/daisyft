"""
Variant System
=============

Shared utilities for creating component variants with DaisyUI support.
"""

from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any

@dataclass
class ComponentVariant:
    """Configuration for component variants."""
    classes: str
    content_wrapper: Optional[Callable] = None
    daisy: bool = True  # Defaults to True for dictionary variants

def variant(name: str, classes: str, *, daisy: bool = False):  # Defaults to False for decorator variants
    """
    Decorator to register complex component variants.
    
    Args:
        name: Identifier for the variant
        classes: CSS classes to apply
        daisy: Whether to include DaisyUI base classes
    """
    def decorator(func):
        # The component needs to define its own VARIANTS dict
        # This will be accessed through the component's module
        func.__module__.VARIANTS[name] = ComponentVariant(
            classes=classes,
            content_wrapper=func,
            daisy=daisy
        )
        return func
    return decorator