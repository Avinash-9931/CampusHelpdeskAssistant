# System Architecture & Technical Design

This document details the architecture, data flows, security mechanisms, and component interactions of the **AI-Powered Campus Helpdesk Assistant**.

---

## 1. High-Level End-to-End System Architecture

The following diagram illustrates the complete multilayer architecture of the platform, from the client browser interface and Cloudflare edge network down through security, RAG pipeline, AI generation, and persistence layers.

```mermaid
flowchart TD
    subgraph Client["Client Tier (Web & Mobile Browser)"]
        User["Student / Faculty / Examiner"]
    end

    subgraph Edge["Edge & Networking Tier"]
        CF["Cloudflare Edge Network"]
        Tunnel["Cloudflare Tunnel (cloudflared HTTP/2)"]
    end

    subgraph Presentation["Presentation & UI Tier (Streamlit)"]
        App["app.py (Main Router & Theme Controller)"]
        LoginPage["ui/pages/login.py (Auth, 2FA, OTP UI)"]
        ChatPage["ui/pages/chatbot.py (Calley Dark Chat View)"]
        KBPage["ui/pages/knowledge_base.py (PDF Management)"]
        EvalPage["ui/pages/evaluation.py (Empirical Benchmarks)"]
        AboutPage["ui/pages/about.py (Team & Project Specs)"]
    end

    subgraph Security["Security & Authentication Subsystem (auth/)"]
        AuthSvc["auth/service.py (Auth Business Logic)"]
        OTPEngine["auth/otp.py (Cryptographic OTP & Rate Limiting)"]
        SessionMgr["auth/session.py (Session Lifecycle & Idle Timeout)"]
        SMTPClient["SMTP Gateway (smtp.gmail.com:587)"]
        AuthDB[("SQLite Database: campus_auth.db")]
    end

    subgraph CoreRAG["Core RAG & Intelligence Pipeline (core/)"]
        ChatCtrl["core/chatbot.py (ChatbotController)"]
        InputVal["Input Validation & Query Sanitizer"]
        Rewriter["Follow-Up Contextual Rewriter"]
        Retriever["core/retriever.py (KnowledgeBase / Dual-Tier Search)"]
        PromptMgr["core/prompt_manager.py (XML-Delimited Grounding)"]
        AIEngine["core/ai_engine.py (Google GenAI Client)"]
        ResponseGuard["core/response_guard.py (Citation Integrity Validator)"]
    end

    subgraph Ingestion["Document Ingestion Pipeline (core/)"]
        PDFProc["core/pdf_processor.py (pypdf Extraction & Normalization)"]
        Chunker["core/text_chunker.py (Sliding-Window Chunker)"]
        DemoGen["data/demo/ (Demo Handbook Generator)"]
    end

    subgraph Storage["Storage & Persistence Tier"]
        Uploads[("data/uploads/ (Raw PDF Documents)")]
        KBStore[("data/processed/knowledge_base.json")]
        TFIDFModel[("In-Memory TF-IDF Sparse Matrix")]
        EmbeddingsCache[("data/processed/embeddings_cache.npy")]
    end

    subgraph External["External Cloud & API Services"]
        GeminiFlash["Google AI Studio (Gemini 2.5 Flash / Flash-Lite)"]
        GeminiEmbed["Google Embeddings API (text-embedding-004)"]
        CampusEmail["Bennett University Mail Delivery (@bennett.edu.in)"]
    end

    %% Network Connections
    User <-->|"HTTPS (Encrypted)"| CF
    CF <-->|"Encrypted TCP/443"| Tunnel
    Tunnel <-->|"Local Reverse Proxy"| App

    %% Presentation routing
    App --> LoginPage
    App --> ChatPage
    App --> KBPage
    App --> EvalPage
    App --> AboutPage

    %% Auth interactions
    LoginPage --> AuthSvc
    AuthSvc --> OTPEngine
    AuthSvc --> SessionMgr
    AuthSvc --> AuthDB
    OTPEngine -->|"Dispatch 6-Digit Code"| SMTPClient
    SMTPClient --> CampusEmail

    %% Ingestion flows
    KBPage --> PDFProc
    DemoGen --> PDFProc
    PDFProc -->|"Extract Pages & Validate"| Chunker
    PDFProc --> Uploads
    Chunker -->|"800-char / 150-overlap Chunks"| Retriever
    Retriever --> KBStore
    Retriever --> TFIDFModel
    Retriever -.->|"Optional Semantic Mode"| GeminiEmbed
    Retriever -.-> EmbeddingsCache

    %% Query & Chat execution flows
    ChatPage --> ChatCtrl
    ChatCtrl --> InputVal
    InputVal --> Rewriter
    Rewriter -->|"Resolved Query"| Retriever
    Retriever -->|"Top-k Chunks (Threshold >= 0.13)"| ChatCtrl
    
    ChatCtrl -->|"Grounded XML Context"| PromptMgr
    PromptMgr -->|"Versioned Prompt"| AIEngine
    AIEngine -->|"Deterministic Sampling (temp=0.0)"| GeminiFlash
    AIEngine -->|"Raw Output"| ResponseGuard
    ResponseGuard -->|"Verified Answer + Strict Citations"| ChatPage
    ChatPage -->|"Persist Turn"| AuthDB
```

