"""
Dual-Tier Document Retriever for AI-Powered Campus Helpdesk Assistant.
Supports:
1. Lexical Retrieval (TF-IDF with morphological normalization and Cosine Similarity) - No API key required.
2. Semantic Retrieval (Gemini Embeddings with Cosine Similarity) - Active when key configured.
Includes persistent storage and similarity threshold gating.
"""

import os
import re
import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import settings


def normalize_text(text: str) -> str:
    """Applies lightweight morphological normalization for robust keyword matching."""
    if not text:
        return ""
    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    res = []
    for w in words:
        if len(w) > 4 and w.endswith("ing"):
            w = w[:-3]
        elif len(w) > 3 and w.endswith("s"):
            w = w[:-1]
        elif len(w) > 4 and w.endswith("ed"):
            w = w[:-2]
        res.append(w)
    return " ".join(res)


class DocumentRetriever:
    """Manages document chunks, builds indices, and executes relevance search."""

    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.chunks: List[Dict[str, Any]] = []
        
        # Lexical Retrieval Structures
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        
        # Semantic Retrieval Structures
        self.embeddings_cache: Dict[str, List[float]] = {}
        
        # Load persisted knowledge base if present
        self.load_knowledge_base()

    def load_knowledge_base(self) -> bool:
        """Loads indexed chunks and metadata from local JSON storage."""
        if not settings.KNOWLEDGE_BASE_FILE.exists():
            return False

        try:
            with open(settings.KNOWLEDGE_BASE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.documents = data.get("documents", {})
                self.chunks = data.get("chunks", [])

            self._rebuild_lexical_index()
            self._load_embeddings_cache()
            return True
        except Exception:
            self.documents = {}
            self.chunks = []
            return False

    def save_knowledge_base(self) -> None:
        """Persists indexed chunks and metadata to local JSON storage."""
        data = {
            "documents": self.documents,
            "chunks": self.chunks,
            "updated_at": datetime.now().isoformat()
        }
        with open(settings.KNOWLEDGE_BASE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_embeddings_cache(self) -> None:
        """Loads semantic embeddings cache if exists."""
        if settings.EMBEDDINGS_CACHE_FILE.exists():
            try:
                self.embeddings_cache = np.load(
                    settings.EMBEDDINGS_CACHE_FILE,
                    allow_pickle=True
                ).item()
            except Exception:
                self.embeddings_cache = {}

    def _save_embeddings_cache(self) -> None:
        """Persists semantic embeddings cache to disk."""
        try:
            np.save(settings.EMBEDDINGS_CACHE_FILE, self.embeddings_cache)
        except Exception:
            pass

    def _rebuild_lexical_index(self) -> None:
        """Fits TF-IDF vectorizer over normalized chunk texts."""
        if not self.chunks:
            self.vectorizer = None
            self.tfidf_matrix = None
            return

        corpus = [normalize_text(c["text"]) for c in self.chunks]
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 1),
            stop_words="english",
            sublinear_tf=True
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def add_document(
        self,
        filename: str,
        file_hash: str,
        size_bytes: int,
        pages_data: List[Dict[str, Any]],
        chunks: List[Dict[str, Any]]
    ) -> None:
        """Adds a processed document and its chunks into the knowledge base."""
        self.documents[filename] = {
            "filename": filename,
            "hash": file_hash,
            "size_bytes": size_bytes,
            "page_count": len(pages_data),
            "chunk_count": len(chunks),
            "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Processed"
        }

        # Remove any existing chunks for this filename (idempotency)
        self.chunks = [c for c in self.chunks if c["filename"] != filename]
        self.chunks.extend(chunks)

        self._rebuild_lexical_index()
        self.save_knowledge_base()

    def delete_document(self, filename: str) -> bool:
        """Removes a document and all associated chunks from the index."""
        if filename not in self.documents:
            return False

        del self.documents[filename]
        self.chunks = [c for c in self.chunks if c["filename"] != filename]

        # Clean embeddings cache
        for chunk_id in list(self.embeddings_cache.keys()):
            if chunk_id.startswith(f"{filename}_"):
                del self.embeddings_cache[chunk_id]

        self._rebuild_lexical_index()
        self.save_knowledge_base()
        self._save_embeddings_cache()
        return True

    def clear_all(self) -> None:
        """Clears all indexed documents and chunks."""
        self.documents = {}
        self.chunks = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.embeddings_cache = {}

        if settings.KNOWLEDGE_BASE_FILE.exists():
            settings.KNOWLEDGE_BASE_FILE.unlink(missing_ok=True)
        if settings.EMBEDDINGS_CACHE_FILE.exists():
            settings.EMBEDDINGS_CACHE_FILE.unlink(missing_ok=True)

    def search_lexical(
        self,
        query: str,
        top_k: int = settings.TOP_K,
        threshold: float = settings.SIMILARITY_THRESHOLD
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Executes lexical matching using TF-IDF and Cosine Similarity with morphological normalization.
        Returns: (ranked_results, has_relevant_context)
        """
        if not self.chunks or self.vectorizer is None or self.tfidf_matrix is None:
            return [], False

        norm_query = normalize_text(query)
        if not norm_query:
            return [], False

        query_vec = self.vectorizer.transform([norm_query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        ranked_indices = np.argsort(similarities)[::-1]

        results = []
        max_score = 0.0

        for idx in ranked_indices[:top_k]:
            score = float(similarities[idx])
            if score > max_score:
                max_score = score

            if score > 0.0:
                chunk = dict(self.chunks[idx])
                chunk["score"] = round(score, 4)
                results.append(chunk)

        has_relevant = (len(results) > 0) and (max_score >= threshold)
        return results, has_relevant

    def search_semantic(
        self,
        query: str,
        ai_engine,
        top_k: int = settings.TOP_K,
        threshold: float = settings.SIMILARITY_THRESHOLD
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Executes semantic matching using Gemini embeddings and Cosine Similarity.
        Returns: (ranked_results, has_relevant_context)
        """
        if not self.chunks or not ai_engine.is_configured():
            return self.search_lexical(query, top_k, threshold)

        try:
            query_embedding = ai_engine.get_embedding(query)
            if not query_embedding:
                return self.search_lexical(query, top_k, threshold)

            chunk_vectors = []
            valid_indices = []

            for i, chunk in enumerate(self.chunks):
                cid = chunk["chunk_id"]
                if cid not in self.embeddings_cache:
                    emb = ai_engine.get_embedding(chunk["text"])
                    if emb:
                        self.embeddings_cache[cid] = emb

                if cid in self.embeddings_cache:
                    chunk_vectors.append(self.embeddings_cache[cid])
                    valid_indices.append(i)

            if not chunk_vectors:
                return self.search_lexical(query, top_k, threshold)

            self._save_embeddings_cache()

            q_vec = np.array(query_embedding, dtype=np.float32)
            c_mat = np.array(chunk_vectors, dtype=np.float32)

            q_norm = np.linalg.norm(q_vec)
            c_norms = np.linalg.norm(c_mat, axis=1)
            scores = np.dot(c_mat, q_vec) / (c_norms * q_norm + 1e-9)

            ranked_order = np.argsort(scores)[::-1]
            results = []
            max_score = 0.0

            for rank_idx in ranked_order[:top_k]:
                score = float(scores[rank_idx])
                if score > max_score:
                    max_score = score

                orig_idx = valid_indices[rank_idx]
                chunk = dict(self.chunks[orig_idx])
                chunk["score"] = round(score, 4)
                results.append(chunk)

            has_relevant = (len(results) > 0) and (max_score >= 0.50)
            return results, has_relevant

        except Exception:
            return self.search_lexical(query, top_k, threshold)

    def search(
        self,
        query: str,
        ai_engine=None,
        top_k: int = settings.TOP_K,
        threshold: float = settings.SIMILARITY_THRESHOLD,
        prefer_semantic: bool = False
    ) -> Tuple[List[Dict[str, Any]], bool, str]:
        """
        Unified search endpoint.
        Returns: (results, has_relevant_context, method_name)
        """
        if not self.chunks:
            return [], False, "No Documents Indexed"

        if prefer_semantic and ai_engine and ai_engine.is_configured():
            results, has_relevant = self.search_semantic(query, ai_engine, top_k, threshold)
            return results, has_relevant, "Semantic Retrieval (Gemini Embeddings)"

        results, has_relevant = self.search_lexical(query, top_k, threshold)
        return results, has_relevant, "Lexical Retrieval (TF-IDF)"

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics for live status strips."""
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
        """Returns set of hashes for duplicate detection."""
        return {d["hash"] for d in self.documents.values() if "hash" in d}
