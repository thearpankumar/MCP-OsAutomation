# MCP WebAutomation Installation Guide

## System Requirements

### Python Version
- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) - Modern Python package manager (recommended)
- pip (fallback option)

### Platform Requirements

#### Windows
- No additional system requirements
- Windows 10/11 recommended

#### macOS
- macOS 10.15 (Catalina) or higher
- Accessibility permissions required for automation
- Xcode Command Line Tools (for some dependencies)

#### Linux
- X11 server (for GUI automation)
- Additional packages required (see below)

## Installation Steps

### 1. Install uv (Recommended)
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on Windows:
# powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone the Repository
```bash
git clone <repository-url>
cd mcp-webautomation
```

### 3. Install Dependencies with uv

#### Basic Installation
```bash
# This will automatically create a virtual environment and install dependencies
uv sync
```

#### With Development Dependencies
```bash
uv sync --extra dev
```

#### With GPU Support
```bash
uv sync --extra gpu
```

#### With All Optional Dependencies
```bash
uv sync --all-extras
```

### Alternative: Install with pip (if uv not available)

#### Create Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install -e .           # Basic
pip install -e .[dev]      # With dev dependencies
pip install -e .[gpu]      # With GPU support
pip install -e .[dev,gpu]  # With all extras
```

### 4. Platform-Specific Setup

#### Linux Additional Packages
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install scrot python3-tk python3-dev

# For X11 support
sudo apt-get install python3-xlib

# Install system dependencies for OpenCV
sudo apt-get install libglib2.0-0 libsm6 libxrender1 libxext6 libfontconfig1 libice6
```

#### macOS Setup
```bash
# Install Xcode Command Line Tools if not already installed
xcode-select --install

# Install dependencies via Homebrew (optional)
brew install tesseract
```

The macOS dependencies (pyobjc) will be automatically installed via pip.

#### Windows Setup
No additional setup required. All dependencies will be installed automatically.

### 5. Verify Installation
```bash
# Activate virtual environment (if using uv)
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate   # On Windows

# Test basic functionality
python start_server.py --test

# Or run the basic usage example
python examples/basic_usage.py
```

## Permission Setup

### macOS Accessibility Permissions
1. Open System Preferences → Security & Privacy → Privacy
2. Select "Accessibility" from the left panel
3. Click the lock icon and enter your password
4. Add your Terminal application and/or Python executable
5. Ensure the checkboxes are checked

### Linux X11 Setup
Ensure you have a running X11 server and the DISPLAY environment variable is set:
```bash
echo $DISPLAY  # Should output something like :0 or :1
```

If running over SSH, use X11 forwarding:
```bash
ssh -X username@hostname
```

## Configuration

### Basic Configuration
The default configuration file is located at `configs/fastmcp.json`. You can modify it to suit your needs:

```json
{
  "server": {
    "name": "WebAutomation",
    "debug": false
  },
  "safety": {
    "require_confirmation": true,
    "max_actions_per_minute": 60
  },
  "ocr": {
    "engine": "paddleocr",
    "confidence_threshold": 0.8,
    "languages": ["en"]
  }
}
```

### Safety Settings
For security, the default configuration requires confirmation for automation actions. To disable this for trusted environments:

```json
{
  "safety": {
    "require_confirmation": false
  }
}
```

## Running the Server

### Stdio Transport (Default)
```bash
python start_server.py
```

### WebSocket Transport
```bash
python start_server.py --transport ws
```

### Debug Mode
```bash
python start_server.py --debug
```

### Custom Configuration
```bash
python start_server.py --config my-config.json
```

## Troubleshooting

### Common Issues

#### "PaddleOCR not found" Error
```bash
pip install paddleocr
```

#### "MSS import error" on Linux
```bash
sudo apt-get install scrot
pip install mss
```

#### "pynput not working" on macOS
1. Ensure accessibility permissions are granted
2. Try running from Terminal instead of IDE
3. Check that Terminal has accessibility permissions

#### "OpenCV import error"
```bash
pip install opencv-python
```

#### Import Errors
Make sure you're in the correct directory and virtual environment:
```bash
cd mcp-webautomation
source venv/bin/activate  # or venv\Scripts\activate on Windows
python start_server.py --test
```

### Performance Issues

#### Slow OCR Processing
1. Install GPU support: `pip install -e .[gpu]`
2. Reduce OCR confidence threshold in config
3. Process smaller screen regions

#### High Memory Usage
1. Enable debug mode to monitor resource usage
2. Adjust image processing settings
3. Implement region-based processing

### Log Files
Check the log files in the `logs/` directory for detailed error information:
```bash
tail -f logs/webautomation.log
```

## Integration with AI Assistants

### Claude Code Integration

Claude Code natively supports MCP servers. To integrate MCP WebAutomation:

#### 1. Start the MCP Server
```bash
# In your project directory
source .venv/bin/activate  # Activate virtual environment
python start_server.py --transport stdio
```

#### 2. Configure Claude Code
Add the server configuration to your Claude Code settings:

**Option A: Using claude_config.json**
```json
{
  "mcpServers": {
    "webautomation": {
      "command": "python",
      "args": ["/path/to/mcp-webautomation/start_server.py", "--transport", "stdio"],
      "cwd": "/path/to/mcp-webautomation",
      "env": {
        "PATH": "/path/to/mcp-webautomation/.venv/bin:$PATH"
      }
    }
  }
}
```

