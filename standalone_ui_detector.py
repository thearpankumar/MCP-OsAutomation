#!/usr/bin/env python3
"""
Standalone UI Element Detection Tool
Extracted from MCP WebAutomation project

This tool captures screenshots and detects UI elements (buttons, textboxes, images)
using computer vision techniques. Shows exact output format that would be passed to LLM.
"""

import asyncio
import base64
import io
import json
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import mss
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel

# === Extracted Models from original source ===

class UIElement(BaseModel):
    """Detected UI element."""

    type: str  # button, textbox, image, etc.
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    center_x: int
    center_y: int
    area: int
    properties: Dict[str, Any] = {}


class CVAnalysisResult(BaseModel):
    """Computer vision analysis result."""

    success: bool
    timestamp: float
    processing_time: float
    elements: List[UIElement]
    image_properties: Dict[str, Any]
    message: str


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


# === Extracted Screenshot Capture System ===

class ScreenshotCapture:
    """Screenshot capture system using MSS."""

    def __init__(self):
        """Initialize screenshot capture system."""
        self.mss_instance = mss.mss()
        self._screens: List[Dict] = []
        print("ScreenshotCapture initialized")

    async def initialize(self) -> None:
        """Initialize screenshot capture system asynchronously."""
        try:
            # Get screen information
            await self._discover_screens()
            print(f"ScreenshotCapture initialized with {len(self._screens)} screens")

        except Exception as e:
            print(f"Failed to initialize ScreenshotCapture: {e}")
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

                screen_info = {
                    "index": i - 1,  # Adjust index since we skip the first
                    "x": monitor["left"],
                    "y": monitor["top"],
                    "width": monitor["width"],
                    "height": monitor["height"],
                    "is_primary": (i == 1)  # First real monitor is primary
                }
                self._screens.append(screen_info)

            print(f"Discovered {len(self._screens)} screens")
            for screen in self._screens:
                print(
                    f"Screen {screen['index']}: {screen['width']}x{screen['height']} "
                    f"at ({screen['x']}, {screen['y']}) {'(Primary)' if screen['is_primary'] else ''}"
                )

        except Exception as e:
            print(f"Failed to discover screens: {e}")
            raise

    async def capture_screen(
        self,
        monitor: int = 0,
        region: Optional[Dict[str, int]] = None,
        format: str = "png"
    ) -> Dict[str, Any]:
        """Capture screenshot of specified monitor or region."""
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
                ).model_dump()

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
                x, y, width, height = screen["x"], screen["y"], screen["width"], screen["height"]

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

            print(
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
            print(f"Screenshot capture failed: {e}")
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


# === Extracted Computer Vision Analyzer ===

class ComputerVisionAnalyzer:
    """Computer vision analyzer for UI element detection."""

    def __init__(self):
        """Initialize CV analyzer."""
        self._initialized = False

        # CV analysis parameters (exact from original)
        self.button_detection_params = {
            "min_area": 100,
            "max_area": 50000,
            "aspect_ratio_range": (0.2, 5.0),
            "roundness_threshold": 0.3
        }

        self.text_box_detection_params = {
            "min_area": 200,
            "max_area": 100000,
            "aspect_ratio_range": (2.0, 20.0),
            "fill_ratio_threshold": 0.1
        }

        print("ComputerVisionAnalyzer initialized")

    async def initialize(self) -> None:
        """Initialize CV analyzer asynchronously."""
        try:
            # Test OpenCV functionality
            test_img = np.zeros((100, 100, 3), dtype=np.uint8)
            _ = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)

            self._initialized = True
            print("ComputerVisionAnalyzer initialized successfully")

        except Exception as e:
            print(f"Failed to initialize ComputerVisionAnalyzer: {e}")
            raise

    def _preprocess_image(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Preprocess image for analysis."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Create binary image using adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        return image, gray, binary

    def _detect_buttons(self, image: np.ndarray, gray: np.ndarray) -> List[UIElement]:
        """Detect button-like elements in the image."""
        buttons = []

        try:
            # Edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                # Calculate contour properties
                area = cv2.contourArea(contour)
                if area < self.button_detection_params["min_area"] or area > self.button_detection_params["max_area"]:
                    continue

                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h

                # Check aspect ratio
                if not (self.button_detection_params["aspect_ratio_range"][0] <= aspect_ratio <= self.button_detection_params["aspect_ratio_range"][1]):
                    continue

                # Calculate roundness (how circular the contour is)
                perimeter = cv2.arcLength(contour, True)
                if perimeter == 0:
                    continue

                roundness = 4 * np.pi * area / (perimeter * perimeter)

                # Check if it looks like a button (rectangular or rounded)
                rect_area = w * h
                fill_ratio = area / rect_area if rect_area > 0 else 0

                if fill_ratio > 0.7 or roundness > self.button_detection_params["roundness_threshold"]:
                    # Calculate confidence based on properties
                    confidence = min(1.0, (fill_ratio + roundness) / 2)

                    button = UIElement(
                        type="button",
                        confidence=confidence,
                        bbox=(x, y, w, h),
                        center_x=x + w // 2,
                        center_y=y + h // 2,
                        area=int(area),
                        properties={
                            "aspect_ratio": aspect_ratio,
                            "fill_ratio": fill_ratio,
                            "roundness": roundness,
                            "perimeter": int(perimeter)
                        }
                    )
                    buttons.append(button)

        except Exception as e:
            print(f"Button detection failed: {e}")

        return buttons

    def _detect_text_boxes(self, image: np.ndarray, gray: np.ndarray, binary: np.ndarray) -> List[UIElement]:
        """Detect text box elements in the image."""
        text_boxes = []

        try:
            # Morphological operations to connect text regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

            # Find contours
            contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                # Calculate contour properties
                area = cv2.contourArea(contour)
                if area < self.text_box_detection_params["min_area"] or area > self.text_box_detection_params["max_area"]:
                    continue

                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h

                # Check aspect ratio (text boxes are usually wider than tall)
                if not (self.text_box_detection_params["aspect_ratio_range"][0] <= aspect_ratio <= self.text_box_detection_params["aspect_ratio_range"][1]):
                    continue

                # Check if it looks like a text box (low fill ratio indicates border/outline)
                rect_area = w * h
                fill_ratio = area / rect_area if rect_area > 0 else 0

                # Check for typical text box characteristics
                roi = binary[y:y+h, x:x+w]
                if roi.size == 0:
                    continue

                # Calculate the ratio of white to black pixels (text boxes often have white interiors)
                white_pixels = np.sum(roi == 255)
                total_pixels = roi.size
                white_ratio = white_pixels / total_pixels if total_pixels > 0 else 0

                # Text boxes typically have borders with white interiors
                if fill_ratio < self.text_box_detection_params["fill_ratio_threshold"] or white_ratio > 0.7:
                    confidence = min(1.0, white_ratio * 0.8 + (1 - fill_ratio) * 0.2)

                    text_box = UIElement(
                        type="textbox",
                        confidence=confidence,
                        bbox=(x, y, w, h),
                        center_x=x + w // 2,
                        center_y=y + h // 2,
                        area=int(area),
                        properties={
                            "aspect_ratio": aspect_ratio,
                            "fill_ratio": fill_ratio,
                            "white_ratio": white_ratio
                        }
                    )
                    text_boxes.append(text_box)

        except Exception as e:
            print(f"Text box detection failed: {e}")

        return text_boxes

    def _detect_images(self, image: np.ndarray, gray: np.ndarray) -> List[UIElement]:
        """Detect image elements in the image."""
        images = []

        try:
            # Use template matching or feature detection for images
            # For now, we'll use a simple approach based on texture analysis

            # Calculate texture using standard deviation in local regions
            kernel_size = 9
            kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)

            # Calculate local mean and standard deviation
            mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)
            sqr_mean = cv2.filter2D((gray.astype(np.float32) ** 2), -1, kernel)
            # Ensure non-negative values before sqrt to avoid RuntimeWarning
            variance = sqr_mean - mean ** 2
            variance = np.maximum(variance, 0)  # Clamp to non-negative values
            texture = np.sqrt(variance)

            # Threshold for high texture regions (likely images)
            texture_threshold = np.mean(texture) + np.std(texture)
            texture_binary = (texture > texture_threshold).astype(np.uint8) * 255

            # Find contours in texture regions
            contours, _ = cv2.findContours(texture_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 1000:  # Minimum area for images
                    continue

                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h

                # Images can have various aspect ratios
                if 0.1 <= aspect_ratio <= 10.0:
                    # Calculate confidence based on texture variance
                    roi_texture = texture[y:y+h, x:x+w]
                    texture_variance = np.var(roi_texture)
                    confidence = min(1.0, texture_variance / 1000.0)  # Normalize

                    image_element = UIElement(
                        type="image",
                        confidence=confidence,
                        bbox=(x, y, w, h),
                        center_x=x + w // 2,
                        center_y=y + h // 2,
                        area=int(area),
                        properties={
                            "aspect_ratio": aspect_ratio,
                            "texture_variance": float(texture_variance)
                        }
                    )
                    images.append(image_element)

        except Exception as e:
            print(f"Image detection failed: {e}")

        return images

    def _calculate_image_properties(self, image: np.ndarray) -> Dict[str, Any]:
        """Calculate general image properties."""
        properties = {}

        try:
            height, width = image.shape[:2]
            properties["width"] = width
            properties["height"] = height
            properties["channels"] = len(image.shape) if len(image.shape) > 2 else 1

            if len(image.shape) == 3:
                properties["channels"] = image.shape[2]

                # Calculate color statistics
                mean_color = np.mean(image, axis=(0, 1))
                properties["mean_color"] = mean_color.tolist()

                # Calculate brightness
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                properties["mean_brightness"] = float(np.mean(gray))
                properties["brightness_std"] = float(np.std(gray))
            else:
                properties["channels"] = 1
                properties["mean_brightness"] = float(np.mean(image))
                properties["brightness_std"] = float(np.std(image))

            # Calculate edge density (measure of complexity)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (width * height)
            properties["edge_density"] = float(edge_density)

        except Exception as e:
            print(f"Failed to calculate image properties: {e}")

        return properties

    async def analyze_image(
        self,
        image_data: bytes,
        detect_buttons: bool = True,
        detect_textboxes: bool = True,
        detect_images: bool = True
    ) -> Dict[str, Any]:
        """Analyze image for UI elements."""
        try:
            if not self._initialized:
                raise RuntimeError("CV analyzer not initialized")

            start_time = time.time()

            # Load image
            image = Image.open(io.BytesIO(image_data))
            image_array = np.array(image)

            # Convert color format for OpenCV
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                # RGB to BGR for OpenCV
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            elif len(image_array.shape) == 3 and image_array.shape[2] == 4:
                # RGBA to BGR for OpenCV
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2BGR)

            # Preprocess image
            original, gray, binary = self._preprocess_image(image_array)

            # Detect elements
            all_elements = []

            if detect_buttons:
                buttons = self._detect_buttons(original, gray)
                all_elements.extend(buttons)
                print(f"Detected {len(buttons)} button elements")

            if detect_textboxes:
                textboxes = self._detect_text_boxes(original, gray, binary)
                all_elements.extend(textboxes)
                print(f"Detected {len(textboxes)} text box elements")

            if detect_images:
                images = self._detect_images(original, gray)
                all_elements.extend(images)
                print(f"Detected {len(images)} image elements")

            # Calculate image properties
            image_properties = self._calculate_image_properties(original)

            processing_time = time.time() - start_time

            print(
                f"CV analysis completed: {len(all_elements)} elements detected "
                f"in {processing_time:.3f}s"
            )

            return CVAnalysisResult(
                success=True,
                timestamp=start_time,
                processing_time=processing_time,
                elements=all_elements,
                image_properties=image_properties,
                message=f"Successfully analyzed image and detected {len(all_elements)} elements"
            ).dict()

        except Exception as e:
            print(f"CV analysis failed: {e}")
            return CVAnalysisResult(
                success=False,
                timestamp=time.time(),
                processing_time=0.0,
                elements=[],
                image_properties={},
                message=f"CV analysis failed: {str(e)}"
            ).dict()


