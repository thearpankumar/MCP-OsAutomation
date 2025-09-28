#!/usr/bin/env python3
"""
Basic usage example for MCP WebAutomation.

This example demonstrates how to use the WebAutomation server
to perform basic automation tasks.
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp_automation.server import WebAutomationServer


async def main():
    """Main example function."""
    print("🚀 MCP WebAutomation - Basic Usage Example")
    print("=" * 50, file=sys.stderr)
    
    # Initialize server
    print("Initializing WebAutomation server...")
    server = WebAutomationServer()
    
    # Test individual components (without running the full MCP server)
    try:
        # Initialize components manually for testing
        await server._initialize_components()
        print("✅ Server components initialized successfully", file=sys.stderr)
        
        # Test screenshot capture
        print("\n📸 Testing screenshot capture...")
        if server.screen_analyzer:
            screenshot_result = await server.screen_analyzer.capture_screen()
            if screenshot_result["success"]:
                print(f"✅ Screenshot captured: {screenshot_result['width']}x{screenshot_result['height']}", file=sys.stderr)
            else:
                print(f"❌ Screenshot failed: {screenshot_result['message']}")
        
        # Test NEW coordinate detection mode (include_ocr=False)
        print("\n📍 Testing COORDINATE DETECTION mode (include_ocr=False)...", file=sys.stderr)
        if server.screen_analyzer:
            analysis_result = await server.screen_analyzer.analyze_screen(
                include_ocr=False,  # NEW: This mode returns clickable element coordinates!
                analysis_detail="standard",
                vision_provider="openai"
            )
            if analysis_result["success"]:
                programs = ", ".join(analysis_result["programs_detected"]) if analysis_result["programs_detected"] else "None detected"
                print(f"✅ Coordinate analysis completed using {analysis_result['provider_used']}")
                print(f"   Programs detected: {programs}", file=sys.stderr)
                print(f"   UI State: {analysis_result['ui_state']}", file=sys.stderr)
                print(f"   Description: {analysis_result['screen_description'][:100]}...", file=sys.stderr)

                # NEW: Check for clickable elements
                clickable_elements = analysis_result.get("clickable_elements")
                if clickable_elements is not None:
                    if isinstance(clickable_elements, list) and clickable_elements:
                        print(f"🎯 CLICKABLE ELEMENTS FOUND: {len(clickable_elements)} elements detected!", file=sys.stderr)
                        for i, element in enumerate(clickable_elements[:3]):  # Show first 3
                            print(f"   Element {i+1}: {element.get('type', 'unknown')} '{element.get('text', 'no text')}' at ({element.get('x', 0)}, {element.get('y', 0)})", file=sys.stderr)
                        if len(clickable_elements) > 3:
                            print(f"   ... and {len(clickable_elements) - 3} more elements", file=sys.stderr)
                    else:
                        print(f"🤖 AI detected interface but no specific clickable elements returned", file=sys.stderr)
                else:
                    print(f"⚠️ No clickable_elements field in response - feature may need API key", file=sys.stderr)
            else:
                print(f"❌ Coordinate analysis failed: {analysis_result['message']}")

        # Test NEW text extraction mode (include_ocr=True)
        if server.screen_analyzer and analysis_result.get("success"):
            print("\n📝 Testing TEXT EXTRACTION mode (include_ocr=True)...", file=sys.stderr)
            ocr_analysis = await server.screen_analyzer.analyze_screen(
                include_ocr=True,  # NEW: This mode returns OCR text, NO coordinates
                analysis_detail="brief",
                vision_provider="openai"
            )
            if ocr_analysis["success"]:
                # Check that coordinates are NOT returned in text mode
                clickable_elements = ocr_analysis.get("clickable_elements")
                print(f"✅ Text mode analysis completed using {ocr_analysis['provider_used']}")
                print(f"   Clickable elements: {clickable_elements} (should be None in text mode)", file=sys.stderr)

                if ocr_analysis.get("ocr_text"):
                    word_count = len(ocr_analysis["ocr_text"].split())
                    print(f"   📄 OCR text extracted: {word_count} words", file=sys.stderr)
                    print(f"   Sample text: {ocr_analysis['ocr_text'][:80]}...", file=sys.stderr)
                else:
                    print(f"   ℹ️ No text found on screen", file=sys.stderr)
            else:
                print(f"❌ Text extraction failed: {ocr_analysis['message']}")

        # Test permission system
        print("\n🔐 Testing permission system...", file=sys.stderr)
        if server.permission_manager:
            # Test safe action
            safe_permission = await server.permission_manager.request_permission(
                "capture_screen", {"monitor": 0, "format": "png"}
            )
            print(f"✅ Safe action permission: {'Granted' if safe_permission else 'Denied'}", file=sys.stderr)
            
            # Test moderate action
            moderate_permission = await server.permission_manager.request_permission(
                "click_element", {"x": 100, "y": 100, "button": "left"}
            )
            print(f"✅ Moderate action permission: {'Granted' if moderate_permission else 'Denied'}")
            
            # Get permission status
            status = await server.permission_manager.get_permission_status()
            print(f"   Permission status: {status['session_permissions']} session permissions", file=sys.stderr)
        
        # Test automation controller (basic info only)
        print("\n🖱️ Testing automation controller...", file=sys.stderr)
        if server.automation_controller:
            mouse_pos = await server.automation_controller.get_mouse_position()
            if mouse_pos["success"]:
                print(f"✅ Mouse position: ({mouse_pos['x']}, {mouse_pos['y']})", file=sys.stderr)
            else:
                print(f"❌ Failed to get mouse position: {mouse_pos.get('message', 'Unknown error')}", file=sys.stderr)
        
        print("\n✅ All tests completed successfully!", file=sys.stderr)
        print("\n🎉 ENHANCED Analyze Screen Features Tested:")
        print("   🎯 COORDINATE MODE (include_ocr=False):")
        print("      • Returns semantic description + clickable element coordinates")
        print("      • Perfect for Claude Code to know WHERE to click")
        print("      • AI identifies buttons, menus, links with pixel positions")
        print("   📝 TEXT MODE (include_ocr=True):")
        print("      • Returns semantic description + OCR text extraction")
        print("      • No coordinates returned (focused on text content)")
        print("      • Ideal for reading screen content")
        print("   🤖 Smart LLM Analysis:")
        print("      • Program detection and workflow understanding")
        print("      • Multiple detail levels (brief/standard/detailed)")
        print("      • Multi-provider fallback (OpenAI/Claude/Gemini)")
        print("\n💡 Usage in Claude Code:")
        print("   analyze_screen(include_ocr=False) → Get coordinates for clicking")
        print("   analyze_screen(include_ocr=True)  → Extract text content")
        print("\n🚀 To run the full MCP server:")
        print("   python start_server.py --transport stdio", file=sys.stderr)
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        raise
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...", file=sys.stderr)
        await server._cleanup()
        print("✅ Cleanup completed", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())