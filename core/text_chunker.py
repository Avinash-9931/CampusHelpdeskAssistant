"""
Text Chunker for AI-Powered Campus Helpdesk Assistant.
Splits page-level extracted text into overlapping chunks while preserving metadata.
"""

from typing import List, Dict, Any
from config import settings


class TextChunker:
    """
    Transforms extracted page text into retrieval chunks.
    Ensures every chunk retains its source filename, page number, and unique chunk_id.
    """

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        if self.chunk_overlap >= self.chunk_size:
            self.chunk_overlap = self.chunk_size // 4

    def chunk_page_text(self, text: str, filename: str, page: int) -> List[Dict[str, Any]]:
        """
        Splits text from a single page into overlapping chunks.
        Attempts to align cuts with sentence boundaries or line breaks.
        """
        if not text or not text.strip():
            return []

        chunks = []
        start = 0
        text_len = len(text)
        chunk_idx = 1

        while start < text_len:
            end = start + self.chunk_size

            if end >= text_len:
                chunk_text = text[start:].strip()
                if chunk_text:
                    chunk_id = f"{filename}_p{page}_c{chunk_idx}"
                    chunks.append({
                        "chunk_id": chunk_id,
                        "filename": filename,
                        "page": page,
                        "text": chunk_text,
                        "char_count": len(chunk_text)
                    })
                break

            # Find best split point near the end: newline, period, question mark, or space
            split_candidates = [
                text.rfind("\n\n", start, end),
                text.rfind(". ", start, end),
                text.rfind(".\n", start, end),
                text.rfind("? ", start, end),
                text.rfind("; ", start, end),
                text.rfind(" ", start, end)
            ]

            best_split = max(split_candidates)

            # If split point is too early (less than half chunk_size), take hard cut
            if best_split == -1 or (best_split - start) < (self.chunk_size // 2):
                split_point = end
            else:
                # Include the delimiter character
                split_point = best_split + 1

            chunk_text = text[start:split_point].strip()

            if chunk_text:
                chunk_id = f"{filename}_p{page}_c{chunk_idx}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "filename": filename,
                    "page": page,
                    "text": chunk_text,
                    "char_count": len(chunk_text)
                })
                chunk_idx += 1

            # Advance start by split_point - chunk_overlap
            advance = split_point - self.chunk_overlap
            if advance <= start:
                advance = split_point
            start = advance

        return chunks

    def chunk_document(self, pages_data: List[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
        """
        Chunks all pages in an extracted document, preserving page-level attribution.
        """
        all_chunks = []
        for page_data in pages_data:
            page_num = page_data["page"]
            text = page_data["text"]
            page_chunks = self.chunk_page_text(text, filename, page_num)
            all_chunks.extend(page_chunks)
        return all_chunks
