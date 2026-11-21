# 🎓 AI-Powered Campus Helpdesk Assistant

> **Milestone 2 Project Submission**  
> **Course:** SCSE4041 – Prompt Engineering | **Problem Statement:** C1  
> **Team:** Invictus | **Team ID:** `PE-B01-15`  
> **Primary Developers:**  
> - **Avinash Kumar** (`S24CSEU0709`) — Backend Architecture, RAG Pipeline & Chatbot Controller  
> - **Divyanshu Raj** (`S24CSEU0800`) — Frontend Design, System Integration & Empirical Testing  
> **Team Members:**  
> - Kushagra Varshney (`S24CSEU0060`)  
> - Lakshay Bhatia (`S24CSEU062`)  
> - Shivendra Singh (`S24CSEU0416`)  
> - Devvrat Arya (`S24CSEU0866`)

---

## 📌 Executive Summary & Objective

The **AI-Powered Campus Helpdesk Assistant** is an enterprise-grade Retrieval-Augmented Generation (RAG) system engineered to answer student inquiries strictly and exclusively using official university policy PDF documents. 

Designed under strict zero-hallucination non-negotiable principles, the assistant:
1. **Answers only from verified PDF context:** Never invents fees, deadlines, attendance quotas, regulations, or page numbers.
2. **Defensive Refusal & Routing:** When uploaded documents lack the requested facts, the system terminates generation immediately **without calling the LLM** and provides direct departmental referrals (e.g., Accounts Desk, Examination Branch, Library, Student Welfare).
3. **Dual-Tier Retrieval:** Operates in offline **Lexical Fallback Mode** (TF-IDF with morphological normalization and score thresholding) when no API key is present, and seamlessly transitions to **Semantic Embeddings + Gemini 2.5 Flash** when a Google AI Studio key is configured.
4. **Metadata-Grounded Citations:** Every claim is linked directly to document filenames, page numbers, and passage excerpts extracted from indexed chunks.
5. **Prompt Injection Defense:** Strict XML boundaries (`<context>`, `<user_query>`) and system prompt immunity directives prevent adversarial prompt hijacking embedded in uploaded files or student queries.

---

## 🛠️ Tech Stack & Dependencies

- **Language & Runtime:** Python 3.10+ (Tested on Python 3.12)
- **Frontend Framework:** Streamlit (Custom editorial SaaS design with injected CSS design tokens)
- **Generative AI / LLM SDK:** Google GenAI Official SDK (`google-genai`) with exponential backoff retries
- **Document Processing:** `pypdf` with per-page text normalization and exception classification
- **Information Retrieval:** `scikit-learn` (TF-IDF & Cosine Similarity) + Gemini Embeddings (`text-embedding-004`)
- **Evaluation & Testing:** `pytest`, `pandas`, `numpy`
- **Demo Document Generation:** `reportlab`
- **Environment Management:** `python-dotenv`

---

## 📂 Project Directory Structure

```
campus-helpdesk-assistant/
├── app.py                      # Multi-page Streamlit application & custom UI styles
├── requirements.txt            # System dependencies
├── README.md                   # System documentation & usage manual
├── CHANGELOG.md                # Milestone evolution & version history
├── .env.example                # Sample environment template (Secrets gitignored)
├── .gitignore                  # Git exclusions (.env, .venv, caches)
├── config/
│   ├── __init__.py
│   └── settings.py             # Global settings, paths, thresholds, and metadata
├── core/
│   ├── __init__.py
│   ├── pdf_processor.py        # PDF validation, corruption/encryption detection, text extraction
│   ├── text_chunker.py         # Metadata-preserving sliding-window chunker
│   ├── retriever.py            # Dual-tier indexer (Lexical TF-IDF / Semantic Embeddings)
│   ├── ai_engine.py            # Google GenAI client, error classifier & retry logic
│   ├── prompt_manager.py       # Versioned prompt loader & context delimiter assembler
│   └── chatbot.py              # Central controller: input validation, rewriting, retrieval, citations
├── prompts/
│   ├── prompt_v1.md            # Baseline zero-shot prompt
│   ├── prompt_v2.md            # Standard context-augmented prompt
│   ├── prompt_v3.md            # Hallucination-control & negative constraint prompt
│   ├── final_prompt.md         # Production-optimized prompt (XML tags, injection defense, conflict detection)
│   └── iteration_log.md        # Comprehensive prompt engineering evolution log
├── data/
│   ├── uploads/                # User-uploaded PDFs (persisted locally)
│   ├── processed/              # Indexed knowledge base (knowledge_base.json, embeddings_cache.npy)
│   └── demo/                   # Synthetic demo PDF generator & generated policy handbook
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest discovery configuration
│   ├── test_pdf_processor.py   # Unit tests for PDF extraction & error classification
│   ├── test_retriever.py       # Unit tests for lexical search & threshold gating
│   ├── test_prompt_rules.py    # Unit tests for prompt integrity & injection immunity
│   └── test_chatbot.py         # End-to-end integration tests for chatbot behavior
├── evaluation/
│   ├── test_cases.csv          # 12 empirical test scenarios with verified outputs
│   ├── run_evaluation.py       # Automated test runner script
│   └── evaluation_report.md    # Empirical metrics report & edge-case case studies
├── docs/
│   ├── architecture.md         # Mermaid diagrams for query, ingestion & component topology
│   ├── workflow.md             # Operational lifecycle specification
│   └── limitations.md          # Transparent assessment of boundary conditions
└── assets/
    └── logo.svg                # Custom academic crest & AI vector artwork
```

