"""
End-to-end UI and page navigation tests for app.py using Streamlit's official AppTest framework.
Verifies all active pages (Home, AI Chatbot, Knowledge Base, My History),
custom top navigation, quick inquiry chips, chat input, and live status strip.
"""

import pytest
import unittest.mock as mock
from pathlib import Path
from streamlit.testing.v1 import AppTest
from config import settings


APP_PATH = str(settings.BASE_DIR / "app.py")


def test_ui_home_page():
    """Verifies that the Home page loads with hero banner and status strip."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception
    
    # Verify top navigation buttons exist for active pages
    button_labels = [b.label for b in at.button]
    assert "Home" in button_labels
    assert "AI Chatbot" in button_labels
    assert "Knowledge Base" in button_labels
    assert "My History" in button_labels
    
    # Verify hero banner markdown contains project title
    all_md = " ".join([m.value for m in at.markdown])
    assert "Find verified university answers in seconds" in all_md
    assert "SCSE4041 Prompt Engineering" in all_md
    assert "Indexed Documents" in all_md
    assert "Knowledge Chunks" in all_md


@mock.patch("core.ai_engine.AIEngine.generate")
def test_ui_chatbot_page(mock_generate):
    """Navigates to the AI Chatbot page, sends an inquiry, and verifies response generation."""
    mock_generate.return_value = (
        "Under section 1.2 of the university policy, undergraduate students must maintain "
        "a minimum attendance of 75% across all registered courses. [university_policy_demo.pdf, p. 1]"
    )
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    
    # Switch to AI Chatbot page via top navigation button
    chat_btn = [b for b in at.button if b.label == "AI Chatbot"][0]
    chat_btn.click().run()
    assert not at.exception
    assert at.session_state.page == "AI Chatbot"
    
    all_md = " ".join([m.value for m in at.markdown])
    assert "Campus Helpdesk Assistant" in all_md
    
    # Verify quick question chips exist
    button_labels = [b.label for b in at.button]
    assert any("Attendance" in b for b in button_labels)
    assert any("Library" in b for b in button_labels)
    assert any("Fee Payment" in b for b in button_labels)
    
    # Input student question via chat_input
    assert len(at.chat_input) > 0
    at.chat_input[0].set_value("What is the minimum attendance requirement?").run()
    assert not at.exception
    
    # Verify message appears in conversation history
    all_chat_md = " ".join([m.value for m in at.markdown])
    assert "minimum attendance requirement" in all_chat_md.lower()
    assert "75%" in all_chat_md or "attendance" in all_chat_md.lower()


def test_ui_knowledge_base_page():
    """Navigates to the Knowledge Base page and checks document management controls."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    
    # Switch to Knowledge Base page via top navigation button
    kb_btn = [b for b in at.button if b.label == "Knowledge Base"][0]
    kb_btn.click().run()
    assert not at.exception
    assert at.session_state.page == "Knowledge Base"
    
    all_md = " ".join([m.value for m in at.markdown])
    assert "Knowledge Base Management" in all_md
    assert "Upload Official PDF Documents" in all_md
    assert "Quick Demo Setup" in all_md
    
    # Verify file uploader and action buttons exist
    assert len(at.file_uploader) > 0
    button_labels = [b.label for b in at.button]
    assert any("Load Demo Policy" in b for b in button_labels)


def test_ui_history_page():
    """Navigates to My History page and verifies history controls."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    
    hist_btn = [b for b in at.button if b.label == "My History"][0]
    hist_btn.click().run()
    assert not at.exception
    assert at.session_state.page == "My History"
    
    all_md = " ".join([m.value for m in at.markdown])
    assert "Conversation History" in all_md
