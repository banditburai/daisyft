import pytest
from pathlib import Path
from typer.testing import CliRunner
from daisyft.cli.main import app
from daisyft.utils.config import ProjectConfig
from daisyft.registry.decorators import Registry, RegistryType

@pytest.fixture
def runner():
    """Create a CLI test runner"""
    return CliRunner()

@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory"""
    return tmp_path

@pytest.fixture
def mock_config(temp_project):
    """Create a mock project configuration"""
    config = ProjectConfig(
        style="daisy",
        app_path=temp_project / "main.py",
        paths={
            "components": temp_project / "components",
            "ui": temp_project / "components/ui",
            "static": temp_project / "static",
            "css": temp_project / "static/css",
            "js": temp_project / "static/js",
            "icons": temp_project / "icons"
        }
    )
    config_path = temp_project / "daisyft.conf.py"
    config.save(config_path)
    return config

# CLI Tests
def test_cli_help(runner):
    """Test CLI help text display"""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "DaisyUI/Tailwind/Motion components for FastHTML" in result.output

def test_cli_no_config(runner, temp_project):
    """Test CLI behavior without config file"""
    with runner.isolated_filesystem(temp_dir=temp_project):
        result = runner.invoke(app, ["add"], input="n\n")  # Answer no to init prompt
        assert result.exit_code == 1
        assert "No daisyft configuration found" in result.output

def test_cli_invalid_command(runner, mock_config, temp_project):
    """Test CLI behavior with invalid command"""
    with runner.isolated_filesystem(temp_dir=temp_project):
        result = runner.invoke(app, ["invalid-command"])
        assert result.exit_code == 2
        assert "No such command" in result.output

# Registry Tests
def test_registry_component_decorator():
    """Test Registry.component decorator"""
    # Test with explicit description
    @Registry.component(
        name="test-button",
        description="Test button component",
        categories=["ui"],
        author="test"
    )
    class TestButton:
        pass

    assert "test-button" in Registry._components
    meta = TestButton._registry_meta
    assert meta.name == "test-button"
    assert meta.type == RegistryType.COMPONENT
    assert meta.description == "Test button component"
    assert "ui" in meta.categories
    assert meta.author == "test"

    # Test with docstring description
    @Registry.component(
        name="test-button-2",
        categories=["ui"],
        author="test"
    )
    class TestButton2:
        """Docstring description"""
        pass

    meta2 = TestButton2._registry_meta
    assert meta2.description == "Docstring description"

def test_registry_block_decorator():
    """Test Registry.block decorator"""
    @Registry.block(
        name="test-block",
        description="Test block component",
        dependencies=["test-button"]
    )
    class TestBlock:
        pass

    assert "test-block" in Registry._blocks
    meta = TestBlock._registry_meta
    assert meta.name == "test-block"
    assert meta.type == RegistryType.BLOCK
    assert "test-button" in meta.dependencies

def test_registry_component_lookup():
    """Test Registry component lookup methods"""
    @Registry.component(name="lookup-test")
    class LookupTest:
        pass

    assert Registry.get_component("lookup-test") == LookupTest
    assert Registry.get_any("lookup-test") == LookupTest
    assert "lookup-test" in [c.split(":")[0].strip() for c in Registry.get_available_components()]

# Config Tests
def test_config_initialization(temp_project):
    """Test ProjectConfig initialization"""
    config = ProjectConfig(
        style="daisy",
        app_path=temp_project / "main.py"
    )
    assert config.style == "daisy"
    assert config.app_path == temp_project / "main.py"
    assert isinstance(config.paths["components"], Path)

def test_config_save_load(temp_project):
    """Test ProjectConfig save and load"""
    config = ProjectConfig(style="daisy")
    config_path = temp_project / "daisyft.conf.py"
    config.save(config_path)
    
    loaded_config = ProjectConfig.load(config_path)
    assert loaded_config.style == config.style
    assert loaded_config.paths == config.paths

def test_config_component_tracking(temp_project):
    """Test ProjectConfig component tracking"""
    config = ProjectConfig()
    config.add_component(
        name="test-component",
        type="component",
        path=temp_project / "components/ui/test.py"
    )
    
    assert config.has_component("test-component")
    assert config.get_component_path("test-component") == temp_project / "components/ui/test.py"
    
    config.remove_component("test-component")
    assert not config.has_component("test-component")

def test_config_binary_metadata():
    """Test ProjectConfig binary metadata handling"""
    config = ProjectConfig()
    release_info = {
        "tag_name": "v1.0.0",
        "sha": "test-sha",
        "id": 123
    }
    
    config.update_binary_metadata(release_info)
    assert config.binary_metadata.version == "v1.0.0"
    assert config.binary_metadata.sha == "test-sha"
    assert config.binary_metadata.release_id == 123
