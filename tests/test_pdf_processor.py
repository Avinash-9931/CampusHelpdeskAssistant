"""
Unit tests for core/pdf_processor.py.
Validates file extension and magic-byte checks, empty files, size limits, duplicate hashing,
text cleaning, and error classification for corrupted, encrypted, and scanned PDFs.
"""

import io
import pytest
from pypdf import PdfWriter

from core.pdf_processor import (
    validate_upload,
    extract_pdf,
    clean_text,
    file_hash,
    process_document,
    PageData,
    ProcessedDocument,
    PDFProcessor,
    InvalidFileTypeError,
    EmptyFileError,
    EmptyPDFError,
    FileTooLargeError,
    DuplicateFileError,
    PasswordProtectedPDFError,
    EncryptedPDFError,
    CorruptedPDFError,
    CorruptPDFError,
    ScannedPDFError
)


def create_minimal_pdf_bytes(text: str = "Sample policy text", encrypted: bool = False, password: str = "") -> bytes:
    """Helper to generate in-memory valid PDF bytes with magic bytes header."""
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    
    if encrypted:
        writer.encrypt(password)

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_validate_upload_invalid_extension():
    """Rejects non-pdf extensions."""
    with pytest.raises(InvalidFileTypeError) as exc:
        validate_upload("syllabus.docx", b"some bytes")
    assert "Unsupported file format" in str(exc.value)


def test_validate_upload_invalid_magic_bytes():
    """Rejects files with .pdf extension but missing %PDF magic bytes."""
    corrupt_header_bytes = b"NOT_A_REAL_PDF_STREAM"
    with pytest.raises(InvalidFileTypeError) as exc:
        validate_upload("fake.pdf", corrupt_header_bytes)
    assert "valid PDF magic bytes" in str(exc.value)


def test_validate_upload_empty_file():
    """Rejects 0-byte files."""
    with pytest.raises(EmptyFileError) as exc:
        validate_upload("empty.pdf", b"")
    assert "empty (0 bytes)" in str(exc.value)


def test_validate_upload_too_large():
    """Rejects files exceeding MAX_UPLOAD_MB."""
    huge_bytes = b"%PDF-" + b"0" * (16 * 1024 * 1024)  # 16 MB
    with pytest.raises(FileTooLargeError) as exc:
        validate_upload("oversized.pdf", huge_bytes)
    assert "exceeds maximum limit" in str(exc.value)


def test_validate_upload_duplicate_hash():
    """Detects duplicate files via SHA-256 hash."""
    valid_bytes = create_minimal_pdf_bytes()
    f_hash = file_hash(valid_bytes)
    existing_hashes = {f_hash}
    with pytest.raises(DuplicateFileError) as exc:
        validate_upload("duplicate.pdf", valid_bytes, existing_hashes=existing_hashes)
    assert "Duplicate SHA-256 hash" in str(exc.value)


def test_validate_upload_valid_pdf():
    """Accepts valid PDF and returns metadata dictionary."""
    valid_bytes = create_minimal_pdf_bytes()
    meta = validate_upload("handbook.pdf", valid_bytes)
    assert meta["valid"] is True
    assert meta["filename"] == "handbook.pdf"
    assert len(meta["hash"]) == 64
    assert meta["size_bytes"] == len(valid_bytes)


def test_clean_text_normalizes_formatting():
    """Tests whitespace normalization, hyphen reconnection, and paragraph preservation."""
    raw = "The   uni-\nversity  will   re-open.\n\n\n\nNext  paragraph."
    cleaned = clean_text(raw)
    assert "university" in cleaned
    assert "The university will re-open." in cleaned
    assert "\n\nNext paragraph." in cleaned


def test_extract_pdf_corrupted_bytes():
    """Handles corrupted PDF stream with CorruptedPDFError."""
    corrupt_bytes = b"%PDF-1.4\nCorrupted binary payload with broken xref table"
    with pytest.raises((CorruptedPDFError, CorruptPDFError)):
        extract_pdf(corrupt_bytes, "broken.pdf")


def test_extract_pdf_encrypted():
    """Handles password-protected PDF with PasswordProtectedPDFError."""
    enc_bytes = create_minimal_pdf_bytes(encrypted=True, password="secret_pass_123")
    with pytest.raises((PasswordProtectedPDFError, EncryptedPDFError)):
        extract_pdf(enc_bytes, "locked.pdf")


def test_extract_pdf_scanned_document():
    """Detects blank or scanned document with no extractable text layer."""
    blank_bytes = create_minimal_pdf_bytes()
    with pytest.raises(ScannedPDFError) as exc:
        extract_pdf(blank_bytes, "scanned_doc.pdf")
    assert "scanned image" in str(exc.value) or "OCR is not currently enabled" in str(exc.value)


def test_process_document_success():
    """Validates full end-to-end document processing returning ProcessedDocument."""
    # Use demo PDF which has extractable text
    from config import settings
    demo_pdf_path = settings.DEMO_DIR / "university_policy_demo.pdf"
    if not demo_pdf_path.exists():
        from data.demo.generate_demo_pdf import build_pdf
        build_pdf()

    with open(demo_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    doc = process_document(pdf_bytes, filename="policy_demo.pdf")
    assert isinstance(doc, ProcessedDocument)
    assert doc.filename == "policy_demo.pdf"
    assert doc.page_count >= 1
    assert len(doc.pages) == doc.page_count
    assert doc.pages[0].page_number == 1
    assert doc.status == "Processed"
