#!/usr/bin/env python3
"""
Start script for MCP WebAutomation Server.

This script provides an easy way to start the MCP WebAutomation server
with different configurations and transports.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_automation.server import WebAutomationServer


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MCP WebAutomation Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_server.py                    # Start with stdio transport
  python start_server.py --transport ws    # Start with WebSocket transport
  python start_server.py --config custom.json --debug
        """
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (default: configs/fastmcp.json)"
    )
    
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "ws", "sse"],
        help="Transport method (default: stdio)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run basic functionality tests instead of starting server"
    )
    
    args = parser.parse_args()
    
    # Only print to stderr to avoid contaminating MCP stdout communication
    import sys
    
    if args.test:
        # Test mode - run tests and exit
        print("🧪 Running functionality tests...", file=sys.stderr)
        from examples.basic_usage import main as test_main
        try:
            asyncio.run(test_main())
            print("✅ Tests completed successfully!", file=sys.stderr)
        except KeyboardInterrupt:
            print("\n🛑 Tests interrupted by user", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"\n💥 Tests failed: {e}", file=sys.stderr)
            if args.debug:
                import traceback
                traceback.print_exc(file=sys.stderr)
            sys.exit(1)
    else:
        # Server mode - start the MCP server
        # For MCP communication, we need clean stdout - log to stderr instead
        print("🚀 MCP WebAutomation Server", file=sys.stderr)
        print("=" * 40, file=sys.stderr)
        print(f"Transport: {args.transport}", file=sys.stderr)
        print(f"Config: {args.config or 'configs/fastmcp.json'}", file=sys.stderr)
        print(f"Debug: {args.debug}", file=sys.stderr)
        print("-" * 40, file=sys.stderr)
        
        try:
            # Create server
            print("Creating WebAutomation server...", file=sys.stderr)
            server = WebAutomationServer(config_path=args.config)
            print("Server created successfully", file=sys.stderr)
            
            # Override debug setting if specified
            if args.debug:
                server.config.server.debug = True
                print("Debug mode enabled", file=sys.stderr)
            
            # Run server
            print("Starting server...", file=sys.stderr)
            server.run(transport=args.transport)
            
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user", file=sys.stderr)
        except Exception as e:
            print(f"\n💥 Server failed: {e}", file=sys.stderr)
            if args.debug:
                import traceback
                traceback.print_exc(file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()