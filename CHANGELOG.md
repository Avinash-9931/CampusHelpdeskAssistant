# Changelog

All notable changes to the **AI-Powered Campus Helpdesk Assistant** project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - Milestone 2 Release - 2026-11-21

### Added
- **Core Retrieval-Augmented Generation (RAG) Architecture**:
  - `core/pdf_processor.py`: Multi-page text extraction with `pypdf`, content normalization, and robust validation against corrupted, password-protected, empty, and scanned PDFs.
  - `core/text_chunker.py`: Sliding-window character chunker maintaining strict metadata linkage (`filename`, `page`, `chunk_id`).
  - `core/retriever.py`: Dual-tier retrieval supporting Lexical (TF-IDF + Cosine Similarity) and Semantic (Gemini Embeddings + Cosine Similarity), complete with similarity thresholding and persistent local caching.
  - `core/ai_engine.py`: Google GenAI SDK (`google-genai`) integration with automated backoff retries, error classification, and offline fallback detection.
  - `core/prompt_manager.py`: Systematic prompt version loading (`v1`, `v2`, `v3`, `final`) and context delimiter formatting with injection defense wrappers.
  - `core/chatbot.py`: Full orchestrator executing input validation, follow-up intent resolution, retrieval threshold verification, AI generation or verified fallback presentation, and metadata-grounded page-level citation extraction.
- **User Interface & Experience (Streamlit)**:
  - Custom editorial SaaS theme with deep navy (`#0B1F3A`), crisp borders (`#E2E8F0`), and Google Fonts (`Plus Jakarta Sans`, `Space Grotesk`, `JetBrains Mono`).
  - Five core modules: Home (Hero, live metrics, workflow steps), AI Chatbot (chat history, quick questions, collapsible source cards), Knowledge Base (drag & drop uploader, doc status cards, demo loader), Test / Evaluation (interactive test suite runner), and About Project.
  - Pure-CSS interactive animations, hover feedback, active navigation indicators, and responsive card layouts.
- **Evaluation Suite**:
  - `evaluation/test_cases.csv`: 12 comprehensive validation scenarios encompassing standard queries, out-of-domain refusals, citation checks, conflicting policies, and prompt injection attacks.
  - `evaluation/evaluation_report.md`: Complete empirical assessment with detailed edge-case case studies.
- **Prompt Engineering Research**:
  - Four evolution steps (`prompts/prompt_v1.md`, `prompt_v2.md`, `prompt_v3.md`, `final_prompt.md`).
  - `prompts/iteration_log.md` detailing failure modes, modifications, and empirical results.
- **Demo Data & Testing**:
  - Auto-generated synthetic university policy document `data/demo/university_policy_demo.pdf` containing visible demo watermarks, deliberate policy conflicts, and office contacts.
  - Pytest test suite in `tests/` validating PDF extraction, retrieval scoring, prompt integrity, and end-to-end chatbot behavior.
