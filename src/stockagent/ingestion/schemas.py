
"""Schemas and contracts for StockAgent document ingestion."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Protocol, TypeAlias


MetadataValue: TypeAlias = str | int | float | bool | None


@dataclass(frozen=True)
class DocumentMetadata:
    """Describe the origin and temporal context of a financial document."""

    source_path: str
    file_type: str
    title: str | None = None
    document_type: str | None = None
    published_date: date | None = None
    effective_date: date | None = None
    extra: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and normalize metadata fields."""

        if not isinstance(self.source_path, str):
            raise TypeError("Source path must be a string.")

        source_path = self.source_path.strip()
        if not source_path:
            raise ValueError("Source path cannot be empty.")

        if not isinstance(self.file_type, str):
            raise TypeError("File type must be a string.")

        file_type = self.file_type.strip().lower().lstrip(".")
        if not file_type:
            raise ValueError("File type cannot be empty.")

        for field_name in ("title", "document_type"):
            value = getattr(self, field_name)

            if value is not None and not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string or None.")

            if isinstance(value, str):
                normalized_value = value.strip() or None
                object.__setattr__(self, field_name, normalized_value)

        for field_name in ("published_date", "effective_date"):
            value = getattr(self, field_name)

            if value is not None and not isinstance(value, date):
                raise TypeError(
                    f"{field_name} must be a date or None."
                )

        if not isinstance(self.extra, Mapping):
            raise TypeError("Extra metadata must be a mapping.")

        normalized_extra: dict[str, MetadataValue] = {}

        for key, value in self.extra.items():
            if not isinstance(key, str):
                raise TypeError("Metadata keys must be strings.")

            normalized_key = key.strip()
            if not normalized_key:
                raise ValueError("Metadata keys cannot be empty.")

            if not (
                value is None
                or isinstance(value, (str, int, float, bool))
            ):
                raise TypeError(
                    f"Unsupported value for metadata key: {normalized_key}"
                )

            if isinstance(value, float):
                import math

                if not math.isfinite(value):
                    raise ValueError(
                        "Metadata float values must be finite."
                    )

            normalized_extra[normalized_key] = value

        object.__setattr__(self, "source_path", source_path)
        object.__setattr__(self, "file_type", file_type)
        object.__setattr__(
            self,
            "extra",
            MappingProxyType(normalized_extra),
        )


@dataclass(frozen=True)
class IngestedDocument:
    """Represent extracted document text and its associated metadata."""

    document_id: str
    text: str
    metadata: DocumentMetadata

    def __post_init__(self) -> None:
        """Validate the document ingestion contract."""

        if not isinstance(self.document_id, str):
            raise TypeError("Document ID must be a string.")

        document_id = self.document_id.strip()
        if not document_id:
            raise ValueError("Document ID cannot be empty.")

        if not isinstance(self.text, str):
            raise TypeError("Document text must be a string.")

        if not self.text.strip():
            raise ValueError("Document text cannot be empty.")

        if not isinstance(self.metadata, DocumentMetadata):
            raise TypeError(
                "Metadata must be a DocumentMetadata instance."
            )

        object.__setattr__(self, "document_id", document_id)

    @property
    def content_sha256(self) -> str:
        """Return a SHA-256 fingerprint of the exact extracted text."""

        return hashlib.sha256(
            self.text.encode("utf-8")
        ).hexdigest()


class DocumentLoader(Protocol):
    """Contract that future file-specific loaders must implement."""

    supported_extensions: frozenset[str]

    def load(self, source_path: Path) -> IngestedDocument:
        """Load one source file and return its extracted document."""
        ...
