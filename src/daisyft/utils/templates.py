from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader("daisyft", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

def render_template(template_name: str, output_path: Path, **kwargs) -> None:
    """Render a template to a file"""
    template = env.get_template(template_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(template.render(**kwargs)) 