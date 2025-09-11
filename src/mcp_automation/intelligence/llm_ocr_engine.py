"""
LLM-based OCR Engine using Claude, Gemini, and OpenAI vision models.

This replaces PaddleOCR with modern LLM vision capabilities for better accuracy
and no dependency management issues.
"""

import asyncio
import base64
import json
import io
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

import aiohttp
from PIL import Image
from loguru import logger
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logger.warning("python-dotenv not available. Install with: pip install python-dotenv")

from ..utils.config import Config


class LLMProvider(str, Enum):
    """Supported LLM providers for OCR."""
    CLAUDE = "claude"
    GEMINI = "gemini" 
    OPENAI = "openai"


class TextDetection(BaseModel):
    """Single text detection result."""
    
    text: str
    confidence: float
    bbox: List[List[float]]  # 4 points: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    center_x: float
    center_y: float
    width: float
    height: float


class OCRResult(BaseModel):
    """OCR analysis result."""
    
    success: bool
    timestamp: float
    processing_time: float
    text_detections: List[TextDetection]
    full_text: str
    word_count: int
    confidence_avg: float
    message: str
    provider_used: Optional[str] = None


class LLMOCREngine:
    """LLM-based OCR engine using Claude, Gemini, and OpenAI vision models."""
    
    def __init__(self, config: Config):
        """Initialize LLM OCR engine.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self._is_initialized = False
        
        # Load environment variables from .env file
        self._load_dotenv()
        
        # API credentials from environment variables
        self.claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Provider preference order (fallback chain)
        self.provider_chain = [
            LLMProvider.CLAUDE,
            LLMProvider.GEMINI,
            LLMProvider.OPENAI
        ]
        
        # API endpoints
        self.api_endpoints = {
            LLMProvider.CLAUDE: "https://api.anthropic.com/v1/messages",
            LLMProvider.GEMINI: "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            LLMProvider.OPENAI: "https://api.openai.com/v1/chat/completions"
        }
        
        # Model configurations
        self.models = {
            LLMProvider.CLAUDE: "claude-3-5-sonnet-20241022",
            LLMProvider.GEMINI: "gemini-2.5-flash",
            LLMProvider.OPENAI: "gpt-4o-mini"
        }
        
        logger.info("LLM OCR Engine initialized")
    
    def _load_dotenv(self) -> None:
        """Load environment variables from .env file."""
        if not DOTENV_AVAILABLE:
            return
        
        # Look for .env file in current directory and parent directories
        current_dir = Path.cwd()
        env_locations = [
            current_dir / ".env",
            current_dir.parent / ".env",
            current_dir.parent.parent / ".env",  # For when running from examples/
            Path(__file__).parent.parent.parent.parent / ".env"  # Project root
        ]
        
        for env_file in env_locations:
            if env_file.exists():
                load_dotenv(env_file)
                logger.info(f"Loaded environment variables from {env_file}")
                return
        
        # Try to load from default location
        load_dotenv()
        logger.debug("Attempted to load .env from current directory")
    
    async def initialize(self) -> None:
        """Initialize LLM OCR engine asynchronously."""
        if self._is_initialized:
            return
            
        try:
            # Check available providers
            available_providers = []
            
            if self.claude_api_key:
                available_providers.append(LLMProvider.CLAUDE)
                logger.info("Claude API key found - Claude OCR available")
            
            if self.gemini_api_key:
                available_providers.append(LLMProvider.GEMINI)
                logger.info("Gemini API key found - Gemini OCR available")
            
            if self.openai_api_key:
                available_providers.append(LLMProvider.OPENAI)
                logger.info("OpenAI API key found - OpenAI Vision OCR available")
            
            if not available_providers:
                logger.warning("No LLM API keys found. LLM OCR will run in demo mode.")
                logger.info("To enable full LLM OCR, set one or more API keys:")
                logger.info("  export ANTHROPIC_API_KEY='your-claude-key'")
                logger.info("  export GEMINI_API_KEY='your-gemini-key'")
                logger.info("  export OPENAI_API_KEY='your-openai-key'")
                # Continue in demo mode rather than raising an error
            
            # Filter provider chain to only available providers
            self.provider_chain = [p for p in self.provider_chain if p in available_providers]
            
            logger.info(f"LLM OCR providers available: {[p.value for p in available_providers]}")
            logger.info(f"Provider fallback chain: {[p.value for p in self.provider_chain]}")
            
            self._is_initialized = True
            logger.info("LLM OCR Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM OCR Engine: {e}")
            raise
    
    def _prepare_image_data(self, image_data: bytes) -> str:
        """Prepare image data as base64 string.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Base64 encoded image string
        """
        return base64.b64encode(image_data).decode('utf-8')
    
    def _create_ocr_prompt(self, detailed: bool = False) -> str:
        """Create OCR prompt for LLM.
        
        Args:
            detailed: Whether to request detailed text location information
            
        Returns:
            OCR prompt string
        """
        if detailed:
            return """
