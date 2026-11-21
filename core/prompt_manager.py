"""
Prompt Manager for AI-Powered Campus Helpdesk Assistant.
Loads prompt templates (v1, v2, v3, final) and formats queries with XML-delimited context.
"""

from pathlib import Path
from typing import List, Dict, Any, Union
from config import settings
from core.text_chunker import TextChunk


class PromptManager:
    """Manages prompt versions and formats RAG context with injection defense."""

    def __init__(self, prompts_dir: Path = settings.PROMPTS_DIR):
        self.prompts_dir = prompts_dir
        self.templates: Dict[str, str] = {}
        self.reload_prompts()

    def reload_prompts(self) -> None:
        """Reads all prompt files into memory."""
        prompt_files = {
            "v1": self.prompts_dir / "prompt_v1.md",
            "v2": self.prompts_dir / "prompt_v2.md",
            "v3": self.prompts_dir / "prompt_v3.md",
            "final": self.prompts_dir / "final_prompt.md",
        }

        for version, path in prompt_files.items():
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self.templates[version] = f.read().strip()
            else:
                self.templates[version] = ""

    def get_template(self, version: str = "final") -> str:
        """Returns the raw prompt template for a given version."""
        return self.templates.get(version.lower(), self.templates.get("final", ""))

    def format_context(self, chunks: List[Any]) -> str:
        """
        Formats retrieved chunks into clear, delimited blocks with source metadata.
        Explicitly presents filename, page, and chunk identifier.
        Marks context as untrusted reference text.
        """
        if not chunks:
            return "No matching official document context found."

        formatted_entries = []
        for idx, chunk in enumerate(chunks, 1):
            if isinstance(chunk, TextChunk):
                filename = chunk.filename
                page = chunk.page
                chunk_id = chunk.chunk_id
                text = chunk.text.strip()
            elif hasattr(chunk, "chunk"):  # RetrievedChunk
                filename = chunk.chunk.filename
                page = chunk.chunk.page
                chunk_id = chunk.chunk.chunk_id
                text = chunk.chunk.text.strip()
            elif isinstance(chunk, dict):
                filename = chunk.get("filename", "Unknown Document")
                page = chunk.get("page", 1)
                chunk_id = chunk.get("chunk_id", f"chunk_{idx}")
                text = chunk.get("text", "").strip()
            else:
                filename = getattr(chunk, "filename", "Unknown Document")
                page = getattr(chunk, "page", 1)
                chunk_id = getattr(chunk, "chunk_id", f"chunk_{idx}")
                text = getattr(chunk, "text", "").strip()

            entry = (
                f'<document_context filename="{filename}" page="{page}" chunk_id="{chunk_id}">\n'
                f"[Source: {filename} | Page: {page} | Chunk ID: {chunk_id}]\n"
                f"{text}\n"
                f"</document_context>"
            )
            formatted_entries.append(entry)

        return "\n\n".join(formatted_entries)

    def build_prompt(
        self,
        query: str,
        chunks: List[Any],
        version: str = "final"
    ) -> str:
        """
        Assembles the final prompt by injecting context and student query.
        """
        template = self.get_template(version)
        if not template:
            template = self.get_template("final")

        formatted_context = self.format_context(chunks)

        if version.lower() == "v1":
            return template.format(query=query)
        elif version.lower() in ["v2", "v3"]:
            return template.format(context=formatted_context, query=query)
        else:
            # Final optimized prompt
            return template.format(context=formatted_context, query=query)

    def get_all_prompts(self) -> Dict[str, str]:
        """Returns all prompt templates for comparison and UI display."""
        return self.templates
