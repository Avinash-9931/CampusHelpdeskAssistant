"""
Centralized Domain Exceptions for AI-Powered Campus Helpdesk Assistant.
Provides a clear exception hierarchy for PDF processing, retrieval, AI engine,
prompt evaluation, and response guard checks.
"""

# ==============================================================================
# Base Application Exception
# ==============================================================================
class CampusHelpdeskError(Exception):
    """Base exception for all Campus Helpdesk Assistant domain errors."""
    def __init__(self, message: str, user_friendly_message: str = ""):
        super().__init__(message)
        self.message = message
        self.user_friendly_message = user_friendly_message or message


# ==============================================================================
# PDF Processing Exceptions
# ==============================================================================
class PDFProcessingError(CampusHelpdeskError):
    """Base exception for PDF parsing and upload validation errors."""
    pass


class InvalidFileTypeError(PDFProcessingError):
    """Raised when uploaded file is not a PDF or lacks %PDF magic bytes."""
    pass


class EmptyFileError(PDFProcessingError):
    """Raised when uploaded file has 0 bytes."""
    pass


class EmptyPDFError(EmptyFileError):
    """Raised when PDF document contains 0 pages."""
    pass


class FileTooLargeError(PDFProcessingError):
    """Raised when file exceeds size limit (MAX_UPLOAD_MB)."""
    pass


class DuplicateFileError(PDFProcessingError):
    """Raised when file content SHA-256 matches an already processed file."""
    pass


class PasswordProtectedPDFError(PDFProcessingError):
    """Raised when PDF is password protected or encrypted."""
    pass


class EncryptedPDFError(PasswordProtectedPDFError):
    """Backward-compatible alias for PasswordProtectedPDFError."""
    pass


class CorruptedPDFError(PDFProcessingError):
    """Raised when PDF structure is corrupt or unreadable."""
    pass


class ScannedPDFError(PDFProcessingError):
    """Raised when PDF has no extractable text layer (scanned document)."""
    pass


# ==============================================================================
# AI Engine Exceptions
# ==============================================================================
class AIEngineError(CampusHelpdeskError):
    """Base exception for LLM generation and embedding errors."""
    pass


class MissingKeyError(AIEngineError):
    """Raised when GEMINI_API_KEY is not configured."""
    pass


class InvalidKeyError(AIEngineError):
    """Raised when GEMINI_API_KEY is rejected by Google GenAI."""
    pass


class RateLimitError(AIEngineError):
    """Raised when rate limit or quota is exceeded."""
    pass


class QuotaExceededError(RateLimitError):
    """Backward-compatible alias for RateLimitError."""
    pass


class NetworkFailureError(AIEngineError):
    """Raised on connection issues or DNS resolution failure."""
    pass


class NetworkError(NetworkFailureError):
    """Backward-compatible alias for NetworkFailureError."""
    pass


class ModelTimeoutError(AIEngineError):
    """Raised when API generation times out."""
    pass


class SafetyBlockError(AIEngineError):
    """Raised when output is blocked by safety filters."""
    pass


# ==============================================================================
# Retrieval & Indexing Exceptions
# ==============================================================================
class RetrievalError(CampusHelpdeskError):
    """Base exception for index search and loading failures."""
    pass


class CorruptedIndexError(RetrievalError):
    """Raised when persistent index file is corrupted."""
    pass


# ==============================================================================
# Response Guard Exceptions
# ==============================================================================
class ResponseGuardError(CampusHelpdeskError):
    """Base exception for response guard validation."""
    pass


class UnverifiedCitationError(ResponseGuardError):
    """Raised when model cites a document or page not present in retrieved context."""
    pass