Please perform OCR on this image and extract all visible text. 

Provide the response as JSON with this exact structure:
{
  "texts": [
    {
      "text": "extracted text here",
      "confidence": 0.95,
      "region": "description of location (e.g., 'top-left', 'center', 'bottom-right')"
    }
  ],
  "full_text": "all extracted text joined together",
  "summary": "brief description of what kind of document/content this appears to be"
}

Rules:
1. Extract ALL visible text, including small text, watermarks, and UI elements
2. Maintain text order (top to bottom, left to right)
3. Assign confidence scores (0.0-1.0) - be realistic, use 0.95+ for very clear text
4. Include region descriptions to help locate text
5. Preserve formatting and line breaks where meaningful
6. If no text is found, return empty texts array
"""
        else:
            return """
Please perform OCR on this image and extract all visible text.

Simply provide all the text you can see in the image, maintaining the natural reading order (top to bottom, left to right). If there's no text visible, respond with "NO TEXT FOUND".
"""
    
    async def _call_claude_api(self, image_base64: str, prompt: str) -> Dict[str, Any]:
        """Call Claude API for OCR.
        
        Args:
            image_base64: Base64 encoded image
            prompt: OCR prompt
            
        Returns:
            API response
        """
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.claude_api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # Detect image format from base64 data
        try:
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes))
            image_format = image.format.lower() if image.format else "png"
        except:
            image_format = "png"  # Default fallback
        
        payload = {
            "model": self.models[LLMProvider.CLAUDE],
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": f"image/{image_format}",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text", 
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_endpoints[LLMProvider.CLAUDE],
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "content": result["content"][0]["text"],
                        "provider": "claude"
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Claude API error {response.status}: {error_text}")
                    return {"success": False, "error": f"Claude API error: {response.status}"}
    
    async def _call_gemini_api(self, image_base64: str, prompt: str) -> Dict[str, Any]:
        """Call Gemini API for OCR.
        
        Args:
            image_base64: Base64 encoded image
            prompt: OCR prompt
            
        Returns:
            API response
        """
        try:
            # Detect image format
            try:
                image_bytes = base64.b64decode(image_base64)
                image = Image.open(io.BytesIO(image_bytes))
                mime_type = f"image/{image.format.lower()}" if image.format else "image/png"
            except Exception as e:
                logger.warning(f"Could not detect image format: {e}, defaulting to PNG")
                mime_type = "image/png"
            
            # Updated payload structure for Gemini 2.5 Flash
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_base64
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 4096
                }
            }
            
            url = f"{self.api_endpoints[LLMProvider.GEMINI]}?key={self.gemini_api_key}"
            
            # Use stderr for Gemini debug logs to avoid MCP stdout contamination
            import sys
            print(f"DEBUG: Calling Gemini API: {url}", file=sys.stderr)
            print(f"DEBUG: Payload structure: contents with {len(payload['contents'][0]['parts'])} parts", file=sys.stderr)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_text = await response.text()
                    print(f"DEBUG: Gemini API response status: {response.status}", file=sys.stderr)
                    
                    if response.status == 200:
                        try:
                            # Log raw response for debugging
                            print(f"DEBUG: Gemini raw response (first 200 chars): {response_text[:200]}...", file=sys.stderr)
                            
                            # Find the first valid JSON object in the response
                            cleaned_response = response_text.strip()
                            
                            # Look for the start of JSON (opening brace)
                            json_start = cleaned_response.find('{')
                            if json_start == -1:
                                raise json.JSONDecodeError("No JSON object found in response", cleaned_response, 0)
                            
                            # Extract from the first { to the end, let json.loads handle validation
                            json_part = cleaned_response[json_start:]
                            
                            # Try to find matching closing brace
                            brace_count = 0
                            json_end = -1
                            for i, char in enumerate(json_part):
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_end = i + 1
                                        break
                            
                            if json_end > 0:
                                cleaned_response = json_part[:json_end]
                            else:
                                cleaned_response = json_part
                            
                            print(f"DEBUG: Cleaned JSON: {cleaned_response[:200]}...", file=sys.stderr)
                            
                            # Parse JSON
                            result = json.loads(cleaned_response)
                            logger.debug(f"Gemini API response structure: {list(result.keys())}")
                            
                            if "candidates" in result and result["candidates"]:
                                candidate = result["candidates"][0]
                                if "content" in candidate and "parts" in candidate["content"]:
                                    content = candidate["content"]["parts"][0]["text"]
                                    return {
                                        "success": True,
                                        "content": content,
                                        "provider": "gemini"
                                    }
                                else:
                                    logger.error(f"Unexpected Gemini response structure: {result}")
                                    return {"success": False, "error": f"Unexpected response structure: {result}"}
                            else:
                                logger.error(f"No candidates in Gemini response: {result}")
                                return {"success": False, "error": f"No response from Gemini: {result}"}
                                
                        except json.JSONDecodeError as json_error:
                            print(f"ERROR: Gemini JSON decode error: {json_error}", file=sys.stderr)
                            print(f"ERROR: Raw response (first 500 chars): {response_text[:500]}", file=sys.stderr)
                            
                            # Log each character at position 4 and nearby for debugging
                            if len(response_text) > 10:
                                print(f"DEBUG: Characters around position 4:", file=sys.stderr)
                                for i in range(max(0, 4-5), min(len(response_text), 4+5)):
                                    char = response_text[i]
                                    print(f"  pos {i}: '{char}' (ord: {ord(char)})", file=sys.stderr)
                            
                            # If JSON parsing fails, try to extract text directly from response
                            # Sometimes Gemini returns plain text instead of JSON
                            if response_text and len(response_text.strip()) > 0:
                                logger.info("Attempting to use raw response as OCR text")
                                return {
                                    "success": True,
                                    "content": response_text.strip(),
                                    "provider": "gemini"
                                }
                            else:
                                return {"success": False, "error": f"Invalid JSON response: {json_error}"}
                                
                        except Exception as other_error:
                            logger.error(f"Other error parsing Gemini response: {other_error}")
                            logger.error(f"Raw response: {response_text}")
                            return {"success": False, "error": f"Response parsing error: {other_error}"}
                    else:
                        logger.error(f"Gemini API error {response.status}: {response_text}")
                        return {"success": False, "error": f"Gemini API error {response.status}: {response_text}"}
                        
        except Exception as e:
            logger.error(f"Exception in Gemini API call: {e}")
            return {"success": False, "error": f"Gemini API exception: {str(e)}"}
    
    async def _call_openai_api(self, image_base64: str, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API for OCR with retry logic.
        
        Args:
            image_base64: Base64 encoded image
            prompt: OCR prompt
            
        Returns:
            API response
        """
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Validate API key
                if not self.openai_api_key or self.openai_api_key.strip() == "":
                    return {"success": False, "error": "OpenAI API key not provided"}
                
                # Validate and process image
                try:
                    image_bytes = base64.b64decode(image_base64)
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # Optimize image size for OpenAI (only resize if extremely large)
                    max_dimension = 4096  # Increased to preserve text quality
                    if image.width > max_dimension or image.height > max_dimension:
                        # Calculate new size maintaining aspect ratio
                        ratio = min(max_dimension / image.width, max_dimension / image.height)
                        new_size = (int(image.width * ratio), int(image.height * ratio))
                        image = image.resize(new_size, Image.Resampling.LANCZOS)
                        logger.info(f"Resized image to {new_size} for OpenAI")
                    
                    # Use PNG for better text quality, only convert to JPEG if too large
                    img_buffer = io.BytesIO()
                    image.save(img_buffer, format="PNG", optimize=True)
                    optimized_bytes = img_buffer.getvalue()
                    image_format = "png"
                    
                    # If PNG is too large, then use high-quality JPEG
                    max_size = 20 * 1024 * 1024  # 20MB limit
                    if len(optimized_bytes) > max_size:
                        img_buffer = io.BytesIO()
                        if image.mode in ('RGBA', 'LA', 'P'):
                            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                            rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                            image = rgb_image
                        image.save(img_buffer, format="JPEG", quality=95, optimize=True)
                        optimized_bytes = img_buffer.getvalue()
                        image_format = "jpeg"
                    
                    image_base64 = base64.b64encode(optimized_bytes).decode('utf-8')
                        
                except Exception as e:
                    return {"success": False, "error": f"Image processing failed: {str(e)}"}
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_api_key}"
                }
                
                payload = {
                    "model": self.models[LLMProvider.OPENAI],
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Extract ALL visible text from this image. Include every word, number, symbol, button text, menu items, labels, and any other readable text. Format as JSON with text and coordinates."},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/{image_format};base64,{image_base64}",
                                        "detail": "high"  # Use high detail for complete text extraction
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 4096,  # Increased for more text
                    "temperature": 0.0   # Deterministic for OCR
                }
                
                # Shorter timeout for faster failure
                timeout = aiohttp.ClientTimeout(total=30, connect=5, sock_read=20)
                connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
                
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                        async with session.post(
                            self.api_endpoints[LLMProvider.OPENAI],
                            headers=headers,
                            json=payload
                        ) as response:
                            response_text = await response.text()
                            
                            if response.status == 200:
                                try:
                                    result = json.loads(response_text)
                                    if "choices" in result and len(result["choices"]) > 0:
                                        content = result["choices"][0]["message"]["content"]
                                        return {
                                            "success": True,
                                            "content": content,
                                            "provider": "openai"
                                        }
                                    else:
                                        return {"success": False, "error": f"Unexpected response structure: {result}"}
                                except json.JSONDecodeError as e:
                                    logger.error(f"OpenAI JSON decode error: {e}")
                                    return {"success": False, "error": f"Invalid JSON response: {e}"}
                            else:
                                logger.error(f"OpenAI API error {response.status}: {response_text}")
                                # Parse error details if available
                                try:
                                    error_data = json.loads(response_text)
                                    error_message = error_data.get("error", {}).get("message", response_text)
                                except:
                                    error_message = response_text
                                
                                return {"success": False, "error": f"OpenAI API error {response.status}: {error_message}"}
                
            except (asyncio.TimeoutError, aiohttp.ClientError, asyncio.CancelledError) as e:
                logger.warning(f"OpenAI API attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    logger.error(f"OpenAI API call failed after {max_retries} attempts")
                    return {"success": False, "error": f"OpenAI API timeout/connection error after {max_retries} attempts: {str(e)}"}
            except Exception as e:
                logger.error(f"OpenAI API call exception: {str(e)}")
                import traceback
                logger.error(f"OpenAI API traceback: {traceback.format_exc()}")
                return {"success": False, "error": f"OpenAI API exception: {str(e)}"}
        
        # If we get here, all retries failed
        return {"success": False, "error": f"OpenAI API failed after {max_retries} attempts"}
    
    async def _call_llm_with_fallback(self, image_base64: str, prompt: str) -> Dict[str, Any]:
        """Call LLM APIs with fallback chain.
        
        Args:
            image_base64: Base64 encoded image
            prompt: OCR prompt
            
        Returns:
            API response from first successful provider
        """
        last_errors = []
        
        for provider in self.provider_chain:
            try:
                logger.debug(f"Trying {provider.value} for OCR...")
                
                if provider == LLMProvider.CLAUDE and self.claude_api_key:
                    result = await self._call_claude_api(image_base64, prompt)
                elif provider == LLMProvider.GEMINI and self.gemini_api_key:
                    result = await self._call_gemini_api(image_base64, prompt)
                elif provider == LLMProvider.OPENAI and self.openai_api_key:
                    result = await self._call_openai_api(image_base64, prompt)
                else:
                    logger.debug(f"Skipping {provider.value} - no API key available")
                    continue
                
                if result["success"]:
                    logger.info(f"OCR successful using {provider.value}")
                    return result
                else:
                    error_msg = result.get('error', 'Unknown error')
                    last_errors.append(f"{provider.value}: {error_msg}")
                    logger.warning(f"{provider.value} OCR failed: {error_msg}")
                    
            except Exception as e:
                import traceback
                error_detail = f"{provider.value} exception: {str(e)}"
                last_errors.append(error_detail)
                logger.error(f"{provider.value} OCR failed with exception: {e}")
                logger.debug(f"Exception details: {traceback.format_exc()}")
                continue
        
        # Return detailed error information
        error_summary = "; ".join(last_errors) if last_errors else "No providers available"
        return {"success": False, "error": f"All OCR providers failed - {error_summary}"}
    
    def _parse_structured_response(self, content: str) -> Tuple[List[Dict], str]:
        """Parse structured JSON response from LLM.
        
        Args:
            content: LLM response content
            
        Returns:
            Tuple of (text_detections, full_text)
        """
        try:
            # Try to parse as JSON first
            if content.strip().startswith('{'):
                data = json.loads(content)
                if "texts" in data:
                    return data["texts"], data.get("full_text", "")
        except:
            pass
        
        # Fallback: treat as plain text
        return [], content.strip()
    
    def _create_text_detections(
        self, 
        structured_data: List[Dict], 
        full_text: str,
        image_width: int,
        image_height: int
    ) -> List[TextDetection]:
        """Create TextDetection objects from parsed data.
        
        Args:
            structured_data: Parsed text detection data
            full_text: Full extracted text
            image_width: Image width for bbox calculation
            image_height: Image height for bbox calculation
            
        Returns:
            List of TextDetection objects
        """
        detections = []
        
        if not structured_data:
            # If no structured data, create a single detection for the full text
            if full_text and full_text != "NO TEXT FOUND":
                detection = TextDetection(
                    text=full_text,
                    confidence=0.9,  # Default confidence for simple extraction
                    bbox=[[0, 0], [image_width, 0], [image_width, image_height], [0, image_height]],
                    center_x=image_width / 2,
                    center_y=image_height / 2,
                    width=image_width,
                    height=image_height
                )
                detections.append(detection)
        else:
            # Process structured detections
            region_positions = {
                "top-left": (0.25, 0.25),
                "top": (0.5, 0.25),
                "top-right": (0.75, 0.25),
                "left": (0.25, 0.5),
                "center": (0.5, 0.5),
                "right": (0.75, 0.5),
                "bottom-left": (0.25, 0.75),
                "bottom": (0.5, 0.75),
                "bottom-right": (0.75, 0.75),
            }
            
            for item in structured_data:
                text = item.get("text", "")
                confidence = float(item.get("confidence", 0.85))
                region = item.get("region", "center")
                
                if text:
                    # Estimate position based on region description
                    pos_x, pos_y = region_positions.get(region.lower(), (0.5, 0.5))
                    center_x = pos_x * image_width
                    center_y = pos_y * image_height
                    
                    # Estimate text box size (rough approximation)
                    char_width = 8  # Average character width in pixels
                    char_height = 16  # Average character height in pixels
                    text_width = min(len(text) * char_width, image_width * 0.8)
                    text_height = char_height
                    
                    # Create bounding box
                    half_width = text_width / 2
                    half_height = text_height / 2
                    bbox = [
                        [center_x - half_width, center_y - half_height],
                        [center_x + half_width, center_y - half_height],
                        [center_x + half_width, center_y + half_height],
                        [center_x - half_width, center_y + half_height]
                    ]
                    
                    detection = TextDetection(
                        text=text,
                        confidence=confidence,
                        bbox=bbox,
                        center_x=center_x,
                        center_y=center_y,
                        width=text_width,
                        height=text_height
                    )
                    detections.append(detection)
        
        return detections
    
    async def extract_text_from_image(
        self,
        image_data: bytes,
        confidence_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Extract text from image data using LLM vision models.
        
        Args:
            image_data: Image data as bytes
            confidence_threshold: Minimum confidence threshold (for compatibility)
            
        Returns:
            OCR result with extracted text
        """
        try:
            if not self._is_initialized:
                raise RuntimeError("LLM OCR engine not initialized")
            
            start_time = time.time()
            
            # Get image dimensions
            image = Image.open(io.BytesIO(image_data))
            image_width, image_height = image.size
            
            # Prepare image data
            image_base64 = self._prepare_image_data(image_data)
            
            # Create OCR prompt
            prompt = self._create_ocr_prompt(detailed=True)
            
            # Check if we have any providers available
            if not self.provider_chain:
                # Demo mode - return mock OCR result
                logger.info("Running in demo mode - returning mock OCR result")
                demo_text = "Demo Mode: LLM OCR would extract text from this image if API keys were provided"
                
                mock_detection = TextDetection(
                    text=demo_text,
                    confidence=0.95,
                    bbox=[[50, 50], [image_width-50, 50], [image_width-50, 100], [50, 100]],
                    center_x=image_width / 2,
                    center_y=75,
                    width=image_width - 100,
                    height=50
                )
                
                processing_time = time.time() - start_time
                
                return OCRResult(
                    success=True,
                    timestamp=start_time,
                    processing_time=processing_time,
                    text_detections=[mock_detection],
                    full_text=demo_text,
                    word_count=len(demo_text.split()),
                    confidence_avg=0.95,
                    message="Demo mode: LLM OCR simulation completed (set API keys for real OCR)",
                    provider_used="demo"
                ).dict()
            
            # Call LLM with fallback
            llm_result = await self._call_llm_with_fallback(image_base64, prompt)
            
            if not llm_result["success"]:
                return OCRResult(
                    success=False,
                    timestamp=start_time,
                    processing_time=time.time() - start_time,
                    text_detections=[],
                    full_text="",
                    word_count=0,
                    confidence_avg=0.0,
                    message=f"LLM OCR failed: {llm_result.get('error', 'Unknown error')}"
                ).dict()
            
            # Parse response
            content = llm_result["content"]
            structured_data, full_text = self._parse_structured_response(content)
            
            # If structured parsing failed, use content as full_text
            if not structured_data and not full_text:
                full_text = content
            
            # Create text detections
            text_detections = self._create_text_detections(
                structured_data, full_text, image_width, image_height
            )
            
            # Apply confidence threshold filter if specified
            if confidence_threshold is not None:
                text_detections = [
                    d for d in text_detections 
                    if d.confidence >= confidence_threshold
                ]
                full_text = ' '.join([d.text for d in text_detections])
            
            # Calculate statistics
            word_count = len(full_text.split()) if full_text else 0
            confidence_avg = (
                sum(d.confidence for d in text_detections) / len(text_detections)
                if text_detections else 0.0
            )
            
            processing_time = time.time() - start_time
            
            logger.info(
                f"LLM OCR completed using {llm_result['provider']}: "
                f"{len(text_detections)} detections, {word_count} words, "
                f"avg_confidence={confidence_avg:.3f}, time={processing_time:.3f}s"
            )
            
            return OCRResult(
                success=True,
                timestamp=start_time,
                processing_time=processing_time,
                text_detections=text_detections,
                full_text=full_text,
                word_count=word_count,
                confidence_avg=confidence_avg,
                message=f"LLM OCR completed successfully with {len(text_detections)} text detections",
                provider_used=llm_result['provider']
            ).dict()
            
        except Exception as e:
            logger.error(f"LLM OCR failed: {e}")
            return OCRResult(
                success=False,
                timestamp=time.time(),
                processing_time=0.0,
                text_detections=[],
                full_text="",
                word_count=0,
                confidence_avg=0.0,
                message=f"LLM OCR failed: {str(e)}"
            ).dict()
    
    async def extract_text_from_base64(
        self,
        base64_data: str,
        confidence_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Extract text from base64 encoded image.
        
        Args:
            base64_data: Base64 encoded image data
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            OCR result with extracted text
        """
        try:
            # Decode base64
            image_data = base64.b64decode(base64_data)
            
            # Process with OCR
            return await self.extract_text_from_image(image_data, confidence_threshold)
            
        except Exception as e:
            logger.error(f"Failed to process base64 image: {e}")
            return OCRResult(
                success=False,
                timestamp=time.time(),
                processing_time=0.0,
                text_detections=[],
                full_text="",
                word_count=0,
                confidence_avg=0.0,
                message=f"Failed to process base64 image: {str(e)}"
            ).dict()
    
    async def find_text_in_image(
        self,
        image_data: bytes,
        search_text: str,
        confidence_threshold: Optional[float] = None,
        case_sensitive: bool = False
    ) -> Dict[str, Any]:
        """Find specific text in image.
        
        Args:
            image_data: Image data as bytes
            search_text: Text to search for
            confidence_threshold: Minimum confidence threshold
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            Search result with matching text locations
        """
        try:
            # Extract all text from image
            ocr_result = await self.extract_text_from_image(image_data, confidence_threshold)
            
            if not ocr_result["success"]:
                return ocr_result
            
            # Search for matching text
            matches = []
            search_text_norm = search_text if case_sensitive else search_text.lower()
            
            for detection in ocr_result["text_detections"]:
                text_norm = detection["text"] if case_sensitive else detection["text"].lower()
                
                # Check for exact match or substring match
                if search_text_norm in text_norm:
                    matches.append(detection)
            
            # Update result
            ocr_result["text_detections"] = matches
            ocr_result["message"] = f"Found {len(matches)} matches for '{search_text}'"
            
            logger.info(f"Text search completed: found {len(matches)} matches for '{search_text}'")
            
            return ocr_result
            
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return {
                "success": False,
                "timestamp": time.time(),
                "processing_time": 0.0,
                "text_detections": [],
                "full_text": "",
                "word_count": 0,
                "confidence_avg": 0.0,
                "message": f"Text search failed: {str(e)}"
            }
    
    async def extract_text_from_region(
        self,
        image_data: bytes,
        region: Dict[str, int],
        confidence_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Extract text from specific region of image.
        
        Args:
            image_data: Image data as bytes
            region: Region dict with x, y, width, height
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            OCR result for the specified region
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))
            
            # Crop to region
            crop_box = (
                region["x"],
                region["y"],
                region["x"] + region["width"],
                region["y"] + region["height"]
            )
            cropped_image = image.crop(crop_box)
            
            # Convert cropped image back to bytes
            img_buffer = io.BytesIO()
            cropped_image.save(img_buffer, format="PNG")
            cropped_data = img_buffer.getvalue()
            
            # Extract text from cropped region
            result = await self.extract_text_from_image(cropped_data, confidence_threshold)
            
            # Adjust bounding box coordinates to original image coordinates
            if result["success"]:
                for detection in result["text_detections"]:
                    # Adjust bbox coordinates
                    for point in detection["bbox"]:
                        point[0] += region["x"]  # Adjust x coordinate
                        point[1] += region["y"]  # Adjust y coordinate
                    
                    # Adjust center coordinates
                    detection["center_x"] += region["x"]
                    detection["center_y"] += region["y"]
            
            logger.info(f"Region OCR completed for region {region}")
            
            return result
            
        except Exception as e:
            logger.error(f"Region OCR failed: {e}")
            return OCRResult(
                success=False,
                timestamp=time.time(),
                processing_time=0.0,
                text_detections=[],
                full_text="",
                word_count=0,
                confidence_avg=0.0,
                message=f"Region OCR failed: {str(e)}"
            ).dict()
    
    async def cleanup(self) -> None:
        """Cleanup LLM OCR engine resources."""
        try:
            self._is_initialized = False
            logger.info("LLM OCR Engine cleaned up")
        except Exception as e:
            logger.error(f"LLM OCR cleanup failed: {e}")


# Alias for compatibility - this will be imported as OCREngine
OCREngine = LLMOCREngine