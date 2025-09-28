# MCP WebAutomation - Claude Code Instructions

## Environment Setup
- **System**: Single monitor setup with terminal-based workflow
- **Primary Interface**: Terminal/CLI applications preferred
- **Display**: One screen with multiple applications via Alt+Tab switching

## Tools Available
| Tool | Purpose |
|------|---------|
| `analyze_screen()` | **DUAL MODE**: Get coordinates OR extract text |
| `click_element()` | Click by coordinates or text |
| `type_text()` | Type text with options |
| `press_key()` | Keyboard shortcuts |
| `emergency_stop()` | Stop all automation |

## Workflow Protocol

### 1. Task Analysis & Program Discovery
Before performing any task:
```python
# Step 1: Switch to see available programs
mcp.call_tool("press_key", {"key": "tab", "modifiers": ["alt"]})

# Step 2: Analyze current screen to understand what's available
screen = mcp.call_tool("analyze_screen", {"include_ocr": False})

# Step 3: Check if required programs are running via bash
result = mcp.call_tool("bash_command", {"command": "pgrep -l firefox|chrome|code|terminal"})
```

### 2. Program Navigation Strategy
```python
# Navigate through applications using Alt+Tab until target found
def find_target_program(target_program):
    max_attempts = 10
    for attempt in range(max_attempts):
        screen = mcp.call_tool("analyze_screen", {"include_ocr": False})

        if target_program.lower() in screen["screen_description"].lower():
            return True

        # Switch to next program
        mcp.call_tool("press_key", {"key": "tab", "modifiers": ["alt"]})

    return False
```

### 3. Task Execution Priority
1. **PREFER BASH**: If task can be done via terminal commands
2. **GUI FALLBACK**: Use desktop automation only when necessary
3. **HYBRID APPROACH**: Combine bash + GUI for optimal efficiency

### 4. Complete Task Workflow
```python
def execute_user_task(user_request):
    # Step 1: Analyze what user wants
    # Step 2: Check if bash can handle it
    if can_use_bash(user_request):
        return execute_bash_solution(user_request)

    # Step 3: Find required GUI program
    target_program = determine_required_program(user_request)

    # Step 4: Navigate to program
    if find_target_program(target_program):
        return execute_gui_task(user_request)
    else:
        # Step 5: Launch program if not running
        launch_program(target_program)
        return execute_gui_task(user_request)
```

## Mandatory Workflow Steps

### Before ANY Task
1. **Alt+Tab** to survey available programs
2. **analyze_screen()** to understand current state
3. **Check bash first** - prefer terminal solutions
4. **Navigate to correct program** using Alt+Tab
5. **Execute task** with appropriate method

## Core Usage

### analyze_screen - Two Modes
```python
# COORDINATE MODE: Get clickable elements
screen = mcp.call_tool("analyze_screen", {"include_ocr": False})
# Returns: clickable_elements with x,y coordinates

# TEXT MODE: Extract screen text
screen = mcp.call_tool("analyze_screen", {"include_ocr": True})
# Returns: ocr_text content, no coordinates
```

### Essential Patterns
```python
# 1. Always analyze first
screen = mcp.call_tool("analyze_screen", {"include_ocr": False})

# 2. Find and click with coordinates
if screen["clickable_elements"]:
    button = next((el for el in screen["clickable_elements"]
                   if "save" in el["text"].lower()), None)
    if button:
        mcp.call_tool("click_element", {"x": button["x"], "y": button["y"]})

# 3. Alternative text-based clicking
mcp.call_tool("click_element", {"element_text": "Save"})

# 4. Common keyboard shortcuts
mcp.call_tool("press_key", {"key": "s", "modifiers": ["ctrl"]})  # Save
mcp.call_tool("press_key", {"key": "tab"})  # Next field
```

## Key Parameters
- `analysis_detail`: "brief", "standard", "detailed"
- `vision_provider`: "openai" (default), "claude", "gemini"
- `include_ocr`: `false` = coordinates, `true` = text

## Practical Examples

### Example 1: File Operations (PREFER BASH)
```python
# User: "Create a new file called test.txt"
# DON'T: Open file manager GUI
# DO: Use bash command
bash_result = bash("touch test.txt && echo 'File created: test.txt'")
```

### Example 2: Browser Task (GUI Required)
```python
# User: "Open YouTube and search for tutorials"
# Step 1: Check programs
mcp.call_tool("press_key", {"key": "tab", "modifiers": ["alt"]})
# Step 2: Find browser or launch it
if not find_target_program("firefox"):
    bash("firefox &")
# Step 3: Navigate and search
```

### Example 3: Code Editing (HYBRID)
```python
# User: "Edit main.py and add a print statement"
# Option 1: Bash (if simple)
bash("echo 'print(\"Hello World\")' >> main.py")
# Option 2: VS Code (if complex)
find_target_program("Visual Studio Code")
# Then use GUI automation
```

## Critical Rules
- **ALWAYS** start with Alt+Tab + analyze_screen
- **ALWAYS** prefer bash for file/system operations
- **ONLY** use GUI when bash cannot accomplish the task
- **NAVIGATE** programs with Alt+Tab, not clicking taskbar

## Testing
- Run `python start_server.py --test` to verify functionality
- Use `emergency_stop()` if automation goes wrong