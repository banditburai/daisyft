from typing import Optional
import typer
from daisyft.utils.config import ProjectConfig
from daisyft.utils.console import console

app = typer.Typer()

@app.command()
def config(
    verbose_docs: bool = typer.Option(
        None, 
        "--verbose-docs/--brief-docs", 
        help="Set documentation verbosity for components"
    ),
):
    """Configure project settings"""
    config = ProjectConfig.load()
    
    if verbose_docs is not None:
        config.verbose_docs = verbose_docs
        config.save()
        console.print(f"Documentation verbosity set to: [green]{'verbose' if verbose_docs else 'brief'}[/green]")
