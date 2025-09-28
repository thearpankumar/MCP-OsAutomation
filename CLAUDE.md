# Claude Code Instructions for MCP WebAutomation

## Overview
This MCP WebAutomation server provides intelligent desktop automation capabilities. As Claude Code, you can use these tools to analyze screens, control the desktop, and automate complex workflows through semantic understanding rather than rigid coordinate-based scripts.

## Available Tools (5 Total)

| Tool | Purpose |
|------|---------|
| `analyze_screen()` | LLM vision analysis of current screen (with optional OCR) |
| `click_element()` | Smart clicking by coordinates or text |
| `type_text()` | Intelligent text input with options |
| `press_key()` | Keyboard shortcuts and combinations |
| `emergency_stop()` | Safety stop for all automation |

**Key Changes**: Removed `capture_screen` and `find_text` tools to eliminate token overflow issues and redundancy.

## Quick Start for Claude Code

### 1. Understanding Screen Context
Use `analyze_screen` as your primary tool for understanding what's currently on the user's screen:

```python
# Get semantic understanding of the current screen
result = mcp.call_tool("analyze_screen", {
    "analysis_detail": "standard",
    "vision_provider": "openai"
})

# The result contains:
# - screen_description: Natural language description
# - programs_detected: List of applications (e.g., ["Visual Studio Code", "Chrome"])
# - ui_state: Current activity (e.g., "Active development/coding session")
# - actionable_elements: What the user can interact with
```

### 2. Key Principles for Effective Usage

#### Always Analyze First
Before taking any automation actions, understand the current screen state:
```python
# ✅ Good: Understand context first
screen = mcp.call_tool("analyze_screen")
print(f"Current context: {screen['screen_description']}")
print(f"Available actions: {screen['actionable_elements']}")

# Then proceed with automation based on understanding
```

#### Use Semantic Understanding Over Coordinates
The vision analysis provides meaningful context instead of raw coordinates:
```python
# ✅ Good: Use semantic understanding
if "Visual Studio Code" in screen['programs_detected']:
    # User is coding, suggest development-related actions

if "coding session" in screen['ui_state']:
    # Adapt behavior to development workflow
```

### 3. Common Automation Patterns

#### Pattern 1: Smart Element Finding
```python
# Click UI elements by text rather than hardcoded coordinates
mcp.call_tool("click_element", {
    "element_text": "Save"
})

# Or get screen analysis with OCR for text finding
screen = mcp.call_tool("analyze_screen", {
    "include_ocr": True
})
# Then use coordinates if needed
```

#### Pattern 2: Context-Aware Automation
```python
# Adapt actions based on detected programs
screen = mcp.call_tool("analyze_screen")

if "Chrome" in screen['programs_detected']:
    # Browser-specific automation
    mcp.call_tool("press_key", {"key": "f5"})  # Refresh page

elif "Visual Studio Code" in screen['programs_detected']:
    # IDE-specific automation
    mcp.call_tool("press_key", {"key": "s", "modifiers": ["ctrl"]})  # Save file
```

#### Pattern 3: Multi-Step Workflows
```python
# Complex automation with verification
def automate_form_filling():
    # 1. Understand current state
    screen = mcp.call_tool("analyze_screen", {"analysis_detail": "detailed"})

    # 2. Verify we're in the right context
    if "form" not in screen['screen_description'].lower():
        return {"error": "No form detected on screen"}

    # 3. Fill form fields
    mcp.call_tool("click_element", {"x": 200, "y": 100})
    mcp.call_tool("type_text", {"text": "John Doe", "clear_first": True})

    # 4. Move to next field
    mcp.call_tool("press_key", {"key": "tab"})
    mcp.call_tool("type_text", {"text": "john@example.com"})

    # 5. Submit
    mcp.call_tool("click_element", {"element_text": "Submit"})
```

## Tool Reference for Claude Code

### Primary Analysis Tool

#### `analyze_screen` - Your Main Intelligence Tool
**When to use**: Before any automation, to understand context, verify state changes

**Key parameters**:
- `analysis_detail`: Use "standard" for most cases, "detailed" for complex UIs
- `include_ocr`: Set to `true` only when you need exact text extraction
- `vision_provider`: Defaults to "openai", fallback to "claude" or "gemini"

**Best practices**:
```python
# For general understanding
screen = mcp.call_tool("analyze_screen")

# For detailed UI analysis
detailed = mcp.call_tool("analyze_screen", {
    "analysis_detail": "detailed",
    "include_ocr": True  # Only when text extraction needed
})

# For quick verification
brief = mcp.call_tool("analyze_screen", {"analysis_detail": "brief"})
```

### Action Tools

#### `click_element` - Smart Clicking
```python
# Precise clicking with context
mcp.call_tool("click_element", {
    "x": 150, "y": 75,
    "element_text": "Save Button"  # For logging/debugging
})

# Right-click for context menus
mcp.call_tool("click_element", {
    "x": 300, "y": 200,
    "button": "right"
})
```

#### `type_text` - Intelligent Text Input
```python
# Safe text input with clearing
mcp.call_tool("type_text", {
    "text": "Hello World",
    "clear_first": True,  # Clear existing text
    "delay": 0.05  # Faster typing for efficiency
})

# Text input with submission
mcp.call_tool("type_text", {
    "text": "search query",
    "submit": True  # Press Enter after typing
})
```

