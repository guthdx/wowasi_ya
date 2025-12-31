"""LLM Client Abstraction - supports Claude and Llama CPP.

This module provides a unified interface for different LLM providers:
- ClaudeClient: Anthropic Claude API (supports web search)
- LlamaCPPClient: Local Llama via Cloudflare Tunnel

Architecture:
- Research layer (core/research.py): Uses Claude (web search required)
- Generation layer (core/generator.py): Uses configurable provider

Future-proofing:
To add a new provider, implement BaseLLMClient protocol and update the factory.
"""

import logging
from typing import Any, Protocol

import httpx

from wowasi_ya.config import Settings

logger = logging.getLogger(__name__)


class BaseLLMClient(Protocol):
    """Protocol for LLM clients."""

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate text from prompt.

        Args:
            prompt: The input prompt.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0.0-1.0).

        Returns:
            Generated text content.
        """
        ...

    def supports_web_search(self) -> bool:
        """Check if this client supports web search."""
        ...

    async def health_check(self) -> bool:
        """Check if the LLM service is available."""
        ...


class ClaudeClient:
    """Claude API client - supports web search.

    Used for:
    - Research (always) - requires web search
    - Generation (fallback) - when Llama unavailable
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize Claude client.

        Args:
            settings: Application settings.
        """
        self.settings = settings
        self._client: Any = None

    def _ensure_client(self) -> Any:
        """Lazily initialize the Anthropic async client."""
        if self._client is None:
            try:
                import anthropic

                self._client = anthropic.AsyncAnthropic(
                    api_key=self.settings.anthropic_api_key.get_secret_value()
                )
            except ImportError:
                raise RuntimeError("anthropic package not installed")
        return self._client

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using Claude API.

        Args:
            prompt: The input prompt.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            Generated text content.
        """
        client = self._ensure_client()

        try:
            response = await client.messages.create(
                model=self.settings.claude_model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text content from response
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

            return content

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise

    def supports_web_search(self) -> bool:
        """Claude supports web search."""
        return True

    async def health_check(self) -> bool:
        """Claude API is always available (no local dependency)."""
        # Could optionally ping the API, but for now assume it's available
        return True


class LlamaCPPClient:
    """Llama CPP server client - accessed via Cloudflare Tunnel.

    Used for:
    - Document generation (primary) - cost savings
    - Requires Mac to be online with tunnel active
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize Llama CPP client.

        Args:
            settings: Application settings.
        """
        self.settings = settings
        self.base_url = settings.llamacpp_base_url
        self.timeout = settings.llamacpp_timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using Llama CPP server.

        Args:
            prompt: The input prompt.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            Generated text content.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        # Llama CPP servers typically support OpenAI-compatible API
        url = f"{self.base_url}/v1/chat/completions"

        payload = {
            "model": self.settings.llamacpp_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            # Extract content from OpenAI-compatible response
            content = data["choices"][0]["message"]["content"]
            return content

        except httpx.HTTPError as e:
            logger.error(f"Llama CPP request failed: {e}")
            raise
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected Llama CPP response format: {e}")
            raise

    def supports_web_search(self) -> bool:
        """Llama CPP does not support web search."""
        return False

    async def health_check(self) -> bool:
        """Check if Mac Llama server is reachable.

        Returns:
            True if server responds, False otherwise.
        """
        try:
            # Try the health endpoint first
            response = await self.client.get(
                f"{self.base_url}/health",
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            # If /health doesn't exist, try /v1/models
            try:
                response = await self.client.get(
                    f"{self.base_url}/v1/models",
                    timeout=5.0,
                )
                return response.status_code == 200
            except Exception as e:
                logger.warning(f"Llama CPP health check failed: {e}")
                return False

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()


async def get_generation_client(settings: Settings) -> BaseLLMClient:
    """Factory for generation clients with intelligent fallback.

    Returns Claude or Llama based on:
    1. User configuration (GENERATION_PROVIDER)
    2. Mac availability (health check)
    3. Fallback settings (LLAMACPP_FALLBACK_TO_CLAUDE)

    Args:
        settings: Application settings.

    Returns:
        LLM client instance.
    """
    if settings.generation_provider == "llamacpp":
        # Try Llama first
        llama_client = LlamaCPPClient(settings)
        is_available = await llama_client.health_check()

        if is_available:
            logger.info("Using Llama CPP for document generation (via Cloudflare)")
            return llama_client
        else:
            logger.warning("Llama CPP unavailable (Mac may be offline or asleep)")

            if settings.llamacpp_fallback_to_claude:
                logger.info("Falling back to Claude API for generation")
                return ClaudeClient(settings)
            else:
                raise RuntimeError(
                    "Llama CPP unavailable and fallback disabled. "
                    "Please ensure Mac is online with Cloudflare tunnel running, "
                    "or set LLAMACPP_FALLBACK_TO_CLAUDE=true"
                )

    # Default to Claude
    logger.info("Using Claude API for document generation")
    return ClaudeClient(settings)


def get_research_client(settings: Settings) -> BaseLLMClient:
    """Factory for research clients.

    Currently always returns Claude (web search requirement).

    Future: Could support other providers with web search capability.

    Args:
        settings: Application settings.

    Returns:
        LLM client instance for research.
    """
    # Always use Claude for research (has web search)
    logger.info("Using Claude API for research (web search enabled)")
    return ClaudeClient(settings)
