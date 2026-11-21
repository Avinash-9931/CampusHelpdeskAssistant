"""
AI Engine for AI-Powered Campus Helpdesk Assistant.
Interfaces with Google Gemini via the official google-genai SDK.
Handles exponential backoff retries, error classification, timeouts, and embeddings.
"""

import time
import socket
from typing import Optional, List, Dict, Any

from config import settings


class AIEngineError(Exception):
    """Base exception for AI Engine errors."""
    pass


class MissingKeyError(AIEngineError):
    """Raised when API key is missing."""
    pass


class InvalidKeyError(AIEngineError):
    """Raised when API key is rejected by Google GenAI."""
    pass


class QuotaExceededError(AIEngineError):
    """Raised when rate limits or quotas are hit."""
    pass


class NetworkError(AIEngineError):
    """Raised on connection issues or DNS failures."""
    pass


class ModelTimeoutError(AIEngineError):
    """Raised when API call takes too long."""
    pass


class AIEngine:
    """Wrapper around Google GenAI client with defensive error handling."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name = model_name if model_name is not None else settings.GEMINI_MODEL
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        """Initializes the google-genai client if API key is provided."""
        if not self.api_key:
            self._client = None
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        except ImportError:
            self._client = None
        except Exception:
            self._client = None

    def update_key(self, new_key: str) -> None:
        """Updates API key dynamically at runtime (e.g., from UI)."""
        self.api_key = new_key.strip()
        self._init_client()

    def is_configured(self) -> bool:
        """Returns True if a non-empty API key is configured."""
        return bool(self.api_key and self.api_key.strip())

    def classify_error(self, exc: Exception) -> AIEngineError:
        """Translates low-level API exceptions into classified domain errors."""
        err_msg = str(exc).lower()

        if "api_key" in err_msg or "invalid api key" in err_msg or "permission" in err_msg or "403" in err_msg or "401" in err_msg:
            return InvalidKeyError(
                "Invalid or expired Gemini API key. Please check your credentials at https://aistudio.google.com/"
            )
        if "quota" in err_msg or "rate limit" in err_msg or "429" in err_msg or "resource_exhausted" in err_msg:
            return QuotaExceededError(
                "Gemini API rate limit or quota exceeded. Please wait a moment or check your quota."
            )
        if "timeout" in err_msg or "deadline" in err_msg:
            return ModelTimeoutError(
                "Gemini API request timed out. Please retry."
            )
        if "connection" in err_msg or "network" in err_msg or "nodename" in err_msg or "getaddrinfo" in err_msg:
            return NetworkError(
                "Unable to connect to Google Gemini services. Please verify your internet connection."
            )

        return AIEngineError(f"Gemini API error: {str(exc)}")

    def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.0,
        max_retries: int = 3
    ) -> str:
        """
        Calls Gemini to generate content with exponential backoff retries.
        Temperature defaults to 0.0 for deterministic, un-hallucinated facts.
        """
        if not self.is_configured():
            raise MissingKeyError(
                "No Gemini API key configured. The assistant is operating in Lexical Fallback Mode."
            )

        if self._client is None:
            self._init_client()
            if self._client is None:
                raise AIEngineError("Failed to initialize Google GenAI SDK client.")

        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=1024,
        )
        if system_instruction:
            config.system_instruction = system_instruction

        last_error = None
        for attempt in range(max_retries):
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                if response and response.text:
                    return response.text.strip()
                return "No response text returned by the model."
            except Exception as e:
                classified = self.classify_error(e)
                last_error = classified

                # Do not retry on invalid key
                if isinstance(classified, InvalidKeyError):
                    raise classified

                # Wait with backoff before next attempt
                if attempt < max_retries - 1:
                    time.sleep(1.5 * (2 ** attempt))

        raise last_error if last_error else AIEngineError("Unknown generation failure.")

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generates semantic text embeddings using Gemini embed_content."""
        if not self.is_configured() or self._client is None:
            return None

        try:
            # Clean and truncate text if too long
            cleaned = text.strip()[:2000]
            if not cleaned:
                return None

            response = self._client.models.embed_content(
                model="text-embedding-004",
                contents=cleaned,
            )

            if hasattr(response, "embedding") and response.embedding:
                # response.embedding.values or list
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
