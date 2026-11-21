"""
PDF Processor for AI-Powered Campus Helpdesk Assistant.
Validates, inspects, extracts, cleans text per page, and detects errors.
"""

import io
import re
import hashlib
from typing import List, Dict, Any, Optional
import pypdf
from config import settings


class PDFProcessingError(Exception):
    """Base exception for PDF processing errors."""
    pass


class InvalidFileTypeError(PDFProcessingError):
    """Raised when uploaded file is not a valid PDF."""
    pass


class EmptyFileError(PDFProcessingError):
    """Raised when uploaded file has 0 bytes."""
    pass


class FileTooLargeError(PDFProcessingError):
    """Raised when file exceeds size limit."""
    pass


class DuplicateFileError(PDFProcessingError):
    """Raised when file content hash matches an already processed file."""
    pass


class EncryptedPDFError(PDFProcessingError):
    """Raised when PDF is password protected or encrypted."""
    pass


class CorruptPDFError(PDFProcessingError):
    """Raised when PDF structure is corrupt or unreadable."""
    pass


class ScannedPDFError(PDFProcessingError):
    """Raised when PDF has no extractable text layer (likely scanned)."""
    pass


class PDFProcessor:
    """Handles PDF validation, security checks, and page-level text extraction."""

    @staticmethod
    def compute_hash(data: bytes) -> str:
        """Computes SHA-256 hash of raw file bytes for deduplication."""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """
        Cleans extracted text by normalizing line breaks, hyphens, and whitespace.
        Preserves punctuation and paragraph structure.
        """
        if not raw_text:
            return ""

        # Normalize unicode ligatures and unusual quotes
        text = raw_text.replace("\ufb01", "fi").replace("\ufb02", "fl")
        text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")

        # Fix hyphenated words broken across line wraps (e.g., 'uni-\nversity' -> 'university')
        text = re.sub(r'(\b\w+)-\n(\w+\b)', r'\1\2', text)

        # Normalize diverse newline representations
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Collapse excessive inline spaces and tabs (preserving single spaces)
        text = re.sub(r'[ \t]+', ' ', text)

        # Collapse more than two consecutive newlines into double newlines (paragraphs)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def validate_file(
        self,
        file_bytes: bytes,
        filename: str,
        existing_hashes: Optional[set] = None
    ) -> Dict[str, Any]:
        """
        Pre-flight validation on file properties.
        Raises specific human-readable exceptions on failure.
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

        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise FileTooLargeError(
                f"File '{filename}' ({file_size / (1024*1024):.2f} MB) exceeds maximum limit "
                f"of {settings.MAX_UPLOAD_SIZE_MB} MB."
            )

        file_hash = self.compute_hash(file_bytes)
        if existing_hashes and file_hash in existing_hashes:
            raise DuplicateFileError(
                f"The document '{filename}' is identical to an already indexed file (Duplicate SHA-256 hash)."
            )

        return {
            "filename": filename,
            "size_bytes": file_size,
            "hash": file_hash,
            "valid": True
        }

    def extract_pages(self, file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Extracts cleaned text from each page in the PDF.
        Tracks 1-indexed page numbers.
        Detects encrypted, corrupted, or scanned PDFs.
        """
        try:
            stream = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(stream)
        except Exception as e:
            raise CorruptPDFError(
                f"Failed to read '{filename}'. The file structure appears corrupted or invalid: {str(e)}"
            )

        if reader.is_encrypted:
            try:
                # Attempt empty password decryption
                decrypted = reader.decrypt("")
                if not decrypted:
                    raise EncryptedPDFError(
                        f"Document '{filename}' is password-protected. Please remove password encryption."
                    )
            except Exception:
                raise EncryptedPDFError(
                    f"Document '{filename}' is password-protected or encrypted. Decryption failed."
                )

        total_pages = len(reader.pages)
        if total_pages == 0:
            raise CorruptPDFError(f"Document '{filename}' contains 0 pages.")

        pages_data = []
        total_extracted_chars = 0

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            try:
                raw_text = page.extract_text() or ""
            except Exception as e:
                raw_text = ""

            cleaned = self.clean_text(raw_text)
            char_count = len(cleaned)
            total_extracted_chars += char_count

            pages_data.append({
                "filename": filename,
                "page": page_num,
                "text": cleaned,
                "char_count": char_count
            })

        # Scanned PDF detection: if total extracted characters across all pages is minimal
        if total_extracted_chars < 30:
            raise ScannedPDFError(
                f"Document '{filename}' has no extractable text layer (extracted {total_extracted_chars} characters across {total_pages} pages). "
                f"This document appears to be a scanned image. Optical Character Recognition (OCR) is not currently enabled."
            )

        return pages_data
