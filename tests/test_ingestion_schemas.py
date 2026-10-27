
"""Tests for document ingestion schemas and contracts."""

from datetime import date
from pathlib import Path

import pytest

from stockagent.ingestion import (
    DocumentMetadata,
    IngestedDocument,
)
from stockagent.ingestion.schemas import DocumentLoader


def make_metadata(**overrides: object) -> DocumentMetadata:
    values: dict[str, object] = {
        "source_path": "data/market_report.pdf",
        "file_type": "PDF",
        "title": "Market Report",
        "document_type": "research_report",
        "published_date": date(2026, 1, 15),
        "effective_date": date(2026, 1, 10),
    }
    values.update(overrides)
    return DocumentMetadata(**values)  # type: ignore[arg-type]


def make_document(
    document_id: str = "doc-001",
    text: str = "Market outlook is positive.",
    metadata: DocumentMetadata | None = None,
) -> IngestedDocument:
    return IngestedDocument(
        document_id=document_id,
        text=text,
        metadata=metadata or make_metadata(),
    )


def test_metadata_normalizes_source_and_file_type() -> None:
    metadata = make_metadata(
        source_path="  data/report.PDF  ",
        file_type=".PDF",
    )

    assert metadata.source_path == "data/report.PDF"
    assert metadata.file_type == "pdf"


@pytest.mark.parametrize("source_path", ["", "   "])
def test_metadata_rejects_empty_source_path(
    source_path: str,
) -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        make_metadata(source_path=source_path)


def test_metadata_rejects_non_string_source_path() -> None:
    with pytest.raises(TypeError, match="Source path must be a string"):
        make_metadata(source_path=123)


@pytest.mark.parametrize("file_type", ["", "   ", "."])
def test_metadata_rejects_empty_file_type(file_type: str) -> None:
    with pytest.raises(ValueError, match="File type cannot be empty"):
        make_metadata(file_type=file_type)


def test_metadata_rejects_non_string_file_type() -> None:
    with pytest.raises(TypeError, match="File type must be a string"):
        make_metadata(file_type=123)


def test_metadata_normalizes_optional_text_fields() -> None:
    metadata = make_metadata(
        title="  Annual Report  ",
        document_type="  financial_report  ",
    )

    assert metadata.title == "Annual Report"
    assert metadata.document_type == "financial_report"


def test_metadata_converts_blank_optional_text_to_none() -> None:
    metadata = make_metadata(title="   ", document_type="")

    assert metadata.title is None
    assert metadata.document_type is None


def test_metadata_rejects_invalid_optional_text() -> None:
    with pytest.raises(TypeError, match="title must be a string"):
        make_metadata(title=123)


@pytest.mark.parametrize(
    "field_name",
    ["published_date", "effective_date"],
)
def test_metadata_rejects_invalid_dates(field_name: str) -> None:
    with pytest.raises(TypeError, match="must be a date"):
        make_metadata(**{field_name: "2026-01-15"})


def test_metadata_accepts_extra_metadata() -> None:
    metadata = make_metadata(
        extra={"exchange": "NASDAQ", "pages": 12, "verified": True}
    )

    assert metadata.extra["exchange"] == "NASDAQ"
    assert metadata.extra["pages"] == 12
    assert metadata.extra["verified"] is True


def test_metadata_copies_extra_metadata() -> None:
    original = {"exchange": "NASDAQ"}
    metadata = make_metadata(extra=original)

    original["exchange"] = "NYSE"

    assert metadata.extra["exchange"] == "NASDAQ"


def test_metadata_extra_mapping_cannot_be_modified() -> None:
    metadata = make_metadata(extra={"exchange": "NASDAQ"})

    with pytest.raises(TypeError):
        metadata.extra["exchange"] = "NYSE"  # type: ignore[index]


def test_metadata_rejects_non_mapping_extra() -> None:
    with pytest.raises(TypeError, match="must be a mapping"):
        make_metadata(extra=["exchange"])  # type: ignore[arg-type]


def test_metadata_rejects_invalid_extra_key() -> None:
    with pytest.raises(ValueError, match="keys cannot be empty"):
        make_metadata(extra={"   ": "value"})


def test_metadata_rejects_non_string_extra_key() -> None:
    with pytest.raises(TypeError, match="keys must be strings"):
        make_metadata(extra={123: "value"})


def test_metadata_rejects_unsupported_extra_value() -> None:
    with pytest.raises(TypeError, match="Unsupported value"):
        make_metadata(extra={"items": ["a", "b"]})


@pytest.mark.parametrize(
    "value",
    [float("nan"), float("inf"), float("-inf")],
)
def test_metadata_rejects_non_finite_float(value: float) -> None:
    with pytest.raises(ValueError, match="must be finite"):
        make_metadata(extra={"score": value})


def test_document_accepts_valid_data() -> None:
    metadata = make_metadata()
    document = make_document(metadata=metadata)

    assert document.document_id == "doc-001"
    assert document.text == "Market outlook is positive."
    assert document.metadata is metadata


def test_document_normalizes_document_id() -> None:
    document = make_document(document_id="  doc-001  ")

    assert document.document_id == "doc-001"


@pytest.mark.parametrize("document_id", ["", "   "])
def test_document_rejects_empty_id(document_id: str) -> None:
    with pytest.raises(ValueError, match="ID cannot be empty"):
        make_document(document_id=document_id)


def test_document_rejects_non_string_id() -> None:
    with pytest.raises(TypeError, match="ID must be a string"):
        make_document(document_id=123)  # type: ignore[arg-type]


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_document_rejects_empty_text(text: str) -> None:
    with pytest.raises(ValueError, match="text cannot be empty"):
        make_document(text=text)


def test_document_rejects_non_string_text() -> None:
    with pytest.raises(TypeError, match="text must be a string"):
        make_document(text=123)  # type: ignore[arg-type]


def test_document_rejects_invalid_metadata() -> None:
    with pytest.raises(TypeError, match="DocumentMetadata"):
        make_document(metadata="invalid")  # type: ignore[arg-type]


def test_content_hash_is_sha256_of_exact_text() -> None:
    document = make_document(text="Financial report.")

    import hashlib

    expected = hashlib.sha256(
        b"Financial report."
    ).hexdigest()

    assert document.content_sha256 == expected


def test_content_hash_is_deterministic() -> None:
    first = make_document(text="Same extracted text.")
    second = make_document(
        document_id="doc-002",
        text="Same extracted text.",
    )

    assert first.content_sha256 == second.content_sha256


def test_content_hash_changes_when_text_changes() -> None:
    first = make_document(text="Market outlook is positive.")
    second = make_document(text="Market outlook is negative.")

    assert first.content_sha256 != second.content_sha256


def test_document_preserves_original_text() -> None:
    text = "  Report title\n\nBody text with original spacing.  "
    document = make_document(text=text)

    assert document.text == text


def test_document_loader_protocol_defines_required_interface() -> None:
    class ExampleLoader:
        supported_extensions = frozenset({".txt", ".pdf"})

        def load(self, source_path: Path) -> IngestedDocument:
            return make_document(
                document_id=source_path.name,
                metadata=make_metadata(source_path=str(source_path)),
            )

    loader: DocumentLoader = ExampleLoader()
    document = loader.load(Path("report.pdf"))

    assert loader.supported_extensions == frozenset({".txt", ".pdf"})
    assert document.document_id == "report.pdf"
