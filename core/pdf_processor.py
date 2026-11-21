"""
PDF Processor for AI-Powered Campus Helpdesk Assistant.
Validates uploads, extracts per-page text, cleans content, and classifies errors.
"""

import io
import re
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pypdf

from config import settings


# ==============================================================================
# Domain Exceptions
# ==============================================================================
class PDFProcessingError(Exception):
    """Base exception for PDF processing errors."""
    pass


class InvalidFileTypeError(PDFProcessingError):
    """Raised when uploaded file is not a valid PDF or fails magic-byte verification."""
    pass


class EmptyFileError(PDFProcessingError):
    """Raised when uploaded file has 0 bytes."""
    pass


class EmptyPDFError(EmptyFileError):
    """Raised when PDF document contains 0 pages."""
    pass


class FileTooLargeError(PDFProcessingError):
    """Raised when file exceeds size limit."""
    pass


class DuplicateFileError(PDFProcessingError):
    """Raised when file content hash matches an already processed file."""
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


class CorruptPDFError(CorruptedPDFError):
    """Backward-compatible alias for CorruptedPDFError."""
    pass


class ScannedPDFError(PDFProcessingError):
    """Raised when PDF has no extractable text layer (likely scanned)."""
    pass


# ==============================================================================
# Data Structures
# ==============================================================================
@dataclass
class PageData:
    """Represents extracted text and metadata for a single PDF page."""
    page_number: int
    text: str
    char_count: int

    def __getitem__(self, item: str) -> Any:
        # Compatibility with legacy dict-style access
        if item == "page":
            return self.page_number
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return self[item]
        except KeyError:
            return default


@dataclass
class ProcessedDocument:
    """Represents a validated and processed PDF document."""
    filename: str
    hash: str
    page_count: int
    pages: List[PageData] = field(default_factory=list)
    status: str = "Processed"
    error: Optional[str] = None


# ==============================================================================
# Utility & Processing Functions
# ==============================================================================
def file_hash(file_bytes: bytes) -> str:
    """
    Computes SHA-256 hash of raw file bytes for cryptographic deduplication.
    
    Args:
        file_bytes: Raw binary content of the file.
        
    Returns:
        Hexadecimal SHA-256 digest string.
    """
    return hashlib.sha256(file_bytes).hexdigest()


def clean_text(raw_text: str) -> str:
    """
    Cleans extracted text by normalizing line breaks, hyphens, and whitespace.
    Preserves paragraph breaks and punctuation.
    
    Args:
        raw_text: Raw string extracted from a PDF stream.
        
    Returns:
        Cleaned, normalized text string.
    """
    if not raw_text:
        return ""

    # Normalize unicode ligatures and unusual quotes
    text = raw_text.replace("\ufb01", "fi").replace("\ufb02", "fl")
    text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")

    # Fix hyphenated words broken across line wraps (e.g. 'uni-\nversity' -> 'university')
    text = re.sub(r'(\b\w+)-\n(\w+\b)', r'\1\2', text)

    # Normalize diverse newline representations
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse horizontal spaces and tabs while keeping newlines
    text = re.sub(r'[ \t]+', ' ', text)

    # Collapse 3+ consecutive newlines into standard double-newline paragraph breaks
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def validate_upload(
    filename: str,
    file_bytes: bytes,
    existing_hashes: Optional[set] = None
) -> Dict[str, Any]:
    """
    Pre-flight validation on uploaded file:
    1. Checks file extension is .pdf
    2. Verifies PDF magic bytes (%PDF)
    3. Checks non-empty (0 bytes)
    4. Checks size limit (MAX_UPLOAD_BYTES)
    5. Checks duplicate SHA-256 hash if existing_hashes provided.
    
    Args:
        filename: Name of the uploaded file.
        file_bytes: Raw binary content.
        existing_hashes: Optional set of known file hashes.
        
    Returns:
        Dictionary with validation metadata: filename, size_bytes, hash, valid.
        
    Raises:
        InvalidFileTypeError, EmptyFileError, FileTooLargeError, DuplicateFileError.
    """
    if not filename.lower().endswith(".pdf"):
        raise InvalidFileTypeError(
            f"Unsupported file format '{filename}'. Only official PDF documents are accepted."
        )

    file_size = len(file_bytes)
    if file_size == 0:
        raise EmptyFileError(
            f"The file '{filename}' is empty (0 bytes). Please upload a valid document."
        )

    # Magic-bytes check for PDF: %PDF (hex 25 50 44 46) must appear in the first 1024 bytes
    if not file_bytes[:1024].startswith(b"%PDF-") and b"%PDF" not in file_bytes[:1024]:
        raise InvalidFileTypeError(
            f"File '{filename}' does not have valid PDF magic bytes. Only valid PDF files are supported."
        )

    if file_size > settings.MAX_UPLOAD_BYTES:
        raise FileTooLargeError(
            f"File '{filename}' ({file_size / (1024*1024):.2f} MB) exceeds maximum limit "
            f"of {settings.MAX_UPLOAD_MB} MB."
        )

    f_hash = file_hash(file_bytes)
    if existing_hashes and f_hash in existing_hashes:
        raise DuplicateFileError(
            f"The document '{filename}' is identical to an already indexed file (Duplicate SHA-256 hash)."
        )

    return {
        "filename": filename,
        "size_bytes": file_size,
        "hash": f_hash,
        "valid": True
    }