**Option B: Using environment variables**
```bash
export MCP_WEBAUTOMATION_PATH="/path/to/mcp-webautomation"
export MCP_WEBAUTOMATION_PYTHON="$MCP_WEBAUTOMATION_PATH/.venv/bin/python"
```

#### 3. Available Tools in Claude Code
Once connected, Claude Code will have access to:
- `capture_screen` - Take screenshots for analysis
- `analyze_screen` - Get AI-powered screen analysis
- `find_text` - Locate text on screen using OCR
- `click_element` - Click on UI elements
- `type_text` - Type text with intelligent input
- `detect_ui_elements` - Find buttons, textboxes, images
- `emergency_stop` - Safety stop for all automation

#### 4. Example Claude Code Usage
```markdown
Please take a screenshot and analyze what's on my screen, then help me automate clicking on the "Save" button.
```

Claude Code will:
1. Use `analyze_screen` to understand the current screen
2. Use `find_text` or `detect_ui_elements` to locate the "Save" button
3. Use `click_element` to perform the click action

### Gemini Integration

For Google's Gemini, you can integrate using the MCP client protocol:

#### 1. Install MCP Client Library
```bash
# In your Gemini project
uv add mcp
```

#### 2. Python Integration Example
```python
import asyncio
from mcp.client import Session, StdioServerParameters
from mcp.client.stdio import stdio_client

async def connect_webautomation():
    """Connect to WebAutomation MCP server."""
    server_params = StdioServerParameters(
        command="python",
        args=["/path/to/mcp-webautomation/start_server.py", "--transport", "stdio"],
        cwd="/path/to/mcp-webautomation"
    )
    
    async with stdio_client(server_params) as (read, write):
        async with Session(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # Get available tools
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            
            # Take a screenshot and analyze
            result = await session.call_tool("analyze_screen", {
                "include_ocr": True,
                "include_elements": True
            })
            
            return result

# Usage
result = asyncio.run(connect_webautomation())
```

#### 3. Gemini API Integration
```python
import google.generativeai as genai
from mcp_integration import WebAutomationMCP

class GeminiWebAutomation:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro-vision')
        self.webautomation = WebAutomationMCP()
    
    async def analyze_and_act(self, instruction):
        # Get screen context
        screen_analysis = await self.webautomation.analyze_screen()
        
        # Send to Gemini with screen context
        prompt = f"""
        Current screen analysis: {screen_analysis}
        User instruction: {instruction}
        
        Based on the screen analysis, determine what automation actions to take.
        Respond with specific MCP tool calls.
        """
        
        response = self.model.generate_content(prompt)
        
        # Parse and execute automation commands
        return await self._execute_automation(response.text)
```

### Advanced Integration Patterns

#### 1. Multi-Modal Workflows
```python
async def intelligent_automation_workflow():
    """Example of intelligent automation workflow."""
    
    # 1. Capture and analyze screen
    analysis = await session.call_tool("analyze_screen", {
        "include_ocr": True,
        "include_elements": True
    })
    
    # 2. Use AI to understand context
    screen_context = analysis["screen_context"]["summary"]
    
    # 3. Find specific elements
    save_buttons = await session.call_tool("find_text", {
        "text": "Save",
        "confidence": 0.8
    })
    
    # 4. Perform intelligent clicking
    if save_buttons["matches"]:
        best_match = save_buttons["matches"][0]
        await session.call_tool("click_element", {
            "x": best_match["center_x"],
            "y": best_match["center_y"]
        })
```

#### 2. Safety-First Automation
```python
async def safe_automation_example():
    """Example with safety checks."""
    
    # Enable confirmation for sensitive actions
    config = {
        "safety": {
            "require_confirmation": True,
            "automation_bounds": {
                "x": 0, "y": 100,  # Avoid top menu bar
                "width": 1920, "height": 900
            }
        }
    }
    
    # All automation will require permission
    result = await session.call_tool("type_text", {
        "text": "Hello from AI automation!",
        "delay": 0.1
    })
```

### Testing the Integration

#### 1. Test with Claude Code
```bash
# Start the server
python start_server.py --debug

# In Claude Code, try:
# "Please take a screenshot and tell me what's on my screen"
```

#### 2. Test with Gemini
```python
# Run the integration test
python -c "
import asyncio
from examples.gemini_integration import test_gemini_integration
asyncio.run(test_gemini_integration())
"
```

### Security Considerations

1. **Permission System**: Always enable confirmations for production use
2. **Bounds Checking**: Set automation bounds to prevent system-wide access
3. **Rate Limiting**: Configure appropriate action limits
4. **Logging**: Monitor all automation activities
5. **Emergency Stop**: Ensure emergency stop functionality is accessible

### Performance Optimization

1. **GPU Acceleration**: Install GPU extras for faster OCR processing
2. **Region Processing**: Analyze specific screen regions instead of full screen
3. **Caching**: Enable caching for repeated screen analysis
4. **Async Operations**: Use async patterns for better performance

## Next Steps

1. Read the [README.md](README.md) for usage examples
2. Try the examples in the `examples/` directory
3. Review the configuration options in `configs/fastmcp.json`
4. Set up your MCP client to connect to the server
5. Test the integration with Claude Code or Gemini
6. Configure safety settings for your use case

## Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Review the log files for error details
3. Ensure all system requirements are met
4. Try running the test examples first
5. Test MCP server connectivity separately
6. Verify AI assistant integration configuration