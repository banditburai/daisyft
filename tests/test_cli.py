import pytest
from pathlib import Path
from typer.testing import CliRunner
from daisyft.cli.main import app
from daisyft.utils.config import ProjectConfig
from daisyft.utils.toml_config import load_config, save_config
import datetime
from unittest.mock import patch

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
            "static": temp_project / "static",
            "css": temp_project / "static/css",
            "js": temp_project / "static/js",
        }
    )
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
        # Use 'build' command as an example that requires config
        result = runner.invoke(app, ["build"])
        # Expect exit code 1 due to missing config check in main callback
        assert result.exit_code == 1 
        assert "Project not initialized" in result.output

def test_cli_invalid_command(runner):
    """Test CLI behavior with invalid command"""
    # No config needed to check for invalid command
    result = runner.invoke(app, ["invalid-command"])
    assert result.exit_code == 2
    assert "No such command 'invalid-command'" in result.output

# Config Tests
def test_config_initialization(temp_project):
    """Test ProjectConfig initialization"""
    config = ProjectConfig(
        style="daisy",
        app_path=temp_project / "main.py"
    )
    assert config.style == "daisy"
    assert config.app_path == temp_project / "main.py"
    assert isinstance(config.paths["static"], Path)

def test_config_save_load(temp_project):
    """Test ProjectConfig save and load using utility functions"""
    config = ProjectConfig(style="daisy")
    config_path = temp_project / ".daisyft" / "daisyft.toml"
    
    # Ensure .daisyft dir exists
    config_path.parent.mkdir(exist_ok=True)
    
    save_config(config, config_path)
    assert config_path.exists()
    
    # Pass path explicitly to load_config for test isolation
    loaded_config = load_config(config_path)
    assert loaded_config is not None
    assert loaded_config.style == config.style
    # Convert loaded paths back to relative strings for comparison if necessary,
    # or compare Path objects directly if default factory guarantees consistency.
    # Comparing the objects directly is usually fine.
    assert loaded_config.paths == config.paths 

def test_config_binary_metadata(mocker):
    """Test ProjectConfig binary metadata handling"""
    config = ProjectConfig()
    # Mock datetime.now() specifically in the config module
    mock_dt = mocker.patch('daisyft.utils.config.datetime')
    mock_dt.now.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0)
    
    release_info = {
        "tag_name": "v1.0.0",
        # Removed fields no longer used by update_binary_metadata
        # "sha": "test-sha", 
        # "id": 123 
    }
    
    config.update_binary_metadata(release_info)
    assert config.binary_metadata is not None
    assert config.binary_metadata.version == "v1.0.0"
    assert config.binary_metadata.downloaded_at == mock_dt.now.return_value
    # Removed assertions for sha/release_id
    # assert config.binary_metadata.sha == "test-sha" 
    # assert config.binary_metadata.release_id == 123 

# --- Sync Command Tests --- 

def test_sync_config_missing(runner, temp_project):
    """Test sync command when config file is missing."""
    with runner.isolated_filesystem(temp_dir=temp_project):
        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 1
        # Check for the error message from the main callback, not the sync command
        assert "Project not initialized" in result.output
        assert "Please run daisyft init." in result.output # Check plain text

@pytest.mark.parametrize("force_flag, check_update_return, expect_download, expect_output", [
    ([], False, False, "binary is up to date"),  # No force, up to date
    ([], True, True, "updated successfully"),     # No force, update available
    (["--force"], False, True, "updated successfully"), # Force, up to date
    (["--force"], True, True, "updated successfully"),  # Force, update available
])
@patch('daisyft.cli.sync.load_config')
@patch('daisyft.cli.sync.save_config')
@patch('daisyft.cli.sync.check_for_binary_update')
@patch('daisyft.cli.sync.download_tailwind_binary')
@patch('pathlib.Path.exists') # Mock Path.exists globally for this test
def test_sync_command_scenarios(
    mock_exists, 
    mock_download, 
    mock_check_update, 
    mock_save, 
    mock_load, 
    runner, 
    temp_project, 
    force_flag, 
    check_update_return, 
    expect_download, 
    expect_output
):
    """Test sync command under various conditions (up-to-date, update, force)."""
    # Mock config file existence
    mock_exists.return_value = True 
    
    # Mock load_config to return a valid config object
    mock_config = ProjectConfig(style="daisy") # Create a dummy config
    mock_load.return_value = mock_config
    
    # Mock check_for_binary_update based on scenario
    mock_check_update.return_value = check_update_return

    # Ensure the .daisyft directory exists for isolated filesystem
    config_dir = temp_project / ".daisyft"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "daisyft.toml").touch() # Create dummy file

    with runner.isolated_filesystem(temp_dir=temp_project):
        cmd = ["sync"] + force_flag
        result = runner.invoke(app, cmd)
        
        print(f"Sync command output ({cmd}): {result.output}") # Debug output
        
        assert result.exit_code == 0
        assert expect_output in result.output
        
        mock_load.assert_called_once()
        mock_check_update.assert_called_once_with(mock_config)
        
        if expect_download:
            # Check if download was called (with force=True regardless of flag due to sync logic)
            mock_download.assert_called_once_with(mock_config, force=True)
            mock_save.assert_called_once_with(mock_config)
        else:
            mock_download.assert_not_called()
            mock_save.assert_not_called()
