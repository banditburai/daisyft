from dataclasses import dataclass
from typing import Union, List, Any, Dict
from fasthtml.common import Button as FastButton, Span
from ..decorators import Registry
from daisyft.utils.variants import ComponentVariant, variant

DOCS = """
Button Component
===============

A flexible button component that supports both DaisyUI and custom variants.

Usage:
    Button("Click me")                      # Basic button
    Button("Submit", var="primary")         # DaisyUI variant
    Button("Custom", var="fancy-gradient")  # Custom variant
    Button([Icon.check, "Submit"])       # With icon

Adding Variants:
1. DaisyUI variants (uses btn- classes):
    BUTTON_VARIANTS["primary"] = ButtonVariant("btn-primary")

2. Custom class-based variants:
    BUTTON_VARIANTS["custom"] = ButtonVariant("bg-purple-500...", daisy=False)

3. Complex variants with custom structure:
    @variant("fancy", "relative group...")
    def fancy_button(content):
        return [Span(...), Span(...)]
"""

@Registry.component(
    name="button",
    description="A versatile button component with multiple variants and states",
    categories=["ui"],
    dependencies=["python-fasthtml"],
    files=["button.py"],
    imports=[
        "from dataclasses import dataclass",
        "from typing import Union, List, Any, Optional, Callable, Dict",
        "from functools import partial",
        "from daisyft import ComponentVariant, variant",
        "from fasthtml.common import Button as FastButton, Span",
    ],
    detailed_docs=DOCS
)

@dataclass
class Button:
    """A button component that supports DaisyUI classes and custom variants."""
    content: Union[str, List[Any], None]
    cls: str = ""
    var: str = ""
    disabled: bool = False
    loading: bool = False

    def get_classes(self) -> str:
        """Generate the complete class string."""
        variant_config = BUTTON_VARIANTS.get(self.var, ButtonVariant(""))
        
        classes = []
        if variant_config.daisy:
            classes.append("btn")
        if variant_config.classes:
            classes.append(variant_config.classes)
        if self.cls:
            classes.append(self.cls)
        if self.disabled:
            classes.append("btn-disabled" if variant_config.daisy else "opacity-50 cursor-not-allowed")
        if self.loading:
            classes.append("loading" if variant_config.daisy else "")
            
        return " ".join(filter(None, classes))

    def prepare_content(self) -> List[Any]:
        """Prepare button content including loading state and wrappers."""
        variant_config = BUTTON_VARIANTS.get(self.var, ButtonVariant(""))
        
        content = []
        if self.loading:
            content.append(Span(cls="loading loading-spinner"))
        
        if isinstance(self.content, (list, tuple)):
            content.extend(self.content)
        elif self.content is not None:
            content.append(self.content)
            
        if variant_config.content_wrapper:
            content = variant_config.content_wrapper(self.content)
            
        return content

    def __ft__(self) -> Any:
        """Render the button component."""
        return FastButton(
            *self.prepare_content(),
            cls=self.get_classes(),
            tabindex="0" if not self.disabled else "-1",
            aria_disabled="true" if self.disabled else None,
            type="button"
        )

# ============================================================================
#  Button Variants
# ============================================================================

ButtonVariant = ComponentVariant

# Built-in DaisyUI variants
BUTTON_VARIANTS: Dict[str, ButtonVariant] = {
    # DaisyUI variants - implicit daisy=True
    "primary": ButtonVariant("btn-primary"),
    "secondary": ButtonVariant("btn-secondary"),
    "accent": ButtonVariant("btn-accent"),
    "info": ButtonVariant("btn-info"),
    "success": ButtonVariant("btn-success"),
    "warning": ButtonVariant("btn-warning"),
    "error": ButtonVariant("btn-error"),
    
    # Sizes
    "xs": ButtonVariant("btn-xs"),
    "sm": ButtonVariant("btn-sm"),
    "lg": ButtonVariant("btn-lg"),
    "xl": ButtonVariant("btn-xl"),
    
    # Styles
    "outline": ButtonVariant("btn-outline"),
    "ghost": ButtonVariant("btn-ghost"),
    "link": ButtonVariant("btn-link"),
    
    # Common combinations
    "sm-primary": ButtonVariant("btn-sm btn-primary"),
    "lg-secondary-outline": ButtonVariant("btn-lg btn-secondary btn-outline"),
    
    # Custom variants - explicit daisy=False needed
    "custom-purple": ButtonVariant(
        "px-5 py-2.5 rounded font-medium text-white "
        "bg-purple-500 hover:bg-purple-600 "
        "transition-colors duration-200",
        daisy=False
    ),
    
    "simple-gradient": ButtonVariant(
        "px-5 py-2.5 rounded font-medium text-white "
        "bg-gradient-to-r from-purple-500 to-pink-500 "
        "hover:from-purple-600 hover:to-pink-600 "
        "transition-all duration-300 border-0",
        daisy=False
    ),
}

# Complex custom variants
@variant("fancy-gradient",
    "px-5 py-2.5 relative rounded group font-medium text-white inline-block",
    daisy=False)
def fancy_gradient(content):
    """Complex button with custom structure."""
    text = content[0] if isinstance(content, (list, tuple)) else content
    return [
        Span(cls="absolute top-0 left-0 w-full h-full rounded opacity-50 filter blur-sm bg-gradient-to-br from-purple-600 to-blue-500"),
        Span(cls="h-full w-full inset-0 absolute mt-0.5 ml-0.5 bg-gradient-to-br filter group-active:opacity-0 rounded opacity-50 from-purple-600 to-blue-500"),
        Span(cls="absolute inset-0 w-full h-full transition-all duration-200 ease-out rounded shadow-xl bg-gradient-to-br filter group-active:opacity-0 group-hover:blur-sm from-purple-600 to-blue-500"),
        Span(cls="absolute inset-0 w-full h-full transition duration-200 ease-out rounded bg-gradient-to-br to-purple-600 from-blue-500"),
        Span(text, cls="relative")
    ]

@variant("slide-overlay",
    "relative inline-flex items-center justify-start inline-block px-5 py-3 overflow-hidden font-bold rounded-full group",
    daisy=False)
def slide_overlay(content):
    """Create sliding overlay button structure."""
    text = content[0] if isinstance(content, (list, tuple)) else content
    return [
        Span(cls="w-32 h-32 rotate-45 translate-x-12 -translate-y-2 absolute left-0 top-0 bg-white opacity-[3%]"),
        Span(cls="absolute top-0 left-0 w-48 h-48 -mt-1 transition-all duration-500 ease-in-out rotate-45 -translate-x-56 -translate-y-24 bg-white opacity-100 group-hover:-translate-x-8"),
        Span(text, cls="relative w-full text-left text-white transition-colors duration-200 ease-in-out group-hover:text-gray-900"),
        Span(cls="absolute inset-0 border-2 border-white rounded-full")
    ]

