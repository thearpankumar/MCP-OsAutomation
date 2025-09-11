"""
Computer Vision analyzer using OpenCV for UI element detection and analysis.
"""

import asyncio
import base64
import io
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
from loguru import logger
from pydantic import BaseModel

from ..utils.config import Config


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


class ComputerVisionAnalyzer:
    """Computer vision analyzer for UI element detection."""
    
    def __init__(self, config: Config):
        """Initialize CV analyzer.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self._initialized = False
        
        # CV analysis parameters
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
        
        logger.info("ComputerVisionAnalyzer initialized")
    
    async def initialize(self) -> None:
        """Initialize CV analyzer asynchronously."""
        try:
            # Test OpenCV functionality
            test_img = np.zeros((100, 100, 3), dtype=np.uint8)
            _ = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
            
            self._initialized = True
            logger.info("ComputerVisionAnalyzer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ComputerVisionAnalyzer: {e}")
            raise
    
    def _preprocess_image(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Preprocess image for analysis.
        
        Args:
            image: Input image
            
        Returns:
            Tuple of (original, grayscale, binary)
        """
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
        """Detect button-like elements in the image.
        
        Args:
            image: Original image
            gray: Grayscale image
            
        Returns:
            List of detected button elements
        """
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
            logger.error(f"Button detection failed: {e}")
        
        return buttons
    
    def _detect_text_boxes(self, image: np.ndarray, gray: np.ndarray, binary: np.ndarray) -> List[UIElement]:
        """Detect text box elements in the image.
        
        Args:
            image: Original image
            gray: Grayscale image
            binary: Binary image
            
        Returns:
            List of detected text box elements
        """
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
            logger.error(f"Text box detection failed: {e}")
        
        return text_boxes
    
    def _detect_images(self, image: np.ndarray, gray: np.ndarray) -> List[UIElement]:
        """Detect image elements in the image.
        
        Args:
            image: Original image
            gray: Grayscale image
            
        Returns:
            List of detected image elements
        """
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
            logger.error(f"Image detection failed: {e}")
        
        return images
    
    def _calculate_image_properties(self, image: np.ndarray) -> Dict[str, Any]:
        """Calculate general image properties.
        
        Args:
            image: Input image
            
        Returns:
            Dictionary of image properties
        """
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
            logger.error(f"Failed to calculate image properties: {e}")
        
        return properties
    
    async def analyze_image(
        self,
        image_data: bytes,
        detect_buttons: bool = True,
        detect_textboxes: bool = True,
        detect_images: bool = True
    ) -> Dict[str, Any]:
        """Analyze image for UI elements.
        
        Args:
            image_data: Image data as bytes
            detect_buttons: Whether to detect button elements
            detect_textboxes: Whether to detect text box elements
            detect_images: Whether to detect image elements
            
        Returns:
            Analysis result with detected elements
        """
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
                logger.debug(f"Detected {len(buttons)} button elements")
            
            if detect_textboxes:
                textboxes = self._detect_text_boxes(original, gray, binary)
                all_elements.extend(textboxes)
                logger.debug(f"Detected {len(textboxes)} text box elements")
            
            if detect_images:
                images = self._detect_images(original, gray)
                all_elements.extend(images)
                logger.debug(f"Detected {len(images)} image elements")
            
            # Calculate image properties
            image_properties = self._calculate_image_properties(original)
            
            processing_time = time.time() - start_time
            
            logger.info(
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
            logger.error(f"CV analysis failed: {e}")
            return CVAnalysisResult(
                success=False,
                timestamp=time.time(),
                processing_time=0.0,
                elements=[],
                image_properties={},
                message=f"CV analysis failed: {str(e)}"
            ).dict()
    
    async def find_elements_by_type(
        self,
        image_data: bytes,
        element_type: str
    ) -> Dict[str, Any]:
        """Find elements of specific type in image.
        
        Args:
            image_data: Image data as bytes
            element_type: Type of element to find (button, textbox, image)
            
        Returns:
            Analysis result filtered by element type
        """
        # Determine which detection to run
        detect_buttons = element_type == "button"
        detect_textboxes = element_type == "textbox"
        detect_images = element_type == "image"
        
        result = await self.analyze_image(
            image_data,
            detect_buttons=detect_buttons,
            detect_textboxes=detect_textboxes,
            detect_images=detect_images
        )
        
        if result["success"]:
            filtered_elements = [
                elem for elem in result["elements"] 
                if elem["type"] == element_type
            ]
            result["elements"] = filtered_elements
            result["message"] = f"Found {len(filtered_elements)} {element_type} elements"
        
        return result
    
    async def cleanup(self) -> None:
        """Cleanup CV analyzer resources."""
        try:
            self._initialized = False
            logger.info("ComputerVisionAnalyzer cleaned up")
        except Exception as e:
            logger.error(f"CV analyzer cleanup failed: {e}")