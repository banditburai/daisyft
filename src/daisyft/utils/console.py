from rich.console import Console
from rich.theme import Theme

# Define custom theme/styles if needed
theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green",
    "command": "bold cyan",
})

# Create shared console instance
console = Console(theme=theme) 