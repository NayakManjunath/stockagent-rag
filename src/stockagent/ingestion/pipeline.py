
"""Resilient document-ingestion orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from stockagent.ingestion.discovery import FileDiscovery
from stockagent.ingestion.loader import DocumentFileLoader
from stockagent.ingestion.normalizer import TextNormalizer
from stockagent.ingestion.schemas import DocumentLoader
from stockagent.ingestion.validation import (
    DocumentValidator,
    IngestionFailure,
    IngestionReport,
)


class IngestionPipeline:
    """Discover, load, normalize, and validate financial documents."""

    def __init__(
        self,
        loader: DocumentLoader | None = None,
        normalizer: TextNormalizer | None = None,
        validator: DocumentValidator | None = None,
        discovery: FileDiscovery | None = None,
    ) -> None:
        """Configure the ingestion pipeline and its dependencies."""

        self._loader = (
            loader if loader is not None else DocumentFileLoader()
        )
        self._normalizer = (
            normalizer if normalizer is not None else TextNormalizer()
        )
        self._validator = (
            validator if validator is not None else DocumentValidator()
        )
        self._discovery = (
            discovery
            if discovery is not None
            else FileDiscovery(
                supported_extensions=self._loader.supported_extensions
            )
        )

    def ingest_paths(
        self,
        paths: Iterable[str | Path],
    ) -> IngestionReport:
        """Ingest multiple paths while recording individual failures."""

        if isinstance(paths, (str, bytes, Path)):
            raise TypeError(
                "Paths must be an iterable of file paths, "
                "not a single path."
            )

        try:
            iterator = iter(paths)
        except TypeError as exc:
            raise TypeError(
                "Paths must be an iterable of file paths."
            ) from exc

        documents = []
        failures: list[IngestionFailure] = []
        seen_document_ids: set[str] = set()
        discovered_count = 0

        for source in iterator:
            discovered_count += 1
            source_label = str(source)

            try:
                if not isinstance(source, (str, Path)):
                    raise TypeError(
                        "Each source path must be a string or Path."
                    )

                if isinstance(source, str) and not source.strip():
                    raise ValueError("Source path cannot be empty.")

                document = self._loader.load(Path(source))
                document = self._normalizer.normalize_document(document)
                document = self._validator.validate(document)

                if document.document_id in seen_document_ids:
                    raise ValueError(
                        "Duplicate document ID encountered: "
                        f"{document.document_id}"
                    )

                documents.append(document)
                seen_document_ids.add(document.document_id)

            except Exception as exc:
                failures.append(
                    IngestionFailure(
                        source_path=source_label,
                        error_type=type(exc).__name__,
                        message=str(exc) or type(exc).__name__,
                    )
                )

        return IngestionReport(
            documents=tuple(documents),
            failures=tuple(failures),
            discovered_count=discovered_count,
        )

    def ingest_directory(
        self,
        directory: str | Path,
    ) -> IngestionReport:
        """Discover supported files in a directory and ingest them."""

        paths = self._discovery.discover(directory)
        return self.ingest_paths(paths)
