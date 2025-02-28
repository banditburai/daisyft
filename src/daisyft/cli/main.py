import typer
from pathlib import Path
from typing import Optional, List
from daisyft.cli import init, config, build, dev, run, sync

from ..utils.console import console
from ..utils.toml_config import load_config

app = typer.Typer(
    name="daisyft",
    help="DaisyUI/Tailwind/Motion components for FastHTML projects",
    no_args_is_help=True,
    rich_markup_mode="rich"
)

# Register commands
app.command()(init.init)
app.command()(build.build)
app.command()(dev.dev)
app.command()(run.run)
app.command()(sync.sync)

@app.callback()
def callback(ctx: typer.Context):
    """
    [bold blue]DaisyFT CLI[/bold blue] - DaisyUI components for FastHTML projects
    
    A toolkit for building beautiful web interfaces with FastHTML, Tailwind CSS, and DaisyUI.
    
    [bold]Getting Started:[/bold]
    - Run [green]daisyft init[/green] to create a new project with minimal setup
    - Run [green]daisyft init --advanced[/green] for more configuration options
    - Run [green]daisyft init --binaries[/green] to download Tailwind binaries only
    - Run [green]daisyft dev[/green] to start the development server    
    - Run [green]daisyft sync[/green] to check for Tailwind binary updates
    
    [dim]For more information, visit: https://github.com/banditburai/daisyft[/dim]
    """
    # Skip checks if we're running init
    if ctx.invoked_subcommand == "init":
        return

    if not Path("daisyft.toml").exists():
        console.print("[yellow]No daisyft configuration found.[/yellow]")
        if typer.confirm(
            "Would you like to initialize a new project?",
            default=True
        ):
            ctx.invoke(init.init)
            raise typer.Exit()
        else:
            console.print("[red]Error:[/red] daisyft requires configuration to run. Use 'daisyft init' to set up a new project.")
            console.print("Tip: Use [green]daisyft init --binaries[/green] to download only the Tailwind binaries without modifying existing files.")
            raise typer.Exit(1)
    
    try:
        # Try to load config to validate it
        config = load_config(Path("daisyft.toml"))
    except Exception as e:
        console.print(f"[red]Error:[/red] Invalid daisyft.toml configuration: {e}")
        if typer.confirm("Would you like to reinitialize the project?", default=False):
            ctx.invoke(init.init)
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 