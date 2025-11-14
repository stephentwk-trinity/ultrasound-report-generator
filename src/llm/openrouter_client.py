"""
OpenRouter API Client for Multimodal LLM Integration

This module provides a client for interacting with OpenRouter's API,
specifically designed for multimodal conversations with Google's Gemini models.
Supports text and image inputs for ultrasound report generation.
"""

import os
import base64
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path


class OpenRouterClient:
    """
    Client for OpenRouter API with multimodal support.

    Handles authentication, request formatting, and response parsing
    for Google's Gemini models via OpenRouter.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://openrouter.ai/api/v1"):
        """
        Initialize the OpenRouter client.

        Args:
            api_key: OpenRouter API key. If None, reads from OPENROUTER_API_KEY env var.
            base_url: Base URL for OpenRouter API.

        Raises:
            ValueError: If API key is not provided and not found in environment.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable.")

        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ultrasound-report-generator",
        })

    def encode_image_to_base64(self, image_path: str) -> str:
        """
        Encode a local image file to base64 string for API requests.

        Args:
            image_path: Path to the image file (JPG, PNG, etc.)

        Returns:
            Base64 encoded string with data URL prefix.

        Raises:
            FileNotFoundError: If image file doesn't exist.
            ValueError: If file is not a valid image format.
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Determine MIME type based on extension
        ext = path.suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }

        if ext not in mime_types:
            raise ValueError(f"Unsupported image format: {ext}. Supported: {list(mime_types.keys())}")

        # Read and encode
        with open(path, "rb") as f:
            image_data = f.read()

        encoded = base64.b64encode(image_data).decode('utf-8')
        return f"data:{mime_types[ext]};base64,{encoded}"

    def generate_response(
        self,
        messages: List[Dict[str, Any]],
        model: str = "google/gemini-2.0-flash-exp:free",
        max_tokens: int = 4000,
        temperature: float = 0.3,
        **kwargs
    ) -> str:
        """
        Generate a response from the LLM using the provided conversation history.

        Args:
            messages: List of message dictionaries with OpenAI-compatible format.
                     Each message should have 'role' and 'content' keys.
                     Content can be string (text-only) or list (multimodal).
            model: Model identifier to use.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature (0.0 to 1.0).
            **kwargs: Additional parameters for the API request.

        Returns:
            Generated response text.

        Raises:
            requests.RequestException: If API request fails.
            ValueError: If response format is invalid.
        """
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        url = f"{self.base_url}/chat/completions"
        response = self.session.post(url, json=payload)

        if response.status_code != 200:
            error_msg = f"OpenRouter API error: {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f" - {error_data.get('error', {}).get('message', response.text)}"
            except:
                error_msg += f" - {response.text}"
            raise requests.RequestException(error_msg)

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid response format from OpenRouter API: {e}")

    def create_multimodal_message(self, text: str, image_paths: List[str]) -> Dict[str, Any]:
        """
        Helper to create a multimodal message with text and images.

        Args:
            text: Text content for the message.
            image_paths: List of paths to image files.

        Returns:
            Message dictionary in OpenAI multimodal format.
        """
        content = []

        # Add text
        if text:
            content.append({"type": "text", "text": text})

        # Add images
        for image_path in image_paths:
            base64_data = self.encode_image_to_base64(image_path)
            content.append({
                "type": "image_url",
                "image_url": {"url": base64_data}
            })

        return {"role": "user", "content": content}