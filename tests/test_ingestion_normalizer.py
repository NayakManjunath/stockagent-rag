
"""Tests for financial document text normalization."""

from datetime import date

import pytest

from stockagent.ingestion import (
    DocumentMetadata,
    IngestedDocument,
    TextNormalizer,
)


@pytest.fixture
def normalizer() -> TextNormalizer:
    return TextNormalizer()


@pytest.fixture
def sample_document() -> IngestedDocument:
    metadata = DocumentMetadata(
        source_path="data/market_report.pdf",
        file_type="pdf",
        title="Market Report",
        document_type="research_report",
        published_date=date(2026, 1, 15),
        extra={"exchange": "NASDAQ", "page_count": 3},
    )
    return IngestedDocument(
        document_id="doc-market-001",
        text="  Market   outlook\r\n\r\nRevenue increased  by 10%.  ",
        metadata=metadata,
    )


def test_normalize_repeated_spaces(
    normalizer: TextNormalizer,
) -> None:
    assert normalizer.normalize_text(
        "Revenue   increased    by 10%."
    ) == "Revenue increased by 10%."


def test_normalize_tabs_inside_text(
    normalizer: TextNormalizer,
) -> None:
    assert normalizer.normalize_text(
        "Revenue\t\tincreased\tby 10%."
    ) == "Revenue increased by 10%."


def test_normalize_windows_line_endings(
    normalizer: TextNormalizer,
) -> None:
    assert normalizer.normalize_text("First\r\nSecond") == "First\nSecond"


def test_normalize_legacy_mac_line_endings(
    normalizer: TextNormalizer,
) -> None:
    assert normalizer.normalize_text("First\rSecond") == "First\nSecond"


def test_normalize_mixed_line_endings(
    normalizer: TextNormalizer,
) -> None:
    result = normalizer.normalize_text("First\r\nSecond\rThird\nFourth")

    assert result == "First\nSecond\nThird\nFourth"


def test_preserve_single_paragraph_break(
    normalizer: TextNormalizer,
) -> None:
    assert normalizer.normalize_text(
        "First paragraph.\n\nSecond paragraph."
    ) == "First paragraph.\n\nSecond paragraph."


def test_collapse_excessive_blank_lines(
    normalizer: TextNormalizer,
) -> None:
    assert normalizer.normalize_text(
        "First paragraph.\n\n\n\nSecond paragraph."
    ) == "First paragraph.\n\nSecond paragraph."


def test_remove_leading_and_trailing_blank_lines(
    normalizer: TextNormalizer,
) -> None:
    result = normalizer.normalize_text(
        "\n\nFinancial report.\n\n"
    )

    assert result == "Financial report."


def test_remove_control_characters(
    normalizer: TextNormalizer,
) -> None:
    result = normalizer.normalize_text(
        "Revenue\x00 increased\x07 by 10%."
    )

    assert result == "Revenue increased by 10%."


def test_preserve_tabs_as_indentation(
    normalizer: TextNormalizer,
) -> None:
    assert normalizer.normalize_text(
        "\t- Revenue increased"
    ) == "\t- Revenue increased"


def test_preserve_markdown_indentation(
    normalizer: TextNormalizer,
) -> None:
    text = "- Main item\n  - Nested item"

    assert normalizer.normalize_text(text) == text


def test_preserve_markdown_headings_and_tables(
    normalizer: TextNormalizer,
) -> None:
    text = (
        "# Quarterly Results\n\n"
        "| Metric | Value |\n"
        "| --- | --- |\n"
        "| Revenue | ₹1,25,000 |"
    )

    assert normalizer.normalize_text(text) == text


def test_preserve_financial_values(
    normalizer: TextNormalizer,
) -> None:
    text = (
        "Price: ₹1,25,000\n"
        "Revenue: $1,250.50\n"
        "Return: -2.5%\n"
        "Tax: 18%\n"
        "Date: 2026-10-27"
    )

    assert normalizer.normalize_text(text) == text


def test_preserve_unicode_currency_and_accented_text(
    normalizer: TextNormalizer,
) -> None:
    text = "Café earned ₹500 and €20; 市場 outlook remains stable."

    assert normalizer.normalize_text(text) == text


def test_normalize_empty_string(
    normalizer: TextNormalizer,
) -> None:
    assert normalizer.normalize_text("") == ""


def test_normalize_whitespace_only_text(
    normalizer: TextNormalizer,
) -> None:
    assert normalizer.normalize_text(" \t \n \t ") == ""


def test_normalize_rejects_non_string_input(
    normalizer: TextNormalizer,
) -> None:
    with pytest.raises(TypeError, match="must be a string"):
        normalizer.normalize_text(123)  # type: ignore[arg-type]


def test_normalize_document_returns_new_instance(
    normalizer: TextNormalizer,
    sample_document: IngestedDocument,
) -> None:
    result = normalizer.normalize_document(sample_document)

    assert result is not sample_document
    assert isinstance(result, IngestedDocument)


def test_normalize_document_preserves_id_and_metadata(
    normalizer: TextNormalizer,
    sample_document: IngestedDocument,
) -> None:
    result = normalizer.normalize_document(sample_document)

    assert result.document_id == sample_document.document_id
    assert result.metadata is sample_document.metadata
    assert result.metadata.source_path == sample_document.metadata.source_path
    assert result.metadata.published_date == date(2026, 1, 15)
    assert result.metadata.extra["exchange"] == "NASDAQ"


def test_normalize_document_does_not_mutate_original(
    normalizer: TextNormalizer,
    sample_document: IngestedDocument,
) -> None:
    original_text = sample_document.text

    result = normalizer.normalize_document(sample_document)

    assert sample_document.text == original_text
    assert result.text != sample_document.text


def test_normalize_document_normalizes_extracted_text(
    normalizer: TextNormalizer,
    sample_document: IngestedDocument,
) -> None:
    result = normalizer.normalize_document(sample_document)

    assert result.text == (
    "  Market outlook\n\nRevenue increased by 10%."
)


def test_normalize_document_rejects_invalid_object(
    normalizer: TextNormalizer,
) -> None:
    with pytest.raises(
        TypeError,
        match="IngestedDocument",
    ):
        normalizer.normalize_document("not a document")  # type: ignore[arg-type]


def test_normalization_is_idempotent(
    normalizer: TextNormalizer,
) -> None:
    text = "Revenue   increased\r\n\r\n\r\nby 10%."

    once = normalizer.normalize_text(text)
    twice = normalizer.normalize_text(once)

    assert twice == once
