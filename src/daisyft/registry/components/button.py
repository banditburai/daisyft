from dataclasses import dataclass
from typing import Optional, Union, List, Any
from fasthtml.common import *
from ..base import RegistryBase
from ..decorators import Registry
from daisyft.utils.templates import render_template
import inspect

@Registry.component(
    name="button",
    description="A versatile button component with multiple variants and states",
    categories=["ui"],
    dependencies=["python-fasthtml"],
    files=["button.py"],
    imports=[
        "from dataclasses import dataclass",
        "from typing import Optional, Union, List, Any",
        "from fasthtml.common import *"
    ],
    # Add CSS definitions for custom variants
    tailwind={
        "components": {
            # Custom button variants
            "btn-custom": """
                @apply btn bg-purple-500 text-white hover:bg-purple-600;
                /* Custom styles for the custom variant */
            """,
            "btn-gradient": """
                @apply btn bg-gradient-to-r from-cyan-500 to-blue-500 text-white border-0;
                /* Gradient button style */
            """
        }
    }
)
@dataclass
class Button(RegistryBase):
    """A versatile button component with multiple variants and states.
    
    This component wraps DaisyUI's button classes for easy use in FastHTML.
    
    Args:
        content: Button content (text, icons, or list of elements)
        variant: Color variant of the button
        size: Size variant of the button
        style: Style variant of the button
        modifier: Layout modifier for the button
        disabled: Whether the button is disabled
        loading: Whether to show a loading spinner
        cls: Additional custom classes
    
    Available Variants (colors):
        - default: Default button style
        - neutral: Neutral color
        - primary: Primary brand color
        - secondary: Secondary brand color
        - accent: Accent color
        - info: Information color
        - success: Success/positive color
        - warning: Warning color
        - error: Error/negative color
    
    Available Sizes:
        - xs: Extra small
        - sm: Small
        - md: Medium (default)
        - lg: Large
        - xl: Extra large
    
    Available Styles:
        - outline: Outlined variant
        - ghost: Ghost/transparent variant
        - link: Looks like a link
        - soft: Soft/subtle variant
    
    Available Modifiers:
        - wide: More horizontal padding
        - block: Full width button
        - square: 1:1 aspect ratio
        - circle: 1:1 aspect ratio with rounded corners
    
    States:
        - disabled: Applies disabled styling
        - loading: Shows loading spinner
    
    Examples:
        ```python
        # Basic button
        Button("Click me")
        
        # Primary button with icon
        Button([Icon("check"), "Submit"], variant="primary")
        
        # Large ghost button
        Button("Menu", style="ghost", size="lg")
        
        # Full width success button
        Button("Download", variant="success", modifier="block")
        
        # Loading state
        Button("Processing", loading=True)
        
        # Custom classes
        Button("Custom", cls="my-custom-class")
        ```
    
    Notes:
        - All DaisyUI button classes are supported
        - Custom classes can be added via the cls parameter
        - Content can be a string, element, or list of elements
        - Icons are automatically sized and positioned
    """
    content: Union[str, List, None] = None
    variant: str = "default"
    size: str = "md"
    style: Optional[str] = None  # outline, ghost, etc.
    modifier: Optional[str] = None  # wide, block, square, circle
    disabled: bool = False
    loading: bool = False
    cls: str = ""  # Additional classes

    def get_classes(self) -> str:
        """Combine all classes based on props"""
        classes = [
            # Base button class
            "btn",
            # Variant (color)
            f"btn-{self.variant}" if self.variant != "default" else "",
            # Size
            f"btn-{self.size}" if self.size != "md" else "",
            # Style (outline, ghost, etc)
            f"btn-{self.style}" if self.style else "",
            # Modifier (wide, block, etc)
            f"btn-{self.modifier}" if self.modifier else "",
            # States
            "btn-disabled" if self.disabled else "",
            "loading" if self.loading else "",
            # Custom classes
            self.cls
        ]
        return " ".join(filter(None, classes))

    def __ft__(self) -> Any:
        """Render the button component."""
        content = []
        if self.loading:
            content.append(Span(cls="loading loading-spinner"))
        
        if isinstance(self.content, (list, tuple)):
            content.extend(self.content)
        elif self.content is not None:
            content.append(self.content)
            
        return Button(
            *content,
            cls=self.get_classes(),
            role="button",
            tabindex="0" if not self.disabled else "-1",
            aria_disabled="true" if self.disabled else None,
        )