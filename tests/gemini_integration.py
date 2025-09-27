#!/usr/bin/env python3
"""
Example integration with Google Gemini using MCP protocol.

This example demonstrates how to integrate MCP WebAutomation
with Google's Gemini AI for intelligent screen automation.
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from mcp.client import Session, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_CLIENT_AVAILABLE = True
except ImportError:
    MCP_CLIENT_AVAILABLE = False


class GeminiMCPIntegration:
    """Integration class for Gemini with MCP WebAutomation."""
    
    def __init__(self, server_path: str):
        """Initialize the integration.
        
        Args:
            server_path: Path to the MCP WebAutomation server
        """
        self.server_path = server_path
        self.session = None
    
    async def connect(self):
        """Connect to the MCP WebAutomation server."""
        if not MCP_CLIENT_AVAILABLE:
            raise RuntimeError("MCP client library not available. Install with: uv add mcp")
        
        server_params = StdioServerParameters(
            command="python",
            args=[f"{self.server_path}/start_server.py", "--transport", "stdio"],
            cwd=self.server_path
        )
        
        print("🔗 Connecting to MCP WebAutomation server...", file=sys.stderr)
        
        self.stdio_client = stdio_client(server_params)
        self.read, self.write = await self.stdio_client.__aenter__()
        
        self.session = Session(self.read, self.write)
        await self.session.__aenter__()
        
        # Initialize the session
        await self.session.initialize()
        
        print("✅ Connected successfully!", file=sys.stderr)
        return self.session
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            await self.session.__aexit__(None, None, None)
        if hasattr(self, 'stdio_client'):
            await self.stdio_client.__aexit__(None, None, None)
        print("🔌 Disconnected from MCP server", file=sys.stderr)
    
    async def get_available_tools(self):
        """Get list of available tools from the server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        tools = await self.session.list_tools()
        return [tool.name for tool in tools.tools]
    
    async def analyze_screen(self):
        """Analyze the current screen."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        result = await self.session.call_tool("analyze_screen", {
            "include_ocr": True,
            "include_elements": True
        })
        
        return result
    
    async def find_and_click(self, text: str, confidence: float = 0.8):
        """Find text on screen and click on it."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        # Find text
        search_result = await self.session.call_tool("find_text", {
            "text": text,
            "confidence": confidence
        })
        
        if search_result.get("matches"):
            # Click on the first match
            match = search_result["matches"][0]
            click_result = await self.session.call_tool("click_element", {
                "x": int(match["center_x"]),
                "y": int(match["center_y"])
            })
            return {
                "found": True,
                "clicked": click_result.get("success", False),
                "location": (match["center_x"], match["center_y"]),
                "confidence": match["confidence"]
            }
        else:
            return {
                "found": False,
                "clicked": False,
                "message": f"Text '{text}' not found on screen"
            }
    
    async def intelligent_automation_workflow(self, instruction: str):
        """Example of intelligent automation based on natural language instruction."""
        print(f"🤖 Processing instruction: '{instruction}'")
        
        # 1. Analyze current screen
        print("📸 Analyzing current screen...", file=sys.stderr)
        analysis = await self.analyze_screen()
        
        if not analysis.get("success"):
            return {"error": "Failed to analyze screen"}
        
        screen_context = analysis.get("screen_context", {})
        print(f"✅ Screen analysis complete: {screen_context.get('summary', 'No summary available')})
        
        # 2. Extract key information
        ocr_result = analysis.get("ocr_result", {})
        cv_result = analysis.get("cv_result", {})
        
        text_content = ocr_result.get("full_text", "")
        ui_elements = cv_result.get("elements", [])
        
        print(f"📝 Found {ocr_result.get('word_count', 0)} words on screen")
        print(f"🔲 Found {len(ui_elements)} UI elements")
        
        # 3. Simple instruction parsing (in a real implementation, you'd use Gemini API here)
        result = await self._simple_instruction_parser(instruction, text_content, ui_elements)
        
        return result
    
    async def _simple_instruction_parser(self, instruction: str, text_content: str, ui_elements: list):
        """Simple instruction parser (placeholder for Gemini AI integration)."""
        instruction_lower = instruction.lower()
        
        # Simple keyword-based actions
        if "click" in instruction_lower and "save" in instruction_lower:
            return await self.find_and_click("Save")
        
        elif "click" in instruction_lower and "ok" in instruction_lower:
            return await self.find_and_click("OK")
        
        elif "click" in instruction_lower and "cancel" in instruction_lower:
            return await self.find_and_click("Cancel")
        
        elif "type" in instruction_lower:
            # Extract text to type (very simple implementation)
            words = instruction.split()
            try:
                type_index = words.index("type")
                if type_index + 1 < len(words):
                    text_to_type = " ".join(words[type_index + 1:])
                    
                    result = await self.session.call_tool("type_text", {
                        "text": text_to_type,
                        "delay": 0.1
                    })
                    
                    return {
                        "action": "type",
                        "text": text_to_type,
                        "success": result.get("success", False)
                    }
            except ValueError:
                pass
        
        elif "screenshot" in instruction_lower or "screen" in instruction_lower:
            screenshot_result = await self.session.call_tool("capture_screen", {})
            return {
                "action": "screenshot",
                "success": screenshot_result.get("success", False),
                "message": "Screenshot captured"
            }
        
        return {
            "action": "unknown",
            "message": f"Don't know how to handle instruction: '{instruction}'",
            "available_text": text_content[:200] + "..." if len(text_content) > 200 else text_content,
            "available_elements": [{"type": e["type"], "confidence": e["confidence"]} for e in ui_elements[:5]]
        }


async def test_gemini_integration():
    """Test the Gemini MCP integration."""
    print("🧪 Testing Gemini MCP Integration")
    print("=" * 50, file=sys.stderr)
    
    # Get server path
    server_path = Path(__file__).parent.parent
    
    integration = GeminiMCPIntegration(str(server_path))
    
    try:
        # Connect to server
        await integration.connect()
        
        # Test available tools
        print("\n🔧 Available tools:")
        tools = await integration.get_available_tools()
        for tool in tools:
            print(f"  • {tool}", file=sys.stderr)
        
        # Test screen analysis
        print("\n📸 Testing screen analysis...")
        analysis_result = await integration.analyze_screen()
        
        if analysis_result.get("success"):
            print("✅ Screen analysis successful", file=sys.stderr)
            context = analysis_result.get("screen_context", {})
            print(f"   Summary: {context.get('summary', 'No summary')})
        else:
            print(f"❌ Screen analysis failed: {analysis_result.get('message', 'Unknown error')}")
        
        # Test intelligent automation
        print("\n🤖 Testing intelligent automation workflows...", file=sys.stderr)
        
        test_instructions = [
            "Take a screenshot",
            "Click on Save button",
            "Type Hello World",
        ]
        
        for instruction in test_instructions:
            print(f"\n📝 Testing: '{instruction}'")
            result = await integration.intelligent_automation_workflow(instruction)
            
            if result.get("success") or result.get("found"):
                print(f"   ✅ Success: {result}", file=sys.stderr)
            else:
                print(f"   ℹ️ Result: {result.get('message', result)}")
        
        print("\n✅ All tests completed!", file=sys.stderr)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if "MCP client library not available" in str(e):
            print("\n💡 To enable MCP client integration:", file=sys.stderr)
            print("   uv add mcp")
            print("   # or with pip:", file=sys.stderr)
            print("   pip install mcp")
    
    finally:
        await integration.disconnect()


async def gemini_api_example():
    """Example of how to integrate with Gemini API (requires API key)."""
    print("\n🔮 Gemini API Integration Example", file=sys.stderr)
    print("=" * 40, file=sys.stderr)
    
    print("""
This is a conceptual example of how to integrate with Gemini API.
To use this, you would need to:

1. Install Google AI SDK:
   uv add google-generativeai

2. Get API key from: https://makersuite.google.com/app/apikey

3. Implement the integration:
""", file=sys.stderr)
    
    example_code = '''
import google.generativeai as genai
from gemini_integration import GeminiMCPIntegration

class GeminiWebAutomation:
    def __init__(self, api_key, mcp_server_path):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.mcp = GeminiMCPIntegration(mcp_server_path)
    
    async def process_instruction(self, instruction):
        # Connect to MCP server
        await self.mcp.connect()
        
        try:
            # Get screen context
            analysis = await self.mcp.analyze_screen()
            screen_context = analysis.get("screen_context", {})
            
            # Create prompt for Gemini
            prompt = f"""
            You are an AI assistant that can control a computer screen.
            
            Current screen context: {screen_context}
            User instruction: {instruction}
            
            Available MCP tools:
            - find_text(text, confidence) - Find text on screen
            - click_element(x, y) - Click at coordinates
            - type_text(text) - Type text
            - capture_screen() - Take screenshot
            
            Based on the screen analysis, determine the best sequence of MCP tool calls
            to fulfill the user's instruction. Respond with a JSON list of tool calls.
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse and execute Gemini's suggested actions
            return await self._execute_gemini_plan(response.text)
            
        finally:
            await self.mcp.disconnect()

# Usage:
# automation = GeminiWebAutomation("your-api-key", "/path/to/mcp-webautomation")
# result = await automation.process_instruction("Click the save button and then type 'Hello World'")
'''
    
    print(example_code)
    
    print("\n💡 This approach allows Gemini to:", file=sys.stderr)
    print("   • Understand screen context through MCP analysis")
    print("   • Plan complex automation sequences", file=sys.stderr)
    print("   • Execute multi-step workflows intelligently")
    print("   • Adapt to different screen layouts dynamically", file=sys.stderr)


def main():
    """Main function."""
    print("🚀 MCP WebAutomation - Gemini Integration Examples")
    print("=" * 60, file=sys.stderr)
    
    try:
        # Run the basic integration test
        asyncio.run(test_gemini_integration())
        
        # Show API integration example
        asyncio.run(gemini_api_example())
        
    except KeyboardInterrupt:
        print("\n🛑 Examples interrupted by user")
    except Exception as e:
        print(f"\n💥 Examples failed: {e}", file=sys.stderr)
        print("\n🔧 Troubleshooting:")
        print("   • Ensure MCP WebAutomation server dependencies are installed", file=sys.stderr)
        print("   • Check that the server can start successfully")
        print("   • Verify screen capture permissions on your system", file=sys.stderr)


if __name__ == "__main__":
    main()