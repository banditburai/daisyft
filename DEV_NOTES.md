# ft-daisy Development Plan

## Overview
ft-daisy is a CLI tool for integrating/styling DaisyUI/tailwind components into FastHTML projects, heavily inspired by the shadcn/ui component system architecture but implemented in a more Pythonic way.

## Core Components

### 1. CLI Structure

1. User-facing CLI
- `ft-daisy init` - Initialize project
- `ft-daisy add` - Add components/blocks to project

2. Development CLI (for contributors)
- `ft-daisy dev` - Start development server
- `ft-daisy build` - Build registry
- `ft-daisy preview` - Preview blocks

Project Structure:
```
ft-daisy/
├── src/
│   └── daisyft/
│       ├── cli/
│       │   ├── main.py
│       │   ├── init.py
│       │   ├── add.py
│       │   └── dev/           # Development commands
│       │       ├── __init__.py
│       │       ├── server.py  # Dev server
│       │       └── build.py   # Registry builder
│       ├── registry/
│       │   ├── decorators.py  # Registry decorator system
│       │   ├── blocks/        # Block implementations
│       │   │   ├── __init__.py
│       │   │   ├── dashboard.py
│       │   │   └── marketing.py
│       │   └── components/    # Base components
│       │       ├── __init__.py
│       │       ├── button.py
│       │       └── card.py
│       ├── templates/         # Jinja2 templates
│       │   ├── components/
│       │   └── config/
│       └── utils/
│           ├── __init__.py
│           └── template.py
└── www/                      # Documentation + Preview site
    ├── blocks/               # Block previews
    ├── templates/           
    └── static/
```

Key changes:
- Replaced JSON registry files with Python modules
- Added templates directory for Jinja2 templates
- Organized components and blocks as Python packages
- Added utils for shared functionality

### 2. Project Initialization (`init`)
The init command will:
- Create TOML configuration file (daisyft.toml)
- Set up project structure:

  ```
  project/
  ├── components/
  │   └── ui/
  ├── static/
  │   ├── css/
  │   │   └── input.css    # All Tailwind config here
  │   ├── js/
  │   ├── sprite.svg
  │   └── icons/
  └── daisyft.toml
  ```

- Install required dependencies:
  - tailwindcss
  - daisyui
- Generate starter templates:
  - Basic main.py with FastHTML setup
  - CSS configuration
  - Example components

project/
├── static/
│   ├── css/
│   │   ├── input.css
│   │   └── output.css
│   ├── js/
│   │   └── theme.js
│   ├── icons/               # Individual SVG icons
│   │   ├── check.svg
│   │   └── arrow.svg
│   ├── images/             # Other image assets
│   │   └── logo.png
│   └── sprite.svg          # Compiled sprite sheet
├── components/
│   ├── ui/                 # Base UI components
│   │   ├── button.py
│   │   └── card.py
│   ├── dashboard/          # Dashboard components
│   │   ├── nav.py
│   │   └── sidebar.py
│   └── marketing/          # Marketing components
│       └── header.py
├── main.py
└── components.json

project/
├── components/
│   ├── ui/                 # Base UI components
│   │   ├── button.py
│   │   └── card.py
│   ├── dashboard/          # Complex multi-component blocks
│   │   ├── nav.py
│   │   └── sidebar.py
│   ├── marketing_header.py # Single-component blocks
│   └── pricing_table.py

The CLI could handle this automatically based on the block's complexity:
If block has multiple related components -> create subdirectory
If block is single component -> create underscore-named file
Does this feel more maintainable?



### 3. Modern Tailwind Integration
Instead of separate configuration files, Tailwind is configured directly in input.css:
```css
@import "tailwindcss";
@plugin "daisyui";

/* Theme configuration */
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
  }
  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 0 0% 100%;
  }
}

/* Component styles */
@layer components {
  .btn-primary {
    @apply bg-primary text-primary-foreground;
  }
}
```

### 3. Components Registry
Components are registered using Python decorators:

- Each component should include:
  - Python FastHTML component code
  - Associated styles
  - Documentation
  - Dependencies

```python
@Registry.component(
    description="A button component with variants",
    categories=["ui"],
    author="ft-daisy",
    tailwind=TailwindConfig(
        content=["./components/**/*.py"],
        theme={"extend": {"colors": {"primary": "#000"}}}
    ),
    css_vars=CSSVars(
        light={"button-bg": "#fff"},
        dark={"button-bg": "#000"}
    )
)
@dataclass
class Button:
    variant: str = "default"
    size: str = "default"
    # ... component implementation
```


### 5. Component Installation (`add`)
The add command will:
- Allow selection of components to add
- Handle dependencies between components
- Place components in correct project structure
- Update imports in main.py
- Add any required CSS classes

### 6. Registry System
The registry provides a type-safe way to:
- Track component metadata
- Manage dependencies
- Configure styling
- Handle documentation
- Organize components by category

Components can be:
- Base UI components (`@Registry.component`)
- Complex blocks (`@Registry.block`)
- Theme configurations (`RegistryType.THEME`)
- Utility hooks (`RegistryType.HOOK`)
- Page templates (`RegistryType.PAGE`)

## Implementation Phases

### Phase 1: Basic Structure
- [x] Create CLI framework with Typer
- [x] Implement basic init command
- [ ] Set up project templates
- [x] Create Python-based configuration system

### Phase 2: Component Registry
- [x] Design decorator-based registry system
- [ ] Create initial set of basic components
- [ ] Implement component dependency resolution
- [ ] Add component documentation

### Phase 3: Component Installation
- [ ] Implement add command
- [ ] Create component installation logic
- [ ] Add import management
- [ ] Implement template rendering

### Phase 4: Testing & Documentation
- [ ] Create test suite
- [ ] Write user documentation
- [ ] Create example projects
- [ ] Add error handling

## Technical Considerations

### FastHTML Integration
- Components need to work with FastHTML's FT objects([1](https://docs.fastht.ml/llms-ctx.txt))
- Support for HTMX attributes
- Handle both function-based and dataclass-based components

### DaisyUI Compatibility
- Ensure proper Tailwind/DaisyUI class handling
- Support themes/customization
- Handle component variants

### Project Structure
- Follow FastHTML best practices
- Maintain compatibility with existing FastHTML projects
- Support both new and existing project integration

## Future Enhancements
- Component preview functionality
- Custom component templates
- Theme management
- Interactive component configuration
- Component update mechanism



daisyft.toml

```python
from pathlib import Path
from daisyft import ProjectConfig, TailwindConfig

config = ProjectConfig(
    style="daisy",
    tailwind=TailwindConfig(
        css=Path("static/css/input.css"),
        output=Path("static/css/output.css")
    ),
    paths={
        "components": Path("components"),
        "ui": Path("components/ui"),
        "static": Path("static"),
        "icons": Path("static/icons")
    }
)
```