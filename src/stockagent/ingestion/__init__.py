
"""Document ingestion schemas, discovery, loading, and normalization."""

from stockagent.ingestion.discovery import FileDiscovery
from stockagent.ingestion.loader import DocumentFileLoader
from stockagent.ingestion.normalizer import TextNormalizer
from stockagent.ingestion.schemas import (
    DocumentLoader,
    DocumentMetadata,
    IngestedDocument,
    MetadataValue,
)

__all__ = [
    "DocumentFileLoader",
    "DocumentLoader",
    "DocumentMetadata",
    "FileDiscovery",
    "IngestedDocument",
    "MetadataValue",
    "TextNormalizer",
]
