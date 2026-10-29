
"""Document ingestion schemas, discovery, loading, and validation."""

from stockagent.ingestion.discovery import FileDiscovery
from stockagent.ingestion.loader import DocumentFileLoader
from stockagent.ingestion.normalizer import TextNormalizer
from stockagent.ingestion.pipeline import IngestionPipeline
from stockagent.ingestion.schemas import (
    DocumentLoader,
    DocumentMetadata,
    IngestedDocument,
    MetadataValue,
)
from stockagent.ingestion.validation import (
    DocumentValidationError,
    DocumentValidator,
    IngestionFailure,
    IngestionReport,
)

__all__ = [
    "DocumentFileLoader",
    "DocumentLoader",
    "DocumentMetadata",
    "DocumentValidationError",
    "DocumentValidator",
    "FileDiscovery",
    "IngestedDocument",
    "IngestionFailure",
    "IngestionPipeline",
    "IngestionReport",
    "MetadataValue",
    "TextNormalizer",
]