---

## 2. Sequential Query & Grounded Retrieval Lifecycle

This sequence diagram depicts what occurs when a student asks a question—from rate limiting, query rewriting, threshold verification, fallback routing, Gemini generation, to citation validation.

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student / Faculty
    participant UI as Chatbot UI (Streamlit)
    participant Auth as Auth & Session Service
    participant Bot as ChatbotController
    participant Ret as Dual-Tier Retriever
    participant KB as KnowledgeBase Index
    participant LLM as Google Gemini Engine
    participant Guard as Response Citation Guard
    participant DB as SQLite DB (campus_auth.db)

    Student->>UI: Submits inquiry ("What is the attendance criteria?")
    UI->>Auth: Validate active session & idle timeout
    Auth-->>UI: Session Valid (Role: student / faculty)

    UI->>Bot: ask(question, history, prompt_version="final")
    Bot->>Bot: Step 1: Input Validation (length, characters, prompt injection checks)
    Bot->>Bot: Step 2: Contextual Follow-Up Query Resolution (using prior 5 turns)

    Bot->>Ret: search(query, top_k=4, prefer_semantic=False)
    Ret->>KB: Vector search (TF-IDF Cosine Similarity / Semantic Embeddings)
    KB-->>Ret: Ranked chunks with similarity scores

    alt Score < Relevance Threshold (0.13) or Empty
        Ret-->>Bot: Empty retrieved chunks []
        Bot->>Bot: Resolve responsible department (Office of Academic Affairs / Registrar)
        Bot-->>UI: Safe Refusal + Direct Official Office Referral (No LLM called)
    else Score >= Relevance Threshold (0.13)
        Ret-->>Bot: Top-k verified passages with page & filename metadata
        Bot->>Bot: Construct verified SourceCitation list strictly from chunk metadata

        alt Gemini API Key Configured & Service Available
            Bot->>Bot: Build Prompt with XML Delimiters (<context>, <user_query>)
            Bot->>LLM: generate_content(model="gemini-2.5-flash", temperature=0.0)
            alt Model Success
                LLM-->>Bot: Candidate Grounded Answer Text
            else Model 503 / High Demand / Timeout
                Bot->>LLM: Automated Failover to Alternate Flash Model
                LLM-->>Bot: Candidate Grounded Answer Text
            end
            Bot->>Guard: validate_and_guard_response(answer, retrieved_chunks)
            Guard-->>Bot: Guarded Answer (Hallucinated citations stripped)
        else No API Key Configured / Offline Fallback Mode
            Bot->>Bot: Assemble Direct Evidence Mode (Verbatim policy excerpts)
        end

        Bot-->>UI: ChatResult(answer, citations, mode)
    end

    UI->>DB: save_chat_turn(user_id, role, content, metadata_json)
    UI-->>Student: Render Calley Chat Bubble with Verified Citations Expander
