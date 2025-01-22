"""UI Components Registry

This module automatically registers all UI components with the Registry system.
Each component should:
1. Inherit from RegistryBase
2. Use the @Registry.component decorator
3. Be imported here to register it
"""

from .button import Button

__all__ = [
    "Button",
]

# Add other components here as they're created 