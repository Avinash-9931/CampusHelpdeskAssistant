"""
Dual-Tier Document Retriever & Knowledge Base for AI-Powered Campus Helpdesk Assistant.
Supports:
1. Lexical Retrieval (TF-IDF with n-grams, sublinear tf, and morphological normalization).
2. Semantic Retrieval (Gemini Embeddings with Cosine Similarity and disk caching).
Implements KnowledgeBase management, persistence, and relevance thresholding.
"""

import os
import re
import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional, Union
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

from config import settings
from core.pdf_processor import ProcessedDocument, PageData
from core.text_chunker import TextChunk


# ==============================================================================
# Data Structures
# ==============================================================================
@dataclass
class RetrievedChunk:
    """Represents a retrieved chunk with its relevance score and retrieval method."""
    chunk: TextChunk
    score: float
    method: str

    def __getitem__(self, item: str) -> Any:
        if hasattr(self.chunk, item):
            return getattr(self.chunk, item)
        elif item == "score":
            return self.score
        elif item == "method":
            return self.method
        elif item == "char_count":
            return len(self.chunk.text)
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return self[item]
        except KeyError:
            return default

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk.chunk_id,
            "filename": self.chunk.filename,
            "page": self.chunk.page,
            "text": self.chunk.text,
            "score": self.score,
            "method": self.method,
            "char_count": len(self.chunk.text)
        }


# ==============================================================================
# Morphological Normalization Helper
# ==============================================================================
def normalize_text(text: str) -> str:
    """Applies lightweight morphological normalization for robust keyword matching."""
    if not text:
        return ""
    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    res = []
    for w in words:
        if len(w) > 4 and w.endswith("ing"):
            w = w[:-3]
            if len(w) > 2 and w[-1] == w[-2]:
                w = w[:-1]
        elif len(w) > 5 and w.endswith("ation"):
            w = w[:-5]
        elif len(w) > 6 and w.endswith("drawal"):
            w = w[:-2]
        elif len(w) > 6 and w.endswith("ance"):
            w = w[:-4]  # attendance -> attend
        elif len(w) > 4 and w.endswith("sses"):
            w = w[:-2]
        elif len(w) > 4 and w.endswith("ies"):
            w = w[:-3] + "y"
        elif len(w) > 3 and w.endswith("es"):
            w = w[:-2]  # classes -> class
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        elif len(w) > 4 and w.endswith("ed"):
            w = w[:-2]
            if len(w) > 2 and w[-1] == w[-2]:
                w = w[:-1]
        res.append(w)
    return " ".join(res)


