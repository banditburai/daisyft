import typer
from rich.console import Console
from pathlib import Path
from typing import Optional, List
from daisyft.cli import init, add
from . import build, dev, run, sync
from .registry import commands as registry_commands

app = typer.Typer(
    name="daisyft",
    help="DaisyUI/Tailwind/Motion components for FastHTML",
    no_args_is_help=True
)
console = Console()

# Register commands
app.command()(init.init)
app.command()(add.add)
app.command()(build.build)
app.command()(dev.dev)
app.command()(run.run)
app.command()(sync.sync)

# Add registry commands as a group
app.add_typer(registry_commands.registry_app, name="registry")

@app.callback()
def callback(ctx: typer.Context):
    """
    ft-daisy CLI - DaisyUI components for FastHTML projects
    
    Run 'daisyft init' to create a new project or 'daisyft add' to add components.
    """
    # Skip checks if we're running init
    if ctx.invoked_subcommand == "init":
        return

    if not Path("daisyft.conf.py").exists():
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
        from importlib.util import spec_from_file_location, module_from_spec
        spec = spec_from_file_location("daisyft_conf", "daisyft.conf.py")
        config_module = module_from_spec(spec)
        spec.loader.exec_module(config_module)
    except Exception as e:
        console.print(f"[red]Error:[/red] Invalid daisyft.conf.py configuration: {e}")
        if typer.confirm("Would you like to reinitialize the project?", default=False):
            ctx.invoke(init.init)
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 