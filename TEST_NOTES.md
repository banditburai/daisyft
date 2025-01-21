# daisyft Testing Plan

## CLI Tests

### Main CLI (`cli/main.py`)
- [x] Test CLI initialization and command registration
- [x] Test help text and command documentation
- [x] Test error handling for invalid commands
- [x] Test behavior without configuration
- [ ] Test version information display
- [ ] Test command aliases if any

### Init Command (`cli/init.py`)
- [ ] Test project initialization in empty directory
- [ ] Test initialization with existing project
- [ ] Test creation of project structure
  - Verify all directories are created
  - Verify all template files are generated
- [ ] Test dependency installation
  - Verify tailwindcss installation
  - Verify daisyui installation
- [ ] Test configuration file generation
- [ ] Test error handling
  - Invalid directory permissions
  - Missing dependencies
  - Corrupted templates

### Add Command (`cli/add.py`)
- [ ] Test component addition workflow
- [ ] Test interactive component selection
- [ ] Test dependency resolution
- [ ] Test component placement in project structure
- [ ] Test import updates in main.py
- [ ] Test CSS class additions
- [ ] Test error handling
  - Invalid component selection
  - Missing dependencies
  - File conflicts

### Development Commands (`cli/dev/`)

#### Server (`server.py`)
- [ ] Test development server startup
- [ ] Test file watching functionality
- [ ] Test live reload capabilities
- [ ] Test error handling during server operation

#### Build (`build.py`)
- [ ] Test registry building process
- [ ] Test component compilation
- [ ] Test error handling during build

## Registry Tests (`registry/`)

### Decorators (`decorators.py`)
- [x] Test `@Registry.component` decorator
  - [x] Test explicit description
  - [x] Test docstring description
  - [x] Test metadata registration
  - [x] Test category assignment
  - [x] Test author information
- [x] Test `@Registry.block` decorator
  - [x] Test block registration
  - [x] Test dependency tracking
- [x] Test component lookup methods
  - [x] Test direct component lookup
  - [x] Test block lookup
  - [x] Test category-based lookup
- [ ] Test validation of decorator parameters
- [ ] Test Tailwind configuration
- [ ] Test CSS variables

### Components (`registry/components/`)
- [ ] Test base component implementations
  - Button component
  - Card component
- [ ] Test component styling
- [ ] Test component variants
- [ ] Test component documentation
- [ ] Test component dependencies

### Blocks (`registry/blocks/`)
- [ ] Test dashboard block implementations
- [ ] Test marketing block implementations
- [ ] Test block composition
- [ ] Test block styling
- [ ] Test block documentation

## Configuration Tests
- [x] Test ProjectConfig initialization
- [x] Test configuration save/load functionality
- [x] Test component tracking
  - [x] Test adding components
  - [x] Test removing components
  - [x] Test component path resolution
- [x] Test binary metadata handling
- [ ] Test path resolution
- [ ] Test style configuration
- [ ] Test custom configuration options

## Template Tests (`templates/`)
- [ ] Test Jinja2 template rendering
- [ ] Test template variables
- [ ] Test template inheritance
- [ ] Test component templates
- [ ] Test configuration templates

## Utility Tests (`utils/`)
- [ ] Test template utilities
- [ ] Test file operations
- [ ] Test path handling
- [ ] Test configuration management

## Integration Tests
- [ ] Test complete project initialization flow
- [ ] Test component addition workflow
- [ ] Test build process
- [ ] Test development server
- [ ] Test with different project structures
- [ ] Test with existing FastHTML projects

## Performance Tests
- [ ] Test initialization time
- [ ] Test component addition performance
- [ ] Test build performance
- [ ] Test memory usage
- [ ] Test with large number of components

## Compatibility Tests
- [ ] Test FastHTML integration
  - FT object compatibility
  - HTMX attribute handling
- [ ] Test DaisyUI compatibility
  - Theme support
  - Class handling
- [ ] Test across different Python versions
- [ ] Test across different operating systems

## Documentation Tests
- [ ] Test CLI documentation accuracy
- [ ] Test component documentation generation
- [ ] Test example project documentation
- [ ] Test error message clarity

## Test Environment Setup
```python
@pytest.fixture
def temp_project():
    """Create temporary project directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def initialized_project(temp_project):
    """Create initialized project for testing"""
    # Initialize project
    return temp_project
```

## Test Categories
- Unit Tests: Individual component and function testing
- Integration Tests: Component interaction testing
- End-to-End Tests: Complete workflow testing
- Performance Tests: Speed and resource usage
- Documentation Tests: Accuracy and completeness

## Testing Tools
- pytest for test execution
- pytest-cov for coverage reporting
- pytest-mock for mocking
- pytest-asyncio for async testing
- black for code formatting
- mypy for type checking

## Continuous Integration
- GitHub Actions workflow
- Pre-commit hooks
- Automated testing on pull requests
- Coverage reporting 