"""
Chatbot Controller for AI-Powered Campus Helpdesk Assistant.
Coordinates query validation, follow-up rewriting, retrieval thresholding,
answer generation (or fallback evidence display), and metadata-grounded citations.
"""

import sys
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

from config import settings
from core.retriever import KnowledgeBase, RetrievedChunk
from core.ai_engine import AIEngine
from core.prompt_manager import PromptManager
from core.response_guard import validate_and_guard_response
from core.logger import logger


# ==============================================================================
# Data Structures
# ==============================================================================
@dataclass
class SourceCitation:
    """Represents a verified citation linked directly to chunk metadata."""
    filename: str
    page: int
    snippet: str
    score: float

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return getattr(self, item)
        except AttributeError:
            return default

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "page": self.page,
            "snippet": self.snippet,
            "score": self.score
        }


@dataclass
class ChatResult:
    """Complete response returned by the chatbot controller."""
    answer: str
    sources: List[SourceCitation] = field(default_factory=list)
    mode: str = "fallback"  # "gemini" | "fallback" | "no_context" | "error"
    retrieval_method: str = "TF-IDF lexical"
    error: Optional[str] = None
    rewritten_query: Optional[str] = None
    rewriter_used: str = "none"  # "llm" | "heuristic" | "none"

    def __getitem__(self, item: str) -> Any:
        # Compatibility with legacy dict-style access
        if item == "citations":
            return [s.to_dict() for s in self.sources]
        elif item == "is_fallback":
            return self.mode == "fallback"
        elif item == "has_context":
            return self.mode in ("gemini", "fallback") and len(self.sources) > 0
        elif item == "method":
            return self.retrieval_method
        elif item == "resolved_query":
            return self.rewritten_query
        elif hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return self[item]
        except KeyError:
            return default


