
"""Document ingestion schemas and contracts."""

from stockagent.ingestion.discovery import FileDiscovery
from stockagent.ingestion.schemas import (
    DocumentLoader,
    DocumentMetadata,
    IngestedDocument,
    MetadataValue,
)

__all__ = [
    "DocumentLoader",
    "DocumentMetadata",
    "FileDiscovery",
    "IngestedDocument",
    "MetadataValue",
]
