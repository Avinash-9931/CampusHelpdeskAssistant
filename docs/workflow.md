# Operational Workflow & Pipeline Specification

This document details the operational mechanics, decision trees, and state management throughout the life cycle of the **AI-Powered Campus Helpdesk Assistant**.

---

## 1. End-to-End Chatbot Lifecycle

### Step 1: Input Validation & Sanitization
1. When a student enters text in the chat input:
   - Check if string is empty or contains only whitespace. If so, ignore or return an informational hint.
   - Check character length: if query exceeds 1,000 characters, truncate or reject with a user-friendly message.
   - Check for excessive repetitive characters or control characters.

### Step 2: Contextual Query Resolution (Follow-up Rewriting)
- If prior chat history exists within the current session:
  - Detect whether the latest user utterance is a follow-up (e.g., pronouns "it", "they", "those", or phrases like "what about masters?", "where is that office?", "and the deadline?").
  - In AI mode with Gemini: A lightweight one-shot query reformulation prompt generates a standalone question incorporating prior topic context.
  - In Fallback / Lexical mode: Prior subject keywords are heuristically joined to ensure the TF-IDF search retrieves the relevant topic context.

### Step 3: Information Retrieval Execution
- Check the active knowledge base state:
  - If no documents are loaded, immediately return:
    > "No official university documents are currently indexed in the knowledge base. Please upload documents in the Knowledge Base tab or contact your university department directly."
- If documents exist:
  - Compute query representations using the active retriever (Lexical TF-IDF n-gram matching or Gemini Semantic Embeddings).
  - Calculate cosine similarity scores against all indexed chunks.
  - Rank chunks in descending order and select the top $K$ ($K=4$ by default).

### Step 4: Relevance Thresholding & Refusal Gate
- Evaluate the maximum similarity score among retrieved chunks against `SIMILARITY_THRESHOLD` ($0.15$):
  - **Case A: Maximum Score < Threshold**:
    - The question is determined to be out-of-scope or unsupported.
    - **Crucial Rule:** The system terminates the pipeline immediately **without invoking the LLM**.
    - The student is presented with a clear refusal statement and directed to the most relevant campus department (Office of Academic Affairs, Accounts, Student Welfare, or Examination Branch).
  - **Case B: Maximum Score >= Threshold**:
    - Chunks with score >= threshold are formatted as candidate context.

### Step 5: Answer Generation & Fallback Execution
- **When GEMINI_API_KEY is configured & valid**:
  - `prompt_manager.py` combines the query, candidate chunks, and system instructions into `final_prompt.md`.
  - Chunks are enclosed in `<context>` tags with `[Document: ..., Page: ...]` metadata headers.
  - The API call to Gemini is made with temperature $0.0$ (deterministic, zero-hallucination).
  - Exponential backoff retry logic handles any transient network timeouts.
- **When GEMINI_API_KEY is absent or invalid (Fallback Mode)**:
  - The system bypasses generative synthesis entirely.
  - Displays a banner: *"AI generation unavailable (no API key configured). Showing retrieved evidence from official documents:"*
  - Excerpts the retrieved passages directly with their exact source filenames and page numbers.

### Step 6: Citation Extraction & Source Grounding
- Citations are synthesized strictly from the retrieved chunk metadata (`filename`, `page_number`, `score`, and `text snippet`).
- Even if the model generates a text response, the citations list rendered in the UI is anchored directly to the verified database chunks, preventing hallucinated page citations.

---

## 2. Document Ingestion Lifecycle

1. **Upload & Pre-flight Inspection**:
   - File extension must be `.pdf`.
   - File size must be $\le 15$ MB (configurable via `MAX_UPLOAD_SIZE_MB`).
   - Byte length must be $> 0$.
2. **Cryptographic Deduplication**:
   - Computes SHA-256 hash of file content.
   - If an existing active document shares the identical hash, user is notified that the document is already indexed.
3. **PDF Decoding & Exception Classification**:
   - Attempt parsing with `pypdf.PdfReader`.
   - If `reader.is_encrypted`: raise `EncryptedPDFError`.
   - If parsing raises EOF or stream corruption errors: raise `CorruptPDFError`.
4. **Text Extraction & Quality Check**:
   - Loop over pages ($1$-indexed).
   - Clean whitespace, hyphens, and ligatures.
   - If total extractable text across all pages is $< 20$ characters, flag as `ScannedPDFError` with notice: *"Scanned PDF detected. No extractable text found, OCR is not enabled."*
5. **Chunking & Index Construction**:
   - Apply a sliding character window (800 characters, 150 character overlap) aligned to sentence boundaries.
   - Store chunks in memory and serialize to `data/processed/knowledge_base.json`.
   - Re-fit TF-IDF vectorizer matrix. If semantic mode is enabled, pre-compute embeddings and save to `embeddings_cache.npy`.