```

---

## 3. Database Entity-Relationship (ER) Architecture

The platform uses a persistent, normalized SQLite relational database (`data/campus_auth.db`) with foreign key enforcement and automatic timestamp tracking.

```mermaid
erDiagram
    USERS ||--o{ SESSIONS : "creates"
    USERS ||--o{ OTPS : "receives"
    USERS ||--o{ LOGIN_ATTEMPTS : "records"
    USERS ||--o{ USER_CHAT_HISTORY : "persists"

    USERS {
        TEXT id PK "Unique User ID / Student Roll Number"
        TEXT email UK "Verified Email Address (@bennett.edu.in)"
        TEXT name "Full Name"
        TEXT password_hash "PBKDF2-HMAC-SHA256 Hash + Salt"
        TEXT role "student | faculty | admin"
        TEXT created_at "Registration Timestamp"
        TEXT updated_at "Last Profile Update Timestamp"
        INTEGER is_active "Account status flag (1/0)"
    }

    SESSIONS {
        TEXT session_token PK "Cryptographic 64-char Hex Token"
        TEXT user_id FK "References USERS(id)"
        TEXT created_at "Session Initialization Timestamp"
        TEXT expires_at "Hard Session Expiration (8 hrs)"
        TEXT last_active "Rolling Idle Timeout Timestamp (30 mins)"
        INTEGER is_revoked "Explicit Logout Revocation Flag (1/0)"
    }

    OTPS {
        INTEGER id PK "Auto-increment primary key"
        TEXT email "Target Recipient Email"
        TEXT otp_hash "SHA-256 Hashed 6-Digit OTP"
        TEXT purpose "registration | login | password_reset"
        TEXT expires_at "Expiration Timestamp (5 minutes)"
        TEXT created_at "Generation Timestamp"
        INTEGER attempts "Failed Entry Counter (Max 5)"
        INTEGER is_used "Single-Use Invalidation Flag (1/0)"
    }

    LOGIN_ATTEMPTS {
        INTEGER id PK "Auto-increment primary key"
        TEXT user_id "Target User Identifier"
        TEXT ip_address "Client Origin / Remote Host"
        TEXT attempt_time "Timestamp of Attempt"
        INTEGER success "Success Flag (1/0)"
    }

    USER_CHAT_HISTORY {
        INTEGER id PK "Auto-increment primary key"
        TEXT user_id FK "References USERS(id)"
        TEXT conversation_id "Conversation Session Key"
        TEXT role "user | assistant"
        TEXT content "Message Body Content"
        TEXT metadata_json "Citations, Mode, Scores (JSON)"
        TEXT timestamp "Message Creation Timestamp"
    }
```

---

## 4. Software Component & Class Topology

```mermaid
classDiagram
    class StreamlitApp {
        +init_session_state() void
        +handle_authentication() bool
        +render_sidebar_navigation() void
        +dispatch_current_page() void
    }

    class ChatbotController {
        -retriever: KnowledgeBase
        -ai_engine: AIEngine
        -prompt_manager: PromptManager
        +validate_input(question) dict
        +rewrite_followup(question, history) tuple
        +get_department_referral(question) str
        +ask(question, history, prefer_semantic, prompt_version) ChatResult
    }

    class KnowledgeBase {
        -documents: dict
        -chunks: list
        -vectorizer: TfidfVectorizer
        -tfidf_matrix: ndarray
        -embeddings_cache: dict
        +add_document(doc_info, chunks) void
        +remove_document(filename) bool
        +search(query, top_k, prefer_semantic) list
        +save_state() void
        +load_state() bool
        +get_stats() dict
    }

    class PDFProcessor {
        +validate_pdf(file_path_or_bytes) dict
        +extract_text_by_page(file_path_or_bytes, filename) list
        +clean_text(raw_text) str
        +compute_file_hash(data) str
    }

    class TextChunker {
        +chunk_pages(pages_data, filename) list
        +chunk_text(text, chunk_size, chunk_overlap) list
    }

    class AIEngine {
        -api_key: str
        -model_name: str
        -client: genai.Client
        +is_available() bool
        +classify_error(exc) AIEngineError
        +generate(system_prompt, user_prompt, temperature) str
        +embed(text) list
    }

    class PromptManager {
        -prompts: dict
        +load_prompts() void
        +get_prompt(version) str
        +build_prompt(query, chunks, version) str
    }

    class AuthService {
        +authenticate_user(user_id_or_email, password) dict
        +register_user(user_id, email, password, name, role) tuple
        +is_account_locked(user_id) bool
        +record_login_attempt(user_id, success) void
        +reset_password_with_otp(email, otp, new_password) tuple
    }

    class OTPService {
        +generate_and_send_otp(email, purpose) tuple
        +verify_otp(email, otp_code, purpose) tuple
        +hash_otp(code) str
    }

    class SessionService {
        +create_session(user_id) str
        +validate_session(token) dict
        +revoke_session(token) void
    }

    StreamlitApp --> AuthService : authenticates user
    StreamlitApp --> SessionService : validates session
    AuthService --> OTPService : verifies 2FA
    StreamlitApp --> ChatbotController : handles inquiry
    ChatbotController --> KnowledgeBase : retrieves context
    ChatbotController --> PromptManager : loads template
    ChatbotController --> AIEngine : queries model
    KnowledgeBase --> TextChunker : splits document
    TextChunker --> PDFProcessor : extracts clean pages
```
