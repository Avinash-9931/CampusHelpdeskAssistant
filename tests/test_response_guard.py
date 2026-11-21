"""
Unit tests for core/response_guard.py.
Validates extraction of citation patterns, detection of unverified citations,
stripping of hallucinated citations, and appending of verified disclosure notices.
"""

import pytest
from core.response_guard import (
    extract_citations_from_text,
    validate_and_guard_response,
)
from core.chatbot import SourceCitation
from core.text_chunker import TextChunk


def test_extract_citations_various_formats():
    """Tests extracting citations in multiple standard formats."""
    text = (
        "Students need 75% attendance [Source: policy.pdf, Page: 1]. "
        "Also refer to (academic_rules.pdf, Page 4) and [library_guide.pdf, p. 12]."
    )
    extracted = extract_citations_from_text(text)
    assert len(extracted) == 3
    
    # 1. policy.pdf, page 1
    assert extracted[0][1] == "policy.pdf"
    assert extracted[0][2] == 1
    
    # 2. academic_rules.pdf, page 4
    assert extracted[1][1] == "academic_rules.pdf"
    assert extracted[1][2] == 4
    
    # 3. library_guide.pdf, page 12
    assert extracted[2][1] == "library_guide.pdf"
    assert extracted[2][2] == 12


def test_response_guard_valid_citations_preserved():
    """Verifies that citations matching retrieved sources are retained unchanged."""
    valid_sources = [
        SourceCitation(filename="handbook.pdf", page=2, snippet="...", score=0.85)
    ]
    model_answer = "You may drop courses within 10 days [Source: handbook.pdf, Page: 2]."
    guarded_text, removed = validate_and_guard_response(model_answer, valid_sources)
    
    assert len(removed) == 0
    assert "[Source: handbook.pdf, Page: 2]" in guarded_text
    assert "Notice: Unverified citation" not in guarded_text


def test_response_guard_hallucinated_document_stripped():
    """Verifies that a citation to a non-existent document is removed and flagged."""
    valid_sources = [
        SourceCitation(filename="handbook.pdf", page=1, snippet="...", score=0.9)
    ]
    # Model hallucinated 'fake_catalog.pdf'
    model_answer = (
        "Graduation requires 120 credits [Source: fake_catalog.pdf, Page: 45]. "
        "Attendance is 75% [Source: handbook.pdf, Page: 1]."
    )
    guarded_text, removed = validate_and_guard_response(model_answer, valid_sources)
    
    assert len(removed) == 1
    assert removed[0]["filename"] == "fake_catalog.pdf"
    assert removed[0]["page"] == 45
    
    # Hallucinated citation should be replaced
    assert "[Source: fake_catalog.pdf, Page: 45]" not in guarded_text
    assert "[Unverified citation removed]" in guarded_text
    # Valid citation preserved
    assert "[Source: handbook.pdf, Page: 1]" in guarded_text
    # Notice appended
    assert "Notice: Unverified citation(s) removed" in guarded_text
    assert "fake_catalog.pdf" in guarded_text


def test_response_guard_hallucinated_page_stripped():
    """Verifies that a citation to a valid document but wrong page number is stripped."""
    valid_sources = [
        SourceCitation(filename="handbook.pdf", page=1, snippet="...", score=0.9)
    ]
    # Model cited page 99 which was not in retrieved chunks
    model_answer = "Library hours are 8am to 8pm [Source: handbook.pdf, Page: 99]."
    guarded_text, removed = validate_and_guard_response(model_answer, valid_sources)
    
    assert len(removed) == 1
    assert removed[0]["filename"] == "handbook.pdf"
    assert removed[0]["page"] == 99
    assert "[Source: handbook.pdf, Page: 99]" not in guarded_text
    assert "Notice: Unverified citation(s) removed" in guarded_text