# ==============================================================================
# Chatbot Controller Class
# ==============================================================================
class ChatbotController:
    """The central brain orchestrating student inquiries through the RAG pipeline."""

    def __init__(
        self,
        retriever: Optional[KnowledgeBase] = None,
        ai_engine: Optional[AIEngine] = None,
        prompt_manager: Optional[PromptManager] = None
    ):
        self.retriever = retriever if retriever is not None else KnowledgeBase()
        self.ai_engine = ai_engine if ai_engine is not None else AIEngine()
        self.prompt_manager = prompt_manager if prompt_manager is not None else PromptManager()
        self.retriever.set_ai_engine(self.ai_engine)

    def validate_input(self, question: str) -> Dict[str, Any]:
        """
        Validates student question string.
        Rejects empty/whitespace input, oversized questions, or repeated character floods.
        """
        if not question or not question.strip():
            return {
                "valid": False,
                "error": "Please enter a valid question or topic."
            }

        cleaned = question.strip()
        if len(cleaned) > settings.MAX_QUESTION_CHARS:
            return {
                "valid": False,
                "error": f"Your question exceeds the maximum allowed length of {settings.MAX_QUESTION_CHARS} characters. Please shorten your question."
            }

        # Check for spammy character repetition (e.g. 'aaaaaaaaaaaa')
        if re.search(r'(.)\1{20,}', cleaned):
            return {
                "valid": False,
                "error": "Inquiry contains excessive repetitive characters. Please enter a natural question."
            }

        return {
            "valid": True,
            "query": cleaned
        }

    def validate_query(self, query: str) -> Dict[str, Any]:
        """Backward-compatible alias for validate_input."""
        return self.validate_input(query)

    def rewrite_followup(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, str]:
        """
        Resolves conversational follow-up questions into standalone search queries.
        Uses LLM if available, otherwise a simple keyword-appending heuristic.
        
        Returns:
            Tuple of (rewritten_query, rewriter_name) where rewriter_name is 'llm', 'heuristic', or 'none'.
        """
        if not history:
            return question, "none"

        # Detect pronouns or typical conversational continuation signals
        continuation_signals = [
            r"\b(it|its|they|them|their|those|these|this|that)\b",
            r"\b(and|what about|how about|where is it|when is it|who do i contact|why|can i also)\b",
            r"\b(the deadline|the fee|the office|the date|the form|that office)\b"
        ]

        is_followup = any(re.search(sig, question.lower()) for sig in continuation_signals)
        is_short = len(question.strip().split()) <= 4

        if not is_followup and not is_short:
            return question, "none"

        # Try LLM rewriter if API is available
        if self.ai_engine.is_available():
            try:
                recent_history = history[-settings.HISTORY_TURNS:]
                formatted_history = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                    for msg in recent_history
                ])
                rewrite_prompt = (
                    "Given the chat history below, rewrite the student's follow-up question into a standalone, "
                    "self-contained search query. Preserve the original intent. Output ONLY the standalone query.\n\n"
                    f"Chat History:\n{formatted_history}\n\n"
                    f"Follow-up Question: {question}\nStandalone Query:"
                )
                rewritten = self.ai_engine.generate(
                    system_prompt="You are a query rewriting assistant. Output only the standalone question.",
                    user_prompt=rewrite_prompt,
                    temperature=0.0
                )
                if rewritten and len(rewritten.strip()) > 3:
                    return rewritten.strip(), "llm"
            except Exception:
                pass

        # Heuristic fallback: borrow meaningful subject nouns from previous user turn
        last_user_query = ""
        for msg in reversed(history):
            if msg.get("role") == "user":
                last_user_query = msg.get("content", "")
                break

        if not last_user_query:
            return question, "none"

        stop_words = {
            "what", "is", "the", "for", "in", "a", "an", "how", "can", "i", "where",
            "does", "do", "tell", "me", "about", "and", "to", "of", "it", "that", "this"
        }
        prev_words = [w for w in re.findall(r'\b\w+\b', last_user_query.lower()) if w not in stop_words]
        context_hint = " ".join(prev_words[:4])

        if context_hint:
            return f"{question} ({context_hint})", "heuristic"

        return question, "none"

    def get_department_referral(self, query: str) -> str:
        """
        Determines the appropriate official campus department based on query domain.
        Used when the uploaded documents lack verified facts.
        """
        q = query.lower()

        if any(w in q for w in ["fee", "tuition", "dues", "payment", "fine", "refund", "bank", "receipt", "scholarship", "pool", "swimming"]):
            return "Accounts & Finance Desk (Administrative Block, Room 102 | accounts@university.edu)"
        elif any(w in q for w in ["exam", "grade", "gpa", "transcript", "marksheet", "revaluation", "result", "backlog"]):
            return "Office of the Controller of Examinations (Exam Block, Ground Floor | examdesk@university.edu)"
        elif any(w in q for w in ["hostel", "mess", "room", "warden", "accommodation", "curfew", "boarding"]):
            return "Hostel & Residential Life Office (Student Activity Center | hostelaffairs@university.edu)"
        elif any(w in q for w in ["admission", "enrollment", "transfer", "counseling", "eligibility", "prospectus"]):
            return "Admissions Directorate (Main Welcome Center | admissions@university.edu)"
        elif any(w in q for w in ["library", "book", "journal", "borrow", "catalog", "reading room"]):
            return "Central University Library Desk (Knowledge Center, Level 1 | library@university.edu)"
        elif any(w in q for w in ["health", "medical", "doctor", "emergency", "clinic", "counselor"]):
            return "University Health & Wellness Center (Campus Clinic | health@university.edu)"
        elif any(w in q for w in ["wifi", "email", "portal", "lms", "login", "password", "it helpdesk", "laptop"]):
            return "IT & Network Services Helpdesk (Tech Annex, Room 204 | itsupport@university.edu)"
        else:
            return "Office of Academic Affairs & Student Records (Main Building, Window 4 | helpdesk@university.edu)"

    def ask(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
        prefer_semantic: bool = False,
        prompt_version: str = "final"
    ) -> ChatResult:
        """
        Processes a student question through the complete Phase 2 backend pipeline.
        
        Flow:
        1. Input validation (empty/whitespace/too long).
        2. Verify documents are indexed.
        3. Follow-up query rewriting.
        4. Information retrieval with relevance threshold gating.
        5. Grounded Gemini generation (if key configured) or Fallback evidence display.
        6. Citations constructed strictly from retrieved chunk metadata.
        
        Returns:
            ChatResult dataclass instance.
        """
        # Step 1: Input Validation
        validation = self.validate_input(question)
        if not validation["valid"]:
            return ChatResult(
                answer=f"⚠️ {validation['error']}",
                sources=[],
                mode="error",
                retrieval_method=self.retriever.active_method(),
                error=validation["error"]
            )

        cleaned_question = validation["query"]

        # Step 2: Check Document Ingestion State
        stats = self.retriever.get_stats()
        if stats["chunk_count"] == 0:
            office = self.get_department_referral(cleaned_question)
            return ChatResult(
                answer=(
                    "ℹ️ **No official university documents are currently indexed in the knowledge base.**\n\n"
                    "Please upload the relevant university handbook or policy document in the **Knowledge Base** tab, "
                    f"or reach out to the:\n\n👉 **{office}**"
                ),
                sources=[],
                mode="no_context",
                retrieval_method=self.retriever.active_method(),
                error="No documents indexed in knowledge base"
            )

        # Step 3: Conversational Follow-Up Query Resolution
        resolved_query, rewriter_used = self.rewrite_followup(cleaned_question, history)

        # Step 4: Information Retrieval
        retrieved_chunks: List[RetrievedChunk] = self.retriever.search(
            query=resolved_query,
            top_k=settings.TOP_K,
            prefer_semantic=prefer_semantic
        )

        active_method_label = self.retriever.active_method()

        # Step 5: Relevance Thresholding & Immediate Refusal Gate
        # When nothing clears the threshold, retriever returns an empty list []
        if not retrieved_chunks:
            office = self.get_department_referral(cleaned_question)
            refusal_text = (
                "I cannot verify this information in the uploaded official university documents.\n\n"
                f"To get authoritative assistance on this matter, please contact the:\n\n"
                f"🏛️ **{office}**"
            )
            return ChatResult(
                answer=refusal_text,
                sources=[],
                mode="no_context",
                retrieval_method=active_method_label,
                rewritten_query=resolved_query,
                rewriter_used=rewriter_used
            )

        # Step 6: Construct Structured Citations Strictly from Retrieved Metadata
        citations: List[SourceCitation] = []
        for rc in retrieved_chunks:
            chunk = rc.chunk
            snippet_text = chunk.text[:240].strip() + ("..." if len(chunk.text) > 240 else "")
            citations.append(SourceCitation(
                filename=chunk.filename,
                page=chunk.page,
                snippet=snippet_text,
                score=rc.score
            ))

        # Step 7: Answer Generation vs. Fallback Evidence Display
        if self.ai_engine.is_available():
            try:
                final_prompt = self.prompt_manager.build_prompt(
                    query=cleaned_question,
                    chunks=retrieved_chunks,
                    version=prompt_version
                )
                generated_answer = self.ai_engine.generate(
                    system_prompt=None,
                    user_prompt=final_prompt,
                    temperature=0.0
                )
                # Response guard: ensure no hallucinated citations remain
                guarded_answer, removed_citations = validate_and_guard_response(
                    generated_answer,
                    retrieved_chunks
                )
                logger.info(
                    f"Generated AI answer with {len(citations)} sources "
                    f"(unverified citations removed: {len(removed_citations)})"
                )
                return ChatResult(
                    answer=guarded_answer,
                    sources=citations,
                    mode="gemini",
                    retrieval_method=active_method_label,
                    rewritten_query=resolved_query,
                    rewriter_used=rewriter_used
                )
            except Exception as e:
                # On any API error, gracefully degrade to fallback evidence
                error_msg = str(e)
                fallback_header = (
                    f"⚠️ **AI generation encountered an error ({error_msg}).**\n\n"
                    "*Showing direct retrieved evidence from official documents:*\n\n"
                )
                excerpts = []
                for idx, rc in enumerate(retrieved_chunks, 1):
                    clean_text = "\n> ".join(line.strip() for line in rc.chunk.text.strip().splitlines() if line.strip())
                    excerpts.append(
                        f"📄 **Passage {idx}** (From `{rc.chunk.filename}`, Page {rc.chunk.page}):\n"
                        f"> {clean_text}"
                    )
                return ChatResult(
                    answer=fallback_header + "\n\n".join(excerpts),
                    sources=citations,
                    mode="fallback",
                    retrieval_method=f"{active_method_label} (API Error Fallback)",
                    error=error_msg,
                    rewritten_query=resolved_query,
                    rewriter_used=rewriter_used
                )
        else:
            # Fallback Mode: No API Key Configured
            fallback_header = (
                "⚠️ **AI generation unavailable (no Gemini API key configured).**\n\n"
                "**Showing retrieved evidence from official university documents:**\n\n"
            )
            excerpts = []
            for idx, rc in enumerate(retrieved_chunks, 1):
                clean_text = "\n> ".join(line.strip() for line in rc.chunk.text.strip().splitlines() if line.strip())
                excerpts.append(
                    f"📄 **Excerpt {idx}** — *{rc.chunk.filename}* (Page {rc.chunk.page}):\n"
                    f"> {clean_text}"
                )
            evidence_body = fallback_header + "\n\n".join(excerpts)
            return ChatResult(
                answer=evidence_body,
                sources=citations,
                mode="fallback",
                retrieval_method=active_method_label,
                rewritten_query=resolved_query,
                rewriter_used=rewriter_used
            )

    def answer_query(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
        prefer_semantic: bool = False,
        prompt_version: str = "final"
    ) -> ChatResult:
        """Backward-compatible alias for ask()."""
        return self.ask(
            question=query,
            history=history,
            prefer_semantic=prefer_semantic,
            prompt_version=prompt_version
        )


