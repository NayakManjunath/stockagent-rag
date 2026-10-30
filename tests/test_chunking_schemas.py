
"""Tests for document chunk schemas."""

from dataclasses import FrozenInstanceError

import pytest

from stockagent.chunking import DocumentChunk
from stockagent.ingestion.schemas import DocumentMetadata


@pytest.fixture
def metadata() -> DocumentMetadata:
    """Return sample source metadata."""

    return DocumentMetadata(
        source_path="reports/annual_report.txt",
        file_type="txt",
        title="Annual Report",
    )



@pytest.fixture
def valid_chunk(metadata: DocumentMetadata) -> DocumentChunk:
    """Return a valid document chunk."""

    return DocumentChunk(
        chunk_id="doc-001-chunk-000",
        document_id="doc-001",
        text="Revenue increased.",
        chunk_index=0,
        start_char=0,
        end_char=18,
        metadata=metadata,
    )

def test_create_valid_chunk(valid_chunk: DocumentChunk) -> None:
    assert valid_chunk.chunk_id == "doc-001-chunk-000"
    assert valid_chunk.document_id == "doc-001"
    assert valid_chunk.text == "Revenue increased."
    assert valid_chunk.chunk_index == 0
    assert valid_chunk.start_char == 0
    assert valid_chunk.end_char == 18


def test_preserve_source_metadata(
    valid_chunk: DocumentChunk,
    metadata: DocumentMetadata,
) -> None:
    assert valid_chunk.metadata is metadata
    assert valid_chunk.metadata.title == "Annual Report"
    assert valid_chunk.metadata.source_path == "reports/annual_report.txt"


@pytest.mark.parametrize("chunk_id", ["", " ", "\t"])
def test_reject_empty_chunk_id(
    metadata: DocumentMetadata,
    chunk_id: str,
) -> None:
    with pytest.raises(ValueError, match="Chunk ID"):
        DocumentChunk(
            chunk_id=chunk_id,
            document_id="doc-001",
            text="Revenue",
            chunk_index=0,
            start_char=0,
            end_char=7,
            metadata=metadata,
        )


@pytest.mark.parametrize("document_id", ["", " ", "\t"])
def test_reject_empty_document_id(
    metadata: DocumentMetadata,
    document_id: str,
) -> None:
    with pytest.raises(ValueError, match="Document ID"):
        DocumentChunk(
            chunk_id="chunk-001",
            document_id=document_id,
            text="Revenue",
            chunk_index=0,
            start_char=0,
            end_char=7,
            metadata=metadata,
        )


@pytest.mark.parametrize("text", ["", " ", "\t\n"])
def test_reject_empty_chunk_text(
    metadata: DocumentMetadata,
    text: str,
) -> None:
    with pytest.raises(ValueError, match="Chunk text"):
        DocumentChunk(
            chunk_id="chunk-001",
            document_id="doc-001",
            text=text,
            chunk_index=0,
            start_char=0,
            end_char=len(text),
            metadata=metadata,
        )


@pytest.mark.parametrize("chunk_index", [-1, 1.5, True])
def test_reject_invalid_chunk_index(
    metadata: DocumentMetadata,
    chunk_index: int,
) -> None:
    with pytest.raises(ValueError, match="Chunk index"):
        DocumentChunk(
            chunk_id="chunk-001",
            document_id="doc-001",
            text="Revenue",
            chunk_index=chunk_index,
            start_char=0,
            end_char=7,
            metadata=metadata,
        )


@pytest.mark.parametrize("start_char", [-1, 1.5, True])
def test_reject_invalid_start_offset(
    metadata: DocumentMetadata,
    start_char: int,
) -> None:
    with pytest.raises(ValueError, match="Start offset"):
        DocumentChunk(
            chunk_id="chunk-001",
            document_id="doc-001",
            text="Revenue",
            chunk_index=0,
            start_char=start_char,
            end_char=7,
            metadata=metadata,
        )


@pytest.mark.parametrize("end_char", [-1, 0, 1.5, True])
def test_reject_invalid_end_offset(
    metadata: DocumentMetadata,
    end_char: int,
) -> None:
    with pytest.raises(ValueError, match="End offset"):
        DocumentChunk(
            chunk_id="chunk-001",
            document_id="doc-001",
            text="Revenue",
            chunk_index=0,
            start_char=0,
            end_char=end_char,
            metadata=metadata,
        )


def test_reject_offsets_that_do_not_match_text_length(
    metadata: DocumentMetadata,
) -> None:
    with pytest.raises(ValueError, match="text length"):
        DocumentChunk(
            chunk_id="chunk-001",
            document_id="doc-001",
            text="Revenue",
            chunk_index=0,
            start_char=0,
            end_char=8,
            metadata=metadata,
        )


def test_reject_invalid_metadata() -> None:
    with pytest.raises(TypeError, match="DocumentMetadata"):
        DocumentChunk(
            chunk_id="chunk-001",
            document_id="doc-001",
            text="Revenue",
            chunk_index=0,
            start_char=0,
            end_char=7,
            metadata=None,  # type: ignore[arg-type]
        )


def test_chunk_is_immutable(valid_chunk: DocumentChunk) -> None:
    with pytest.raises(FrozenInstanceError):
        valid_chunk.text = "Modified text"  # type: ignore[misc]


def test_accept_nonzero_character_offsets(
    metadata: DocumentMetadata,
) -> None:
    chunk = DocumentChunk(
        chunk_id="doc-001-chunk-001",
        document_id="doc-001",
        text="increased",
        chunk_index=1,
        start_char=8,
        end_char=17,
        metadata=metadata,
    )

    assert chunk.end_char - chunk.start_char == len(chunk.text)
