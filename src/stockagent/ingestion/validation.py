
"""Validation and structured reporting for document ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from stockagent.ingestion.schemas import IngestedDocument


class DocumentValidationError(ValueError):
    """Raised when an ingested document violates the ingestion contract."""


@dataclass(frozen=True)
class IngestionFailure:
    """Describe a failed document-ingestion attempt."""

    source_path: str
    error_type: str
    message: str


@dataclass(frozen=True)
class IngestionReport:
    """Summarize the outcomes of a batch ingestion operation."""

    documents: tuple[IngestedDocument, ...]
    failures: tuple[IngestionFailure, ...]
    discovered_count: int

    @property
    def succeeded_count(self) -> int:
        """Return the number of successfully ingested documents."""

        return len(self.documents)

    @property
    def failed_count(self) -> int:
        """Return the number of failed ingestion attempts."""

        return len(self.failures)

    @property
    def is_successful(self) -> bool:
        """Return whether the batch completed without file-level failures."""

        return not self.failures


class DocumentValidator:
    """Validate extracted documents before downstream processing."""

    supported_extensions = frozenset({".pdf", ".txt", ".md"})

    def validate(self, document: IngestedDocument) -> IngestedDocument:
        """Validate a document and return it unchanged if it is valid."""

        if not isinstance(document, IngestedDocument):
            raise TypeError(
                "Document must be an IngestedDocument instance."
            )

        if not document.document_id.strip():
            raise DocumentValidationError(
                "Document ID cannot be empty."
            )

        if not document.text.strip():
            raise DocumentValidationError(
                "Document text cannot be empty or whitespace-only."
            )

        metadata = document.metadata
        source_path = Path(metadata.source_path)
        extension = source_path.suffix.lower()

        if extension not in self.supported_extensions:
            supported = ", ".join(sorted(self.supported_extensions))
            raise DocumentValidationError(
                f"Unsupported source file extension: "
                f"{extension or '<no extension>'}. "
                f"Supported extensions: {supported}"
            )

        metadata_file_type = metadata.file_type.lower().lstrip(".")

        if metadata_file_type != extension.lstrip("."):
            raise DocumentValidationError(
                "Metadata file type does not match the source file "
                f"extension: {metadata_file_type!r} versus "
                f"{extension!r}."
            )

        return document
