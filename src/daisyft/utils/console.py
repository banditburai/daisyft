"""
Console utilities for DaisyFT.
"""
from rich.console import Console
from rich.theme import Theme

# Define custom theme/styles for consistent UI
theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green",
    "command": "bold cyan",
})

# Create a single console instance for consistent styling
console = Console(theme=theme) 