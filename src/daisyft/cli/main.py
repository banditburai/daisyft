import typer
from pathlib import Path
from typing import Optional, List
from daisyft.cli import init, add, config, build, dev, run, sync
from .registry import commands as registry_commands
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
app.command()(add.add)
app.command()(build.build)
app.command()(dev.dev)
app.command()(run.run)
app.command()(sync.sync)
app.command()(config.config)

# Add registry commands as a group
app.add_typer(registry_commands.registry_app, name="registry")

@app.callback()
def callback(ctx: typer.Context):
    """
    [bold blue]DaisyFT CLI[/bold blue] - DaisyUI components for FastHTML projects
    
    A toolkit for building beautiful web interfaces with FastHTML, Tailwind CSS, and DaisyUI.
    
    [bold]Getting Started:[/bold]
    - Run [green]daisyft init[/green] to create a new project with minimal setup
    - Run [green]daisyft init --advanced[/green] for more configuration options
    - Run [green]daisyft dev[/green] to start the development server
    - Run [green]daisyft add button[/green] to add the Button component
    
    [dim]For more information, visit: https://github.com/banditburai/daisyft[/dim]
    """
    # Skip checks if we're running init
    if ctx.invoked_subcommand == "init":
        return

    if not Path("daisyft.toml").exists():
        if typer.confirm(
            "[yellow]No daisyft configuration found.[/yellow] Would you like to initialize a new project?",
            default=True
        ):
            ctx.invoke(init.init)
            raise typer.Exit()
        else:
            console.print("[red]Error:[/red] daisyft requires configuration to run. Use 'daisyft init' to set up a new project.")
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