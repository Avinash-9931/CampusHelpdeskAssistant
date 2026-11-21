"""
Unit tests for core/prompt_manager.py and prompt rules.
Validates template loading, delimiter wrapping, anti-hallucination constraints,
and prompt injection defense instructions in final_prompt.md.
"""

import pytest
from core.prompt_manager import PromptManager


@pytest.fixture
def prompt_mgr():
    return PromptManager()


def test_all_prompt_versions_exist(prompt_mgr):
    """Verifies that v1, v2, v3, and final prompt templates are loaded."""
    prompts = prompt_mgr.get_all_prompts()
    assert "v1" in prompts and len(prompts["v1"]) > 10
    assert "v2" in prompts and len(prompts["v2"]) > 10
    assert "v3" in prompts and len(prompts["v3"]) > 10
    assert "final" in prompts and len(prompts["final"]) > 50


def test_final_prompt_critical_rules(prompt_mgr):
    """Verifies that final_prompt.md contains all non-negotiable prompt instructions."""
    final_text = prompt_mgr.get_template("final")

    # Role definition
    assert "Campus Helpdesk Assistant" in final_text

    # Groundedness & Zero Hallucination
    assert "STRICTLY on official university policy documents" in final_text
    assert "NEVER assume, extrapolate, or invent fees" in final_text
    assert "<context>" in final_text

    # Refusal & Routing
    assert "cannot verify" in final_text
    assert "Office of Academic Affairs" in final_text

    # Citation Requirement
    assert "[Source: <filename>, Page: <page>]" in final_text or "[Source:" in final_text

    # Policy Conflict Handling
    assert "conflicting" in final_text.lower()
    assert "highlight the conflict" in final_text.lower()

    # Prompt Injection Defense
    assert "PROMPT INJECTION" in final_text
    assert "UNDER NO CIRCUMSTANCES" in final_text
    assert "untrusted" in final_text.lower()


def test_format_context_metadata_linkage(prompt_mgr):
    """Verifies that chunks are formatted with explicit filename and page attribution."""
    mock_chunks = [
        {
            "filename": "academic_handbook.pdf",
            "page": 3,
            "chunk_id": "academic_handbook_p3_c1",
            "text": "Library operating hours are Monday to Saturday 8 AM to 10 PM."
        }
    ]
    formatted = prompt_mgr.format_context(mock_chunks)
    assert "[Source: academic_handbook.pdf | Page: 3 | Chunk ID: academic_handbook_p3_c1]" in formatted
    assert "Library operating hours" in formatted


def test_build_prompt_wraps_in_delimiters(prompt_mgr):
    """Verifies that assembled prompt safely encloses context and student query."""
    mock_chunks = [
        {
            "filename": "demo.pdf",
            "page": 1,
            "chunk_id": "c1",
            "text": "Minimum attendance is 75%."
        }
    ]
    built = prompt_mgr.build_prompt(
        query="What is the attendance rule?",
        chunks=mock_chunks,
        version="final"
    )
    assert "<context>" in built
    assert "</context>" in built
    assert "<user_query>" in built
    assert "What is the attendance rule?" in built
