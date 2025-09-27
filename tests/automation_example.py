#!/usr/bin/env python3
"""
Automation workflow example for MCP WebAutomation.

This example demonstrates a complete automation workflow:
1. Capture and analyze screen
2. Find specific text or UI elements
3. Perform automation actions
4. Verify results
"""

import asyncio
import sys
import time

from mcp_automation.automation.controller import AutomationController
from mcp_automation.intelligence.screen_analyzer import ScreenAnalyzer
from mcp_automation.safety.permission_manager import PermissionManager
from mcp_automation.utils.config import Config, ServerConfig, SafetyConfig, OCRConfig


async def automation_workflow_example():
    """Example of a complete automation workflow."""
    print("🤖 MCP WebAutomation - Automation Workflow Example")
    print("=" * 60, file=sys.stderr)
    
    # Create configuration
    config = Config(
        server=ServerConfig(debug=True),
        safety=SafetyConfig(require_confirmation=False),  # Disable confirmations for demo
        ocr=OCRConfig(confidence_threshold=0.7)
    )
    
    # Initialize components
    screen_analyzer = ScreenAnalyzer(config)
    automation_controller = AutomationController(config)
    permission_manager = PermissionManager(config)
    
    try:
        # Initialize all components
        print("🔧 Initializing components...", file=sys.stderr)
        await asyncio.gather(
            screen_analyzer.initialize(),
            automation_controller.initialize(),
            permission_manager.initialize()
        )
        print("✅ All components initialized")
        
        # Step 1: Capture and analyze current screen
        print("\n📸 Step 1: Capturing and analyzing screen...", file=sys.stderr)
        analysis = await screen_analyzer.analyze_screen(
            include_ocr=True,
            include_elements=True
        )
        
        if not analysis["success"]:
            print(f"❌ Screen analysis failed: {analysis['message']}")
            return
        
        print(f"✅ Screen analyzed successfully:", file=sys.stderr)
        if analysis["ocr_result"]:
            print(f"   📝 Found {analysis['ocr_result']['word_count']} words")
            print(f"   🎯 OCR confidence: {analysis['ocr_result']['confidence_avg']:.2f}", file=sys.stderr)
        
        if analysis["cv_result"]:
            elements = analysis["cv_result"]["elements"]
            buttons = [e for e in elements if e["type"] == "button"]
            textboxes = [e for e in elements if e["type"] == "textbox"]
            print(f"   🔲 UI Elements: {len(buttons)} buttons, {len(textboxes)} textboxes")
        
        # Step 2: Demonstrate text search
        print("\n🔍 Step 2: Searching for specific text...", file=sys.stderr)
        search_terms = ["File", "Edit", "View", "Help", "Settings"]
        
        for term in search_terms:
            search_result = await screen_analyzer.find_text(term, confidence=0.6)
            if search_result["success"] and search_result["matches"]:
                match = search_result["matches"][0]
                print(f"   ✅ Found '{term}' at ({match['center_x']:.0f}, {match['center_y']:.0f}, file=sys.stderr)")
                
                # Demonstrate click automation (with permission check)
                click_permission = await permission_manager.request_permission(
                    "click_element",
                    {"x": int(match['center_x']), "y": int(match['center_y']), "button": "left"}
                )
                
                if click_permission:
                    print(f"   🖱️ Permission granted, would click '{term}' (demo mode, file=sys.stderr)")
                    # In real usage, you would uncomment the next line:
                    # await automation_controller.click_element(x=int(match['center_x']), y=int(match['center_y']))
                else:
                    print(f"   🚫 Permission denied for clicking '{term}'")
                
                break
        else:
            print("   ℹ️ No common UI text found (this is normal, file=sys.stderr)")
        
        # Step 3: Demonstrate UI element interaction
        print("\n🎯 Step 3: UI Element interaction demo...", file=sys.stderr)
        if analysis["cv_result"] and analysis["cv_result"]["elements"]:
            elements = analysis["cv_result"]["elements"]
            
            # Find the most confident button
            buttons = [e for e in elements if e["type"] == "button"]
            if buttons:
                best_button = max(buttons, key=lambda x: x["confidence"])
                print(f"   🔲 Found button at ({best_button['center_x']}, {best_button['center_y']}, file=sys.stderr) "
                      f"with confidence {best_button['confidence']:.2f}")
                
                # Demonstrate permission request
                click_permission = await permission_manager.request_permission(
                    "click_element",
                    {"x": best_button['center_x'], "y": best_button['center_y'], "button": "left"}
                )
                print(f"   {'✅ Permission granted' if click_permission else '🚫 Permission denied'}")
        
        # Step 4: Demonstrate typing automation
        print("\n⌨️ Step 4: Typing automation demo...", file=sys.stderr)
        type_permission = await permission_manager.request_permission(
            "type_text",
            {"text": "Hello from MCP WebAutomation!", "delay": 0.1}
        )
        
        if type_permission:
            print("   ✅ Permission granted for typing demo", file=sys.stderr)
            # In real usage, you would uncomment the next lines:
            # result = await automation_controller.type_text(
            #     "Hello from MCP WebAutomation!", delay=0.1
            # )
            # print(f"   📝 Typing result: {result['message']}")
        else:
            print("   🚫 Permission denied for typing demo", file=sys.stderr)
        
        # Step 5: Get current context summary
        print("\n📋 Step 5: Current screen context summary...")
        context = await screen_analyzer.get_screen_context()
        if context["success"]:
            ctx = context["context"]
            print(f"   🖥️ Screen: {ctx['screen_info']['width']}x{ctx['screen_info']['height']}", file=sys.stderr)
            print(f"   📝 Text: {ctx['text_content']['word_count']} words")
            print(f"   🔲 UI: {ctx['ui_elements']['total_count']} elements", file=sys.stderr)
            print(f"   📊 Summary: {ctx['analysis_summary']['summary']}")
        
        # Step 6: Permission status
        print("\n🔐 Step 6: Permission system status...", file=sys.stderr)
        perm_status = await permission_manager.get_permission_status()
        print(f"   📊 Session permissions: {perm_status['session_permissions']}")
        print(f"   ✅ Approved actions: {perm_status['approved_actions']}", file=sys.stderr)
        print(f"   ❌ Denied actions: {perm_status['denied_actions']}")
        print(f"   🕐 Recent actions: {perm_status['recent_actions']}", file=sys.stderr)
        
        print("\n✅ Automation workflow completed successfully!")
        print("\n💡 This example demonstrates the key capabilities:", file=sys.stderr)
        print("   • Screen capture and analysis")
        print("   • OCR text detection and search", file=sys.stderr)
        print("   • UI element detection")
        print("   • Permission-based automation", file=sys.stderr)
        print("   • Safe automation workflows")
        
    except Exception as e:
        print(f"❌ Workflow error: {e}", file=sys.stderr)
        raise
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up components...", file=sys.stderr)
        await asyncio.gather(
            screen_analyzer.cleanup(),
            automation_controller.cleanup(),
            permission_manager.cleanup(),
            return_exceptions=True
        )
        print("✅ Cleanup completed")


if __name__ == "__main__":
    print("⚠️  This example demonstrates automation capabilities.", file=sys.stderr)
    print("    It will analyze your screen but won't perform actual clicks/typing.", file=sys.stderr)
    print("    To enable full automation, modify the permission settings.\n")
    
    try:
        asyncio.run(automation_workflow_example())
    except KeyboardInterrupt:
        print("\n🛑 Example interrupted by user", file=sys.stderr)
    except Exception as e:
        print(f"\n💥 Example failed: {e}")
        print("   Make sure all dependencies are installed:", file=sys.stderr)
        print("   pip install -e .", file=sys.stderr)