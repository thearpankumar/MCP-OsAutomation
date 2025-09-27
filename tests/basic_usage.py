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
        
        # Test screen analysis with LLM vision
        print("\n🔍 Testing screen analysis with LLM vision...", file=sys.stderr)
        if server.screen_analyzer:
            analysis_result = await server.screen_analyzer.analyze_screen(
                include_ocr=False,  # Test vision-only analysis first
                analysis_detail="standard",
                vision_provider="openai"  # Test the new vision provider
            )
            if analysis_result["success"]:
                programs = ", ".join(analysis_result["programs_detected"]) if analysis_result["programs_detected"] else "None detected"
                print(f"✅ Screen analysis completed using {analysis_result['provider_used']}")
                print(f"   Programs detected: {programs}", file=sys.stderr)
                print(f"   UI State: {analysis_result['ui_state']}", file=sys.stderr)
                print(f"   Description: {analysis_result['screen_description'][:100]}...", file=sys.stderr)
            else:
                print(f"❌ Screen analysis failed: {analysis_result['message']}")

        # Test OCR functionality (if vision analysis succeeded)
        if server.screen_analyzer and analysis_result.get("success"):
            print("\n📝 Testing OCR text extraction...", file=sys.stderr)
            ocr_analysis = await server.screen_analyzer.analyze_screen(
                include_ocr=True,  # Now test with OCR enabled
                analysis_detail="brief",
                vision_provider="openai"
            )
            if ocr_analysis["success"] and ocr_analysis.get("ocr_text"):
                word_count = len(ocr_analysis["ocr_text"].split())
                print(f"✅ OCR extraction successful: {word_count} words extracted", file=sys.stderr)
                print(f"   Sample text: {ocr_analysis['ocr_text'][:80]}...", file=sys.stderr)
            else:
                print(f"ℹ️ OCR text extraction: No text found or OCR disabled", file=sys.stderr)

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
        print("\n🎉 New LLM Vision Analysis Features Tested:")
        print("   • Semantic screen understanding (not just coordinates)")
        print("   • Program detection and workflow analysis")
        print("   • Optional OCR text extraction")
        print("   • Multiple detail levels (brief/standard/detailed)")
        print("\n💡 To run the full MCP server, use:")
        print("   python -m mcp_automation.server --transport stdio", file=sys.stderr)
        
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