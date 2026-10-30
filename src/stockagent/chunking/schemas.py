
"""Data contracts for document chunks."""

from __future__ import annotations

from dataclasses import dataclass

from stockagent.ingestion.schemas import DocumentMetadata


@dataclass(frozen=True)
class DocumentChunk:
    """Represent a text chunk derived from an ingested document."""

    chunk_id: str
    document_id: str
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: DocumentMetadata

    def __post_init__(self) -> None:
        """Validate the chunk's structural invariants."""

        if not isinstance(self.chunk_id, str) or not self.chunk_id.strip():
            raise ValueError("Chunk ID cannot be empty.")

        if (
            not isinstance(self.document_id, str)
            or not self.document_id.strip()
        ):
            raise ValueError("Document ID cannot be empty.")

        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("Chunk text cannot be empty or whitespace-only.")

        if (
            not isinstance(self.chunk_index, int)
            or isinstance(self.chunk_index, bool)
            or self.chunk_index < 0
        ):
            raise ValueError("Chunk index must be a non-negative integer.")

        if (
            not isinstance(self.start_char, int)
            or isinstance(self.start_char, bool)
            or self.start_char < 0
        ):
            raise ValueError("Start offset must be a non-negative integer.")

        if (
            not isinstance(self.end_char, int)
            or isinstance(self.end_char, bool)
            or self.end_char <= self.start_char
        ):
            raise ValueError("End offset must be greater than start offset.")

        if self.end_char - self.start_char != len(self.text):
            raise ValueError(
                "Chunk offsets must match the chunk text length."
            )

        if not isinstance(self.metadata, DocumentMetadata):
            raise TypeError(
                "Metadata must be a DocumentMetadata instance."
            )
