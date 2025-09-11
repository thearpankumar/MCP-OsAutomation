"""
Screenshot capture system using MSS for multi-monitor support.
"""

import asyncio
import base64
import io
import time
from typing import Any, Dict, List, Optional, Tuple

import mss
import numpy as np
from PIL import Image
from loguru import logger
from pydantic import BaseModel

from ..utils.config import Config


class ScreenInfo(BaseModel):
    """Screen information model."""
    
    index: int
    x: int
    y: int
    width: int
    height: int
    is_primary: bool


class ScreenshotResult(BaseModel):
    """Screenshot capture result model."""
    
    success: bool
    timestamp: float
    monitor: int
    x: int
    y: int
    width: int
    height: int
    format: str
    size_bytes: int
    base64_data: Optional[str] = None
    file_path: Optional[str] = None
    message: str


class ScreenshotCapture:
    """Screenshot capture system using MSS."""
    
    def __init__(self, config: Config):
        """Initialize screenshot capture system.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.mss_instance = mss.mss()
        self._screens: List[ScreenInfo] = []
        
        logger.info("ScreenshotCapture initialized")
    
    async def initialize(self) -> None:
        """Initialize screenshot capture system asynchronously."""
        try:
            # Get screen information
            await self._discover_screens()
            
            logger.info(f"ScreenshotCapture initialized with {len(self._screens)} screens")
            
        except Exception as e:
            logger.error(f"Failed to initialize ScreenshotCapture: {e}")
            raise
    
    async def _discover_screens(self) -> None:
        """Discover available screens/monitors."""
        try:
            # Get monitor information from MSS
            monitors = self.mss_instance.monitors
            
            self._screens = []
            for i, monitor in enumerate(monitors):
                if i == 0:
                    # Skip the first monitor (all monitors combined)
                    continue
                
                screen_info = ScreenInfo(
                    index=i - 1,  # Adjust index since we skip the first
                    x=monitor["left"],
                    y=monitor["top"],
                    width=monitor["width"],
                    height=monitor["height"],
                    is_primary=(i == 1)  # First real monitor is primary
                )
                self._screens.append(screen_info)
            
            logger.debug(f"Discovered {len(self._screens)} screens")
            for screen in self._screens:
                logger.debug(
                    f"Screen {screen.index}: {screen.width}x{screen.height} "
                    f"at ({screen.x}, {screen.y}) {'(Primary)' if screen.is_primary else ''}"
                )
                
        except Exception as e:
            logger.error(f"Failed to discover screens: {e}")
            raise
    
    async def get_screen_info(self) -> List[Dict[str, Any]]:
        """Get information about available screens.
        
        Returns:
            List of screen information dictionaries
        """
        return [screen.dict() for screen in self._screens]
    
    async def capture_screen(
        self,
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
        try:
            start_time = time.time()
            
            # Validate monitor number
            if monitor >= len(self._screens):
                return ScreenshotResult(
                    success=False,
                    timestamp=start_time,
                    monitor=monitor,
                    x=0,
                    y=0,
                    width=0,
                    height=0,
                    format=format,
                    size_bytes=0,
                    message=f"Invalid monitor number: {monitor}"
                ).dict()
            
            # Determine capture area
            if region:
                # Use custom region
                capture_area = {
                    "left": region["x"],
                    "top": region["y"],
                    "width": region["width"],
                    "height": region["height"]
                }
                x, y, width, height = region["x"], region["y"], region["width"], region["height"]
            else:
                # Use entire monitor
                monitor_idx = monitor + 1  # MSS uses 1-based indexing (0 is all monitors)
                capture_area = self.mss_instance.monitors[monitor_idx]
                screen = self._screens[monitor]
                x, y, width, height = screen.x, screen.y, screen.width, screen.height
            
            # Capture screenshot
            screenshot = self.mss_instance.grab(capture_area)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Convert to requested format
            img_buffer = io.BytesIO()
            save_format = format.upper()
            if save_format == "JPG":
                save_format = "JPEG"
            
            img.save(img_buffer, format=save_format, quality=95)
            img_data = img_buffer.getvalue()
            
            # Encode to base64
            base64_data = base64.b64encode(img_data).decode('utf-8')
            
            capture_time = time.time() - start_time
            
            logger.info(
                f"Captured screenshot: monitor={monitor}, "
                f"size={width}x{height}, format={format}, "
                f"bytes={len(img_data)}, time={capture_time:.3f}s"
            )
            
            return ScreenshotResult(
                success=True,
                timestamp=start_time,
                monitor=monitor,
                x=x,
                y=y,
                width=width,
                height=height,
                format=format,
                size_bytes=len(img_data),
                base64_data=base64_data,
                message=f"Screenshot captured successfully in {capture_time:.3f}s"
            ).dict()
            
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return ScreenshotResult(
                success=False,
                timestamp=time.time(),
                monitor=monitor,
                x=0,
                y=0,
                width=0,
                height=0,
                format=format,
                size_bytes=0,
                message=f"Screenshot capture failed: {str(e)}"
            ).dict()
    
    async def capture_all_screens(
        self,
        format: str = "png"
    ) -> List[Dict[str, Any]]:
        """Capture screenshots of all available monitors.
        
        Args:
            format: Image format (png, jpeg, webp)
            
        Returns:
            List of screenshot results
        """
        results = []
        
        for i in range(len(self._screens)):
            result = await self.capture_screen(monitor=i, format=format)
            results.append(result)
        
        logger.info(f"Captured {len(results)} screenshots across all monitors")
        return results
    
    async def save_screenshot(
        self,
        file_path: str,
        monitor: int = 0,
        region: Optional[Dict[str, int]] = None,
        format: Optional[str] = None
    ) -> Dict[str, Any]:
        """Capture and save screenshot to file.
        
        Args:
            file_path: Path to save screenshot
            monitor: Monitor number (0 for primary)
            region: Optional region to capture
            format: Optional format override (inferred from file_path if not provided)
            
        Returns:
            Save result
        """
        try:
            # Infer format from file extension if not provided
            if format is None:
                format = file_path.split('.')[-1].lower()
                if format not in ['png', 'jpg', 'jpeg', 'webp']:
                    format = 'png'
            
            # Capture screenshot
            result = await self.capture_screen(monitor=monitor, region=region, format=format)
            
            if not result["success"]:
                return result
            
            # Decode base64 and save to file
            img_data = base64.b64decode(result["base64_data"])
            
            with open(file_path, 'wb') as f:
                f.write(img_data)
            
            # Update result
            result["file_path"] = file_path
            result["base64_data"] = None  # Remove base64 data to save memory
            result["message"] = f"Screenshot saved to {file_path}"
            
            logger.info(f"Screenshot saved to {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
            return {
                "success": False,
                "timestamp": time.time(),
                "monitor": monitor,
                "file_path": file_path,
                "message": f"Failed to save screenshot: {str(e)}"
            }
    
    def get_pixel_color(
        self,
        x: int,
        y: int,
        monitor: int = 0
    ) -> Optional[Tuple[int, int, int]]:
        """Get pixel color at specified coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            monitor: Monitor number
            
        Returns:
            RGB color tuple or None if failed
        """
        try:
            # Capture single pixel region
            region = {"x": x, "y": y, "width": 1, "height": 1}
            
            # Use synchronous capture for single pixel (faster)
            if monitor >= len(self._screens):
                return None
            
            monitor_idx = monitor + 1  # MSS uses 1-based indexing
            capture_area = {
                "left": x,
                "top": y,
                "width": 1,
                "height": 1
            }
            
            screenshot = self.mss_instance.grab(capture_area)
            
            # Get RGB values (MSS returns BGRA, we need RGB)
            bgra = screenshot.pixel(0, 0)
            rgb = (bgra[2], bgra[1], bgra[0])  # Convert BGRA to RGB
            
            return rgb
            
        except Exception as e:
            logger.error(f"Failed to get pixel color at ({x}, {y}): {e}")
            return None
    
    async def monitor_screen_changes(
        self,
        monitor: int = 0,
        threshold: float = 0.1,
        check_interval: float = 1.0
    ) -> None:
        """Monitor screen for changes (basic implementation).
        
        Args:
            monitor: Monitor to watch
            threshold: Change threshold (0.0 to 1.0)
            check_interval: Check interval in seconds
            
        Note:
            This is a basic implementation. For production use,
            consider more efficient change detection algorithms.
        """
        try:
            logger.info(f"Starting screen change monitoring on monitor {monitor}")
            
            # Take initial screenshot
            prev_result = await self.capture_screen(monitor=monitor)
            if not prev_result["success"]:
                logger.error("Failed to take initial screenshot for monitoring")
                return
            
            prev_image = Image.open(io.BytesIO(
                base64.b64decode(prev_result["base64_data"])
            ))
            prev_array = np.array(prev_image)
            
            while True:
                await asyncio.sleep(check_interval)
                
                # Take current screenshot
                curr_result = await self.capture_screen(monitor=monitor)
                if not curr_result["success"]:
                    continue
                
                curr_image = Image.open(io.BytesIO(
                    base64.b64decode(curr_result["base64_data"])
                ))
                curr_array = np.array(curr_image)
                
                # Calculate difference
                diff = np.mean(np.abs(curr_array - prev_array)) / 255.0
                
                if diff > threshold:
                    logger.info(f"Screen change detected: {diff:.3f}")
                    # Here you could emit events or call callbacks
                
                prev_array = curr_array
                
        except Exception as e:
            logger.error(f"Screen monitoring failed: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup screenshot capture resources."""
        try:
            if self.mss_instance:
                self.mss_instance.close()
            logger.info("ScreenshotCapture cleaned up")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")