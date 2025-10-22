"""
LLM service for Agent LLM Deployment System.

This module handles interactions with various LLM providers
with fallback and rotation capabilities for the autonomous AI web developer.
"""

import asyncio
import json
import random
from typing import List, Dict, Any, Optional

from src.core.logging import get_logger
from src.core.config import settings

logger = get_logger(__name__)


class LLMService:
    """Service for LLM provider management and interactions."""

    def __init__(self):
        self.providers = []
        self.current_provider_index = 0

        # Initialize available providers
        logger.info(f"Initializing LLM providers...")

        if settings.llm.openai_api_key:
            self.providers.append(OpenAIProvider(settings.llm.openai_api_key))
            logger.info("Loaded OpenAI provider")

        if settings.llm.anthropic_api_key:
            self.providers.append(AnthropicProvider(settings.llm.anthropic_api_key))
            logger.info("Loaded Anthropic provider")

        # Free providers - check for API keys
        logger.info(f"Checking free providers...")
        logger.info(f"settings.llm.groq_api_key: {getattr(settings.llm, 'groq_api_key', 'NOT_FOUND')}")
        logger.info(f"settings.llm.huggingface_api_key: {getattr(settings.llm, 'huggingface_api_key', 'NOT_FOUND')}")
        logger.info(f"hasattr groq: {hasattr(settings.llm, 'groq_api_key')}")
        logger.info(f"hasattr hf: {hasattr(settings.llm, 'huggingface_api_key')}")

        if hasattr(settings.llm, 'groq_api_key') and settings.llm.groq_api_key:
            self.providers.append(GroqProvider(settings.llm.groq_api_key))
            logger.info("Loaded Groq provider")
        else:
            logger.info("Skipping Groq provider - no API key or attribute missing")

        if hasattr(settings.llm, 'huggingface_api_key') and settings.llm.huggingface_api_key:
            self.providers.append(HuggingFaceProvider(settings.llm.huggingface_api_key))
            logger.info("Loaded Hugging Face provider")
        else:
            logger.info("Skipping Hugging Face provider - no API key or attribute missing")

        logger.info(f"Total providers loaded: {len(self.providers)} - {[p.__class__.__name__ for p in self.providers]}")

        if not self.providers:
            logger.warning("No LLM providers configured - AI agent will not function properly")

    async def close(self):
        """Close LLM connections."""
        for provider in self.providers:
            await provider.close()

    async def generate_response(
        self,
        prompt: str,
        system_message: str = "",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate response using available LLM providers with fallback."""
        if not self.providers:
            raise ValueError("No LLM providers available")

        last_error = None

        # Try each provider in rotation
        for i in range(len(self.providers)):
            provider = self.providers[self.current_provider_index]
            logger.info(f"Trying provider {i+1}/{len(self.providers)}: {provider.__class__.__name__}")

            try:
                response = await provider.generate_response(
                    prompt=prompt,
                    system_message=system_message,
                    max_tokens=max_tokens,
                    temperature=temperature
                )

                # Rotate to next provider for load balancing
                self.current_provider_index = (self.current_provider_index + 1) % len(self.providers)

                logger.info(f"Successfully generated response using {provider.__class__.__name__}")
                return response

            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
                last_error = e

            # Move to next provider
            self.current_provider_index = (self.current_provider_index + 1) % len(self.providers)

        # If all providers failed
        error_msg = f"All LLM providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    async def generate_code(
        self,
        requirements: str,
        file_type: str = "html",
        existing_code: str = ""
    ) -> str:
        """Generate code for a specific file type."""

        if file_type == "html":
            prompt = self._get_html_prompt(requirements, existing_code)
        elif file_type == "css":
            prompt = self._get_css_prompt(requirements, existing_code)
        elif file_type == "javascript":
            prompt = self._get_js_prompt(requirements, existing_code)
        else:
            prompt = f"Generate {file_type} code for: {requirements}"

        system_message = """
        You are an expert web developer. Generate clean, functional, well-structured code.
        Follow best practices and ensure the code is production-ready.
        """

        return await self.generate_response(
            prompt=prompt,
            system_message=system_message,
            max_tokens=2000,
            temperature=0.3
        )

    def _get_html_prompt(self, requirements: str, existing_code: str = "") -> str:
        """Generate prompt for HTML code generation."""
        context = f"Existing code: {existing_code}" if existing_code else "No existing code"

        return f"""
        Generate clean, semantic HTML code for the following requirements:

        Requirements: {requirements}
        {context}

        Generate only the HTML code without explanation. Include proper DOCTYPE, head, and body structure.
        Use modern HTML5 standards and semantic elements.
        """

    def _get_css_prompt(self, requirements: str, existing_code: str = "") -> str:
        """Generate prompt for CSS code generation."""
        context = f"Existing CSS: {existing_code}" if existing_code else "No existing CSS"

        return f"""
        Generate clean, responsive CSS code for the following requirements:

        Requirements: {requirements}
        {context}

        Generate only the CSS code without explanation. Use modern CSS features and ensure responsiveness.
        """

    def _get_js_prompt(self, requirements: str, existing_code: str = "") -> str:
        """Generate prompt for JavaScript code generation."""
        context = f"Existing JavaScript: {existing_code}" if existing_code else "No existing JavaScript"

        return f"""
        Generate clean, functional JavaScript code for the following requirements:

        Requirements: {requirements}
        {context}

        Generate only the JavaScript code without explanation. Use modern ES6+ features and follow best practices.
        """


class BaseLLMProvider:
    """Base class for LLM providers."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate_response(
        self,
        prompt: str,
        system_message: str = "",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate response - to be implemented by subclasses."""
        raise NotImplementedError

    async def close(self):
        """Close provider connection."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = None

    async def generate_response(
        self,
        prompt: str,
        system_message: str = "",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate response using OpenAI."""
        try:
            import openai

            if not self.client:
                self.client = openai.AsyncOpenAI(api_key=self.api_key)

            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            return response.choices[0].message.content.strip()

        except ImportError:
            raise ValueError("OpenAI package not installed")
        except Exception as e:
            raise ValueError(f"OpenAI API error: {e}")


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = None

    async def generate_response(
        self,
        prompt: str,
        system_message: str = "",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate response using Anthropic."""
        try:
            import anthropic

            if not self.client:
                self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

            messages = [{"role": "user", "content": prompt}]

            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                system=system_message,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            return response.content[0].text.strip()

        except ImportError:
            raise ValueError("Anthropic package not installed")
        except Exception as e:
            raise ValueError(f"Anthropic API error: {e}")


class GroqProvider(BaseLLMProvider):
    """Groq LLM provider (Free tier available)."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "llama3.1-70b-versatile"  # Fast, free model
        self.client = None

    async def generate_response(
        self,
        prompt: str,
        system_message: str = "",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate response using Groq API."""
        try:
            import openai
            
            if not self.client:
                self.client = openai.AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )

            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            return response.choices[0].message.content.strip()

        except ImportError:
            raise ValueError("OpenAI package not installed")
        except Exception as e:
            raise ValueError(f"Groq API error: {e}")

    async def close(self):
        """Close Groq connection."""
        pass


class HuggingFaceProvider(BaseLLMProvider):
    """Hugging Face Inference API provider (Free tier available)."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "facebook/blenderbot-400M-distill"  # Free conversational model
        self.client = None

    async def generate_response(
        self,
        prompt: str,
        system_message: str = "",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate response using Hugging Face Inference API."""
        try:
            import httpx
            
            if not self.client:
                self.client = httpx.AsyncClient()

            # Combine system message and prompt
            full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt

            response = await self.client.post(
                f"https://router.huggingface.co/hf-inference/models/{self.model}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "inputs": full_prompt,
                    "parameters": {
                        "max_length": max_tokens,
                        "temperature": temperature,
                        "do_sample": True,
                        "return_full_text": False
                    },
                    "options": {"wait_for_model": True}
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise ValueError(f"Hugging Face API error: {response.status_code} - {response.text}")

            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0]["generated_text"].strip()
            else:
                raise ValueError("Unexpected response format from Hugging Face API")

        except ImportError:
            raise ValueError("httpx package not installed")
        except Exception as e:
            raise ValueError(f"Hugging Face API error: {e}")

    async def close(self):
        """Close Hugging Face connection."""
        if self.client:
            await self.client.aclose()
