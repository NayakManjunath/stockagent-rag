
"""Text normalization for StockAgent financial documents."""

from __future__ import annotations

import re
import unicodedata

from stockagent.ingestion.schemas import IngestedDocument


class TextNormalizer:
    """Normalize extracted text without modifying the source document."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize line endings, control characters, and whitespace."""

        if not isinstance(text, str):
            raise TypeError("Text to normalize must be a string.")

        # Normalize Windows and legacy Mac line endings.
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove control characters except tabs and line breaks.
        normalized = "".join(
            character
            for character in normalized
            if character in {"\n", "\t"}
            or unicodedata.category(character) != "Cc"
        )

        normalized_lines: list[str] = []

        for line in normalized.split("\n"):
            # Preserve blank lines and paragraph boundaries.
            if not line.strip():
                normalized_lines.append("")
                continue

            # Preserve indentation for Markdown lists and code blocks.
            indentation_length = len(line) - len(line.lstrip(" \t"))
            indentation = line[:indentation_length]
            content = line[indentation_length:]

            # Normalize horizontal whitespace within the content.
            content = re.sub(r"[ \t]+", " ", content).rstrip()

            normalized_lines.append(indentation + content)

        # Limit consecutive blank lines to one blank line.
        result = "\n".join(normalized_lines)
        result = re.sub(r"\n{3,}", "\n\n", result)

        # Remove blank lines at the beginning and end.
        result = result.strip("\n")

        return result

    @classmethod
    def normalize_document(
        cls,
        document: IngestedDocument,
    ) -> IngestedDocument:
        """Normalize text while preserving document identity and metadata."""

        if not isinstance(document, IngestedDocument):
            raise TypeError(
                "Document must be an IngestedDocument instance."
            )

        return IngestedDocument(
            document_id=document.document_id,
            text=cls.normalize_text(document.text),
            metadata=document.metadata,
        )
