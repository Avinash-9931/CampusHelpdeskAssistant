"""
Integration and behavior tests for core/chatbot.py.
Validates input sanitization, zero-document handling, no-context refusal (asserting LLM not called),
fallback mode without API key, citation metadata grounding, API error degradation, and query expansion.
"""

from unittest.mock import MagicMock
import pytest

from core.chatbot import ChatbotController, ChatResult
from core.retriever import KnowledgeBase
from core.text_chunker import TextChunk
from core.pdf_processor import ProcessedDocument, PageData
from core.prompt_manager import PromptManager
from core.ai_engine import AIEngine, UnknownAPIError


@pytest.fixture
def mock_kb(tmp_path, monkeypatch):
    """Provides a KnowledgeBase populated with multi-page mock policy chunks."""
    kb_file = tmp_path / "chat_test_kb.json"
    emb_file = tmp_path / "chat_test_emb.npy"
    monkeypatch.setattr("config.settings.KNOWLEDGE_BASE_FILE", kb_file)
    monkeypatch.setattr("config.settings.EMBEDDINGS_CACHE_FILE", emb_file)

    kb = KnowledgeBase()
    kb.clear_all()

    doc = ProcessedDocument(
        filename="university_policy_demo.pdf",
        hash="test_hash_123",
        page_count=3,
        pages=[PageData(1, "", 0), PageData(2, "", 0), PageData(3, "", 0)]
    )
    chunks = [
        TextChunk(
            chunk_id="demo_p1_c1",
            filename="university_policy_demo.pdf",
            page=1,
            text="Every enrolled undergraduate student must maintain a minimum attendance of 75% in each registered course to be eligible to sit for the End-Semester Final Examination."
        ),
        TextChunk(
            chunk_id="demo_p2_c1",
            filename="university_policy_demo.pdf",
            page=2,
            text="The late course registration fee is strictly $50 if submitted within the first 5 working days after the semester commences."
        ),
        TextChunk(
            chunk_id="demo_p3_c1",
            filename="university_policy_demo.pdf",
            page=3,
            text="Central University Library is located at Knowledge Tower, Level 1. Undergraduate students may borrow up to 4 books for 14 calendar days."
        )
    ]
    kb.add_document(doc, chunks)
    return kb


def test_empty_input(mock_kb):
    """Rejects empty string or whitespace with error mode, without calling LLM."""
    mock_ai = MagicMock(spec=AIEngine)
    bot = ChatbotController(retriever=mock_kb, ai_engine=mock_ai)

    result = bot.ask("   ")
    assert isinstance(result, ChatResult)
    assert result.mode == "error"
    assert "Please enter a valid question" in result.answer
    assert result.sources == []
    mock_ai.generate.assert_not_called()


def test_no_documents(tmp_path, monkeypatch):
    """When knowledge base has no documents, returns 'upload documents first' notice without calling LLM."""
    kb_file = tmp_path / "empty_kb.json"
    emb_file = tmp_path / "empty_emb.npy"
    monkeypatch.setattr("config.settings.KNOWLEDGE_BASE_FILE", kb_file)
    monkeypatch.setattr("config.settings.EMBEDDINGS_CACHE_FILE", emb_file)

    empty_kb = KnowledgeBase()
    empty_kb.clear_all()

    mock_ai = MagicMock(spec=AIEngine)
    bot = ChatbotController(retriever=empty_kb, ai_engine=mock_ai)

    result = bot.ask("What is the attendance rule?")
    assert result.mode == "no_context"
    assert "No official university documents are currently indexed" in result.answer
    assert result.sources == []
    mock_ai.generate.assert_not_called()


def test_no_context_refusal_assert_llm_not_called(mock_kb):
    """
    Critical non-negotiable rule:
    When inquiry is out of scope / score below threshold, return refusal
    WITH mode 'no_context' and assert the LLM was NOT called.
    """
    mock_ai = MagicMock(spec=AIEngine)
    mock_ai.is_available.return_value = True

    bot = ChatbotController(retriever=mock_kb, ai_engine=mock_ai)

    result = bot.ask("What is the fee for the campus swimming pool pass?")
    assert result.mode == "no_context"
    assert "cannot verify" in result.answer.lower()
    assert result.sources == []
    # Verify LLM was NOT called
    mock_ai.generate.assert_not_called()


