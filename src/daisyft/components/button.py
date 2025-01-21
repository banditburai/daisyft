from daisyft.registry.decorators import Registry
from dataclasses import dataclass
from typing import Optional

@Registry.component(
    description="A button component with variants",
    categories=["ui"],
    author="daisyui"
)
@dataclass
class Button:
    variant: str = "default"
    size: str = "default"
    class_name: Optional[str] = None
    
    def render(self) -> str:
        classes = [
            "btn",
            f"btn-{self.variant}",
            f"btn-{self.size}",
            self.class_name or ""
        ]
        return f'<button class="{" ".join(c for c in classes if c)}">' 