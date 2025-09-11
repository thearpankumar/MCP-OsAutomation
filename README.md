# MCP WebAutomation

A comprehensive MCP (Model Context Protocol) server that provides system-level automation capabilities with real-time screen context awareness for AI agents like Claude Code and Gemini.

## Features

- **System-Level Automation**: Control mouse, keyboard, and desktop applications
- **Real-Time Screen Analysis**: Advanced OCR and computer vision for screen understanding
- **AI Context Integration**: Provide rich context to AI agents about current screen state
- **Cross-Platform Support**: Windows, macOS, and Linux compatibility
- **Safety-First Design**: Built-in permission system and safety mechanisms
- **High Performance**: Optimized for real-time automation workflows

## Technology Stack

- **FastMCP 2.0**: Modern MCP server framework
- **pynput**: Cross-platform input control
- **MSS**: Ultra-fast screenshot capture
- **PaddleOCR**: High-accuracy text extraction (96%+ accuracy)
- **OpenCV**: Computer vision and image analysis
- **Pillow**: Image processing and manipulation

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp-webautomation

# Install dependencies
pip install -e .

# For GPU acceleration (optional)
pip install -e .[gpu]

# For development
pip install -e .[dev]
```

## Quick Start

```python
from mcp_automation import WebAutomationServer

# Create and run the MCP server
server = WebAutomationServer()
server.run()
```

## Available MCP Tools

### Core Automation
- `capture_screen` - Multi-monitor screenshot with region selection
- `click_element` - Smart clicking with element detection
- `type_text` - Intelligent text input with context awareness
- `press_keys` - Keyboard shortcuts and combinations
- `scroll_area` - Directional scrolling with precision
- `drag_drop` - Advanced drag and drop operations

### Intelligence Tools
- `analyze_screen` - Full AI analysis of current screen state
- `find_text` - OCR-based text location and extraction
- `detect_ui_elements` - Computer vision element identification
- `get_screen_context` - Complete contextual understanding
- `wait_for_element` - Smart waiting with visual confirmation
- `suggest_actions` - AI-powered next step recommendations

### Safety & Control
- `request_permission` - User confirmation for sensitive actions
- `set_automation_bounds` - Define safe automation zones
- `emergency_stop` - Immediate halt all operations
- `validate_action` - Pre-action safety checks

## Platform Requirements

### macOS
- Accessibility permissions required for input control
- Python 3.10+ with pyobjc dependencies

### Linux
- X11 server required (Wayland through Xwayland)
- Additional packages: `python3-xlib`, `scrot`, `python3-tk`

### Windows
- No additional system requirements
- Run with appropriate permissions for automation

## Configuration

Create `configs/fastmcp.json` for server configuration:

```json
{
  "server": {
    "name": "WebAutomation",
    "version": "0.1.0"
  },
  "safety": {
    "require_confirmation": true,
    "automation_bounds": null,
    "max_actions_per_minute": 60
  },
  "ocr": {
    "engine": "paddleocr",
    "confidence_threshold": 0.8
  }
}
```

## Development

```bash
# Run tests
pytest

# Code formatting
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/
```

## License

MIT License - see LICENSE file for details.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.