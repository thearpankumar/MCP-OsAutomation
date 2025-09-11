"""
Configuration management for MCP WebAutomation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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


class LLMConfig(BaseModel):
    """LLM provider configuration model."""
    
    primary_provider: str = Field(default="claude", description="Primary LLM provider (claude, gemini, openai)")
    fallback_providers: List[str] = Field(
        default=["gemini", "openai"],
        description="Fallback LLM providers in order"
    )
    claude_model: str = Field(default="claude-3-5-sonnet-20241022", description="Claude model to use")
    gemini_model: str = Field(default="gemini-2.5-flash", description="Gemini model to use")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    timeout_seconds: int = Field(default=30, description="API request timeout in seconds")
    max_retries: int = Field(default=2, description="Maximum API request retries")


class OCRConfig(BaseModel):
    """OCR configuration model."""
    
    confidence_threshold: float = Field(
        default=0.8,
        description="Minimum confidence threshold for OCR results"
    )
    languages: List[str] = Field(
        default=["en"],
        description="Languages to detect in OCR"
    )
    llm_config: LLMConfig = Field(default_factory=LLMConfig, description="LLM-specific configuration")


class Config(BaseModel):
    """Main configuration model."""
    
    server: ServerConfig = Field(default_factory=ServerConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    ocr: OCRConfig = Field(default_factory=OCRConfig)