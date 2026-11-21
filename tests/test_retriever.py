"""
Unit tests for core/retriever.py.
Validates KnowledgeBase ranking, page metadata preservation, relevance thresholding,
persistence round-trip, document deletion, and active method reporting.
"""

import pytest
from core.retriever import KnowledgeBase, RetrievedChunk
from core.text_chunker import TextChunk
from core.pdf_processor import ProcessedDocument, PageData


@pytest.fixture
def empty_kb(tmp_path, monkeypatch):
    """Provides a KnowledgeBase isolated to temporary storage."""
    kb_file = tmp_path / "test_kb.json"
    emb_file = tmp_path / "test_emb.npy"
    monkeypatch.setattr("config.settings.KNOWLEDGE_BASE_FILE", kb_file)
    monkeypatch.setattr("config.settings.EMBEDDINGS_CACHE_FILE", emb_file)
    kb = KnowledgeBase()
    kb.clear_all()
    return kb


@pytest.fixture
def populated_kb(empty_kb):
    """Provides a KnowledgeBase populated with multi-page policy chunks."""
    doc = ProcessedDocument(
        filename="academic_handbook.pdf",
        hash="test_hash_abcdef",
        page_count=3,
        pages=[
            PageData(1, "Attendance rules page", 21),
            PageData(2, "Registration fees page", 22),
            PageData(3, "Library borrowing page", 22)
        ]
    )
    chunks = [
        TextChunk(
            chunk_id="academic_handbook_p1_c1",
            filename="academic_handbook.pdf",
            page=1,
            text="Every enrolled undergraduate student must maintain a minimum attendance of 75% in each registered course to be eligible to sit for the final examination."
        ),
        TextChunk(
            chunk_id="academic_handbook_p2_c1",
            filename="academic_handbook.pdf",
            page=2,
            text="The late course registration fee is strictly $50 if submitted within the first 5 working days of the semester."
        ),
        TextChunk(
            chunk_id="academic_handbook_p3_c1",
            filename="academic_handbook.pdf",
            page=3,
            text="Undergraduate students may borrow up to 4 library books for 14 calendar days from the Central University Library."
        )
    ]
    empty_kb.add_document(doc, chunks)
    return empty_kb


def test_correct_chunk_ranks_first(populated_kb):
    """Asserts that query about attendance ranks the attendance chunk first with top score."""
    results = populated_kb.search("What is the attendance percentage required?")
    assert len(results) > 0
    top_chunk = results[0]
    assert isinstance(top_chunk, RetrievedChunk)
    assert top_chunk.chunk.page == 1
    assert "75%" in top_chunk.chunk.text
    assert top_chunk.score >= 0.13


def test_page_metadata_preserved(populated_kb):
    """Asserts that each retrieved chunk retains its exact source filename and page number."""
    results = populated_kb.search("library book borrow limits")
    assert len(results) > 0
    top = results[0]
    assert top.chunk.filename == "academic_handbook.pdf"
    assert top.chunk.page == 3
    assert "4" in top.chunk.text


def test_threshold_returns_empty_for_unrelated_query(populated_kb):
    """When nothing clears MIN_RELEVANCE_SCORE, search returns empty list (meaning no relevant context)."""
    results = populated_kb.search("quantum mechanics astronaut planetary astrophysics propulsion")
    assert results == []


def test_persistence_round_trip(tmp_path, monkeypatch):
    """Asserts that documents and chunks persist to disk and reload accurately."""
    kb_file = tmp_path / "roundtrip_kb.json"
    emb_file = tmp_path / "roundtrip_emb.npy"
    monkeypatch.setattr("config.settings.KNOWLEDGE_BASE_FILE", kb_file)
    monkeypatch.setattr("config.settings.EMBEDDINGS_CACHE_FILE", emb_file)

    kb1 = KnowledgeBase()
    doc = ProcessedDocument(
        filename="rules.pdf",
        hash="hash_123",
        page_count=1,
        pages=[PageData(1, "Text", 4)]
    )
    chunks = [
        TextChunk("rules_p1_c1", "rules.pdf", 1, "Students must carry their university ID card at all times.")
    ]
    kb1.add_document(doc, chunks)

    # Instantiate new KnowledgeBase instance reading same files
    kb2 = KnowledgeBase()
    assert len(kb2.documents) == 1
    assert "rules.pdf" in kb2.documents
    assert len(kb2.chunks) == 1
    assert kb2.chunks[0].chunk_id == "rules_p1_c1"

    # Search works on reloaded instance
    results = kb2.search("university ID card")
    assert len(results) == 1
    assert results[0].chunk.page == 1


def test_delete_removes_chunks(populated_kb):
    """Asserts that deleting a document purges all of its chunks and resets the index."""
    stats_before = populated_kb.get_stats()
    assert stats_before["document_count"] == 1
    assert stats_before["chunk_count"] == 3

    removed = populated_kb.remove_document("academic_handbook.pdf")
    assert removed is True

    stats_after = populated_kb.get_stats()
    assert stats_after["document_count"] == 0
    assert stats_after["chunk_count"] == 0

    results = populated_kb.search("attendance")
    assert results == []


def test_active_method_label(populated_kb):
    """Asserts active_method returns exact expected name without mislabeling."""
    method = populated_kb.active_method()
    assert method == "TF-IDF lexical"
