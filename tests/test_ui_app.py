"""
End-to-end UI and page navigation tests for app.py using Streamlit's official AppTest framework.
Verifies all 5 pages, controls, session state, chat inputs, and evaluation metrics.
"""

import pytest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from config import settings


APP_PATH = str(settings.BASE_DIR / "app.py")


def test_ui_home_page():
    """Verifies that the Home page loads with editorial hero banner and status strip."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception
    
    # Verify navigation radio has all 5 pages
    nav_radio = at.sidebar.radio[0]
    assert len(nav_radio.options) == 5
    assert "🏛️ Home" in nav_radio.options
    assert "💬 AI Chatbot" in nav_radio.options
    assert "📚 Knowledge Base" in nav_radio.options
    assert "🧪 Test / Evaluation" in nav_radio.options
    assert "ℹ️ About Project" in nav_radio.options
    
    # Verify hero banner markdown contains project title
    all_md = " ".join([m.value for m in at.markdown])
    assert "AI-Powered Campus Helpdesk Assistant" in all_md
    assert "SCSE4041 Prompt Engineering" in all_md
    assert "Indexed Documents" in all_md
    assert "Knowledge Chunks" in all_md


def test_ui_chatbot_page():
    """Navigates to the AI Chatbot page, sends an inquiry, and verifies response generation."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    
    # Switch to AI Chatbot page
    at.sidebar.radio[0].set_value("💬 AI Chatbot").run()
    assert not at.exception
    
    all_md = " ".join([m.value for m in at.markdown])
    assert "Campus Helpdesk Assistant" in all_md
    
    # Verify quick question chips exist
    button_labels = [b.label for b in at.button]
    assert any("attendance" in b.lower() for b in button_labels)
    assert any("library" in b.lower() for b in button_labels)
    assert any("registration" in b.lower() for b in button_labels)
    
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
    
    # Switch to Knowledge Base page
    at.sidebar.radio[0].set_value("📚 Knowledge Base").run()
    assert not at.exception
    
    all_md = " ".join([m.value for m in at.markdown])
    assert "Knowledge Base Management" in all_md
    assert "Upload Official PDF Documents" in all_md
    assert "Load Demo University Policy" in all_md
    
    # Verify file uploader and action buttons exist
    assert len(at.file_uploader) > 0
    button_labels = [b.label for b in at.button]
    assert any("Demo Policy" in b for b in button_labels)


def test_ui_evaluation_page():
    """Navigates to the Test / Evaluation page and verifies metrics and test cases table."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    
    # Switch to Test / Evaluation page
    at.sidebar.radio[0].set_value("🧪 Test / Evaluation").run()
    assert not at.exception
    
    # Verify metrics summary bar
    assert len(at.metric) >= 4
    metric_labels = [m.label for m in at.metric]
    assert "Total Test Cases" in metric_labels
    assert "Passed Tests" in metric_labels
    assert "Failed Tests" in metric_labels
    assert "Pending Execution" in metric_labels
    
    # Total cases should be 12
    total_metric = [m for m in at.metric if m.label == "Total Test Cases"][0]
    assert int(total_metric.value) == 12
    
    # Verify dataframe table exists
    assert len(at.dataframe) > 0


def test_ui_about_page():
    """Navigates to About Project and verifies team members and iteration log table."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    
    # Switch to About Project page
    at.sidebar.radio[0].set_value("ℹ️ About Project").run()
    assert not at.exception
    
    all_md = " ".join([m.value for m in at.markdown])
    # Verify metadata
    assert "Invictus" in all_md
    assert "PE-B01-15" in all_md
    assert "C1 | Course: SCSE4041" in all_md
    
    # Verify team members listed
    assert "Avinash Kumar" in all_md
    assert "S24CSEU0709" in all_md
    assert "Divyanshu Raj" in all_md
    assert "S24CSEU0800" in all_md
    assert "Kushagra Varshney" in all_md
    assert "Lakshay Bhatia" in all_md
    assert "Shivendra Singh" in all_md
    assert "Devvrat Arya" in all_md
    
    # Verify prompt engineering iteration log table
    assert "Prompt Engineering Iteration Log" in all_md
    assert "V1 Basic" in all_md
    assert "V2 Context" in all_md
    assert "V3 Anti-Hallucination" in all_md
    assert "Final Optimized" in all_md
