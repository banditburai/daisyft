"""
Variant System
=============

Shared utilities for creating component variants with DaisyUI support.
"""

from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any
import sys

@dataclass
class ComponentVariant:
    """Configuration for component variants."""
    classes: str
    content_wrapper: Optional[Callable] = None
    daisy: bool = True  # Defaults to True for dictionary variants

def variant(variants_dict_name: str):
    """
    Create a variant decorator factory for a specific component.
    
    Args:
        variants_dict_name: Name of the variants dictionary in the component module
            (e.g., 'BUTTON_VARIANTS', 'CARD_VARIANTS', etc.)
    """
    def variant_decorator(name: str, classes: str, *, daisy: bool = False):
        """
        Decorator to register complex component variants.
        
        Args:
            name: Identifier for the variant
            classes: CSS classes to apply
            daisy: Whether to include DaisyUI base classes
        """
        def decorator(func):
            # Get the module where the decorated function is defined
            module = sys.modules[func.__module__]
            
            # Ensure the module has the variants dict
            if not hasattr(module, variants_dict_name):
                setattr(module, variants_dict_name, {})
            
            # Get the variants dictionary
            variants = getattr(module, variants_dict_name)
            
            # Register the variant
            variants[name] = ComponentVariant(
                classes=classes,
                content_wrapper=func,
                daisy=daisy
            )
            return func
        return decorator
    return variant_decorator