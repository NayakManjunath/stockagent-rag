"""Document ingestion schemas, discovery, and loading."""

from stockagent.ingestion.discovery import FileDiscovery
from stockagent.ingestion.loader import DocumentFileLoader
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
]
