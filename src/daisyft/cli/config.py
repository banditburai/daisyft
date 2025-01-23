from typing import Optional
import typer
from daisyft.utils.config import ProjectConfig
from daisyft.utils.console import console

app = typer.Typer()

@app.command()
def config(
    verbose: bool = typer.Option(
        None, 
        "--verbose/--brief", 
        help="Set documentation verbosity for components"
    ),
):
    """Configure project settings"""
    config = ProjectConfig.load()
    
    if verbose is not None:
        config.verbose = verbose
        config.save()
        console.print(f"Documentation verbosity set to: [green]{'verbose' if verbose else 'brief'}[/green]")
