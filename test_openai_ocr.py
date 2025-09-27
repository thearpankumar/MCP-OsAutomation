#!/usr/bin/env python3
"""
Simple OpenAI OCR test script.

This script takes a screenshot and uses OpenAI to extract text,
testing if your OpenAI API key is working.
"""

import asyncio
import base64
import io
import os
import sys
from pathlib import Path

import aiohttp
import mss
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_openai_ocr():
    """Test OpenAI OCR functionality."""
    print("🧪 Testing OpenAI OCR...")
    print("=" * 40)

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables!")
        print("💡 Make sure you have OPENAI_API_KEY in your .env file")
        return False

    print(f"✅ OpenAI API key found: {api_key[:12]}...")

    # Take screenshot
    print("\n📸 Taking screenshot...")
    try:
        with mss.mss() as sct:
            # Capture primary monitor
            monitor = sct.monitors[1]  # 0 is all monitors, 1 is primary
            screenshot = sct.grab(monitor)

            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

            # Convert to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_data = img_buffer.getvalue()
            base64_image = base64.b64encode(img_data).decode('utf-8')

            print(f"✅ Screenshot captured: {screenshot.size[0]}x{screenshot.size[1]}")

    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
        return False

    # Test OpenAI API
    print("\n🤖 Testing OpenAI Vision API...")
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all visible text from this screenshot. Return the text in a clean, organized format."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    extracted_text = result["choices"][0]["message"]["content"]

                    print("✅ OpenAI OCR successful!")
                    print("\n📝 Extracted text:")
                    print("-" * 40)
                    print(extracted_text)
                    print("-" * 40)

                    # Save result to file
                    with open("openai_ocr_test_result.txt", "w") as f:
                        f.write(f"OpenAI OCR Test Result\n")
                        f.write(f"=====================\n\n")
                        f.write(f"Screenshot size: {screenshot.size[0]}x{screenshot.size[1]}\n")
                        f.write(f"Model used: gpt-4o-mini\n\n")
                        f.write(f"Extracted text:\n")
                        f.write(extracted_text)

                    print(f"\n💾 Result saved to: openai_ocr_test_result.txt")
                    return True

                else:
                    error_text = await response.text()
                    print(f"❌ OpenAI API error ({response.status}): {error_text}")
                    return False

    except Exception as e:
        print(f"❌ OpenAI API request failed: {e}")
        return False

async def main():
    """Main function."""
    print("🔑 OpenAI OCR Test Script")
    print("========================\n")

    success = await test_openai_ocr()

    if success:
        print("\n🎉 OpenAI OCR test completed successfully!")
        print("💡 Your OpenAI API key is working correctly.")
    else:
        print("\n💥 OpenAI OCR test failed!")
        print("🔧 Check your API key and internet connection.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())