"""
Text Chunker for AI-Powered Campus Helpdesk Assistant.
Splits page-level extracted text into overlapping chunks while preserving metadata.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Union
from config import settings
from core.pdf_processor import PageData


@dataclass
class TextChunk:
    """Represents a discrete text chunk anchored to a specific document page."""
    chunk_id: str
    filename: str
    page: int
    text: str

    def __getitem__(self, item: str) -> Any:
        # Compatibility with legacy dict-style access
        if hasattr(self, item):
            return getattr(self, item)
        elif item == "char_count":
            return len(self.text)
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return self[item]
        except KeyError:
            return default

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "filename": self.filename,
            "page": self.page,
            "text": self.text,
            "char_count": len(self.text)
        }


def chunk_page_text(
    text: str,
    filename: str,
    page: int,
    chunk_size: int = settings.CHUNK_SIZE,
    chunk_overlap: int = settings.CHUNK_OVERLAP,
    min_chunk_chars: int = 15
) -> List[TextChunk]:
    """
    Splits text from a single page into overlapping chunks.
    Prefers paragraph (\n\n) and sentence boundaries (. , ? ! ; \n).
    Never crosses page boundaries. Skips near-empty chunks.
    
    Args:
        text: Page text to chunk.
        filename: Document source name.
        page: 1-indexed page number.
        chunk_size: Target character length per chunk.
        chunk_overlap: Overlapping characters between adjacent chunks.
        min_chunk_chars: Minimum character length to retain chunk.
        
    Returns:
        List of TextChunk instances.
    """
    if not text or not text.strip():
        return []

    if chunk_overlap >= chunk_size:
        chunk_overlap = chunk_size // 4

    chunks: List[TextChunk] = []
    start = 0
    text_len = len(text)
    chunk_idx = 1

    while start < text_len:
        end = start + chunk_size

        if end >= text_len:
            chunk_content = text[start:].strip()
            if len(chunk_content) >= min_chunk_chars:
                cid = f"{filename}_p{page}_c{chunk_idx}"
                chunks.append(TextChunk(
                    chunk_id=cid,
                    filename=filename,
                    page=page,
                    text=chunk_content
                ))
            break

        # Search for optimal split candidates near the end of the window
        split_candidates = [
            text.rfind("\n\n", start, end),
            text.rfind(". ", start, end),
            text.rfind(".\n", start, end),
            text.rfind("? ", start, end),
            text.rfind("! ", start, end),
            text.rfind("; ", start, end),
            text.rfind("\n", start, end),
            text.rfind(" ", start, end)
        ]

        best_split = max(split_candidates)

        # Fall back to hard boundary if split is too far back (less than half window)
        if best_split == -1 or (best_split - start) < (chunk_size // 2):
            split_point = end
        else:
            split_point = best_split + 1

        chunk_content = text[start:split_point].strip()

        if len(chunk_content) >= min_chunk_chars:
            cid = f"{filename}_p{page}_c{chunk_idx}"
            chunks.append(TextChunk(
                chunk_id=cid,
                filename=filename,
                page=page,
                text=chunk_content
            ))
            chunk_idx += 1

        # Advance start position with overlap
        advance = split_point - chunk_overlap
        if advance <= start:
            advance = split_point
        else:
            # Snap advance forward to the next whitespace boundary to avoid cutting words
            next_space = text.find(" ", advance)
            if next_space != -1 and next_space < split_point:
                advance = next_space + 1
        start = advance

    return chunks


def chunk_pages(
    pages: Union[List[PageData], List[Dict[str, Any]]],
    filename: str,
    chunk_size: int = settings.CHUNK_SIZE,
    chunk_overlap: int = settings.CHUNK_OVERLAP
) -> List[TextChunk]:
    """
    Chunks extracted pages of a document while preserving strict page attribution.
    """
    all_chunks: List[TextChunk] = []
    for p in pages:
        page_num = p.page_number if isinstance(p, PageData) else p.get("page", 1)
        page_text = p.text if isinstance(p, PageData) else p.get("text", "")
        p_chunks = chunk_page_text(
            text=page_text,
            filename=filename,
            page=page_num,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        all_chunks.extend(p_chunks)
    return all_chunks


class TextChunker:
    """Class interface for text chunking, maintaining backward compatibility."""

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_page_text(self, text: str, filename: str, page: int) -> List[TextChunk]:
        return chunk_page_text(
            text=text,
            filename=filename,
            page=page,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

    def chunk_document(
        self,
        pages_data: Union[List[PageData], List[Dict[str, Any]]],
        filename: str
    ) -> List[TextChunk]:
        return chunk_pages(
            pages=pages_data,
            filename=filename,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
