"""
Unit tests for core/retriever.py.
Tests lexical indexing, score thresholding, persistent storage, and document deletion.
"""

import pytest
from core.retriever import DocumentRetriever


@pytest.fixture
def empty_retriever(tmp_path, monkeypatch):
    """Provides a DocumentRetriever isolated to temporary storage."""
    kb_file = tmp_path / "test_kb.json"
    emb_file = tmp_path / "test_emb.npy"
    monkeypatch.setattr("config.settings.KNOWLEDGE_BASE_FILE", kb_file)
    monkeypatch.setattr("config.settings.EMBEDDINGS_CACHE_FILE", emb_file)
    retriever = DocumentRetriever()
    retriever.clear_all()
    return retriever


@pytest.fixture
def populated_retriever(empty_retriever):
    """Provides a retriever pre-loaded with mock university policy chunks."""
    pages = [
        {"page": 1, "text": "Page 1 content", "char_count": 14},
        {"page": 2, "text": "Page 2 content", "char_count": 14}
    ]
    chunks = [
        {
            "chunk_id": "policy_p1_c1",
            "filename": "policy.pdf",
            "page": 1,
            "text": "Every enrolled undergraduate student must maintain a minimum attendance of 75% in each registered course to be eligible to sit for the final examination.",
            "char_count": 156
        },
        {
            "chunk_id": "policy_p2_c1",
            "filename": "policy.pdf",
            "page": 2,
            "text": "The late course registration fee is strictly $50 if submitted within the first 5 working days of the semester.",
            "char_count": 110
        },
        {
            "chunk_id": "policy_p2_c2",
            "filename": "policy.pdf",
            "page": 2,
            "text": "Undergraduate students may borrow up to 4 library books for 14 calendar days from the Central University Library.",
            "char_count": 114
        }
    ]
    empty_retriever.add_document(
        filename="policy.pdf",
        file_hash="dummy_hash_123456",
        size_bytes=1024,
        pages_data=pages,
        chunks=chunks
    )
    return empty_retriever


def test_empty_retriever_search(empty_retriever):
    """Searching an empty knowledge base returns no results and False context signal."""
    results, has_context, method = empty_retriever.search("attendance requirements")
    assert results == []
    assert has_context is False
    assert "No Documents" in method


def test_populated_retriever_relevant_search(populated_retriever):
    """Lexical retrieval matches relevant terms and flags has_relevant_context=True."""
    results, has_context, method = populated_retriever.search("What is the attendance percentage required?")
    assert has_context is True
    assert len(results) > 0
    assert "Lexical Retrieval" in method
    assert results[0]["page"] == 1
    assert "75%" in results[0]["text"]
    assert results[0]["score"] > 0.15


def test_out_of_domain_query_threshold(populated_retriever):
    """Out-of-domain queries fail the similarity threshold and return has_relevant_context=False."""
    # Query with zero vocabulary overlap
    results, has_context, method = populated_retriever.search("quantum mechanics astronaut spaceship propulsion", threshold=0.15)
    assert has_context is False


def test_delete_document(populated_retriever):
    """Deleting a document removes its chunks and resets index."""
    stats_before = populated_retriever.get_stats()
    assert stats_before["document_count"] == 1
    assert stats_before["chunk_count"] == 3

    success = populated_retriever.delete_document("policy.pdf")
    assert success is True

    stats_after = populated_retriever.get_stats()
    assert stats_after["document_count"] == 0
    assert stats_after["chunk_count"] == 0

    results, has_context, method = populated_retriever.search("attendance")
    assert results == []
    assert has_context is False