---

## ⚡ Installation & Setup

### 1. Clone or Navigate to the Repository
```bash
cd /Users/avinashsingh/.gemini/antigravity/scratch/campus-helpdesk-assistant
```

### 2. Set Up Python Virtual Environment
```bash
# Using Python 3.10+ (Recommended: Python 3.12)
python3 -m venv .venv

# Activate virtual environment
# macOS / Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` in any text editor:
```env
# Optional: Google AI Studio Gemini API Key
# If omitted or left empty, the application runs in Lexical Fallback Mode!
GEMINI_API_KEY=

# Default Gemini model
GEMINI_MODEL=gemini-2.5-flash

# System parameters
MAX_UPLOAD_SIZE_MB=15
CHUNK_SIZE=800
CHUNK_OVERLAP=150
SIMILARITY_THRESHOLD=0.13
DEFAULT_RETRIEVAL_METHOD=lexical
```

> ⚠️ **No API Key Required for Core Evaluation:** The application fully launches and operates without an API key using the offline lexical retrieval pipeline, displaying verified verbatim source evidence with citations.

---

## 🚀 Running the Application

Launch the Streamlit web application:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### Core Application Views:
1. **🏛️ Home:** Live status strip (indexed documents, chunks, active AI mode, retrieval tier), 4-step architecture breakdown, and quick launch buttons.
2. **💬 AI Chatbot:** Interactive conversational helpdesk with quick-question chips, follow-up resolution, collapsible citation cards, and automatic departmental routing.
3. **📚 Knowledge Base:** Drag-and-drop multi-file PDF uploader, file status cards (page count, chunk count, upload timestamp), individual delete/reprocess buttons, and a **1-click Demo Document Loader**.
4. **🧪 Test / Evaluation:** Interactive execution module running 12 automated test cases against the live knowledge base, showing real outputs, pass/fail metrics, and highlighted edge-case case studies.
5. **ℹ️ About Project:** Course metadata, team rosters, prompt iteration history table, and technical specifications.

---

## 🧪 Running Automated Tests

### 1. Pytest Unit & Integration Test Suite
Execute the full pytest suite (24 unit and integration tests):
```bash
pytest tests/ -v
```
**Test Coverage Includes:**
- `test_pdf_processor.py`: Extension checks, 0-byte detection, 15MB limits, content hashing, scanned PDF detection, and password-protected PDF rejection.
- `test_retriever.py`: Lexical index construction, TF-IDF cosine similarity, similarity threshold gating, document deletion, and state persistence.
- `test_prompt_rules.py`: Loading of `v1`, `v2`, `v3`, and `final` prompts; verification of XML context delimiters; prompt injection defense instructions; and citation requirements.
- `test_chatbot.py`: Query sanitization, follow-up resolution, offline fallback execution, out-of-domain refusal routing, and prompt injection immunity.

### 2. Empirical Evaluation Suite
Run the 12 evaluation test cases and regenerate `evaluation_report.md`:
```bash
python evaluation/run_evaluation.py
```

---

## 🛡️ Non-Negotiable Rules & Prompt Engineering Standards

| Standard | Implementation Mechanism |
| :--- | :--- |
| **Zero Parametric Hallucination** | System refuses out-of-context queries immediately without calling the LLM when similarity score $< 0.13$. |
| **Departmental Routing** | When context is missing, the student is routed to the verified campus office (e.g. Accounts Desk, Exam Branch, Student Housing). |
| **Exact Citations** | Citations are constructed from chunk metadata (`[Source: filename, Page: page]`) rather than model generation. |
| **Contradiction Detection** | The prompt (`final_prompt.md`) commands the model to flag conflicting sections (e.g. Section 4.2 vs Section 9.1 late fee conflict) rather than guessing. |
| **Prompt Injection Defense** | Retrieved passages and user queries are wrapped in XML tags (`<context>`, `<user_query>`) with instructions to ignore internal role overrides. |
| **Offline Fallback Integrity** | When running without an API key, the system displays retrieved evidence with clean blockquotes without impersonating an AI response. |

---

## ⚠️ Known Boundaries & Limitations

As detailed in [`docs/limitations.md`](docs/limitations.md):
1. **Scanned PDFs (No OCR):** Only PDFs with an underlying text stream are parsed; scanned images raise an informative `ScannedPDFError`.
2. **Lexical Retrieval Boundaries:** In Fallback Mode, matching relies on keyword overlap and morphological normalization; semantic synonyms not present in the text may receive lower scores.
3. **Table & Column Structure:** Multi-column layout tables may experience row concatenation during linear stream extraction.

---

## 👥 Project Team (Invictus)

- **Avinash Kumar** (`S24CSEU0709`) — Primary Developer (Backend Architecture, RAG Pipeline & Chatbot)
- **Divyanshu Raj** (`S24CSEU0800`) — Primary Developer (Frontend Design, Streamlit UX, Integration & Testing)
- **Kushagra Varshney** (`S24CSEU0060`)
- **Lakshay Bhatia** (`S24CSEU0062`)
- **Shivendra Singh** (`S24CSEU0416`)
- **Devvrat Arya** (`S24CSEU0866`)
