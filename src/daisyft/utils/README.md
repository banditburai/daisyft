# DaisyFT Utils Module

This directory contains utility modules for the DaisyFT project. The modules have been refactored to follow single responsibility principles and provide a clean, maintainable codebase.

## Module Structure

- **console.py**: Provides a consistent console interface using Rich.
- **config.py**: Contains data models for project configuration.
- **toml_config.py**: Handles TOML serialization and deserialization for configuration.
- **platform.py**: Manages platform detection and binary naming logic.
- **release_info.py**: Handles GitHub release information for Tailwind binaries.
- **downloader.py**: Manages downloading of Tailwind binaries.

## Design Principles

1. **Single Responsibility**: Each module has a clear, focused purpose.
2. **Dependency Management**: Dependencies flow in a logical direction, avoiding circular imports.
3. **Type Safety**: Type hints are used throughout for better IDE support and error prevention.
4. **Error Handling**: Comprehensive error handling with user-friendly messages.
5. **Documentation**: All functions and classes have docstrings explaining their purpose and usage.

## Configuration System

The project uses TOML for configuration, with the following components:

1. **Data Models** (`config.py`): Defines the structure of configuration data.
2. **Serialization** (`toml_config.py`): Handles reading and writing configuration to TOML files.
3. **Usage**: Other modules import and use these components as needed.

## Binary Management

Binary management is split across several modules:

1. **Platform Detection** (`platform.py`): Determines the correct binary name and location.
2. **Release Information** (`release_info.py`): Manages GitHub release data.
3. **Downloading** (`downloader.py`): Handles the actual download process with progress reporting.

## Usage Examples

```python
# Loading configuration
from daisyft.utils.toml_config import load_config
config = load_config()

# Downloading a binary
from daisyft.utils.downloader import download_tailwind_binary
binary_path = download_tailwind_binary(config) 