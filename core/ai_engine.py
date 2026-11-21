"""
AI Engine for AI-Powered Campus Helpdesk Assistant.
Interfaces with Google Gemini via the official google-genai SDK.
Handles exponential backoff retries, error classification, timeouts, and embeddings.
"""

import time
from typing import Optional, List, Dict, Any

from config import settings
from core.exceptions import (
    AIEngineError,
    MissingKeyError,
    InvalidKeyError,
    RateLimitError,
    QuotaExceededError,
    NetworkFailureError,
    NetworkError,
    ModelTimeoutError,
    SafetyBlockError,
)
from core.logger import logger


class EmptyResponseError(AIEngineError):
    """Raised when the model returns an empty text response."""
    pass


class UnknownAPIError(AIEngineError):
    """Raised on unexpected API errors."""
    pass


# ==============================================================================
# AIEngine Class
# ==============================================================================
class AIEngine:
    """Wrapper around Google GenAI client with defensive error handling."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        embedding_model: Optional[str] = None
    ):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name = model_name if model_name is not None else settings.GEMINI_MODEL
        self.embedding_model = embedding_model if embedding_model is not None else settings.GEMINI_EMBEDDING_MODEL
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        """Initializes the google-genai client if API key is provided."""
        if not self.api_key or not self.api_key.strip():
            self._client = None
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key.strip())
        except ImportError:
            self._client = None
        except Exception:
            self._client = None

    def update_key(self, new_key: str) -> None:
        """Updates API key dynamically at runtime."""
        self.api_key = new_key.strip() if new_key else ""
        self._init_client()

    def is_available(self) -> bool:
        """Returns True if a non-empty API key is configured and client can be initialized."""
        return bool(self.api_key and self.api_key.strip())

    def is_configured(self) -> bool:
        """Backward-compatible alias for is_available."""
        return self.is_available()

    def classify_error(self, exc: Exception) -> AIEngineError:
        """Translates low-level API exceptions into classified domain errors with friendly messages."""
        err_msg = str(exc).lower()

        if "api_key" in err_msg or "invalid api key" in err_msg or "permission" in err_msg or "403" in err_msg or "401" in err_msg:
            return InvalidKeyError(
                "Invalid or expired Gemini API key. Please check your credentials at https://aistudio.google.com/"
            )
        if "quota" in err_msg or "rate limit" in err_msg or "429" in err_msg or "resource_exhausted" in err_msg:
            return RateLimitError(
                "Gemini API rate limit or quota exceeded. Please wait a moment and try again."
            )
        if "timeout" in err_msg or "deadline" in err_msg:
            return ModelTimeoutError(
                "Gemini API request timed out after waiting for response. Please retry."
            )
        if "connection" in err_msg or "network" in err_msg or "nodename" in err_msg or "getaddrinfo" in err_msg:
            return NetworkFailureError(
                "Unable to connect to Google Gemini services. Please verify your internet connection."
            )
        if "safety" in err_msg or "blocked" in err_msg or "harm_category" in err_msg:
            return SafetyBlockError(
                "The requested prompt or response was flagged and blocked by Gemini safety filters."
            )

        return UnknownAPIError(f"Unexpected Gemini API error: {str(exc)}")

    def generate(
        self,
        system_prompt: Optional[str] = None,
        user_prompt: str = "",
        temperature: float = 0.0,
        max_retries: int = 3,
        timeout: float = 30.0
    ) -> str:
        """
        Calls Gemini to generate content with exponential backoff retries.
        
        Args:
            system_prompt: Optional system instruction for the model.
            user_prompt: User message / assembled RAG prompt.
            temperature: Sampling temperature (0.0 for deterministic output).
            max_retries: Number of retry attempts on transient network errors.
            timeout: Request timeout in seconds.
            
        Returns:
            Grounded answer text.
            
        Raises:
            MissingKeyError, InvalidKeyError, RateLimitError, NetworkFailureError,
            SafetyBlockError, EmptyResponseError, UnknownAPIError.
        """
        if not self.is_available():
            raise MissingKeyError(
                "No Gemini API key configured. The assistant is operating in Lexical Fallback Mode."
            )

        if self._client is None:
            self._init_client()
            if self._client is None:
                raise UnknownAPIError("Failed to initialize Google GenAI SDK client.")

        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=1024,
        )
        if system_prompt:
            config.system_instruction = system_prompt

        last_error = None
        for attempt in range(max_retries):
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=config
                )
                if response and response.text and response.text.strip():
                    return response.text.strip()
                raise EmptyResponseError("Gemini returned an empty text response.")
            except EmptyResponseError as ere:
                raise ere
            except Exception as e:
                classified = self.classify_error(e)
                last_error = classified

                # Do not retry on non-transient errors (invalid key or safety blocks)
                if isinstance(classified, (InvalidKeyError, SafetyBlockError)):
                    raise classified

                if attempt < max_retries - 1:
                    time.sleep(1.0 * (2 ** attempt))

        raise last_error if last_error else UnknownAPIError("Generation failed after retries.")

    def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.0,
        max_retries: int = 3
    ) -> str:
        """Backward-compatible signature forwarding to generate()."""
        return self.generate(
            system_prompt=system_instruction,
            user_prompt=prompt,
            temperature=temperature,
            max_retries=max_retries
        )

    def embed(self, text: str) -> Optional[List[float]]:
        """
        Generates semantic text embeddings using Gemini embed_content.
        
        Args:
            text: Input string to embed.
            
        Returns:
            List of float embedding vector, or None on failure.
        """
        if not self.is_available() or self._client is None:
            return None

        try:
            cleaned = text.strip()[:2000]
            if not cleaned:
                return None

            response = self._client.models.embed_content(
                model=self.embedding_model,
                contents=cleaned,
            )

            if hasattr(response, "embedding") and response.embedding:
                if hasattr(response.embedding, "values"):
                    return list(response.embedding.values)
                return list(response.embedding)
            elif hasattr(response, "embeddings") and response.embeddings:
                first = response.embeddings[0]
                if hasattr(first, "values"):
                    return list(first.values)
                return list(first)
            return None
        except Exception:
            return None

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Backward-compatible alias for embed()."""
        return self.embed(text)