# ==============================================================================
# KnowledgeBase Class
# ==============================================================================
class KnowledgeBase:
    """
    Manages document storage, chunk indexes, persistence, and dual-tier search.
    """

    def __init__(self, ai_engine=None):
        self.ai_engine = ai_engine
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.chunks: List[TextChunk] = []
        
        # Lexical Index
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.corpus_vocab: set = set()
        
        # Semantic Index Cache: chunk_id -> list[float]
        self.embeddings_cache: Dict[str, List[float]] = {}
        
        # Load persisted data
        self.load_from_disk()

    def set_ai_engine(self, ai_engine) -> None:
        """Sets or updates the AI engine reference for embeddings."""
        self.ai_engine = ai_engine

    def active_method(self) -> str:
        """
        Returns exactly the name of the currently active retrieval method:
        'TF-IDF lexical' or 'Gemini semantic embeddings'.
        Never mislabels.
        """
        if self.ai_engine and self.ai_engine.is_available() and getattr(self, "prefer_semantic", False):
            return "Gemini semantic embeddings"
        return "TF-IDF lexical"

    # ==========================================================================
    # Persistence
    # ==========================================================================
    def persist_to_disk(self) -> None:
        """Saves documents and chunks metadata to JSON storage."""
        data = {
            "documents": self.documents,
            "chunks": [c.to_dict() for c in self.chunks],
            "updated_at": datetime.now().isoformat()
        }
        with open(settings.KNOWLEDGE_BASE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self._save_embeddings_cache()

    def load_from_disk(self) -> bool:
        """Loads documents and chunks from JSON storage and rebuilds the index."""
        if not settings.KNOWLEDGE_BASE_FILE.exists():
            return False

        try:
            with open(settings.KNOWLEDGE_BASE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.documents = data.get("documents", {})
                raw_chunks = data.get("chunks", [])
                self.chunks = [
                    TextChunk(
                        chunk_id=rc.get("chunk_id", ""),
                        filename=rc.get("filename", ""),
                        page=rc.get("page", 1),
                        text=rc.get("text", "")
                    )
                    for rc in raw_chunks
                ]

            self.rebuild_index()
            self._load_embeddings_cache()
            return True
        except Exception:
            self.documents = {}
            self.chunks = []
            return False

    def _load_embeddings_cache(self) -> None:
        """Loads embeddings cache from disk if available."""
        if settings.EMBEDDINGS_CACHE_FILE.exists():
            try:
                self.embeddings_cache = np.load(
                    settings.EMBEDDINGS_CACHE_FILE,
                    allow_pickle=True
                ).item()
            except Exception:
                self.embeddings_cache = {}

    def _save_embeddings_cache(self) -> None:
        """Persists embeddings cache to disk."""
        try:
            np.save(settings.EMBEDDINGS_CACHE_FILE, self.embeddings_cache)
        except Exception:
            pass

    # ==========================================================================
    # Indexing & Document Management
    # ==========================================================================
    def rebuild_index(self) -> None:
        """Fits TF-IDF vectorizer over normalized chunk texts."""
        if not self.chunks:
            self.vectorizer = None
            self.tfidf_matrix = None
            self.corpus_vocab = set()
            return

        corpus = [normalize_text(c.text) for c in self.chunks]
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 1),
            stop_words="english",
            sublinear_tf=True
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.corpus_vocab = set(self.vectorizer.get_feature_names_out())

    def add_document(
        self,
        doc_or_filename: Union[ProcessedDocument, str, None] = None,
        chunks: Optional[List[Union[TextChunk, Dict[str, Any]]]] = None,
        filename: Optional[str] = None,
        file_hash: Optional[str] = None,
        size_bytes: int = 0,
        pages_data: Optional[List[Any]] = None,
        **kwargs
    ) -> None:
        """
        Adds a processed document and its chunks into the knowledge base.
        Accepts ProcessedDocument, positional parameters, or keyword arguments.
        """
        target_name = filename or ""
        target_hash = file_hash or ""
        target_size = size_bytes
        page_count = len(pages_data) if pages_data else 1
        target_chunks = chunks or []

        if isinstance(doc_or_filename, ProcessedDocument):
            target_name = doc_or_filename.filename
            target_hash = doc_or_filename.hash
            page_count = doc_or_filename.page_count
            target_size = getattr(doc_or_filename, "size_bytes", 0)
        elif isinstance(doc_or_filename, str):
            target_name = doc_or_filename

        if not target_name:
            target_name = "document.pdf"

        # Normalize chunks to List[TextChunk]
        normalized_chunks: List[TextChunk] = []
        for c in target_chunks:
            if isinstance(c, TextChunk):
                normalized_chunks.append(c)
            elif isinstance(c, dict):
                normalized_chunks.append(TextChunk(
                    chunk_id=c.get("chunk_id", ""),
                    filename=c.get("filename", target_name),
                    page=c.get("page", 1),
                    text=c.get("text", "")
                ))

        self.documents[target_name] = {
            "filename": target_name,
            "hash": target_hash,
            "size_bytes": target_size,
            "page_count": page_count,
            "chunk_count": len(normalized_chunks),
            "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Processed"
        }

        # Remove any previous chunks for this document (idempotency)
        self.chunks = [c for c in self.chunks if c.filename != target_name]
        self.chunks.extend(normalized_chunks)

        self.rebuild_index()
        self.persist_to_disk()

    def remove_document(self, filename: str) -> bool:
        """
        Removes a document and all associated chunks from the index.
        Returns True if found and removed.
        """
        if filename not in self.documents:
            return False

        del self.documents[filename]
        self.chunks = [c for c in self.chunks if c.filename != filename]

        # Invalidate embeddings cache for this document
        prefix = f"{filename}_"
        for cid in list(self.embeddings_cache.keys()):
            if cid.startswith(prefix):
                del self.embeddings_cache[cid]

        self.rebuild_index()
        self.persist_to_disk()
        return True

    def delete_document(self, filename: str) -> bool:
        """Backward-compatible alias for remove_document."""
        return self.remove_document(filename)

    def list_documents(self) -> List[Dict[str, Any]]:
        """Returns metadata list of all currently indexed documents."""
        return list(self.documents.values())

    def clear_all(self) -> None:
        """Completely clears all indexed documents, chunks, and caches."""
        self.documents = {}
        self.chunks = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.corpus_vocab = set()
        self.embeddings_cache = {}

        if settings.KNOWLEDGE_BASE_FILE.exists():
            settings.KNOWLEDGE_BASE_FILE.unlink(missing_ok=True)
        if settings.EMBEDDINGS_CACHE_FILE.exists():
            settings.EMBEDDINGS_CACHE_FILE.unlink(missing_ok=True)

    # ==========================================================================
    # Retrieval Methods
    # ==========================================================================
    def search_lexical(
        self,
        query: str,
        top_k: int = settings.TOP_K,
        threshold: float = settings.MIN_RELEVANCE_SCORE
    ) -> List[RetrievedChunk]:
        """
        Executes TF-IDF lexical search with sublinear tf and cosine similarity.
        Applies MIN_RELEVANCE_SCORE. If no chunk clears the threshold, returns [].
        """
        if not self.chunks or self.vectorizer is None or self.tfidf_matrix is None:
            return []

        norm_query = normalize_text(query)
        if not norm_query:
            return []

        # Out-of-vocabulary check: on detailed queries (>=4 substantive terms), reject if >50% missing from corpus
        norm_stops = set(normalize_text(" ".join(ENGLISH_STOP_WORDS)).split())
        q_words = [w for w in norm_query.split() if w not in norm_stops and len(w) > 2]
        if len(q_words) >= 4 and self.corpus_vocab:
            oov_count = sum(1 for w in q_words if w not in self.corpus_vocab)
            if (oov_count / len(q_words)) > 0.50:
                return []

        query_vec = self.vectorizer.transform([norm_query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        ranked_indices = np.argsort(similarities)[::-1]
        results: List[RetrievedChunk] = []

        for idx in ranked_indices[:top_k]:
            score = float(similarities[idx])
            if score >= threshold:
                chunk = self.chunks[idx]
                # Filter out spurious single-word matches on detailed queries (>=4 substantive terms)
                if len(q_words) >= 4:
                    chunk_words = set(normalize_text(chunk.text).split())
                    matching = [w for w in q_words if w in chunk_words]
                    if len(matching) <= 1:
                        continue
                results.append(RetrievedChunk(
                    chunk=chunk,
                    score=round(score, 4),
                    method="TF-IDF lexical"
                ))

        return results

    def search_semantic(
        self,
        query: str,
        top_k: int = settings.TOP_K,
        threshold: float = 0.50
    ) -> List[RetrievedChunk]:
        """
        Executes semantic retrieval using Gemini embeddings and cosine similarity.
        If embedding generation fails, automatically falls back to lexical search.
        """
        if not self.chunks or not self.ai_engine or not self.ai_engine.is_available():
            return self.search_lexical(query, top_k)

        try:
            query_vec_list = self.ai_engine.get_embedding(query)
            if not query_vec_list:
                return self.search_lexical(query, top_k)

            # Ensure all chunks have embeddings cached
            chunk_vectors = []
            valid_indices = []

            for i, chunk in enumerate(self.chunks):
                cid = chunk.chunk_id
                if cid not in self.embeddings_cache:
                    emb = self.ai_engine.get_embedding(chunk.text)
                    if emb:
                        self.embeddings_cache[cid] = emb

                if cid in self.embeddings_cache:
                    chunk_vectors.append(self.embeddings_cache[cid])
                    valid_indices.append(i)

            if not chunk_vectors:
                return self.search_lexical(query, top_k)

            self._save_embeddings_cache()

            q_vec = np.array(query_vec_list, dtype=np.float32)
            c_mat = np.array(chunk_vectors, dtype=np.float32)

            q_norm = np.linalg.norm(q_vec)
            c_norms = np.linalg.norm(c_mat, axis=1)
            scores = np.dot(c_mat, q_vec) / (c_norms * q_norm + 1e-9)

            ranked_order = np.argsort(scores)[::-1]
            results: List[RetrievedChunk] = []

            for rank_idx in ranked_order[:top_k]:
                score = float(scores[rank_idx])
                if score >= threshold:
                    orig_idx = valid_indices[rank_idx]
                    chunk = self.chunks[orig_idx]
                    results.append(RetrievedChunk(
                        chunk=chunk,
                        score=round(score, 4),
                        method="Gemini semantic embeddings"
                    ))

            return results
        except Exception:
            # Fall back to lexical on any semantic error
            return self.search_lexical(query, top_k)

    def search(
        self,
        query: str,
        top_k: int = settings.TOP_K,
        ai_engine=None,
        threshold: Optional[float] = None,
        prefer_semantic: bool = False
    ) -> List[RetrievedChunk]:
        """
        Primary search method.
        Returns List[RetrievedChunk].
        When nothing clears the threshold, returns [] (meaning 'no relevant context').
        """
        thresh = threshold if threshold is not None else settings.MIN_RELEVANCE_SCORE
        engine = ai_engine or self.ai_engine

        if prefer_semantic and engine and engine.is_available():
            results = self.search_semantic(query, top_k=top_k)
            if results:
                return results

        return self.search_lexical(query, top_k=top_k, threshold=thresh)

    def get_stats(self) -> Dict[str, Any]:
        """Returns summary statistics for UI live status displays."""
        doc_count = len(self.documents)
        chunk_count = len(self.chunks)
        total_pages = sum(d.get("page_count", 0) for d in self.documents.values())
        return {
            "document_count": doc_count,
            "chunk_count": chunk_count,
            "total_pages": total_pages,
            "has_index": chunk_count > 0
        }

    def get_existing_hashes(self) -> set:
        """Returns set of all file hashes in the knowledge base."""
        return {d["hash"] for d in self.documents.values() if "hash" in d}


# ==============================================================================
# Backward Compatibility Alias
# ==============================================================================
DocumentRetriever = KnowledgeBase
