"""
MCP WebAutomation Server

A comprehensive MCP server providing system-level automation capabilities
with real-time screen context awareness for AI agents.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from loguru import logger
from pydantic import BaseModel, Field

from .automation.controller import AutomationController
from .intelligence.screen_analyzer import ScreenAnalyzer
from .safety.permission_manager import PermissionManager
from .utils.config import Config


class ServerConfig(BaseModel):
    """Server configuration model."""
    
    name: str = Field(default="WebAutomation", description="Server name")
    version: str = Field(default="0.1.0", description="Server version")
    description: str = Field(
        default="MCP System Automation Tool for AI-driven desktop control",
        description="Server description"
    )
    debug: bool = Field(default=False, description="Enable debug mode")


class SafetyConfig(BaseModel):
    """Safety configuration model."""
    
    require_confirmation: bool = Field(
        default=True, 
        description="Require user confirmation for sensitive actions"
    )
    automation_bounds: Optional[Dict[str, int]] = Field(
        default=None,
        description="Screen bounds for automation (x, y, width, height)"
    )
    max_actions_per_minute: int = Field(
        default=60,
        description="Maximum actions per minute rate limit"
    )
    allowed_applications: Optional[List[str]] = Field(
        default=None,
        description="List of allowed applications for automation"
    )


class OCRConfig(BaseModel):
    """OCR configuration model."""
    
    engine: str = Field(default="paddleocr", description="OCR engine to use")
    confidence_threshold: float = Field(
        default=0.8,
        description="Minimum confidence threshold for OCR results"
    )
    languages: List[str] = Field(
        default=["en"],
        description="Languages to detect in OCR"
    )


class WebAutomationServer:
    """Main MCP WebAutomation Server class."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the WebAutomation server.
        
        Args:
            config_path: Optional path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize FastMCP server
        self.mcp = FastMCP(
            name=self.config.server.name,
            version=self.config.server.version
        )
        
        # Initialize components
        self.automation_controller: Optional[AutomationController] = None
        self.screen_analyzer: Optional[ScreenAnalyzer] = None
        self.permission_manager: Optional[PermissionManager] = None
        
        # Setup MCP tools
        self._setup_mcp_tools()
        
        logger.info(f"WebAutomation Server initialized: {self.config.server.name} v{self.config.server.version}")
    
    def _load_config(self, config_path: Optional[str] = None) -> Config:
        """Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Loaded configuration
        """
        if config_path is None:
            config_path = "configs/fastmcp.json"
            
        config_file = Path(config_path)
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
        else:
            config_data = {}
            logger.info("Using default configuration")
        
        return Config(**config_data)
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        # Remove default handler
        logger.remove()
        
        # Add console handler
        log_level = "DEBUG" if self.config.server.debug else "INFO"
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        # Add file handler
        logger.add(
            "logs/webautomation.log",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="1 day",
            retention="7 days"
        )
    
    async def _initialize_components(self) -> None:
        """Initialize all server components asynchronously."""
        try:
            # Initialize automation controller
            self.automation_controller = AutomationController(self.config)
            await self.automation_controller.initialize()
            logger.info("Automation controller initialized")
            
            # Initialize screen analyzer
            self.screen_analyzer = ScreenAnalyzer(self.config)
            await self.screen_analyzer.initialize()
            logger.info("Screen analyzer initialized")
            
            # Initialize permission manager
            self.permission_manager = PermissionManager(self.config)
            await self.permission_manager.initialize()
            logger.info("Permission manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def _setup_mcp_tools(self) -> None:
        """Setup all MCP tools."""
        
        # Core automation tools
        @self.mcp.tool()
        async def capture_screen(
            monitor: int = 0,
            region: Optional[Dict[str, int]] = None,
            format: str = "png"
        ) -> Dict[str, Any]:
            """Capture screenshot of specified monitor or region.
            
            Args:
                monitor: Monitor number (0 for primary)
                region: Optional region dict with x, y, width, height
                format: Image format (png, jpeg, webp)
                
            Returns:
                Screenshot data and metadata
            """
            if not self.screen_analyzer:
                raise RuntimeError("Screen analyzer not initialized")
                
            return await self.screen_analyzer.capture_screen(
                monitor=monitor,
                region=region,
                format=format
            )
        
        @self.mcp.tool()
        async def click_element(
            x: Optional[int] = None,
            y: Optional[int] = None,
            element_text: Optional[str] = None,
            button: str = "left",
            clicks: int = 1
        ) -> Dict[str, Any]:
            """Click on screen element by coordinates or text.
            
            Args:
                x: X coordinate (if not using element_text)
                y: Y coordinate (if not using element_text)
                element_text: Text to find and click
                button: Mouse button (left, right, middle)
                clicks: Number of clicks
                
            Returns:
                Click result and confirmation
            """
            if not self.automation_controller:
                raise RuntimeError("Automation controller not initialized")
                
            # Check permissions
            if self.permission_manager:
                await self.permission_manager.request_permission(
                    "click_element",
                    {"x": x, "y": y, "text": element_text, "button": button}
                )
            
            return await self.automation_controller.click_element(
                x=x, y=y, element_text=element_text, button=button, clicks=clicks
            )
        
        @self.mcp.tool()
        async def type_text(
            text: str,
            delay: float = 0.1,
            clear_first: bool = False
        ) -> Dict[str, Any]:
            """Type text with optional delay between characters.
            
            Args:
                text: Text to type
                delay: Delay between keystrokes in seconds
                clear_first: Whether to clear existing text first
                
            Returns:
                Typing result confirmation
            """
            if not self.automation_controller:
                raise RuntimeError("Automation controller not initialized")
                
            # Check permissions
            if self.permission_manager:
                await self.permission_manager.request_permission(
                    "type_text",
                    {"text": text[:50] + "..." if len(text) > 50 else text}
                )
            
            return await self.automation_controller.type_text(
                text=text, delay=delay, clear_first=clear_first
            )
        
        @self.mcp.tool()
        async def press_key(
            key: str,
            modifiers: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """Press a key or key combination (keyboard shortcuts). This action completes immediately.
            
            Args:
                key: Key to press (e.g., 'c', 'enter', 'tab', 'f5')
                modifiers: List of modifier keys (e.g., ['ctrl'], ['ctrl', 'shift'])
                
            Returns:
                Key press result confirmation - action is complete, do not repeat
            """
            if not self.automation_controller:
                raise RuntimeError("Automation controller not initialized")
                
            # Check permissions
            if self.permission_manager:
                await self.permission_manager.request_permission(
                    "press_key",
                    {"key": key, "modifiers": modifiers or []}
                )
            
            result = await self.automation_controller.press_key(
                key=key, modifiers=modifiers
            )
            
            # Return clean response to avoid API errors
            return {
                "success": result.get("success", True),
                "message": f"Key combination executed: {'+'.join((modifiers or []) + [key])}",
                "completed": True
            }
        
        @self.mcp.tool()
        async def analyze_screen(
            include_ocr: bool = True,
            include_elements: bool = True,
            region: Optional[Dict[str, int]] = None
        ) -> Dict[str, Any]:
            """Analyze current screen content and provide AI context.
            
            Args:
                include_ocr: Whether to include OCR text extraction
                include_elements: Whether to include UI element detection
                region: Optional region to analyze
                
            Returns:
                Complete screen analysis with AI context
            """
            if not self.screen_analyzer:
                raise RuntimeError("Screen analyzer not initialized")
                
            return await self.screen_analyzer.analyze_screen(
                include_ocr=include_ocr,
                include_elements=include_elements,
                region=region
            )
        
        @self.mcp.tool()
        async def find_text(
            text: str,
            confidence: Optional[float] = None,
            region: Optional[Dict[str, int]] = None
        ) -> Dict[str, Any]:
            """Find text on screen using OCR.
            
            Args:
                text: Text to find
                confidence: Minimum confidence threshold
                region: Optional region to search in
                
            Returns:
                Text locations and confidence scores
            """
            if not self.screen_analyzer:
                raise RuntimeError("Screen analyzer not initialized")
                
            return await self.screen_analyzer.find_text(
                text=text,
                confidence=confidence or self.config.ocr.confidence_threshold,
                region=region
            )
        
        @self.mcp.tool()
        async def emergency_stop() -> Dict[str, Any]:
            """Emergency stop all automation activities.
            
            Returns:
                Stop confirmation
            """
            logger.warning("Emergency stop requested")
            
            if self.automation_controller:
                await self.automation_controller.emergency_stop()
            
            return {
                "status": "stopped",
                "message": "All automation activities stopped",
                "timestamp": asyncio.get_event_loop().time()
            }
        
        logger.info("MCP tools registered successfully")
    
    def run(self, transport: str = "stdio") -> None:
        """Run the MCP server.
        
        Args:
            transport: Transport method (stdio, ws, sse)
        """
        # Initialize components first
        async def initialize():
            await self._initialize_components()
            logger.info(f"WebAutomation server initialized, starting with {transport} transport")
        
        try:
            # Run initialization
            asyncio.run(initialize())
            
            # Run FastMCP server (synchronous) - this handles MCP protocol
            self.mcp.run(transport=transport)
            
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            # Run cleanup
            asyncio.run(self._cleanup())
            raise
        finally:
            # Always cleanup
            try:
                asyncio.run(self._cleanup())
            except Exception:
                pass  # Cleanup errors shouldn't crash the server
    
    async def _cleanup(self) -> None:
        """Cleanup server resources."""
        logger.info("Cleaning up server resources...")
        
        if self.automation_controller:
            await self.automation_controller.cleanup()
        
        if self.screen_analyzer:
            await self.screen_analyzer.cleanup()
        
        if self.permission_manager:
            await self.permission_manager.cleanup()


def main():
    """Main entry point for the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP WebAutomation Server")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "ws", "sse"],
        help="Transport method"
    )
    
    args = parser.parse_args()
    
    # Create and run server
    server = WebAutomationServer(config_path=args.config)
    asyncio.run(server.run(transport=args.transport))


if __name__ == "__main__":
    main()