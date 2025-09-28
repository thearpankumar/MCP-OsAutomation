# MCP WebAutomation: AI-Powered Desktop Intelligence

> **The world's first semantic desktop automation system that thinks like a human, not a robot.**

## 🌟 What Makes This Revolutionary?

While traditional automation tools blindly click coordinates and scrape pixels, **MCP WebAutomation** introduces a paradigm shift: **AI agents that actually understand what's on your screen**. This isn't just another automation framework—it's the future of human-computer interaction.

### 🧠 Intelligence-First Approach

Forget brittle scripts that break when UI changes. Our system uses **cutting-edge LLM vision models** (OpenAI GPT-4V, Claude, Gemini) to:

- **See your screen like a human**: "VS Code is open with a Python file, user is debugging code"
- **Understand context**: "Active development session, multiple files open, terminal showing test output"
- **Adapt to changes**: Works across different themes, resolutions, and UI updates
- **Make smart decisions**: "This looks like a form, let me find the submit button"

### 🚀 What's Truly Unique in the Market

**No existing tool combines these capabilities:**

1. **Semantic Understanding Over Coordinates**
   - Traditional: `click(123, 456)` → Breaks on different screens
   - MCP WebAutomation: `"Find the Save button"` → Works everywhere

2. **LLM Vision Integration**
   - First automation tool to use GPT-4V/Claude vision for screen analysis
   - Understands context, not just pixels
   - Adapts to visual changes automatically

3. **Multi-Provider Intelligence**
   - OpenAI, Claude, and Gemini vision models with intelligent fallback
   - Best-in-class reliability with provider redundancy
   - Choose the best model for your specific use case

4. **Model Context Protocol (MCP) Integration**
   - Built for the new AI ecosystem
   - Native Claude Code integration
   - Designed for AI agents, not just scripts

## ✨ Why This Changes Everything

### Traditional Automation (Brittle)
```python
# Breaks if button moves 1 pixel
selenium.click(x=234, y=567)
time.sleep(2)  # Hope it loaded
selenium.click(x=445, y=123)
```

### MCP WebAutomation (Intelligent)
```python
# 🎯 COORDINATE MODE: Get precise click locations
screen = analyze_screen(include_ocr=False, vision_provider="openai")
# Returns: Semantic description + clickable element coordinates
# {
#   "screen_description": "VS Code editor with file browser open...",
#   "programs_detected": ["Visual Studio Code"],
#   "clickable_elements": [
#     {"type": "button", "text": "Save", "x": 150, "y": 200, "width": 80, "height": 30},
#     {"type": "menu", "text": "File", "x": 50, "y": 25, "width": 40, "height": 20}
#   ]
# }

# 📝 TEXT MODE: Extract readable content
text_screen = analyze_screen(include_ocr=True, vision_provider="openai")
# Returns: Semantic description + OCR text (no coordinates)

# Now Claude Code knows EXACTLY where to click!
if screen["clickable_elements"]:
    save_button = next(el for el in screen["clickable_elements"] if "save" in el["text"].lower())
    click_element(x=save_button["x"], y=save_button["y"])
```

## 🎯 Real-World Magic

### Smart Form Filling
Instead of hardcoded coordinates, the system **understands** forms:
- Detects "This is a registration form with name, email, and submit fields"
- Intelligently navigates between fields
- Adapts to different form layouts automatically

### Cross-Platform Development
- **Semantic window detection**: "Terminal is open, user is running tests"
- **IDE integration**: Understands VS Code, IntelliJ, any editor
- **Context preservation**: Maintains understanding across app switches

### Dynamic UI Adaptation
- **Theme changes**: Dark mode? Light mode? Still works perfectly
- **Resolution independence**: 1080p or 4K, the AI adapts
- **UI updates**: App redesigns don't break your automation

## 🔥 Killer Features

### 1. **Vision-First Architecture**
- No more pixel hunting or coordinate guessing
- AI sees interfaces like humans do
- Robust across different environments

### 2. **Zero-Training Required**
- No machine learning models to train
- No UI mapping or screenshot databases
- Works out-of-the-box with any application

### 3. **Enhanced MCP Tools**
```python
# 5 powerful tools for complete desktop control:
analyze_screen()           # 🎯 DUAL MODE: Coordinates OR Text extraction
click_element()           # Smart clicking by coordinates or text
type_text()              # Intelligent text input
press_key()              # Keyboard shortcuts and combinations
emergency_stop()         # Safety stop for all automation
```

