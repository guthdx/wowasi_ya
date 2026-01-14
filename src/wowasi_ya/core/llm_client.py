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
        """Generate text using Claude API with streaming for long requests.

        Args:
            prompt: The input prompt.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            Generated text content.
        """
        client = self._ensure_client()

        try:
            # Use streaming for requests with high token counts to avoid timeout
            # Claude API requires streaming for operations >10 minutes
            if max_tokens > 8000:
                logger.info(f"Using streaming for large request ({max_tokens} max tokens)")
                content = ""
                async with client.messages.stream(
                    model=self.settings.claude_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}],
                ) as stream:
                    async for text in stream.text_stream:
                        content += text
                return content
            else:
                # Use non-streaming for smaller requests (faster)
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


class FallbackClient:
    """Claude client with automatic Llama fallback on errors.

    Primary: Claude API
    Fallback: Llama CPP (M4 Mac) when Claude has rate limits or errors
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.claude_client = ClaudeClient(settings)
        self._llama_client: LlamaCPPClient | None = None
        self._llama_available: bool | None = None

    async def _get_llama_client(self) -> LlamaCPPClient | None:
        """Get Llama client, checking availability once."""
        if self._llama_client is None:
            self._llama_client = LlamaCPPClient(self.settings)
            self._llama_available = await self._llama_client.health_check()
        return self._llama_client if self._llama_available else None

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate with Claude, fallback to Llama on errors."""
        try:
            return await self.claude_client.generate(prompt, max_tokens, temperature)
        except Exception as e:
            logger.warning(f"Claude API error: {e}")

            if self.settings.claude_fallback_to_llamacpp:
                llama = await self._get_llama_client()
                if llama:
                    logger.info("Falling back to Llama CPP (M4 Mac)")
                    return await llama.generate(prompt, max_tokens, temperature)
                else:
                    logger.warning("Llama fallback unavailable, re-raising Claude error")

            raise

    def supports_web_search(self) -> bool:
        return True

    async def health_check(self) -> bool:
        return True


async def get_generation_client(settings: Settings) -> BaseLLMClient:
    """Factory for generation clients with intelligent fallback.

    Default (claude): Claude API with fallback to Llama when errors occur
    Alternative (llamacpp): Llama CPP with fallback to Claude when Mac offline

    Args:
        settings: Application settings.

    Returns:
        LLM client instance.
    """
    if settings.generation_provider == "llamacpp":
        # Llama primary, Claude fallback
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

    # Default: Claude primary with Llama fallback
    if settings.claude_fallback_to_llamacpp:
        logger.info("Using Claude API for generation (Llama fallback enabled)")
        return FallbackClient(settings)
    else:
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
