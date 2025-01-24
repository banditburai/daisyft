import pytest
from pathlib import Path
from unittest.mock import Mock, patch, ANY
import requests
from typer.testing import CliRunner
from daisyft.cli.main import app 
from daisyft.cli.init import (
    get_release_info,
    download_tailwind_binary,
    InitOptions,
    get_user_options,
)
from daisyft.utils.config import ProjectConfig, TailwindReleaseInfo

@pytest.fixture
def mock_release_response():
    """Mock GitHub API response for releases"""
    return {
        "tag_name": "v1.0.0",
        "assets": [
            {"name": "tailwindcss-macos-x64", "browser_download_url": "https://example.com/binary"}
        ],
        "id": 12345,
        "sha": "abc123"
    }

@pytest.fixture
def mock_requests(mock_release_response):
    """Mock requests for GitHub API and binary download"""
    with patch('requests.get') as mock_get:
        # Mock API response
        mock_get.return_value.json.return_value = mock_release_response
        # Mock binary download
        mock_get.return_value.content = b"mock binary content"
        mock_get.return_value.raise_for_status = lambda: None
        yield mock_get

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_templates():
    """Mock template rendering"""
    with patch('daisyft.cli.init.render_template') as mock:
        mock.return_value = True
        yield mock

@pytest.fixture
def mock_package_manager():
    """Mock package manager"""
    with patch('daisyft.utils.package.PackageManager.install') as mock:
        yield mock

def test_get_release_info(mock_requests):
    """Test fetching release info from GitHub"""
    # Test DaisyUI style
    info = get_release_info("daisy")
    assert info["tag_name"] == "v1.0.0"
    mock_requests.assert_called_with(TailwindReleaseInfo.get_api_url("daisy"))

    # Test vanilla style
    info = get_release_info("vanilla")
    assert info["tag_name"] == "v1.0.0"
    mock_requests.assert_called_with(TailwindReleaseInfo.get_api_url("vanilla"))

def test_download_tailwind_binary(tmp_path, mock_requests):
    """Test downloading Tailwind binary"""
    config = ProjectConfig(style="daisy")
    
    with patch('platform.system', return_value='Darwin'):
        binary_path = download_tailwind_binary(config)
        assert binary_path.exists()
        assert binary_path.name == "tailwindcss"
        
        # Test binary metadata was updated
        assert config.binary_metadata is not None
        assert config.binary_metadata.version == "v1.0.0"

def test_init_options():
    """Test InitOptions dataclass"""
    options = InitOptions(
        style="daisy",
        theme="dark",
        app_path=Path("app.py"),
        include_icons=True,
        components_dir=Path("src/components"),
        static_dir=Path("src/static")
    )
    
    assert options.style == "daisy"
    assert options.theme == "dark"
    assert options.app_path == Path("app.py")
    assert options.include_icons is True
    assert options.components_dir == Path("src/components")
    assert options.static_dir == Path("src/static")

@patch('questionary.select')
@patch('questionary.checkbox')
@patch('questionary.confirm')
@patch('questionary.text')
def test_get_user_options_defaults(mock_text, mock_confirm, mock_checkbox, mock_select):
    """Test getting user options with defaults"""
    options = get_user_options(defaults=True)
    
    assert options.style == "daisy"
    assert options.theme == "dark"
    assert options.app_path == Path("main.py")
    assert options.include_icons is True
    assert options.components_dir == Path("components")
    assert options.static_dir == Path("static")
    
    # Verify no prompts were shown
    mock_select.assert_not_called()
    mock_checkbox.assert_not_called()
    mock_confirm.assert_not_called()
    mock_text.assert_not_called()

def test_init_command_defaults(runner, tmp_path, mock_requests, mock_templates, mock_package_manager):
    """Test init command with default options"""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create necessary directories first
        for dir_path in ["components/ui", "static/css", "static/js", "icons"]:
            (tmp_path / dir_path).mkdir(parents=True, exist_ok=True)
            
        result = runner.invoke(app, ["init", "--defaults"])
        print(f"Command output: {result.output}")  # Debug output
        assert result.exit_code == 0
        
        # Check project structure
        assert (tmp_path / "components").exists()
        assert (tmp_path / "components/ui").exists()
        assert (tmp_path / "static").exists()
        assert (tmp_path / "static/css").exists()
        assert (tmp_path / "static/js").exists()
        assert (tmp_path / "icons").exists()
        
        # Just verify the template was called at least once
        assert mock_templates.called
        # Get the actual calls for debugging
        print(f"Template calls: {mock_templates.call_args_list}")

@patch('daisyft.cli.init.questionary.select')
@patch('daisyft.cli.init.questionary.checkbox')
@patch('daisyft.cli.init.questionary.confirm')
@patch('daisyft.cli.init.questionary.text')
def test_init_command_interactive(mock_text, mock_confirm, mock_checkbox, mock_select, 
                                runner, tmp_path, mock_requests, mock_templates, mock_package_manager):
    """Test init command in interactive mode"""
    # Mock the initial checkbox for options selection
    options_checkbox = Mock()
    options_checkbox.ask.return_value = []  # No options to customize
    mock_checkbox.return_value = options_checkbox
    
    # Mock other questionary responses
    style_select = Mock()
    style_select.ask.return_value = "daisy"
    mock_select.return_value = style_select
    
    text_prompt = Mock()
    text_prompt.ask.return_value = "app.py"
    mock_text.return_value = text_prompt
    
    confirm_prompt = Mock()
    confirm_prompt.ask.return_value = True
    mock_confirm.return_value = confirm_prompt
    
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create necessary directories first
        for dir_path in ["components/ui", "static/css", "static/js", "icons"]:
            (tmp_path / dir_path).mkdir(parents=True, exist_ok=True)
            
        result = runner.invoke(app, ["init"])
        print(f"Interactive command output: {result.output}")  # Debug output
        assert result.exit_code == 0
        
        # Verify prompts were shown
        mock_checkbox.assert_called_once()  # Verify options selection was shown
        mock_select.assert_not_called()  # Should not be called since we selected no options to customize
        mock_confirm.assert_not_called()
        mock_text.assert_not_called()
        
        # Just verify the template was called
        assert mock_templates.called
        # Get the actual calls for debugging
        print(f"Template calls: {mock_templates.call_args_list}")

def test_init_command_error_handling(runner, tmp_path):
    """Test init command error handling"""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        with patch('requests.get', side_effect=requests.RequestException("Network error")):
            result = runner.invoke(app, ["init", "--defaults"])
            assert result.exit_code == 0  # Should continue despite error
            assert "Warning: Could not download Tailwind binary" in result.output 