#### `press_key` - Keyboard Automation
```python
# Common shortcuts
mcp.call_tool("press_key", {"key": "s", "modifiers": ["ctrl"]})  # Save
mcp.call_tool("press_key", {"key": "c", "modifiers": ["ctrl"]})  # Copy
mcp.call_tool("press_key", {"key": "z", "modifiers": ["ctrl"]})  # Undo

# Navigation
mcp.call_tool("press_key", {"key": "tab"})      # Next field
mcp.call_tool("press_key", {"key": "enter"})    # Confirm
mcp.call_tool("press_key", {"key": "escape"})   # Cancel
```

### Safety Tools

#### `emergency_stop` - Safety Control
```python
# Stop all automation immediately
result = mcp.call_tool("emergency_stop")
print(f"Status: {result['status']}")  # "stopped"
```

## Advanced Usage Patterns for Claude Code

### 1. Adaptive Automation
```python
def smart_automation():
    """Automation that adapts to current context"""
    context = mcp.call_tool("analyze_screen")

    # Adapt based on detected programs
    programs = context['programs_detected']

    if "Visual Studio Code" in programs:
        return handle_ide_automation()
    elif "Chrome" in programs or "Firefox" in programs:
        return handle_browser_automation()
    elif "Terminal" in programs:
        return handle_terminal_automation()
    else:
        return {"message": "Context not recognized for automation"}
```

### 2. Error Recovery
```python
def robust_click_action(element_text, max_retries=3):
    """Click with verification and retry logic"""
    for attempt in range(max_retries):
        # Use smart element clicking
        click_result = mcp.call_tool("click_element", {
            "element_text": element_text
        })

        if click_result["success"]:
            return click_result

        # Wait and retry
        time.sleep(1)

    return {"error": f"Failed to click {element_text} after {max_retries} attempts"}
```

### 3. State Verification
```python
def verify_action_completed(expected_state_keywords):
    """Verify that an action had the expected effect"""
    # Wait a moment for UI to update
    time.sleep(2)

    # Check new state
    new_state = mcp.call_tool("analyze_screen", {"analysis_detail": "brief"})
    description = new_state['screen_description'].lower()

    # Check if expected keywords are present
    for keyword in expected_state_keywords:
        if keyword.lower() in description:
            return True

    return False

# Usage example
mcp.call_tool("click_element", {"x": 100, "y": 200})
if verify_action_completed(["dialog", "popup", "modal"]):
    print("Dialog opened successfully")
```

## Best Practices for Claude Code

### 1. Always Use Context First
```python
# ✅ Good pattern
def intelligent_automation():
    # Understand before acting
    context = mcp.call_tool("analyze_screen")

    # Make decisions based on understanding
    if "form" in context['screen_description'].lower():
        return handle_form_interaction()
    elif "menu" in context['actionable_elements'].lower():
        return handle_menu_navigation()
```

### 2. Prefer Text-Based Element Finding
```python
# ✅ Better: Smart clicking by text (robust)
mcp.call_tool("click_element", {"element_text": "Save"})

# ✅ Also good: Use analyze_screen for complex scenarios
screen = mcp.call_tool("analyze_screen", {"include_ocr": True})
# Then use the screen analysis to understand context

# ❌ Avoid: Hardcoded coordinates (brittle)
mcp.call_tool("click_element", {"x": 100, "y": 200})  # May break on different screens
```

### 3. Use Appropriate Detail Levels
```python
# Quick verification
brief = mcp.call_tool("analyze_screen", {"analysis_detail": "brief"})

# General automation
standard = mcp.call_tool("analyze_screen", {"analysis_detail": "standard"})

# Complex UI analysis
detailed = mcp.call_tool("analyze_screen", {"analysis_detail": "detailed"})
```

### 4. Handle Errors Gracefully
```python
def safe_automation():
    try:
        result = mcp.call_tool("analyze_screen")
        if not result["success"]:
            return {"error": "Screen analysis failed", "details": result["message"]}

        # Continue with automation...

    except Exception as e:
        return {"error": "Automation failed", "exception": str(e)}
```

## Common Use Cases

### Web Automation
```python
# Navigate and fill web forms
context = mcp.call_tool("analyze_screen")
if "browser" in context['screen_description'].lower():
    # Browser-specific automation
    pass
```

### IDE Automation
```python
# Code editor automation
if "Visual Studio Code" in context['programs_detected']:
    # Save current file
    mcp.call_tool("press_key", {"key": "s", "modifiers": ["ctrl"]})
```

### System Navigation
```python
# File manager operations
if "File Manager" in context['programs_detected']:
    # Navigate directories
    pass
```

## Troubleshooting for Claude Code

### Screen Analysis Issues
- Use `"analysis_detail": "detailed"` for better program detection
- Try different `vision_provider` if one fails (openai → claude → gemini)
- Check that screenshot capture is successful first

### Element Finding Issues
- Lower `confidence` threshold for fuzzy text matching
- Use `region` parameter to search in specific areas
- Verify text exists with OCR: `"include_ocr": true`

### Action Failures
- Always verify screen state before actions
- Use `get_mouse_position` to debug coordinate issues
- Add delays between actions for UI updates

## Security Notes
- All actions are rate-limited for safety
- Permission levels: Safe (screenshots) → Moderate (clicks) → Dangerous (system)
- Use test mode first: `python start_server.py --test`

This MCP server transforms desktop automation from brittle coordinate-based scripts into intelligent, context-aware workflows that adapt to what's actually on screen.