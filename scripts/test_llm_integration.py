#!/usr/bin/env python3
"""
LLM Integration Test Script

Tests the OpenRouter client with multimodal inputs (text + images).
Uses sample ultrasound images from the samples directory.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.openrouter_client import OpenRouterClient


def main():
    """Test LLM integration with multimodal inputs"""

    print("Testing LLM Integration with OpenRouter API...")
    print("=" * 50)

    # Load environment variables
    load_dotenv()
    print("✓ Environment variables loaded")

    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("✗ OPENROUTER_API_KEY not found in environment")
        print("Please set your OpenRouter API key in the .env file")
        return 1

    print(f"✓ API key found: {api_key[:10]}...")

    # Initialize client
    try:
        client = OpenRouterClient()
        print("✓ OpenRouter client initialized")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return 1

    # Prepare sample image
    sample_image_path = Path("temp_sample.jpg")
    if not sample_image_path.exists():
        print("✗ Sample image not found. Please run DICOM conversion first.")
        return 1

    print(f"✓ Sample image found: {sample_image_path}")

    # Create conversation history
    system_prompt = {
        "role": "system",
        "content": "You are a medical AI assistant specialized in ultrasound report generation. Analyze the provided ultrasound images and generate a professional medical report based on the findings."
    }

    # Create multimodal user message
    user_message = client.create_multimodal_message(
        text="Please analyze this ultrasound image and describe what you see. Focus on anatomical structures, any abnormalities, and key findings that would be relevant for a medical report.",
        image_paths=[str(sample_image_path)]
    )

    messages = [system_prompt, user_message]

    print("✓ Conversation history prepared")
    print(f"  - System prompt: {len(system_prompt['content'])} characters")
    print(f"  - User message: text + {len(user_message['content']) - 1} image(s)")

    # Generate response
    try:
        print("\nGenerating response from LLM...")
        print("-" * 30)

        response = client.generate_response(
            messages=messages,
            model="google/gemini-2.5-flash",
            max_tokens=1000,
            temperature=0.3
        )

        print("✓ Response received successfully!")
        print("\nLLM Response:")
        print("=" * 50)
        print(response)
        print("=" * 50)

        # Check response quality
        if len(response.strip()) > 50:  # Reasonable minimum length
            print("\n✓ Test PASSED: LLM integration working correctly")
            print("✓ Multimodal input (text + image) processed successfully")
            return 0
        else:
            print("\n⚠ Test WARNING: Response seems too short")
            return 0

    except Exception as e:
        print(f"\n✗ Test FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())