def extract_pdf(file_bytes: bytes, filename: str = "document.pdf") -> List[PageData]:
    """
    Extracts text per page from PDF bytes.
    Detects and raises distinct exceptions for:
    - Corrupted PDF structure
    - Password-protected/encrypted PDF
    - Scanned/image-only PDF (no extractable text)
    - Empty document (0 pages)
    
    Args:
        file_bytes: Binary PDF content.
        filename: Name of document for error reporting.
        
    Returns:
        List of PageData instances.
        
    Raises:
        CorruptedPDFError, PasswordProtectedPDFError, EmptyPDFError, ScannedPDFError.
    """
    try:
        stream = io.BytesIO(file_bytes)
        reader = pypdf.PdfReader(stream)
    except Exception as e:
        raise CorruptedPDFError(
            f"Failed to read '{filename}'. The file structure appears corrupted or invalid: {str(e)}"
        )

    if reader.is_encrypted:
        try:
            # Attempt empty password decryption
            decrypted = reader.decrypt("")
            if not decrypted:
                raise PasswordProtectedPDFError(
                    f"Document '{filename}' is password-protected. Please remove password encryption."
                )
        except Exception:
            raise PasswordProtectedPDFError(
                f"Document '{filename}' is password-protected or encrypted. Decryption failed."
            )

    total_pages = len(reader.pages)
    if total_pages == 0:
        raise EmptyPDFError(f"Document '{filename}' contains 0 pages.")

    pages_data: List[PageData] = []
    total_extracted_chars = 0

    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        try:
            raw_text = page.extract_text() or ""
        except Exception:
            raw_text = ""

        cleaned = clean_text(raw_text)
        char_count = len(cleaned)
        total_extracted_chars += char_count

        pages_data.append(PageData(
            page_number=page_num,
            text=cleaned,
            char_count=char_count
        ))

    # Detect scanned document condition: very few extractable characters across all pages
    if total_extracted_chars < 30:
        raise ScannedPDFError(
            f"Document '{filename}' has no extractable text layer (extracted {total_extracted_chars} characters across {total_pages} pages). "
            f"This document appears to be a scanned image. Optical Character Recognition (OCR) is not currently enabled."
        )

    return pages_data


def process_document(
    file_bytes: bytes,
    filename: str,
    existing_hashes: Optional[set] = None
) -> ProcessedDocument:
    """
    Orchestrates full PDF processing pipeline:
    Validates, extracts, and returns a ProcessedDocument.
    """
    validation = validate_upload(filename, file_bytes, existing_hashes=existing_hashes)
    pages = extract_pdf(file_bytes, filename=filename)
    return ProcessedDocument(
        filename=filename,
        hash=validation["hash"],
        page_count=len(pages),
        pages=pages,
        status="Processed"
    )


class PDFProcessor:
    """Class interface for PDF operations, maintaining backward compatibility."""

    @staticmethod
    def compute_hash(data: bytes) -> str:
        return file_hash(data)

    @staticmethod
    def clean_text(raw_text: str) -> str:
        return clean_text(raw_text)

    def validate_file(
        self,
        file_bytes: bytes,
        filename: str,
        existing_hashes: Optional[set] = None
    ) -> Dict[str, Any]:
        return validate_upload(filename, file_bytes, existing_hashes=existing_hashes)

    def extract_pages(self, file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        pages = extract_pdf(file_bytes, filename=filename)
        return [
            {
                "filename": filename,
                "page": p.page_number,
                "text": p.text,
                "char_count": p.char_count
            }
            for p in pages
        ]

    def process(self, file_bytes: bytes, filename: str) -> ProcessedDocument:
        return process_document(file_bytes, filename)
