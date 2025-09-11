"""
Main screen analyzer that combines screenshot capture, OCR, and computer vision.
"""

import asyncio
import base64
import time
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel

from .cv_analyzer import ComputerVisionAnalyzer
from .screenshot import ScreenshotCapture
from ..utils.config import Config

# Import OCR engine - now only LLM-based OCR
from .llm_ocr_engine import LLMOCREngine as OCREngine


class ScreenAnalysis(BaseModel):
    """Complete screen analysis result."""
    
    success: bool
    timestamp: float
    processing_time: float
    screenshot: Dict[str, Any]
    ocr_result: Optional[Dict[str, Any]] = None
    cv_result: Optional[Dict[str, Any]] = None
    screen_context: Dict[str, Any]
    message: str


class ScreenAnalyzer:
    """Main screen analyzer combining all intelligence components."""
    
    def __init__(self, config: Config):
        """Initialize screen analyzer.
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # Initialize components
        self.screenshot_capture = ScreenshotCapture(config)
        self.ocr_engine = OCREngine(config)
        self.cv_analyzer = ComputerVisionAnalyzer(config)
        
        self._initialized = False
        
        logger.info("ScreenAnalyzer initialized")
    
    async def initialize(self) -> None:
        """Initialize all screen analyzer components."""
        try:
            # Initialize all components in parallel
            await asyncio.gather(
                self.screenshot_capture.initialize(),
                self.ocr_engine.initialize(),
                self.cv_analyzer.initialize()
            )
            
            self._initialized = True
            logger.info("ScreenAnalyzer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ScreenAnalyzer: {e}")
            raise
    
    async def capture_screen(
        self,
        monitor: int = 0,
        region: Optional[Dict[str, int]] = None,
        format: str = "png"
    ) -> Dict[str, Any]:
        """Capture screenshot using the screenshot capture system.
        
        Args:
            monitor: Monitor number (0 for primary)
            region: Optional region dict with x, y, width, height
            format: Image format (png, jpeg, webp)
            
        Returns:
            Screenshot data and metadata
        """
        if not self._initialized:
            raise RuntimeError("ScreenAnalyzer not initialized")
        
        return await self.screenshot_capture.capture_screen(monitor, region, format)
    
    async def analyze_screen(
        self,
        include_ocr: bool = True,
        include_elements: bool = True,
        region: Optional[Dict[str, int]] = None,
        monitor: int = 0
    ) -> Dict[str, Any]:
        """Perform comprehensive screen analysis.
        
        Args:
            include_ocr: Whether to include OCR text extraction
            include_elements: Whether to include UI element detection
            region: Optional region to analyze
            monitor: Monitor to capture
            
        Returns:
            Complete screen analysis
        """
        try:
            if not self._initialized:
                raise RuntimeError("ScreenAnalyzer not initialized")
            
            start_time = time.time()
            
            # Step 1: Capture screenshot
            screenshot_result = await self.screenshot_capture.capture_screen(
                monitor=monitor,
                region=region,
                format="png"
            )
            
            if not screenshot_result["success"]:
                return ScreenAnalysis(
                    success=False,
                    timestamp=start_time,
                    processing_time=time.time() - start_time,
                    screenshot=screenshot_result,
                    screen_context={},
                    message="Failed to capture screenshot"
                ).dict()
            
            # Get image data for analysis
            image_data = base64.b64decode(screenshot_result["base64_data"])
            
            # Step 2: Run OCR and CV analysis in parallel if requested
            analysis_tasks = []
            ocr_result = None
            cv_result = None
            
            if include_ocr:
                analysis_tasks.append(self.ocr_engine.extract_text_from_image(image_data))
            
            if include_elements:
                analysis_tasks.append(self.cv_analyzer.analyze_image(image_data))
            
            # Execute analysis tasks
            if analysis_tasks:
                results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
                
                result_idx = 0
                if include_ocr:
                    ocr_result = results[result_idx] if not isinstance(results[result_idx], Exception) else None
                    result_idx += 1
                
                if include_elements:
                    cv_result = results[result_idx] if not isinstance(results[result_idx], Exception) else None
            
            # Step 3: Generate screen context
            screen_context = await self._generate_screen_context(
                screenshot_result, ocr_result, cv_result
            )
            
            processing_time = time.time() - start_time
            
            logger.info(
                f"Screen analysis completed in {processing_time:.3f}s: "
                f"OCR={'✓' if ocr_result and ocr_result.get('success') else '✗'}, "
                f"CV={'✓' if cv_result and cv_result.get('success') else '✗'}"
            )
            
            return ScreenAnalysis(
                success=True,
                timestamp=start_time,
                processing_time=processing_time,
                screenshot=screenshot_result,
                ocr_result=ocr_result,
                cv_result=cv_result,
                screen_context=screen_context,
                message=f"Screen analysis completed successfully in {processing_time:.3f}s"
            ).dict()
            
        except Exception as e:
            logger.error(f"Screen analysis failed: {e}")
            return ScreenAnalysis(
                success=False,
                timestamp=time.time(),
                processing_time=0.0,
                screenshot={},
                screen_context={},
                message=f"Screen analysis failed: {str(e)}"
            ).dict()
    
    async def find_text(
        self,
        text: str,
        confidence: float = 0.8,
        region: Optional[Dict[str, int]] = None,
        monitor: int = 0
    ) -> Dict[str, Any]:
        """Find specific text on screen.
        
        Args:
            text: Text to find
            confidence: Minimum confidence threshold
            region: Optional region to search in
            monitor: Monitor to search on
            
        Returns:
            Text search results
        """
        try:
            if not self._initialized:
                raise RuntimeError("ScreenAnalyzer not initialized")
            
            # Capture screenshot
            screenshot_result = await self.capture_screen(monitor=monitor, region=region)
            
            if not screenshot_result["success"]:
                return {
                    "success": False,
                    "text": text,
                    "matches": [],
                    "message": "Failed to capture screenshot"
                }
            
            # Extract image data
            image_data = base64.b64decode(screenshot_result["base64_data"])
            
            # Search for text using OCR
            search_result = await self.ocr_engine.find_text_in_image(
                image_data, text, confidence_threshold=confidence
            )
            
            if search_result["success"]:
                matches = []
                for detection in search_result["text_detections"]:
                    matches.append({
                        "text": detection["text"],
                        "confidence": detection["confidence"],
                        "center_x": detection["center_x"],
                        "center_y": detection["center_y"],
                        "bbox": detection["bbox"]
                    })
                
                return {
                    "success": True,
                    "text": text,
                    "matches": matches,
                    "screenshot": screenshot_result,
                    "message": f"Found {len(matches)} matches for '{text}'"
                }
            else:
                return {
                    "success": False,
                    "text": text,
                    "matches": [],
                    "message": search_result.get("message", "Text search failed")
                }
            
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return {
                "success": False,
                "text": text,
                "matches": [],
                "message": f"Text search failed: {str(e)}"
            }
    
    async def detect_ui_elements(
        self,
        element_type: Optional[str] = None,
        region: Optional[Dict[str, int]] = None,
        monitor: int = 0
    ) -> Dict[str, Any]:
        """Detect UI elements on screen.
        
        Args:
            element_type: Optional element type filter (button, textbox, image)
            region: Optional region to analyze
            monitor: Monitor to analyze
            
        Returns:
            UI element detection results
        """
        try:
            if not self._initialized:
                raise RuntimeError("ScreenAnalyzer not initialized")
            
            # Capture screenshot
            screenshot_result = await self.capture_screen(monitor=monitor, region=region)
            
            if not screenshot_result["success"]:
                return {
                    "success": False,
                    "elements": [],
                    "message": "Failed to capture screenshot"
                }
            
            # Extract image data
            image_data = base64.b64decode(screenshot_result["base64_data"])
            
            # Detect elements
            if element_type:
                cv_result = await self.cv_analyzer.find_elements_by_type(image_data, element_type)
            else:
                cv_result = await self.cv_analyzer.analyze_image(image_data)
            
            if cv_result["success"]:
                return {
                    "success": True,
                    "elements": cv_result["elements"],
                    "screenshot": screenshot_result,
                    "message": f"Detected {len(cv_result['elements'])} UI elements"
                }
            else:
                return {
                    "success": False,
                    "elements": [],
                    "message": cv_result.get("message", "Element detection failed")
                }
            
        except Exception as e:
            logger.error(f"UI element detection failed: {e}")
            return {
                "success": False,
                "elements": [],
                "message": f"UI element detection failed: {str(e)}"
            }
    
    async def get_screen_context(
        self,
        monitor: int = 0,
        include_screenshot: bool = False
    ) -> Dict[str, Any]:
        """Get comprehensive screen context for AI analysis.
        
        Args:
            monitor: Monitor to analyze
            include_screenshot: Whether to include screenshot data
            
        Returns:
            Screen context summary
        """
        try:
            # Perform full screen analysis
            analysis = await self.analyze_screen(
                include_ocr=True,
                include_elements=True,
                monitor=monitor
            )
            
            if not analysis["success"]:
                return {
                    "success": False,
                    "context": {},
                    "message": "Failed to analyze screen"
                }
            
            # Build context summary
            context = {
                "screen_info": {
                    "width": analysis["screenshot"]["width"],
                    "height": analysis["screenshot"]["height"],
                    "monitor": monitor,
                    "timestamp": analysis["timestamp"]
                },
                "text_content": {
                    "full_text": analysis["ocr_result"]["full_text"] if analysis["ocr_result"] else "",
                    "word_count": analysis["ocr_result"]["word_count"] if analysis["ocr_result"] else 0,
                    "confidence": analysis["ocr_result"]["confidence_avg"] if analysis["ocr_result"] else 0.0
                },
                "ui_elements": {
                    "total_count": len(analysis["cv_result"]["elements"]) if analysis["cv_result"] else 0,
                    "buttons": len([e for e in analysis["cv_result"]["elements"] if e["type"] == "button"]) if analysis["cv_result"] else 0,
                    "textboxes": len([e for e in analysis["cv_result"]["elements"] if e["type"] == "textbox"]) if analysis["cv_result"] else 0,
                    "images": len([e for e in analysis["cv_result"]["elements"] if e["type"] == "image"]) if analysis["cv_result"] else 0
                },
                "analysis_summary": analysis["screen_context"]
            }
            
            # Include screenshot if requested
            if include_screenshot:
                context["screenshot"] = analysis["screenshot"]
            
            return {
                "success": True,
                "context": context,
                "message": f"Screen context generated successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to get screen context: {e}")
            return {
                "success": False,
                "context": {},
                "message": f"Failed to get screen context: {str(e)}"
            }
    
    async def _generate_screen_context(
        self,
        screenshot: Dict[str, Any],
        ocr_result: Optional[Dict[str, Any]],
        cv_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate screen context summary from analysis results.
        
        Args:
            screenshot: Screenshot data
            ocr_result: OCR analysis result
            cv_result: Computer vision analysis result
            
        Returns:
            Screen context summary
        """
        context = {
            "screen_dimensions": f"{screenshot['width']}x{screenshot['height']}",
            "capture_info": {
                "monitor": screenshot["monitor"],
                "format": screenshot["format"],
                "size_bytes": screenshot["size_bytes"]
            }
        }
        
        # Add OCR context
        if ocr_result and ocr_result.get("success"):
            context["text_analysis"] = {
                "has_text": len(ocr_result["text_detections"]) > 0,
                "text_regions": len(ocr_result["text_detections"]),
                "total_words": ocr_result["word_count"],
                "avg_confidence": ocr_result["confidence_avg"],
                "sample_text": ocr_result["full_text"][:200] + "..." if len(ocr_result["full_text"]) > 200 else ocr_result["full_text"]
            }
        
        # Add CV context
        if cv_result and cv_result.get("success"):
            elements_by_type = {}
            for element in cv_result["elements"]:
                elem_type = element["type"]
                if elem_type not in elements_by_type:
                    elements_by_type[elem_type] = []
                elements_by_type[elem_type].append({
                    "confidence": element["confidence"],
                    "center": [element["center_x"], element["center_y"]],
                    "size": [element["bbox"][2], element["bbox"][3]]  # width, height
                })
            
            context["ui_analysis"] = {
                "has_ui_elements": len(cv_result["elements"]) > 0,
                "total_elements": len(cv_result["elements"]),
                "elements_by_type": elements_by_type,
                "image_properties": cv_result.get("image_properties", {})
            }
        
        # Generate summary description
        summary_parts = []
        
        if screenshot["width"] > 0 and screenshot["height"] > 0:
            summary_parts.append(f"Screen resolution: {screenshot['width']}x{screenshot['height']}")
        
        if context.get("text_analysis", {}).get("has_text"):
            summary_parts.append(f"Contains {context['text_analysis']['text_regions']} text regions with {context['text_analysis']['total_words']} words")
        
        if context.get("ui_analysis", {}).get("has_ui_elements"):
            ui_summary = []
            for elem_type, elements in context["ui_analysis"]["elements_by_type"].items():
                ui_summary.append(f"{len(elements)} {elem_type}(s)")
            summary_parts.append(f"UI elements: {', '.join(ui_summary)}")
        
        context["summary"] = "; ".join(summary_parts) if summary_parts else "Basic screen capture completed"
        
        return context
    
    async def cleanup(self) -> None:
        """Cleanup all screen analyzer components."""
        logger.info("Cleaning up ScreenAnalyzer...")
        
        # Cleanup all components in parallel
        await asyncio.gather(
            self.screenshot_capture.cleanup(),
            self.ocr_engine.cleanup(),
            self.cv_analyzer.cleanup(),
            return_exceptions=True
        )
        
        self._initialized = False
        logger.info("ScreenAnalyzer cleaned up successfully")