def test_fallback_mode_without_key(mock_kb):
    """When no API key is available, returns mode 'fallback' with retrieved passages as evidence."""
    ai_engine = AIEngine(api_key="")  # No key
    bot = ChatbotController(retriever=mock_kb, ai_engine=ai_engine)

    result = bot.ask("What is the minimum attendance requirement?")
    assert result.mode == "fallback"
    assert "AI generation unavailable" in result.answer
    assert "75%" in result.answer
    assert len(result.sources) > 0
    assert result.sources[0].page == 1
    assert result.sources[0].filename == "university_policy_demo.pdf"


def test_citations_match_chunk_metadata(mock_kb):
    """Asserts citations are constructed strictly from retrieved chunk metadata."""
    ai_engine = AIEngine(api_key="")
    bot = ChatbotController(retriever=mock_kb, ai_engine=ai_engine)

    result = bot.ask("What are the library borrowing limits?")
    assert len(result.sources) > 0
    citation = result.sources[0]
    assert citation.filename == "university_policy_demo.pdf"
    assert citation.page == 3
    assert "4" in citation.snippet
    assert citation.score >= 0.13


def test_api_error_degrades_gracefully(mock_kb):
    """When Gemini throws an API error, gracefully degrades to fallback mode with error noted."""
    mock_ai = MagicMock(spec=AIEngine)
    mock_ai.is_available.return_value = True
    mock_ai.generate.side_effect = UnknownAPIError("Google API quota exceeded 429")

    bot = ChatbotController(retriever=mock_kb, ai_engine=mock_ai)

    result = bot.ask("What is the late registration fee?")
    assert result.mode == "fallback"
    assert "AI generation encountered an error" in result.answer
    assert "Google API quota exceeded 429" in result.answer
    assert len(result.sources) > 0
    assert result.sources[0].page == 2
    assert "$50" in result.answer


def test_gemini_mode_when_key_configured(mock_kb):
    """When Gemini is available and succeeds, returns mode 'gemini' and model answer."""
    mock_ai = MagicMock(spec=AIEngine)
    mock_ai.is_available.return_value = True
    mock_ai.generate.return_value = "According to university policy, minimum attendance is 75% [Source: university_policy_demo.pdf, Page: 1]."

    bot = ChatbotController(retriever=mock_kb, ai_engine=mock_ai)

    result = bot.ask("What is the attendance rule?")
    assert result.mode == "gemini"
    assert "75%" in result.answer
    assert len(result.sources) > 0
    assert result.sources[0].page == 1
    mock_ai.generate.assert_called_once()


def test_followup_query_expansion(mock_kb):
    """Follow-up query 'Where is that office located?' is rewritten with previous question context."""
    bot = ChatbotController(retriever=mock_kb, ai_engine=AIEngine(api_key=""))
    history = [
        {"role": "user", "content": "Tell me about the central library books."},
        {"role": "assistant", "content": "You can borrow 4 books."}
    ]
    rewritten, rewriter = bot.rewrite_followup("Where is that office located?", history)
    assert rewriter in ("heuristic", "llm")
    assert "library" in rewritten.lower() or "books" in rewritten.lower()


def test_department_referral_classification(mock_kb):
    """Verifies accurate departmental routing for fee, exam, and library questions."""
    bot = ChatbotController(retriever=mock_kb, ai_engine=AIEngine(api_key=""))
    assert "Accounts & Finance Desk" in bot.get_department_referral("How do I pay tuition fees?")
    assert "Controller of Examinations" in bot.get_department_referral("Where do I apply for exam revaluation?")
    assert "Central University Library" in bot.get_department_referral("Can I borrow a library book?")
