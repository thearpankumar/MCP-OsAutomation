"""
Core automation controller using pynput for cross-platform input control.
"""

import asyncio
import platform
import time
from typing import Any, Dict, List, Optional, Tuple

import pynput
from loguru import logger
from pydantic import BaseModel
from pynput import keyboard, mouse

from ..utils.config import Config


class ClickResult(BaseModel):
    """Result of a click operation."""
    
    success: bool
    x: int
    y: int
    button: str
    clicks: int
    timestamp: float
    message: str


class TypeResult(BaseModel):
    """Result of a typing operation."""
    
    success: bool
    text: str
    characters_typed: int
    timestamp: float
    message: str


class AutomationController:
    """Core automation controller using pynput."""
    
    def __init__(self, config: Config):
        """Initialize the automation controller.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        
        # Platform-specific setup
        self.platform = platform.system().lower()
        self._is_trusted = True
        
        # Rate limiting
        self._action_times: List[float] = []
        
        logger.info(f"AutomationController initialized for {self.platform}")
    
    async def initialize(self) -> None:
        """Initialize the automation controller asynchronously."""
        try:
            # Check accessibility permissions on macOS
            if self.platform == "darwin":
                self._check_macos_permissions()
            
            # Test basic functionality
            await self._test_functionality()
            
            logger.info("AutomationController initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AutomationController: {e}")
            raise
    
    def _check_macos_permissions(self) -> None:
        """Check macOS accessibility permissions."""
        try:
            # Try to get current mouse position to test permissions
            current_pos = self.mouse_controller.position
            logger.debug(f"Mouse position test: {current_pos}")
            
            # Check if keyboard listener has permissions
            if hasattr(keyboard.Listener, 'IS_TRUSTED'):
                self._is_trusted = keyboard.Listener.IS_TRUSTED
                if not self._is_trusted:
                    logger.warning(
                        "macOS accessibility permissions not granted. "
                        "Please enable accessibility access for this application in "
                        "System Preferences > Security & Privacy > Privacy > Accessibility"
                    )
                    
        except Exception as e:
            logger.warning(f"Could not check macOS permissions: {e}")
    
    async def _test_functionality(self) -> None:
        """Test basic automation functionality."""
        try:
            # Test mouse position
            position = self.mouse_controller.position
            logger.debug(f"Current mouse position: {position}")
            
            # Test keyboard (non-intrusive)
            # Just check if we can create the controller
            _ = keyboard.Controller()
            
            logger.debug("Basic functionality test passed")
            
        except Exception as e:
            logger.error(f"Functionality test failed: {e}")
            raise
    
    def _check_rate_limit(self) -> bool:
        """Check if action is within rate limits.
        
        Returns:
            True if action is allowed, False if rate limited
        """
        current_time = time.time()
        
        # Remove actions older than 1 minute
        self._action_times = [
            t for t in self._action_times 
            if current_time - t < 60
        ]
        
        # Check if we're under the rate limit
        if len(self._action_times) >= self.config.safety.max_actions_per_minute:
            return False
        
        # Record this action
        self._action_times.append(current_time)
        return True
    
    def _check_bounds(self, x: int, y: int) -> bool:
        """Check if coordinates are within automation bounds.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if coordinates are allowed
        """
        if self.config.safety.automation_bounds is None:
            return True
            
        bounds = self.config.safety.automation_bounds
        return (
            bounds["x"] <= x <= bounds["x"] + bounds["width"] and
            bounds["y"] <= y <= bounds["y"] + bounds["height"]
        )
    
    async def click_element(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        element_text: Optional[str] = None,
        button: str = "left",
        clicks: int = 1
    ) -> Dict[str, Any]:
        """Click on screen element by coordinates or text.
        
        Args:
            x: X coordinate
            y: Y coordinate
            element_text: Text to find and click (requires screen analyzer)
            button: Mouse button (left, right, middle)
            clicks: Number of clicks
            
        Returns:
            Click result
        """
        try:
            # Rate limiting check
            if not self._check_rate_limit():
                return ClickResult(
                    success=False,
                    x=x or 0,
                    y=y or 0,
                    button=button,
                    clicks=clicks,
                    timestamp=time.time(),
                    message="Rate limit exceeded"
                ).dict()
            
            # Determine coordinates
            if element_text and not (x and y):
                # TODO: Integrate with screen analyzer to find text
                raise NotImplementedError("Text-based clicking requires screen analyzer integration")
            
            if x is None or y is None:
                raise ValueError("Either coordinates (x, y) or element_text must be provided")
            
            # Check bounds
            if not self._check_bounds(x, y):
                return ClickResult(
                    success=False,
                    x=x,
                    y=y,
                    button=button,
                    clicks=clicks,
                    timestamp=time.time(),
                    message="Coordinates outside automation bounds"
                ).dict()
            
            # Map button names
            button_map = {
                "left": mouse.Button.left,
                "right": mouse.Button.right,
                "middle": mouse.Button.middle
            }
            
            if button not in button_map:
                raise ValueError(f"Invalid button: {button}. Use: left, right, middle")
            
            mouse_button = button_map[button]
            
            # Perform click
            self.mouse_controller.position = (x, y)
            await asyncio.sleep(0.1)  # Small delay to ensure position is set
            
            for _ in range(clicks):
                self.mouse_controller.click(mouse_button)
                if clicks > 1:
                    await asyncio.sleep(0.1)  # Delay between multiple clicks
            
            logger.info(f"Clicked at ({x}, {y}) with {button} button, {clicks} times")
            
            return ClickResult(
                success=True,
                x=x,
                y=y,
                button=button,
                clicks=clicks,
                timestamp=time.time(),
                message=f"Successfully clicked at ({x}, {y})"
            ).dict()
            
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return ClickResult(
                success=False,
                x=x or 0,
                y=y or 0,
                button=button,
                clicks=clicks,
                timestamp=time.time(),
                message=f"Click failed: {str(e)}"
            ).dict()
    
    async def type_text(
        self,
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
            Typing result
        """
        try:
            # Rate limiting check
            if not self._check_rate_limit():
                return TypeResult(
                    success=False,
                    text=text,
                    characters_typed=0,
                    timestamp=time.time(),
                    message="Rate limit exceeded"
                ).dict()
            
            characters_typed = 0
            
            # Clear existing text if requested
            if clear_first:
                # Select all and delete
                self.keyboard_controller.press(keyboard.Key.ctrl)
                self.keyboard_controller.press("a")
                self.keyboard_controller.release("a")
                self.keyboard_controller.release(keyboard.Key.ctrl)
                await asyncio.sleep(0.05)
                self.keyboard_controller.press(keyboard.Key.delete)
                self.keyboard_controller.release(keyboard.Key.delete)
                await asyncio.sleep(0.1)
            
            # Type text character by character
            for char in text:
                try:
                    self.keyboard_controller.type(char)
                    characters_typed += 1
                    if delay > 0:
                        await asyncio.sleep(delay)
                except Exception as e:
                    logger.warning(f"Failed to type character '{char}': {e}")
                    # Continue with next character
            
            logger.info(f"Typed {characters_typed}/{len(text)} characters")
            
            return TypeResult(
                success=True,
                text=text,
                characters_typed=characters_typed,
                timestamp=time.time(),
                message=f"Successfully typed {characters_typed} characters"
            ).dict()
            
        except Exception as e:
            logger.error(f"Type text failed: {e}")
            return TypeResult(
                success=False,
                text=text,
                characters_typed=0,
                timestamp=time.time(),
                message=f"Type text failed: {str(e)}"
            ).dict()
    
    async def press_key(
        self,
        key: str,
        modifiers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Press a key or key combination.
        
        Args:
            key: Key to press (e.g., 'enter', 'tab', 'a')
            modifiers: List of modifier keys (e.g., ['ctrl', 'shift'])
            
        Returns:
            Key press result
        """
        try:
            # Rate limiting check
            if not self._check_rate_limit():
                return {
                    "success": False,
                    "key": key,
                    "modifiers": modifiers,
                    "timestamp": time.time(),
                    "message": "Rate limit exceeded"
                }
            
            # Map special keys
            special_keys = {
                "enter": keyboard.Key.enter,
                "tab": keyboard.Key.tab,
                "space": keyboard.Key.space,
                "backspace": keyboard.Key.backspace,
                "delete": keyboard.Key.delete,
                "esc": keyboard.Key.esc,
                "escape": keyboard.Key.esc,
                "shift": keyboard.Key.shift,
                "ctrl": keyboard.Key.ctrl,
                "alt": keyboard.Key.alt,
                "cmd": keyboard.Key.cmd,
                "up": keyboard.Key.up,
                "down": keyboard.Key.down,
                "left": keyboard.Key.left,
                "right": keyboard.Key.right,
                "home": keyboard.Key.home,
                "end": keyboard.Key.end,
                "page_up": keyboard.Key.page_up,
                "page_down": keyboard.Key.page_down,
            }
            
            # Map modifiers
            modifier_keys = {
                "ctrl": keyboard.Key.ctrl,
                "shift": keyboard.Key.shift,
                "alt": keyboard.Key.alt,
                "cmd": keyboard.Key.cmd,
            }
            
            # Press modifiers
            pressed_modifiers = []
            if modifiers:
                for modifier in modifiers:
                    if modifier in modifier_keys:
                        self.keyboard_controller.press(modifier_keys[modifier])
                        pressed_modifiers.append(modifier_keys[modifier])
            
            # Press main key
            if key in special_keys:
                self.keyboard_controller.press(special_keys[key])
                await asyncio.sleep(0.05)  # Small delay for key registration
                self.keyboard_controller.release(special_keys[key])
            else:
                self.keyboard_controller.press(key)
                await asyncio.sleep(0.05)  # Small delay for key registration
                self.keyboard_controller.release(key)
            
            # Small delay before releasing modifiers
            await asyncio.sleep(0.05)
            
            # Release modifiers in reverse order
            for modifier_key in reversed(pressed_modifiers):
                self.keyboard_controller.release(modifier_key)
            
            logger.info(f"Pressed key: {key} with modifiers: {modifiers}")
            
            return {
                "success": True,
                "key": key,
                "modifiers": modifiers,
                "timestamp": time.time(),
                "message": f"Successfully pressed {key}",
                "completed": True,
                "action_finished": True
            }
            
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return {
                "success": False,
                "key": key,
                "modifiers": modifiers,
                "timestamp": time.time(),
                "message": f"Key press failed: {str(e)}"
            }
    
    async def scroll(
        self,
        x: int,
        y: int,
        dx: int = 0,
        dy: int = 0
    ) -> Dict[str, Any]:
        """Scroll at specified position.
        
        Args:
            x: X position to scroll at
            y: Y position to scroll at
            dx: Horizontal scroll amount
            dy: Vertical scroll amount
            
        Returns:
            Scroll result
        """
        try:
            # Rate limiting check
            if not self._check_rate_limit():
                return {
                    "success": False,
                    "x": x,
                    "y": y,
                    "dx": dx,
                    "dy": dy,
                    "timestamp": time.time(),
                    "message": "Rate limit exceeded"
                }
            
            # Check bounds
            if not self._check_bounds(x, y):
                return {
                    "success": False,
                    "x": x,
                    "y": y,
                    "dx": dx,
                    "dy": dy,
                    "timestamp": time.time(),
                    "message": "Coordinates outside automation bounds"
                }
            
            # Move mouse to position and scroll
            self.mouse_controller.position = (x, y)
            await asyncio.sleep(0.05)
            
            self.mouse_controller.scroll(dx, dy)
            
            logger.info(f"Scrolled at ({x}, {y}) by ({dx}, {dy})")
            
            return {
                "success": True,
                "x": x,
                "y": y,
                "dx": dx,
                "dy": dy,
                "timestamp": time.time(),
                "message": f"Successfully scrolled at ({x}, {y})"
            }
            
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            return {
                "success": False,
                "x": x,
                "y": y,
                "dx": dx,
                "dy": dy,
                "timestamp": time.time(),
                "message": f"Scroll failed: {str(e)}"
            }
    
    async def get_mouse_position(self) -> Dict[str, Any]:
        """Get current mouse position.
        
        Returns:
            Current mouse position
        """
        try:
            x, y = self.mouse_controller.position
            return {
                "success": True,
                "x": x,
                "y": y,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Failed to get mouse position: {e}")
            return {
                "success": False,
                "x": 0,
                "y": 0,
                "timestamp": time.time(),
                "message": f"Failed to get mouse position: {str(e)}"
            }
    
    async def emergency_stop(self) -> None:
        """Emergency stop all automation activities."""
        try:
            # Clear action queue by resetting rate limiter
            self._action_times.clear()
            
            # Move mouse to a safe position (center of screen)
            # This is a basic implementation - could be enhanced
            self.mouse_controller.position = (500, 500)
            
            logger.warning("Emergency stop executed")
            
        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup automation controller resources."""
        logger.info("Cleaning up AutomationController...")
        
        # Clear rate limiting data
        self._action_times.clear()
        
        # Any other cleanup can be added here