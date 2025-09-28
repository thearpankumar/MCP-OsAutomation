# MCP WebAutomation Server Documentation

## Overview

The MCP WebAutomation Server is a comprehensive Model Context Protocol (MCP) server that provides AI agents with intelligent desktop automation capabilities. It combines advanced LLM vision analysis, cross-platform input control, and real-time screen understanding to enable sophisticated automation workflows.

## Architecture

The server is built on FastMCP 2.0 and provides a streamlined set of tools that allow AI agents to:
- Analyze screen content using LLM vision models (with optional OCR)
- Control mouse and keyboard input intelligently
- Perform automation tasks with semantic understanding
- Safely stop all automation activities

## Core Components

### 1. Screen Intelligence Engine
- **LLM Vision Analysis**: Uses OpenAI, Claude, and Gemini vision models for semantic screen understanding
- **Screenshot Capture**: Multi-monitor support with MSS (Multi-Screen Support)
- **OCR Engine**: LLM-based text extraction with fallback provider chain

### 2. Automation Controller
- **Cross-platform Input**: Mouse and keyboard control using pynput
- **Coordinate-based Actions**: Precise click, drag, and scroll operations
- **Keyboard Automation**: Key combinations and text input

### 3. Permission Management
- **Rate Limiting**: Configurable action limits for safety
- **Permission Levels**: Safe, moderate, and dangerous action classifications
- **Session Management**: Temporary and persistent permission grants

## Available Tools

The MCP WebAutomation server provides 5 streamlined tools optimized for LLM usage:

### `analyze_screen`
**Purpose**: Provides semantic understanding of screen content using LLM vision models.

**Parameters**:
- `include_ocr` (bool, default: false): Include OCR text extraction
- `analysis_detail` (string, default: "standard"): Detail level ("brief", "standard", "detailed")
- `region` (object, optional): Specific screen region {x, y, width, height}
- `monitor` (int, default: 0): Monitor number (0 for primary)
- `vision_provider` (string, default: "openai"): LLM provider ("openai", "claude", "gemini")

**Returns**:
```json
{
  "success": true,
  "screen_description": "VS Code editor with Python file open, terminal at bottom",
  "programs_detected": ["Visual Studio Code"],
  "ui_state": "Active development/coding session",
  "actionable_elements": "File tree, editor tabs, terminal commands",
  "visual_context": "Screen resolution: 1920x1080",
  "ocr_text": "...", // Only if include_ocr=true
  "provider_used": "openai"
}
```

**Use Cases**:
- Understanding current application state
- Workflow analysis and context awareness
- UI element identification for automation
- Screen state verification

---

### `click_element`
**Purpose**: Smart clicking by coordinates or element text.

**Parameters**:
- `x` (int, optional): X coordinate for click (if not using element_text)
- `y` (int, optional): Y coordinate for click (if not using element_text)
- `element_text` (string, optional): Text to find and click
- `button` (string, default: "left"): Mouse button ("left", "right", "middle")
- `clicks` (int, default: 1): Number of clicks

**Returns**:
```json
{
  "success": true,
  "x": 100,
  "y": 200,
  "button": "left",
  "clicks": 1,
  "message": "Click executed successfully",
  "completed": true
}
```

**Use Cases**:
- UI element interaction
- Button and menu activation
- Drag and drop operations (with multiple clicks)
- Context menu access (right-click)

---

### `type_text`
**Purpose**: Types text at the current cursor position.

**Parameters**:
- `text` (string): Text to type
- `delay` (float, default: 0.1): Delay between keystrokes in seconds
- `clear_first` (bool, default: false): Clear existing text before typing
- `submit` (bool, default: false): Press Enter after typing

**Returns**:
```json
{
  "success": true,
  "text": "Hello, World!",
  "delay": 0.1,
  "clear_first": false,
  "submit": false,
  "message": "Text typed successfully",
  "completed": true
}
```

**Use Cases**:
- Form filling and data entry
- Code and document editing
- Search query input
- Command line operations

---

### `press_key`
**Purpose**: Executes keyboard key combinations and shortcuts.

**Parameters**:
- `key` (string): Key to press ("enter", "tab", "escape", "f1-f12", etc.)
- `modifiers` (array, optional): Modifier keys (["ctrl"], ["ctrl", "shift"], etc.)