# ==============================================================================
# CLI Smoke Test Execution Entry Point (python -m core.chatbot)
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("AI-Powered Campus Helpdesk Assistant | CLI Smoke Test")
    print("=" * 70)

    # 1. Ensure demo PDF exists
    demo_pdf_path = settings.DEMO_DIR / "university_policy_demo.pdf"
    if not demo_pdf_path.exists():
        print("Generating demo PDF document...")
        from data.demo.generate_demo_pdf import build_pdf
        build_pdf()

    # 2. Ingest demo PDF
    print(f"\n1. Ingesting demo PDF: {demo_pdf_path.name}")
    from core.pdf_processor import process_document
    from core.text_chunker import chunk_pages

    with open(demo_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    doc = process_document(pdf_bytes, filename=demo_pdf_path.name)
    chunks = chunk_pages(doc.pages, filename=doc.filename)

    kb = KnowledgeBase()
    kb.clear_all()
    kb.add_document(doc, chunks)
    print(f"   Indexed: {len(doc.pages)} pages, {len(chunks)} chunks.")
    print(f"   Active retrieval method: '{kb.active_method()}'")

    # 3. Instantiate Chatbot
    bot = ChatbotController(retriever=kb, ai_engine=AIEngine(api_key=""))

    # 4. In-Scope Question
    q_in = "What is the minimum attendance requirement to appear in final exams?"
    print(f"\n2. Testing In-Scope Question:")
    print(f"   Query: '{q_in}'")
    res_in = bot.ask(q_in)
    print(f"   Mode: {res_in.mode}")
    print(f"   Retrieval Method: {res_in.retrieval_method}")
    print(f"   Sources Found: {len(res_in.sources)}")
    if res_in.sources:
        print(f"   Top Citation: {res_in.sources[0].filename}, Page {res_in.sources[0].page} (Score: {res_in.sources[0].score})")
    print(f"   Answer Preview:\n   {res_in.answer[:200]}...")

    # 5. Out-of-Scope Question
    q_out = "What is the fee for the campus swimming pool membership?"
    print(f"\n3. Testing Out-of-Scope Question (Refusal Test):")
    print(f"   Query: '{q_out}'")
    res_out = bot.ask(q_out)
    print(f"   Mode: {res_out.mode}")
    print(f"   Sources Found: {len(res_out.sources)}")
    print(f"   Answer Preview:\n   {res_out.answer}")

    print("\n" + "=" * 70)
    print("CLI Smoke Test Finished Successfully!")
    print("=" * 70)
