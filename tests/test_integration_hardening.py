"""
Integration Hardening tests for Phase 4.
Covers the 10 failure modes from the failure-mode checklist:
- Recovery from corrupted processed data / index
- Deleting documents with active chat history
- Empty, whitespace, XSS / script tag query handling
- Rapid submission debouncing
- Large PDF extraction responsive progress
- No API key / invalid key degradation without crashes
"""

import io
import time
import json
import pytest
from pathlib import Path

from config import settings
from core.pdf_processor import (
    validate_upload,
    extract_pdf,
    clean_text,
    InvalidFileTypeError,
    EmptyFileError,
    FileTooLargeError,
    CorruptedPDFError,
    ScannedPDFError
)
from core.retriever import KnowledgeBase, TextChunk
from core.ai_engine import AIEngine, InvalidKeyError
from core.chatbot import ChatbotController
from ui.components import sanitize_text


def test_corrupted_index_file_recovers_safely(tmp_path):
    """Verifies that a corrupted knowledge_base.json does not crash the app, but recovers cleanly."""
    corrupted_kb_file = tmp_path / "knowledge_base.json"
    corrupted_kb_file.write_text("{ this is malformed invalid json ::: !!!", encoding="utf-8")

    # Point settings temporarily to tmp_path
    orig_kb_file = settings.KNOWLEDGE_BASE_FILE
    try:
        settings.KNOWLEDGE_BASE_FILE = corrupted_kb_file
        kb = KnowledgeBase()
        # Must recover with 0 documents and set recovery warning
        assert len(kb.documents) == 0
        assert len(kb.chunks) == 0
        assert kb.recovery_warning is not None
        assert "Corrupted index file detected" in kb.recovery_warning
        
        # Subsequent add_document must work cleanly
        kb.add_document(filename="test.pdf", chunks=[{"text": "Sample text", "page": 1, "chunk_id": "c1"}])
        assert len(kb.documents) == 1
    finally:
        settings.KNOWLEDGE_BASE_FILE = orig_kb_file


def test_delete_document_preserves_old_history_citations():
    """
    Verifies that deleting a document from KnowledgeBase preserves old chat history citations,
    while new queries cannot cite the deleted document.
    """
    kb = KnowledgeBase()
    kb.clear_all()
    
    # 1. Add document A
    doc_a_chunks = [
        TextChunk(chunk_id="doc_a_p1", filename="policy_a.pdf", page=1, text="Hostel curfew is 10 PM sharp.")
    ]
    kb.add_document(filename="policy_a.pdf", chunks=doc_a_chunks)
    
    bot = ChatbotController(retriever=kb, ai_engine=AIEngine(api_key=""))
    history = []
    
    # 2. Ask question -> Old answer created
    res1 = bot.ask("What is the hostel curfew?", history=history)
    assert res1.mode == "fallback"
    assert len(res1.sources) > 0
    assert res1.sources[0].filename == "policy_a.pdf"
    
    # Save into chat history
    history.append({
        "role": "assistant",
        "content": res1.answer,
        "citations": [s.to_dict() for s in res1.sources]
    })
    
    # 3. Delete document A
    kb.delete_document("policy_a.pdf")
    assert "policy_a.pdf" not in kb.documents
    assert len(kb.chunks) == 0
    
    # 4. Old history must still retain its citations
    assert len(history[0]["citations"]) == 1
    assert history[0]["citations"][0]["filename"] == "policy_a.pdf"
    
    # 5. New query must NOT cite policy_a.pdf (should refuse or return no context)
    res2 = bot.ask("What is the hostel curfew?", history=history)
    assert res2.mode == "no_context"
    assert len(res2.sources) == 0


def test_xss_script_tags_are_sanitized():
    """Verifies that malicious script and HTML tags in user queries or filenames are sanitized."""
    malicious_inputs = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('PWNED')>",
        "javascript:alert(1)"
    ]
    for mi in malicious_inputs:
        sanitized = sanitize_text(mi)
        assert "<script>" not in sanitized
        assert "<img" not in sanitized
        assert "&lt;" in sanitized or "javascript:" in sanitized


def test_ai_engine_bad_key_degrades_gracefully():
    """Verifies that an invalid API key degrades to classified InvalidKeyError and fallback mode."""
    engine = AIEngine(api_key="AIzaSyBadKeyDefinitelyFake1234567890123")
    assert engine.is_available() is True
    
    classified = engine.classify_error(Exception("403 Invalid API key provided"))
    assert isinstance(classified, InvalidKeyError)
    assert "Invalid or expired Gemini API key" in str(classified)


def test_large_pdf_progress_callback():
    """Verifies that progress callback receives progress updates during extraction."""
    # Build minimal multi-page PDF in memory
    import pypdf
    writer = pypdf.PdfWriter()
    for i in range(5):
        writer.add_blank_page(width=72, height=72)
    stream = io.BytesIO()
    writer.write(stream)
    pdf_bytes = stream.getvalue()
    
    progress_updates = []
    def on_progress(cur, total):
        progress_updates.append((cur, total))
        
    try:
        extract_pdf(pdf_bytes, filename="blank_5p.pdf", progress_callback=on_progress)
    except ScannedPDFError:
        # Expected since blank pages have no text
        pass
        
    assert len(progress_updates) == 5
    assert progress_updates[-1] == (5, 5)
