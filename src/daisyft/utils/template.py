from pathlib import Path
from typing import TypedDict, Any
import jinja2
from .console import console

class TemplateContext(TypedDict):
    """Type hint for template rendering context"""
    style: str
    theme: str
    paths: dict[str, Path]
    port: int
    live: bool
    host: str
    components: dict[str, Any]
    binary_metadata: Any

def render_template(template_name: str, output_path: Path, context: TemplateContext) -> None:
    """Safely render a Jinja template to file"""
    env = jinja2.Environment(
        loader=jinja2.PackageLoader("daisyft"),
        autoescape=jinja2.select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    try:
        template = env.get_template(template_name)
        content = template.render(**context)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(content)
    except jinja2.TemplateError as e:
        console.print(f"[red]Template error in {template_name}:[/red] {e}")
        raise
    except OSError as e:
        console.print(f"[red]File write error for {output_path}:[/red] {e}")
        raise 