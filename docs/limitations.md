# System Limitations & Boundary Analysis

To adhere to non-negotiable transparency rules, this document provides an honest technical assessment of the system's operational constraints and known limitations.

---

## 1. PDF Parsing & Extraction Boundaries

- **Scanned Documents (OCR Absence):**
  - The core pipeline uses native PDF stream parsing (`pypdf`).
  - Scanned documents, image-only PDFs, or rasterized pages without an underlying text layer cannot be parsed without external Tesseract OCR dependencies.
  - *Mitigation:* The system detects zero-text conditions gracefully and issues an informative error rather than failing silently.

- **Complex Multi-Column & Tabular Layouts:**
  - Standard text stream extraction extracts text in reading-order streams. Complex multi-column fee tables, side-by-side matrices, or multi-page financial schedules may have merged rows or misaligned columns.
  - *Mitigation:* The chunker uses sliding windows with sentence boundary heuristics to maintain semantic cohesion, but users are advised to verify tabular fee schedules directly.

- **Embedded Graphics & Flowcharts:**
  - Administrative approval flowcharts, process diagrams, and signature seals embedded as raster images are not parsed by the text extraction pipeline.

---

## 2. Information Retrieval Constraints

- **Lexical Retrieval (TF-IDF / BM25) vs. Semantic Nuance:**
  - In default Fallback Mode (no API key), the system uses TF-IDF with character and word n-grams (1, 2).
  - Lexical matching relies on keyword overlap. Inquiries using synonyms not present in the text (e.g., "cost" vs. "tuition fee") may receive lower similarity scores.
  - *Mitigation:* A low similarity threshold ($0.15$) combined with n-gram tokenization captures sub-phrase similarities.

- **Semantic Embedding Cost & Quota:**
  - Semantic embeddings require Google Gemini API quota when active.
  - High-volume ingestion in semantic mode generates API calls proportional to chunk count.
  - *Mitigation:* Disk-based persistent caching (`embeddings_cache.npy`) ensures chunks are embedded only once per unique document hash.

---

## 3. Generative Model & Context Window Realities

- **Context Window Truncation:**
  - The retriever injects the top $K$ chunks ($K=4$, $\approx 3,200$ characters).
  - If a multi-part policy inquiry requires synthesizing 15 different pages across multiple manuals, standard top-4 retrieval may only present a partial subset of relevant sections.
  - *Mitigation:* The prompt explicitly commands the model to cite only what is present and flag any known gaps.

- **Indirect Prompt Injection:**
  - While our prompt includes strict XML delimiters (`<context>`) and active defense instructions, sophisticated adversarial techniques embedded inside user-uploaded documents can theoretically probe model defenses.
  - *Mitigation:* Comprehensive prompt rules, refusal gates, and automated test cases (`tests/test_prompt_rules.py`) continuously verify resistance to injection attempts.

---

## 4. Hardware & Deployment Dependencies

- **Cold Start & File Persistence:**
  - The application relies on local filesystem persistence (`data/processed/knowledge_base.json`). In ephemeral containerized cloud environments (e.g., standard Google Cloud Run without persistent volumes), indexed state must be restored or mounted to persistent storage.
