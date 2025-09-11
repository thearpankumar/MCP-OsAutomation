# LLM OCR Setup Guide

The MCP WebAutomation server now uses LLM-based OCR (Claude, Gemini, OpenAI) instead of PaddleOCR for better accuracy and reliability.

## Environment Variables

### Option 1: .env File (Recommended)

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your API keys
nano .env
```

Then add your API keys:
```bash
ANTHROPIC_API_KEY=your-claude-api-key
GEMINI_API_KEY=your-gemini-api-key  
OPENAI_API_KEY=your-openai-api-key
```

### Option 2: Environment Variables

Alternatively, set environment variables directly:

```bash
# Claude (Anthropic) - Recommended primary provider
export ANTHROPIC_API_KEY="your-claude-api-key"

# Google Gemini - Good fallback option  
export GEMINI_API_KEY="your-gemini-api-key"

# OpenAI GPT-4 Vision - Additional fallback
export OPENAI_API_KEY="your-openai-api-key"
```

### Getting API Keys

1. **Claude (Anthropic)**:
   - Go to https://console.anthropic.com/
   - Create an account and generate an API key
   - **Most accurate for OCR tasks**

2. **Gemini (Google)**:
   - Go to https://aistudio.google.com/
   - Create an account and generate an API key  
   - **Good balance of speed and accuracy**

3. **OpenAI GPT-4 Vision**:
   - Go to https://platform.openai.com/
   - Create an account and generate an API key
   - **Reliable fallback option**

## Installation

1. Install the updated dependencies:
```bash
# Install core dependencies (no more PaddleOCR issues!)
pip install -e .

# Or using uv
uv install
```

2. Set your environment variables in your shell profile:
```bash
# Add to ~/.bashrc, ~/.zshrc, or create .env file
export ANTHROPIC_API_KEY="your-key-here"
export GEMINI_API_KEY="your-key-here"  
export OPENAI_API_KEY="your-key-here"
```

## Configuration

The server is pre-configured to use LLM OCR. You can customize the provider order in `configs/fastmcp.json`:

```json
{
  "ocr": {
    "confidence_threshold": 0.8,
    "llm_config": {
      "primary_provider": "claude",
      "fallback_providers": ["gemini", "openai"],
      "timeout_seconds": 30,
      "max_retries": 2
    }
  }
}
```

## Testing

Test the new LLM OCR system:

```bash
# Test mode (includes OCR testing)
python start_server.py --test

# Run the basic example
python examples/basic_usage.py

# Test automation workflow  
python examples/automation_example.py
```

## Benefits of LLM OCR

✅ **No dependency issues** - No more PaddleOCR/CUDA problems
✅ **Higher accuracy** - Especially for complex layouts and handwriting  
✅ **Better context understanding** - Understands relationships between text elements
✅ **Multilingual support** - Works with many languages out of the box
✅ **Structured output** - Can return text with layout information
✅ **Fallback system** - Automatically tries multiple providers
✅ **Future-proof** - Uses latest vision AI models

## Troubleshooting

### "No LLM OCR providers available"
- Check that at least one API key environment variable is set
- Verify the API key is valid by testing it directly

### "LLM OCR failed: API error"  
- Check your API key quota/billing
- Verify network connectivity
- Try a different provider in the fallback chain

### Slow OCR performance
- Use Gemini for faster responses 
- Reduce image resolution if possible
- Check your network latency to API endpoints

### High API costs
- Set confidence thresholds higher to reduce processing
- Use caching for repeated images
- Consider using Gemini (typically lower cost than Claude/OpenAI)

## Migration from PaddleOCR

If you were using the old PaddleOCR system:

1. **No code changes needed** - The interface remains the same
2. **Remove PaddleOCR dependencies**:
   ```bash
   pip uninstall paddleocr paddlepaddle paddlepaddle-gpu
   ```
3. **Set up API keys** as described above
4. **Test thoroughly** - LLM OCR may return different results than PaddleOCR

The OCR interface (`extract_text_from_image`, `find_text_in_image`, etc.) remains identical, so existing automation scripts will continue to work.