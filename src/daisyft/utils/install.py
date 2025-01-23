from pathlib import Path
import inspect
from typing import Type
import logging
from ..registry.base import RegistryBase
from ..utils.config import ProjectConfig

def install_component(
    component_class: Type[RegistryBase], 
    config: ProjectConfig,
    verbose: bool = True
) -> None:
    """Install a component into the user's project"""
    meta = component_class._registry_meta
    target_dir = Path(component_class.get_install_path(config))
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Build the output file content
    clean_source = []
    
    # Add detailed docs if verbose mode is on
    if verbose and meta.detailed_docs:
        clean_source.append(meta.detailed_docs)
        clean_source.append("")  # Empty line after docs
    
    # Add imports
    clean_source.extend(meta.imports)
    clean_source.append("")  # Empty line after imports
    
    # Get source code and split into lines
    source = inspect.getsource(component_class)
    lines = source.split('\n')
    
    # Find the actual class definition (skip decorators and DOCS)
    class_start = None
    for i, line in enumerate(lines):
        if line.startswith('class '):
            class_start = i
            break
    
    if class_start is not None:
        # Get class content, removing RegistryBase inheritance
        class_content = lines[class_start:]
        class_content[0] = class_content[0].replace('(RegistryBase)', '')
        clean_source.extend(class_content)
    
    # Write the file
    target_path = target_dir / f"{meta.name}.py"
    target_path.write_text('\n'.join(clean_source)) 
