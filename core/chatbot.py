"""
Chatbot Controller for AI-Powered Campus Helpdesk Assistant.
Coordinates query validation, follow-up rewriting, retrieval thresholding,
answer generation (or fallback evidence display), and metadata-grounded citations.
"""

import re
from typing import List, Dict, Any, Optional

from config import settings
from core.retriever import DocumentRetriever
from core.ai_engine import AIEngine
from core.prompt_manager import PromptManager


class ChatbotController:
    """The central brain orchestrating student queries through the RAG pipeline."""

    def __init__(
        self,
        retriever: Optional[DocumentRetriever] = None,
        ai_engine: Optional[AIEngine] = None,
        prompt_manager: Optional[PromptManager] = None
    ):
        self.retriever = retriever if retriever is not None else DocumentRetriever()
        self.ai_engine = ai_engine if ai_engine is not None else AIEngine()
        self.prompt_manager = prompt_manager if prompt_manager is not None else PromptManager()

    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validates student input string.
        Rejects empty/whitespace input, oversized queries, or repeated character floods.
        """
        if not query or not query.strip():
            return {
                "valid": False,
                "error": "Please enter a valid question or topic."
            }

        cleaned = query.strip()
        if len(cleaned) > 1000:
            return {
                "valid": False,
                "error": "Your inquiry exceeds the maximum allowed length of 1,000 characters. Please shorten your question."
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

    def rewrite_followup(self, query: str, history: List[Dict[str, str]]) -> str:
        """
        Resolves conversational follow-up questions into standalone search queries.
        Uses contextual keywords from recent conversation history.
        """
        if not history:
            return query

        # Detect pronouns or typical conversational continuation signals
        continuation_signals = [
            r"\b(it|its|they|them|their|those|these|this|that)\b",
            r"\b(and|what about|how about|where is it|when is it|who do i contact|why|can i also)\b",
            r"\b(the deadline|the fee|the office|the date|the form)\b"
        ]
        
        is_followup = any(re.search(sig, query.lower()) for sig in continuation_signals)

        if not is_followup:
            return query

        # Extract last user question to borrow subject anchor
        last_user_query = ""
        for msg in reversed(history):
            if msg.get("role") == "user":
                last_user_query = msg.get("content", "")
                break

        if not last_user_query:
            return query

        # Synthesize a contextual query incorporating previous context keywords
        # Extract meaningful nouns/keywords from previous question
        stop_words = {"what", "is", "the", "for", "in", "a", "an", "how", "can", "i", "where", "does", "do"}
        prev_words = [w for w in re.findall(r'\b\w+\b', last_user_query.lower()) if w not in stop_words]
        context_hint = " ".join(prev_words[:4])

        return f"{query} ({context_hint})" if context_hint else query

    def get_department_referral(self, query: str) -> str:
        """
        Determines the appropriate official campus department based on query domain.
        Used when the uploaded documents lack verified facts.
        """
        q = query.lower()

        if any(w in q for w in ["fee", "tuition", "dues", "payment", "fine", "refund", "bank", "receipt", "scholarship"]):
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

    def answer_query(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
        prefer_semantic: bool = False,
        prompt_version: str = "final"
    ) -> Dict[str, Any]:
        """
        Executes the full RAG pipeline for a student inquiry:
        1. Validate query.
        2. Resolve follow-ups if history provided.
        3. Search knowledge base.
        4. If score < threshold, return refusal with department routing WITHOUT calling LLM.
        5. If score >= threshold:
           - Call Gemini (if key configured) with prompt_manager.
           - Or display structured excerpts (if fallback mode).
        6. Extract and return structured citations strictly from retrieved chunks.
        """
        # Step 1: Input Validation
        validation = self.validate_query(query)
        if not validation["valid"]:
            return {
                "answer": f"⚠️ {validation['error']}",
                "citations": [],
                "is_fallback": False,
                "has_context": False,
                "method": "Validation Failed",
                "resolved_query": query
            }

        cleaned_query = validation["query"]

        # Step 2: Check if knowledge base is empty
        stats = self.retriever.get_stats()
        if stats["chunk_count"] == 0:
            office = self.get_department_referral(cleaned_query)
            return {
                "answer": (
                    "ℹ️ **No official university documents are currently indexed in the knowledge base.**\n\n"
                    f"I cannot answer questions without verified official documents. Please upload the relevant university "
                    f"handbook or policy document in the **Knowledge Base** tab, or reach out to the:\n\n"
                    f"👉 **{office}**"
                ),
                "citations": [],
                "is_fallback": True,
                "has_context": False,
                "method": "Knowledge Base Empty",
                "resolved_query": cleaned_query
            }

        # Step 3: Follow-up resolution
        resolved_query = self.rewrite_followup(cleaned_query, history or [])

        # Step 4: Information Retrieval
        results, has_relevant_context, method_name = self.retriever.search(
            query=resolved_query,
            ai_engine=self.ai_engine,
            top_k=settings.TOP_K,
            threshold=settings.SIMILARITY_THRESHOLD,
            prefer_semantic=prefer_semantic
        )

        # Step 5: Relevance Thresholding & Refusal Gate
        if not has_relevant_context or not results:
            office = self.get_department_referral(cleaned_query)
            refusal_text = (
                "I cannot verify this information in the uploaded official university documents.\n\n"
                f"To get authoritative assistance on this matter, please contact the:\n\n"
                f"🏛️ **{office}**"
            )
            return {
                "answer": refusal_text,
                "citations": [],
                "is_fallback": not self.ai_engine.is_configured(),
                "has_context": False,
                "method": method_name,
                "resolved_query": resolved_query
            }

        # Step 6: Construct structured citations from retrieved chunks
        citations = []
        for chunk in results:
            citations.append({
                "filename": chunk.get("filename", "Unknown Document"),
                "page": chunk.get("page", 1),
                "chunk_id": chunk.get("chunk_id", ""),
                "score": chunk.get("score", 0.0),
                "snippet": chunk.get("text", "")[:240].strip() + ("..." if len(chunk.get("text", "")) > 240 else "")
            })

        # Step 7: Grounded Answer Generation vs. Fallback Evidence Display
        if self.ai_engine.is_configured():
            try:
                final_prompt = self.prompt_manager.build_prompt(
                    query=cleaned_query,
                    chunks=results,
                    version=prompt_version
                )
                generated_answer = self.ai_engine.generate_response(
                    prompt=final_prompt,
                    temperature=0.0
                )
                return {
                    "answer": generated_answer,
                    "citations": citations,
                    "is_fallback": False,
                    "has_context": True,
                    "method": method_name,
                    "resolved_query": resolved_query
                }
            except Exception as e:
                # On any API error during generation, gracefully downgrade to Fallback Mode
                fallback_msg = (
                    f"⚠️ **AI generation encountered an error ({str(e)}).**\n\n"
                    f"*Falling back to direct retrieved evidence from official documents:*\n\n"
                )
                excerpts = []
                for idx, c in enumerate(results, 1):
                    excerpts.append(
                        f"**Passage {idx}** (From `{c['filename']}`, Page {c['page']}):\n"
                        f"> {c['text']}"
                    )
                fallback_body = fallback_msg + "\n\n".join(excerpts)
                return {
                    "answer": fallback_body,
                    "citations": citations,
                    "is_fallback": True,
                    "has_context": True,
                    "method": f"{method_name} (API Error Fallback)",
                    "resolved_query": resolved_query
                }
        else:
            # Fallback Mode: API Key Absent
            fallback_header = (
                "⚠️ **AI generation unavailable (no Gemini API key configured).**\n\n"
                "**Showing retrieved evidence from official university documents:**\n\n"
            )
            excerpts = []
            for idx, c in enumerate(results, 1):
                excerpts.append(
                    f"📄 **Excerpt {idx}** — *{c['filename']}* (Page {c['page']}):\n"
                    f"> \"{c['text']}\""
                )
            evidence_body = fallback_header + "\n\n".join(excerpts)
            return {
                "answer": evidence_body,
                "citations": citations,
                "is_fallback": True,
                "has_context": True,
                "method": method_name,
                "resolved_query": resolved_query
            }
