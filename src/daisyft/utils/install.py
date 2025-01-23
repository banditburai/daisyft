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
    
    # Get source code
    source = inspect.getsource(component_class)
    
    # Process source code
    class_content = []
    in_class = False
    
    for line in source.split('\n'):
        # Skip registry decorator and imports we don't need
        if any(x in line for x in ['@Registry', 'from ..base', 'from ..decorators', 'from daisyft', 'DOCS =']):
            continue
            
        # Start collecting when we hit the class definition
        if line.startswith('class '):
            in_class = True
            # Remove RegistryBase from class definition
            line = line.replace('(RegistryBase)', '')
            class_content.append(line)
            continue
            
        if in_class:
            # Add the line to class content
            class_content.append(line)
    
    # Generate clean source
    clean_source = []
    
    # Add detailed docs if verbose
    if verbose and meta.detailed_docs:
        clean_source.append(meta.detailed_docs)
    
    # Add imports
    clean_source.extend(meta.imports)
    clean_source.append("")  # Empty line after imports
    
    # Add class
    clean_source.extend(class_content)
    
    # Write the file
    target_path = target_dir / f"{meta.name}.py"
    target_path.write_text('\n'.join(clean_source))    
