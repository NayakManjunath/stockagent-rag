
"""Load supported financial documents and extract their text."""

from __future__ import annotations

import hashlib
from pathlib import Path

from pypdf import PdfReader

from stockagent.ingestion.discovery import FileDiscovery
from stockagent.ingestion.schemas import (
    DocumentMetadata,
    IngestedDocument,
)


class DocumentFileLoader:
    """Load TXT, Markdown, and PDF files into IngestedDocument objects."""

    supported_extensions = frozenset({".pdf", ".txt", ".md"})

    def __init__(self) -> None:
        self._discovery = FileDiscovery(
            supported_extensions=self.supported_extensions
        )

    def load(self, source_path: Path) -> IngestedDocument:
        """Load a supported file and return its extracted text and metadata."""

        path = self._discovery.validate_file(source_path)
        extension = path.suffix.lower()

        if extension in {".txt", ".md"}:
            text = path.read_text(encoding="utf-8-sig")
            extra: dict[str, str | int | float | bool | None] = {
                "extraction_method": "utf-8-sig",
            }
        elif extension == ".pdf":
            text, page_count = self._extract_pdf(path)
            extra = {
                "extraction_method": "pypdf",
                "page_count": page_count,
            }
        else:
            # FileDiscovery normally rejects this before we reach this branch.
            raise ValueError(f"Unsupported file format: {extension}")

        document_id = self._build_document_id(path)

        metadata = DocumentMetadata(
            source_path=str(path.resolve()),
            file_type=extension,
            title=path.stem,
            extra=extra,
        )

        return IngestedDocument(
            document_id=document_id,
            text=text,
            metadata=metadata,
        )

    @staticmethod
    def _extract_pdf(path: Path) -> tuple[str, int]:
        """Extract text from each PDF page in document order."""

        reader = PdfReader(str(path))
        page_texts: list[str] = []

        for page in reader.pages:
            page_texts.append(page.extract_text() or "")

        text = "\n\n".join(page_texts)

        if not text.strip():
            raise ValueError(
                f"No extractable text found in PDF: {path}. "
                "The file may be scanned or image-only."
            )

        return text, len(reader.pages)

    @staticmethod
    def _build_document_id(path: Path) -> str:
        """Create a deterministic identifier from the resolved source path."""

        canonical_path = str(path.resolve())
        digest = hashlib.sha256(
            canonical_path.encode("utf-8")
        ).hexdigest()

        return f"doc-{digest[:24]}"
