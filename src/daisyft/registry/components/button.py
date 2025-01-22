from dataclasses import dataclass
from typing import Optional, Union, List
from fasthtml.common import *
from ..decorators import Registry, RegistryType

@Registry.component(
    description="A versatile button component with multiple variants and states",
    categories=["ui"],
    dependencies=["python-fasthtml"],
    files=["button.py"],
    # Define all possible button classes for template generation
    tailwind={
        "components": {
            "button": {
                "base": "btn",
                "colors": {
                    "neutral": "btn-neutral",
                    "primary": "btn-primary",
                    "secondary": "btn-secondary",
                    "accent": "btn-accent",
                    "info": "btn-info",
                    "success": "btn-success",
                    "warning": "btn-warning",
                    "error": "btn-error",
                },
                "styles": {
                    "outline": "btn-outline",
                    "soft": "btn-soft",
                    "ghost": "btn-ghost",
                    "link": "btn-link",
                    "active": "btn-active",
                    "disabled": "btn-disabled",
                },
                "sizes": {
                    "xs": "btn-xs",
                    "sm": "btn-sm",
                    "md": "btn-md",
                    "lg": "btn-lg",
                    "xl": "btn-xl",
                },
                "modifiers": {
                    "wide": "btn-wide",
                    "block": "btn-block",
                    "square": "btn-square",
                    "circle": "btn-circle",
                }
            }
        }
    }
)
@dataclass
class Button:
    """A versatile button component with multiple variants and states."""
    content: Union[str, List, None] = None
    variant: str = "default"
    size: str = "md"
    style: Optional[str] = None
    modifier: Optional[str] = None
    disabled: bool = False
    loading: bool = False
    cls: str = ""
    
    def _get_variant_classes(self) -> str:
        """Get variant (color) classes."""
        variants = {
            "default": "btn",
            "neutral": "btn btn-neutral",
            "primary": "btn btn-primary",
            "secondary": "btn btn-secondary",
            "accent": "btn btn-accent",
            "info": "btn btn-info",
            "success": "btn btn-success",
            "warning": "btn btn-warning",
            "error": "btn btn-error",
        }
        return variants.get(self.variant, "btn")
    
    def _get_style_classes(self) -> str:
        """Get style modifier classes."""
        if not self.style:
            return ""
        styles = {
            "outline": "btn-outline",
            "soft": "btn-soft",
            "ghost": "btn-ghost",
            "link": "btn-link",
            "active": "btn-active",
        }
        return styles.get(self.style, "")

    def _get_modifier_classes(self) -> str:
        """Get layout modifier classes."""
        if not self.modifier:
            return ""
        modifiers = {
            "wide": "btn-wide",
            "block": "btn-block",
            "square": "btn-square",
            "circle": "btn-circle",
        }
        return modifiers.get(self.modifier, "")
    
    def _get_base_classes(self) -> str:
        """Get base button classes that are always applied."""
        return "inline-flex items-center justify-center gap-2 transition-colors"
    
    def _get_size_classes(self) -> str:
        """Get classes for the button size."""
        sizes = {
            "default": "",
            "lg": "btn-lg",
            "sm": "btn-sm",
            "xs": "btn-xs",
        }
        return sizes.get(self.size, "")
    
    def _get_state_classes(self) -> str:
        """Get classes for button states."""
        classes = []
        if self.disabled:
            classes.append("btn-disabled")
        if self.loading:
            classes.append("loading")
        return " ".join(classes)

    def render(self):
        """Render the button component.
        
        Customization:
        1. Override specific utilities with cls parameter
        2. Modify theme variables in input.css
        3. Add new variants by extending btn-* classes
        
        Example:
            # Override specific utilities
            Button("Custom", cls="rounded-full")
            
            # Add new variant in input.css
            '''
            @layer components {
              .btn-custom {
                @apply bg-brand-500 text-white hover:bg-brand-600;
              }
            }
            '''
            Button("Themed", variant="custom")
        """
        # Build the class list
        classes = [
            self._get_variant_classes(),
            self._get_style_classes(),
            self._get_modifier_classes(),
            self._get_size_classes(),
            self._get_state_classes(),
            self._get_base_classes(),
            "gap-2 [&_svg]:size-4 [&_svg]:shrink-0",  # Icon styling
            self.cls
        ]
        
        # Handle loading state
        content = []
        if self.loading:
            content.append(Span(cls="loading loading-spinner"))
        
        # Add main content
        if isinstance(self.content, (list, tuple)):
            content.extend(self.content)
        elif self.content is not None:
            content.append(self.content)
            
        return Div(
            *content,
            cls=" ".join(filter(None, classes)),
            role="button",
            tabindex="0" if not self.disabled else "-1",
            aria_disabled="true" if self.disabled else None,
        )

    @classmethod
    def install(cls, config, force=False) -> bool:
        """Install button component"""
        return super().install(config, force) 