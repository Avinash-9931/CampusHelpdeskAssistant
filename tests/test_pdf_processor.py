"""
Unit tests for core/pdf_processor.py.
Validates file extension checks, size limits, duplicate detection, text cleaning,
and error classification for corrupted/encrypted/scanned files.
"""

import io
import pytest
from pypdf import PdfWriter

from core.pdf_processor import (
    PDFProcessor,
    InvalidFileTypeError,
    EmptyFileError,
    FileTooLargeError,
    DuplicateFileError,
    EncryptedPDFError,
    CorruptPDFError,
    ScannedPDFError
)


@pytest.fixture
def processor():
    return PDFProcessor()


def create_minimal_pdf_bytes(text: str = "Test university policy content", encrypted: bool = False, password: str = "") -> bytes:
    """Helper to generate in-memory valid PDF bytes."""
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    
    if encrypted:
        writer.encrypt(password)

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_validate_file_invalid_extension(processor):
    """Rejects non-pdf extensions."""
    with pytest.raises(InvalidFileTypeError) as exc:
        processor.validate_file(b"data", "handbook.docx")
    assert "Unsupported file format" in str(exc.value)


def test_validate_file_empty(processor):
    """Rejects 0-byte files."""
    with pytest.raises(EmptyFileError) as exc:
        processor.validate_file(b"", "empty.pdf")
    assert "empty (0 bytes)" in str(exc.value)


def test_validate_file_too_large(processor):
    """Rejects files over size limit."""
    huge_bytes = b"0" * (16 * 1024 * 1024)  # 16 MB
    with pytest.raises(FileTooLargeError) as exc:
        processor.validate_file(huge_bytes, "huge.pdf")
    assert "exceeds maximum limit" in str(exc.value)


def test_validate_file_duplicate_hash(processor):
    """Detects duplicate files via hash."""
    content = b"sample pdf bytes"
    h = processor.compute_hash(content)
    existing = {h}
    with pytest.raises(DuplicateFileError) as exc:
        processor.validate_file(content, "dup.pdf", existing_hashes=existing)
    assert "Duplicate SHA-256 hash" in str(exc.value)


def test_validate_file_success(processor):
    """Accepts valid PDF file metadata."""
    content = b"%PDF-1.4 minimal"
    res = processor.validate_file(content, "valid.pdf")
    assert res["valid"] is True
    assert res["filename"] == "valid.pdf"
    assert len(res["hash"]) == 64


def test_clean_text(processor):
    """Tests whitespace normalization and hyphen reconnection."""
    raw = "The  uni-\nversity   will   re-open.\n\n\n\nNext paragraph."
    cleaned = processor.clean_text(raw)
    assert "university" in cleaned
    assert "The university will re-open." in cleaned
    assert "\n\nNext paragraph." in cleaned


def test_extract_corrupt_pdf(processor):
    """Handles corrupt file gracefully with CorruptPDFError."""
    corrupt_bytes = b"not a valid pdf stream header"
    with pytest.raises(CorruptPDFError):
        processor.extract_pages(corrupt_bytes, "corrupt.pdf")


def test_extract_encrypted_pdf(processor):
    """Handles password-protected PDFs with EncryptedPDFError."""
    enc_bytes = create_minimal_pdf_bytes(encrypted=True, password="secret_password_123")
    with pytest.raises(EncryptedPDFError):
        processor.extract_pages(enc_bytes, "protected.pdf")


def test_extract_scanned_pdf(processor):
    """Detects blank or image-only scanned PDFs with ScannedPDFError."""
    blank_bytes = create_minimal_pdf_bytes()
    with pytest.raises(ScannedPDFError) as exc:
        processor.extract_pages(blank_bytes, "blank_scanned.pdf")
    assert "scanned image" in str(exc.value) or "OCR is not currently enabled" in str(exc.value)