# === Standalone UI Detection Tool ===

class StandaloneUIDetector:
    """Standalone UI element detection tool."""

    def __init__(self):
        """Initialize the standalone UI detector."""
        self.screenshot_capture = ScreenshotCapture()
        self.cv_analyzer = ComputerVisionAnalyzer()
        print("StandaloneUIDetector initialized")

    async def initialize(self) -> None:
        """Initialize all components."""
        await self.screenshot_capture.initialize()
        await self.cv_analyzer.initialize()
        print("All components initialized successfully")

    async def analyze_current_screen(
        self,
        monitor: int = 0,
        save_screenshot: bool = False,
        output_file: str = "ui_analysis.json"
    ) -> Dict[str, Any]:
        """Analyze current screen for UI elements."""
        try:
            print(f"\n🔍 Analyzing screen {monitor}...")

            # Step 1: Capture screenshot
            screenshot_result = await self.screenshot_capture.capture_screen(monitor=monitor)

            if not screenshot_result["success"]:
                return {
                    "success": False,
                    "error": f"Screenshot capture failed: {screenshot_result['message']}"
                }

            # Step 2: Analyze UI elements
            try:
                # Add padding if needed to fix base64 decoding
                base64_data = screenshot_result["base64_data"]
                # Add padding if missing (base64 length should be multiple of 4)
                missing_padding = len(base64_data) % 4
                if missing_padding:
                    base64_data += '=' * (4 - missing_padding)

                image_data = base64.b64decode(base64_data)
                cv_result = await self.cv_analyzer.analyze_image(image_data)
            except Exception as decode_error:
                print(f"Base64 decode error: {decode_error}")
                # Try alternative: decode without validation
                try:
                    img_data = base64.b64decode(screenshot_result["base64_data"], validate=False)
                    cv_result = await self.cv_analyzer.analyze_image(img_data)
                except Exception as fallback_error:
                    print(f"Fallback decode error: {fallback_error}")
                    cv_result = {
                        "success": False,
                        "elements": [],
                        "image_properties": {},
                        "processing_time": 0.0,
                        "message": f"Image decode failed: {str(fallback_error)}"
                    }

            # Step 3: Combine results
            complete_analysis = {
                "screenshot": screenshot_result,
                "ui_analysis": cv_result,
                "summary": {
                    "total_elements": len(cv_result["elements"]) if cv_result["success"] else 0,
                    "buttons": len([e for e in cv_result["elements"] if e["type"] == "button"]) if cv_result["success"] else 0,
                    "textboxes": len([e for e in cv_result["elements"] if e["type"] == "textbox"]) if cv_result["success"] else 0,
                    "images": len([e for e in cv_result["elements"] if e["type"] == "image"]) if cv_result["success"] else 0,
                    "screen_size": f"{screenshot_result['width']}x{screenshot_result['height']}",
                    "processing_time": cv_result["processing_time"] if cv_result["success"] else 0
                }
            }

            # Step 4: Create annotated screenshot with bounding boxes
            if cv_result["success"] and cv_result["elements"]:
                self.draw_bounding_boxes(
                    screenshot_result,
                    cv_result["elements"],
                    f"annotated_screenshot_{monitor}.png"
                )

            # Step 5: Save results
            with open(output_file, 'w') as f:
                # Remove base64 data for file output to keep it manageable
                analysis_copy = complete_analysis.copy()
                if "base64_data" in analysis_copy["screenshot"]:
                    analysis_copy["screenshot"]["base64_data"] = "[BASE64_DATA_REMOVED_FOR_FILE_OUTPUT]"
                json.dump(analysis_copy, f, indent=2)

            # Step 6: Save original screenshot if requested
            if save_screenshot:
                try:
                    # Use same padding fix for screenshot saving
                    base64_data = screenshot_result["base64_data"]
                    missing_padding = len(base64_data) % 4
                    if missing_padding:
                        base64_data += '=' * (4 - missing_padding)

                    img_data = base64.b64decode(base64_data)
                    with open(f"screenshot_{monitor}.png", 'wb') as f:
                        f.write(img_data)
                    print(f"Screenshot saved to screenshot_{monitor}.png")
                except Exception as save_error:
                    print(f"Failed to save screenshot: {save_error}")

            print(f"Analysis results saved to {output_file}")
            return complete_analysis

        except Exception as e:
            print(f"Analysis failed: {e}")
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }

    def draw_bounding_boxes(
        self,
        screenshot_result: Dict[str, Any],
        elements: List[Dict[str, Any]],
        output_path: str = "annotated_screenshot.png"
    ) -> None:
        """Draw bounding boxes on screenshot to visualize detected UI elements."""
        try:
            # Decode screenshot
            base64_data = screenshot_result["base64_data"]
            missing_padding = len(base64_data) % 4
            if missing_padding:
                base64_data += '=' * (4 - missing_padding)

            img_data = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(img_data))

            # Create drawing context
            draw = ImageDraw.Draw(image)

            # Define colors for different element types
            colors = {
                "button": "#FF0000",      # Red
                "textbox": "#00FF00",     # Green
                "image": "#0000FF"       # Blue
            }

            # Try to load a font, fallback to default
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", 16)
                except:
                    font = ImageFont.load_default()

            # Draw bounding boxes and labels
            for i, element in enumerate(elements):
                elem_type = element["type"]
                bbox = element["bbox"]  # [x, y, width, height]
                confidence = element["confidence"]

                # Convert bbox to PIL format [x1, y1, x2, y2]
                x1, y1, width, height = bbox
                x2, y2 = x1 + width, y1 + height

                # Get color for element type
                color = colors.get(elem_type, "#FFFF00")  # Yellow fallback

                # Draw bounding box
                draw.rectangle([x1, y1, x2, y2], outline=color, width=2)

                # Draw label with type and confidence
                label = f"{elem_type} {confidence:.2f}"

                # Calculate text position (above the box if possible)
                text_y = max(0, y1 - 20)

                # Draw text background
                text_bbox = draw.textbbox((x1, text_y), label, font=font)
                draw.rectangle(text_bbox, fill=color, outline=color)

                # Draw text
                draw.text((x1, text_y), label, fill="white", font=font)

                # Draw center point
                center_x, center_y = element["center_x"], element["center_y"]
                draw.ellipse([center_x-3, center_y-3, center_x+3, center_y+3],
                           fill=color, outline="white")

            # Add legend
            legend_y = 10
            legend_x = image.width - 200

            draw.rectangle([legend_x-5, legend_y-5, image.width-5, legend_y+80],
                         fill="black", outline="white")

            legend_items = [
                ("🔴 Buttons", colors["button"]),
                ("🟢 Text Boxes", colors["textbox"]),
                ("🔵 Images", colors["image"])
            ]

            for i, (text, color) in enumerate(legend_items):
                y = legend_y + i * 25
                draw.text((legend_x, y), text, fill=color, font=font)

            # Save annotated image
            image.save(output_path)
            print(f"📊 Annotated screenshot saved to {output_path}")

        except Exception as e:
            print(f"Failed to draw bounding boxes: {e}")

    def display_results(self, analysis: Dict[str, Any]) -> None:
        """Display analysis results in a readable format."""
        if not analysis.get("success", True):
            print(f"❌ Analysis failed: {analysis.get('error', 'Unknown error')}")
            return

        summary = analysis["summary"]
        ui_analysis = analysis["ui_analysis"]

        print(f"\n📊 UI ELEMENT ANALYSIS RESULTS")
        print(f"=" * 50)
        print(f"Screen Size: {summary['screen_size']}")
        print(f"Processing Time: {summary['processing_time']:.3f}s")
        print(f"Total Elements: {summary['total_elements']}")
        print(f"  - Buttons: {summary['buttons']}")
        print(f"  - Text boxes: {summary['textboxes']}")
        print(f"  - Images: {summary['images']}")

        if ui_analysis["success"] and ui_analysis["elements"]:
            print(f"\n🔍 DETECTED ELEMENTS:")
            print(f"-" * 30)

            for i, element in enumerate(ui_analysis["elements"], 1):
                print(f"Element {i}:")
                print(f"  Type: {element['type']}")
                print(f"  Confidence: {element['confidence']:.3f}")
                print(f"  Location: ({element['center_x']}, {element['center_y']})")
                print(f"  Size: {element['bbox'][2]}x{element['bbox'][3]} px")
                print(f"  Area: {element['area']} px²")

                # Show type-specific properties
                if element['type'] == 'button':
                    props = element['properties']
                    print(f"  Roundness: {props.get('roundness', 0):.3f}")
                    print(f"  Fill Ratio: {props.get('fill_ratio', 0):.3f}")
                elif element['type'] == 'textbox':
                    props = element['properties']
                    print(f"  Aspect Ratio: {props.get('aspect_ratio', 0):.3f}")
                    print(f"  White Ratio: {props.get('white_ratio', 0):.3f}")
                elif element['type'] == 'image':
                    props = element['properties']
                    print(f"  Texture Variance: {props.get('texture_variance', 0):.1f}")

                print()

        # Show what would be passed to LLM
        print(f"\n🤖 LLM INPUT FORMAT:")
        print(f"-" * 30)
        llm_input = {
            "screen_info": {
                "width": analysis["screenshot"]["width"],
                "height": analysis["screenshot"]["height"],
                "timestamp": ui_analysis["timestamp"]
            },
            "detected_elements": [
                {
                    "type": elem["type"],
                    "confidence": elem["confidence"],
                    "center_position": {"x": elem["center_x"], "y": elem["center_y"]},
                    "bounding_box": {"x": elem["bbox"][0], "y": elem["bbox"][1],
                                   "width": elem["bbox"][2], "height": elem["bbox"][3]},
                    "properties": elem["properties"]
                }
                for elem in ui_analysis["elements"]
            ],
            "image_properties": ui_analysis["image_properties"]
        }

        print(json.dumps(llm_input, indent=2))


async def main():
    """Main function to demonstrate the UI detection tool."""
    print("🚀 Standalone UI Element Detection Tool")
    print("=" * 50)
    print("This tool demonstrates the exact UI element detection")
    print("output that would be passed to an LLM in the MCP system.")
    print()

    # Initialize detector
    detector = StandaloneUIDetector()
    await detector.initialize()

    try:
        # Analyze current screen
        analysis = await detector.analyze_current_screen(
            monitor=0,
            save_screenshot=True,
            output_file="ui_analysis_output.json"
        )

        # Display results
        detector.display_results(analysis)

        print(f"\n✅ Analysis complete!")
        print(f"   - Full results saved to: ui_analysis_output.json")
        print(f"   - Original screenshot saved to: screenshot_0.png")
        print(f"   - Annotated screenshot with bounding boxes saved!")
        print(f"\n🎯 Visual Output:")
        print(f"   - 🔴 Red boxes = Buttons")
        print(f"   - 🟢 Green boxes = Text boxes")
        print(f"   - 🔵 Blue boxes = Images")
        print(f"   - Each box shows type + confidence score")
        print(f"   - White dots = center click points")
        print(f"\nThis shows exactly what UI elements are detected and")
        print(f"what data would be passed to the LLM for automation.")

    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())