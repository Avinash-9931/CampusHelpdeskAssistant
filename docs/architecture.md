# System Architecture & Technical Design

This document details the architecture, data flows, and component interactions of the **AI-Powered Campus Helpdesk Assistant**.

---

## 1. High-Level Query & RAG Pipeline

```mermaid
flowchart TD
    A["Student / User"] -->|"Submits Question"| B["Streamlit UI (Chat Interface)"]
    B -->|"Sends Query & Session Context"| C["Chatbot Controller (core/chatbot.py)"]
    
    subgraph Query Processing & Intent Resolution
        C --> D{"Input Validation"}
        D -->|"Invalid (Empty/Too Long)"| D1["Return Validation Error"]
        D -->|"Valid"| E{"Follow-Up Intent Check"}
        E -->|"Follow-up Question"| F["Contextual Query Rewriter"]
        E -->|"Standalone Query"| G["Cleaned Search Query"]
        F --> G
    end

    subgraph Information Retrieval & Threshold Verification
        G --> H["Dual-Tier Retriever (core/retriever.py)"]
        H --> I[("Knowledge Base (chunks + index)")]
        I -->|"Top-k Chunks + Similarity Scores"| J{"Score >= Relevance Threshold?"}
        J -->|"No (Score < 0.15 or Empty)"| K["Immediate Refusal Protocol"]
        K -->|"Route to University Office"| B
    end

    subgraph Grounded Answer Generation
        J -->|"Yes (Relevant Context Found)"| L["Prompt Manager (core/prompt_manager.py)"]
        L -->|"Assemble Prompt with Context Delimiters"| M{"AI Mode Available?"}
        M -->|"API Key Configured"| N["Gemini Engine (core/ai_engine.py)"]
        N -->|"Generate Grounded Response"| O["Answer Post-Processing"]
        M -->|"No Key (Fallback Mode)"| P["Verbatim Evidence Presenter"]
        P --> O
    end

    subgraph Citation & Response Assembly
        O --> Q["Extract Grounded Citations (Filename, Page, Snippet)"]
        Q --> R["Structured Response Object"]
        R --> B
        B -->|"Render Answer + Collapsible Citations"| A
    end
```

---

## 2. Document Ingestion, Processing & Indexing Pipeline

```mermaid
flowchart LR
    A["PDF Upload (User / Demo)"] --> B["PDF Processor (core/pdf_processor.py)"]
    
    subgraph Validation Gate
        B --> C{"Format & Security Check"}
        C -->|"Invalid / Corrupt / Password"| E1["Specific Human Error Message"]
        C -->|"Hash Duplicate"| E2["Skip Redundant Processing"]
        C -->|"Valid PDF"| D["Per-Page Text Extractor (pypdf)"]
    end

    subgraph Text Extraction & Normalization
        D --> F{"Has Extractable Text?"}
        F -->|"Zero Text Found"| E3["Scanned PDF Error (OCR Unavailable)"]
        F -->|"Text Extracted"| G["Text Cleaner (Whitespace, Ligatures, Hyphens)"]
    end

    subgraph Chunking & Metadata Tagging
        G --> H["Text Chunker (core/text_chunker.py)"]
        H --> I["Sliding Window Chunks (800 chars, 150 overlap)"]
        I --> J["Attach Metadata: doc_name, page, chunk_id, sha256"]
    end

    subgraph Indexing & Local Persistence
        J --> K[("data/processed/knowledge_base.json")]
        K --> L["TF-IDF Lexical Vectorizer & Matrix (scikit-learn)"]
        K -.->|"Optional Semantic Mode"| M["Gemini Embeddings Generator & Disk Cache"]
    end
```

---

## 3. Component Interaction & Class Topology

```mermaid
classDiagram
    class StreamlitApp {
        +render_header()
        +render_navigation()
        +render_chat_view()
        +render_knowledge_base()
        +render_evaluation_view()
        +render_about_view()
    }

    class ChatbotController {
        -retriever: DocumentRetriever
        -ai_engine: AIEngine
        -prompt_manager: PromptManager
        +process_message(query, history) dict
        +rewrite_query(query, history) str
        +format_office_referral(query) str
    }

    class DocumentRetriever {
        -chunks: list
        -vectorizer: TfidfVectorizer
        -tfidf_matrix: ndarray
        -embeddings_cache: dict
        +build_index(chunks) void
        +search(query, top_k, threshold) tuple
        +save_to_disk() void
        +load_from_disk() bool
    }

    class PDFProcessor {
        +validate_file(file_path_or_bytes) dict
        +extract_pages(file_path_or_bytes, filename) list
        +clean_text(raw_text) str
        +compute_hash(bytes_data) str
    }

    class TextChunker {
        +chunk_pages(pages_data, filename) list
        +chunk_text(text, chunk_size, overlap) list
    }

    class AIEngine {
        -client: genai.Client
        -model_name: str
        +is_configured() bool
        +generate_response(prompt, system_instruction) str
        +generate_embeddings(texts) list
    }

    class PromptManager {
        -prompts: dict
        +get_prompt(version) str
        +build_rag_prompt(query, chunks, version) str
    }

    StreamlitApp --> ChatbotController : invokes
    ChatbotController --> DocumentRetriever : searches
    ChatbotController --> AIEngine : queries LLM
    ChatbotController --> PromptManager : loads templates
    DocumentRetriever --> TextChunker : consumes chunks
    TextChunker --> PDFProcessor : consumes extracted pages
```
