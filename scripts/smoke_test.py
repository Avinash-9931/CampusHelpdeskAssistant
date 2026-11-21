"""
CLI Smoke Test Script for AI-Powered Campus Helpdesk Assistant.
Ingests the generated demo PDF and answers:
1. One in-scope question in Fallback Mode (asserts sources returned and citations present).
2. One out-of-scope question in Fallback Mode (asserts zero-context refusal and department referral).
"""

import sys
from pathlib import Path

# Set up project root in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from core.pdf_processor import process_document
from core.text_chunker import chunk_pages
from core.retriever import KnowledgeBase
from core.ai_engine import AIEngine
from core.chatbot import ChatbotController


def main():
    print("=" * 75)
    print(" AI-POWERED CAMPUS HELPDESK ASSISTANT — CLI SMOKE TEST")
    print("=" * 75)

    # Step 1: Ingest Demo PDF
    demo_pdf_path = settings.DEMO_DIR / "university_policy_demo.pdf"
    if not demo_pdf_path.exists():
        print("[*] Generating synthetic university policy PDF...")
        from data.demo.generate_demo_pdf import build_pdf
        build_pdf()

    with open(demo_pdf_path, "rb") as f:
        file_bytes = f.read()

    print(f"\n[+] Ingesting: {demo_pdf_path.name}")
    doc = process_document(file_bytes, filename=demo_pdf_path.name)
    chunks = chunk_pages(doc.pages, filename=doc.filename)

    kb = KnowledgeBase()
    kb.clear_all()
    kb.add_document(doc, chunks)

    print(f"    - Extracted Pages: {doc.page_count}")
    print(f"    - Generated Chunks: {len(chunks)}")
    print(f"    - Active Method: '{kb.active_method()}'")

    # Step 2: Initialize Chatbot (No API Key -> Fallback Mode)
    ai_engine = AIEngine(api_key="")
    chatbot = ChatbotController(retriever=kb, ai_engine=ai_engine)

    # Step 3: Test In-Scope Question
    q_in = "What is the minimum attendance requirement to appear in final exams?"
    print(f"\n[+] Running IN-SCOPE Test:")
    print(f"    Question: \"{q_in}\"")
    result_in = chatbot.ask(q_in)

    print(f"    Mode: {result_in.mode}")
    print(f"    Retrieval Method: {result_in.retrieval_method}")
    print(f"    Sources Count: {len(result_in.sources)}")
    assert len(result_in.sources) > 0, "Expected at least 1 citation for in-scope question"
    assert result_in.sources[0].page == 1, "Expected top citation to be Page 1"
    print(f"    Top Citation: {result_in.sources[0].filename} (Page {result_in.sources[0].page}, Score: {result_in.sources[0].score})")
    print(f"    Answer Excerpt: {result_in.answer[:160]}...")
    print("    --> IN-SCOPE TEST: PASSED [OK]")

    # Step 4: Test Out-of-Scope Question (Refusal Gate)
    q_out = "What is the fee for the campus swimming pool membership?"
    print(f"\n[+] Running OUT-OF-SCOPE Test (Zero-Hallucination Refusal Gate):")
    print(f"    Question: \"{q_out}\"")
    result_out = chatbot.ask(q_out)

    print(f"    Mode: {result_out.mode}")
    print(f"    Sources Count: {len(result_out.sources)}")
    assert len(result_out.sources) == 0, "Expected zero citations for out-of-scope question"
    assert result_out.mode == "no_context", "Expected mode 'no_context'"
    assert "cannot verify" in result_out.answer.lower(), "Expected refusal notice"
    print(f"    Delivered Answer:\n{result_out.answer}")
    print("    --> OUT-OF-SCOPE REFUSAL TEST: PASSED [OK]")

    print("\n" + "=" * 75)
    print(" ALL SMOKE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    main()