**Returns**:
```json
{
  "success": true,
  "key": "enter",
  "modifiers": ["ctrl"],
  "message": "Key combination executed: ctrl+enter",
  "completed": true
}
```

**Use Cases**:
- Keyboard shortcuts execution
- Navigation and window management
- Application-specific commands
- System-level operations

---

### `emergency_stop`
**Purpose**: Immediately stops all automation activities for safety.

**Parameters**: None

**Returns**:
```json
{
  "status": "stopped",
  "message": "All automation activities stopped",
  "timestamp": 1695123456.789
}
```

**Use Cases**:
- Emergency safety stop
- Halt runaway automation
- Reset automation state
- Safety testing and validation

## Configuration

### Environment Variables
```bash
# LLM API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_claude_api_key
GEMINI_API_KEY=your_gemini_api_key

# Server Configuration
MCP_SERVER_PORT=3000
MCP_SERVER_HOST=localhost
DEBUG_MODE=false
```

### Rate Limiting
- **Safe Actions**: 1000/hour (screenshots, mouse position)
- **Moderate Actions**: 100/hour (clicks, typing)
- **Dangerous Actions**: 10/hour (system commands)

## Usage Examples

### Basic Screen Analysis
```python
# Get semantic understanding of current screen
result = await client.call_tool("analyze_screen", {
    "analysis_detail": "standard",
    "vision_provider": "openai"
})

print(f"Programs: {result['programs_detected']}")
print(f"Activity: {result['ui_state']}")
print(f"Description: {result['screen_description']}")
```

### UI Automation Workflow
```python
# 1. Analyze screen to understand context
screen = await client.call_tool("analyze_screen", {
    "analysis_detail": "standard",
    "vision_provider": "openai"
})

print(f"Current state: {screen['screen_description']}")
print(f"Programs: {screen['programs_detected']}")

# 2. Click element by text (smart finding)
await client.call_tool("click_element", {
    "element_text": "Submit"
})

# Or use coordinates if known
await client.call_tool("click_element", {
    "x": 150,
    "y": 75
})
```

### Multi-Step Form Automation
```python
# Analyze screen first
screen = await client.call_tool("analyze_screen", {
    "include_ocr": true  # Include text extraction
})

# Fill and submit a form
await client.call_tool("click_element", {
    "element_text": "Name"  # Find name field by text
})
await client.call_tool("type_text", {
    "text": "John Doe",
    "clear_first": true
})

await client.call_tool("press_key", {"key": "tab"})  # Move to next field
await client.call_tool("type_text", {
    "text": "john@example.com"
})

# Submit with keyboard shortcut or button click
await client.call_tool("press_key", {
    "key": "enter",
    "modifiers": ["ctrl"]
})
```

## Error Handling

All tools return a consistent error format:
```json
{
  "success": false,
  "message": "Detailed error description",
  "error_code": "PERMISSION_DENIED",
  "timestamp": 1695123456.789
}
```

## Security Features

- **Permission-based access control**
- **Rate limiting per action type**
- **Safe mode for testing**
- **Session-based temporary permissions**
- **Audit logging for all actions**

## System Requirements

- **Python**: 3.8+
- **Operating Systems**: Windows, macOS, Linux
- **Dependencies**: FastMCP, pynput, MSS, PIL, aiohttp
- **Optional**: OpenAI, Anthropic, or Google API keys for vision analysis

## Installation and Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables in `.env` file
3. Configure Claude Code MCP connection in `~/.claude.json`:
```json
{
  "mcpServers": {
    "webautomation": {
      "command": "python",
      "args": [
        "<your-project-dir>/start_server.py",
        "--transport",
        "stdio"
      ],
      "cwd": "<your-project-dir>",
      "env": {
        "PATH": "<your-project-dir>/.venv/bin:$PATH"
      }
    }
  }
}
```
4. **Configure permissions** in `.claude/settings.local.json`:
```json
{
  "permissions": {
    "allow": [
      "mcp__webautomation__press_key",
      "mcp__webautomation__analyze_screen",
      "mcp__webautomation__click_element",
      "mcp__webautomation__type_text"
    ],
    "deny": [],
    "ask": []
  }
}
```
5. Test functionality: `python start_server.py --test`

## API Reference

For complete API documentation and integration examples, see the FastMCP 2.0 documentation and the included example implementations in the `tests/` directory.