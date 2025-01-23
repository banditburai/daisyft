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
    
    clean_source = []
    
    # Explicitly get docs from registry meta
    if verbose and hasattr(meta, 'detailed_docs') and meta.detailed_docs:
        print(f"Adding docs: {meta.detailed_docs[:50]}...")  # Debug print
        clean_source.append(meta.detailed_docs)
        clean_source.append("")  # Empty line after docs
    
    # Add imports
    if hasattr(meta, 'imports'):
        clean_source.extend(meta.imports)
        clean_source.append("")  # Empty line after imports
    
    # Get the class source
    source = inspect.getsource(component_class)
    lines = source.split('\n')
    
    # Find the class definition
    for i, line in enumerate(lines):
        if line.startswith('class '):
            # Remove RegistryBase inheritance
            class_def = line.replace('(RegistryBase)', '')
            clean_source.append(class_def)
            # Add everything after the class definition
            clean_source.extend(lines[i+1:])
            break
    
    # Write the file
    target_path = target_dir / f"{meta.name}.py"
    print(f"Writing to {target_path} with verbose={verbose}")  # Debug print
    target_path.write_text('\n'.join(clean_source)) 
