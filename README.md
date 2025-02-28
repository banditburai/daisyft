# DaisyFT

<div align="center">

<img src="assets/daisyft.svg" alt="DaisyFT Logo" width="300" />

*DaisyUI + FastHTML + Tailwind CSS = Beautiful Web Apps in Python*

[![PyPI version](https://badge.fury.io/py/daisyft.svg)](https://badge.fury.io/py/daisyft)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-daisyft.com-blue)](https://daisyft.com)

</div>

## Overview

DaisyFT is a toolkit for building beautiful web interfaces with [FastHTML](https://github.com/answerDotAI/fasthtml/), [Tailwind CSS](https://tailwindcss.com/), and [DaisyUI](https://daisyui.com/). It provides a streamlined workflow for creating modern, responsive web applications in Python.

## Documentation

Visit our comprehensive documentation at [daisyft.com](https://daisyft.com) for guides, examples, and API reference.

## Features

- 🚀 **Quick Setup**: Initialize a FastHTML project with Tailwind CSS and DaisyUI in seconds
- 🔄 **Live Reload**: Develop with instant feedback using the built-in dev server
- 🛠️ **Build System**: Optimize your CSS for production with a single command
- 🔌 **Sync Command**: Keep your Tailwind binary and configuration up to date

## Installation

```bash
pip install daisyft
```

## Quick Start

```bash
# Initialize a new project
daisyft init

# Start the development server
daisyft dev

# Build for production
daisyft build

# Build your css and run your app
daisyft run
```

## Commands

- `daisyft init`: Create a new project with minimal setup
- `daisyft init --advanced`: More configuration options
- `daisyft init --binaries`: Download Tailwind binaries only without modifying project files
- `daisyft dev`: Start the development server
- `daisyft build`: Build CSS for production
- `daisyft run`: Run the FastHTML application
- `daisyft sync`: Update Tailwind binary and configuration

## Configuration

DaisyFT uses a `daisyft.toml` file for configuration. This file is created automatically when you run `daisyft init` and used to customize the cli.

```toml
[project]
style = "daisy"  # Options: "daisy", "tailwind"
theme = "dark"   # Options: "dark", "light"
```

## Opinionated Project Structure

Here's the structure new projects default to, which can be customized:

```
my-project/
├── main.py              # Main FastHTML application
├── daisyft.toml         # DaisyFT configuration
├── static/              # Static assets
│   ├── css/             # CSS files
│   │   ├── input.css    # Tailwind/DaisyUI input
│   │   └── output.css   # Generated CSS
│   └── js/              # JavaScript files
└── components/          # FastHTML components
```

## Roadmap

- **Documentation**: ✅ Available at [daisyft.com](https://daisyft.com)
- **Component System**: A library of reusable UI components (coming soon)


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
