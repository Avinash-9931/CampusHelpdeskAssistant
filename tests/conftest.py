"""
Pytest configuration and environment fixtures.
Sets up Python path so core and config modules are discoverable.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from config import settings

@pytest.fixture(scope="session", autouse=True)
def preserve_knowledge_base():
    yield
    # After test session completes, ensure demo handbook is re-seeded if empty
    from core.retriever import KnowledgeBase
    kb = KnowledgeBase()
    if len(kb.documents) == 0:
        demo_pdf = settings.DEMO_DIR / "university_policy_demo.pdf"
        if demo_pdf.exists():
            try:
                with open(demo_pdf, "rb") as f:
                    data = f.read()
                from core.pdf_processor import process_document
                from core.text_chunker import chunk_pages
                doc = process_document(data, "university_policy_demo.pdf")
                chunks = chunk_pages(doc.pages, filename="university_policy_demo.pdf")
                kb.add_document(doc, chunks)
            except Exception:
                pass
