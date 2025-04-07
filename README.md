# Formula One MCP Server

[![PyPI version](https://img.shields.io/pypi/v/f1-mcp-server.svg)](https://pypi.org/project/f1-mcp-server/)
[![Python Versions](https://img.shields.io/pypi/pyversions/f1-mcp-server.svg)](https://pypi.org/project/f1-mcp-server/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server that provides Formula One racing data. This package exposes various tools for querying F1 data including event schedules, driver information, telemetry data, and race results.

## Features

- **Event Schedule**: Access the complete F1 race calendar for any season
- **Event Information**: Detailed data about specific Grand Prix events
- **Session Results**: Comprehensive results from races, qualifying sessions, sprints, and practice sessions
- **Driver Information**: Access driver details for specific sessions
- **Performance Analysis**: Analyze a driver's performance with lap time statistics
- **Driver Comparison**: Compare multiple drivers' performances in the same session
- **Telemetry Data**: Access detailed telemetry for specific laps
- **Championship Standings**: View driver and constructor standings for any season

## Installation

In a `uv` managed python project, add to dependencies by:

```bash
uv add f1-mcp-server
```

Alternatively, for projects using `pip` for dependencies:
```bash
pip install f1-mcp-server
```

To run the server inside your project:

```bash
uv run f1-mcp-server
```

Or to run it globally in isolated environment:

```bash
uvx f1-mcp-server
```

To install directly from the source:

```bash
git clone https://github.com/Machine-To-Machine/f1-mcp-server.git
cd f1-mcp-server
pip install -e .
```

## Usage

### Command Line

The server can be run in two modes:

**Standard I/O mode** (default):

```bash
uvx run f1-mcp-server
```

**SSE transport mode** (for web applications):

```bash
uvx f1-mcp-server --transport sse --port 8000
```

### Python API

```python
from f1_mcp_server import main

# Run the server with default settings
main()

# Or with SSE transport settings
main(port=9000, transport="sse")
```

## API Documentation

The server exposes the following tools via MCP:

| Tool Name | Description |
|-----------|-------------|
| `get_event_schedule` | Get Formula One race calendar for a specific season |
| `get_event_info` | Get detailed information about a specific Formula One Grand Prix |
| `get_session_results` | Get results for a specific Formula One session |
| `get_driver_info` | Get information about a specific Formula One driver |
| `analyze_driver_performance` | Analyze a driver's performance in a Formula One session |
| `compare_drivers` | Compare performance between multiple Formula One drivers |
| `get_telemetry` | Get telemetry data for a specific Formula One lap |
| `get_championship_standings` | Get Formula One championship standings |

See the FastF1 documentation for detailed information about the underlying data: [FastF1 Documentation](https://theoehrly.github.io/Fast-F1/)

## Dependencies

- anyio (>=4.9.0)
- click (>=8.1.8)
- fastf1 (>=3.5.3)
- mcp (>=1.6.0)
- numpy (>=2.2.4)
- pandas (>=2.2.3)
- uvicorn (>=0.34.0)

## Development

### Setup Development Environment

```bash
git clone https://github.com/Machine-To-Machine/f1-mcp-server.git
cd f1-mcp-server
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### Code Quality

```bash
# Run linting
uv run ruff check .

# Run formatting check
uv run ruff format --check .

# Run security checks
uv run bandit -r src/
```

### Contribution Guidelines

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Authors

- **Machine-To-Machine**

## Acknowledgements

This project leverages `FastF1`, an excellent Python package for accessing Formula 1 data. We are grateful to its maintainers and contributors.

This project was inspired by [rakeshgangwar/f1-mcp-server](https://github.com/rakeshgangwar/f1-mcp-server) which was written in TypeScript. The `f1_data.py` module was mostly adapted from their source code.