**🚀 NEW: Dual-Mode analyze_screen()**
```python
# COORDINATE MODE (include_ocr=False)
# → Returns clickable element coordinates for precise automation
screen = analyze_screen(include_ocr=False)
# Result: {"clickable_elements": [{"type": "button", "text": "Save", "x": 150, "y": 200}]}

# TEXT MODE (include_ocr=True)
# → Returns OCR text content for reading screen information
screen = analyze_screen(include_ocr=True)
# Result: {"ocr_text": "Welcome to VS Code...", "clickable_elements": null}
```

### 4. **Intelligent Error Recovery**
- Detects when UI changes unexpectedly
- Automatically adapts to new layouts
- Self-healing automation workflows

### 5. **Multi-Modal Understanding**
- Combines visual analysis with OCR
- Understands both graphics and text
- Context-aware decision making

### 6. **Future Enchancements** 
- teaching mode (tells the cli Coder how to work with a pirticular application)
- memory system (cli coder should remember how to use \
 that work with that application new session)

## 🏆 Market Position

**There is literally nothing like this available today:**

- **RPA Tools** (UiPath, Automation Anywhere): Coordinate-based, fragile
- **Selenium/Playwright**: Web-only, requires developer knowledge
- **Screen Scrapers**: Pixel-based, break constantly
- **AI Automation**: Mostly demos, not production-ready systems

**MCP WebAutomation is the first production-ready system that:**
- Uses LLM vision for semantic understanding
- Works across all desktop applications
- Requires zero training or setup
- Provides human-like screen comprehension

## 🛠 Built for the AI Era

### Claude::Gemini::qwen::OpenCoder etc Code Integration
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

### AI Agent Ecosystem
- **Model Context Protocol (MCP)** native
- **FastMCP 2.0** powered
- **Multi-provider architecture**
- **Rate-limited and secure**

### Permissions Configuration
For proper operation, add these permissions to your Claude settings:

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

Add this to `.claude/settings.local.json` for the tools to work properly.

## 🚀 Get Started in Minutes

1. **Clone and Setup**
   ```bash
   git clone <repo>
   cd MCP-OsAutomation
   uv run python start_server.py --test
   ```

2. **Add Your API Keys**
   ```bash
   echo "OPENAI_API_KEY=your_key" > .env
   ```

3. **Test the Magic**
   ```bash
   uv run python start_server.py --test
   ```

4. **Connect to Claude Code**
   - Copy `.claude.json` to `~/.claude.json`
   - Replace `<your-project-dir>` with actual path
   - Add permissions to `.claude/settings.local.json` (see above)
   - Start automating with AI!

## 🎨 Use Cases That Weren't Possible Before

- **Adaptive Testing**: UI tests that never break on redesigns
- **Smart Data Entry**: Context-aware form filling across any application
- **Cross-App Workflows**: Seamless automation across different tools
- **Dynamic Screenshots**: Intelligent screen capture with context
- **AI-Powered QA**: Testing that understands user intent, not just clicks

## 🛠 Current MCP Tools

Our streamlined toolkit provides everything needed for intelligent desktop automation:

### Core Tools

| Tool | Purpose | Example |
|------|---------|---------|
| `analyze_screen()` | **🎯 DUAL MODE**: Coordinates OR OCR text | `include_ocr=False` → Get clickable coordinates<br/>`include_ocr=True` → Extract text content |
| `click_element()` | Smart clicking by coordinates or text | Click buttons, links, or UI elements |
| `type_text()` | Intelligent text input with options | Fill forms, enter commands, write text |
| `press_key()` | Keyboard shortcuts and combinations | Ctrl+S, Alt+Tab, function keys |
| `emergency_stop()` | Safety stop for all automation | Immediately halt all automation activities |

### Key Features
- **Token-optimized**: No massive base64 responses that break LLM interactions
- **LLM-focused**: Returns semantic data LLMs can understand and act on
- **Complete coverage**: Everything needed for desktop automation
- **Fallback safety**: Emergency stop for safe operation

## 🔮 The Future is Here

This isn't just automation—it's **augmented intelligence**. We're not replacing human intuition; we're giving machines the ability to see and understand like humans do.

**Traditional automation dies when the UI changes.**
**MCP WebAutomation evolves with it.**

---

**Ready to automate like never before?** Check out the [complete documentation](docs/MCP_WEBAUTOMATION_DOCUMENTATION.md) and [Claude Code instructions](CLAUDE.md) to unlock the full potential of AI-powered desktop automation.

*The future of automation is semantic. The future is now.*