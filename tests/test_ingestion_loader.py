
"""Tests for financial document loading and text extraction."""

from pathlib import Path

import pytest

import stockagent.ingestion.loader as loader_module
from stockagent.ingestion import DocumentFileLoader, IngestedDocument


@pytest.fixture
def loader() -> DocumentFileLoader:
    return DocumentFileLoader()


def test_load_txt_file_returns_ingested_document(
    loader: DocumentFileLoader,
    tmp_path: Path,
) -> None:
    path = tmp_path / "report.txt"
    path.write_text("Revenue increased by 10%.", encoding="utf-8")

    document = loader.load(path)

    assert isinstance(document, IngestedDocument)
    assert document.text == "Revenue increased by 10%."
    assert document.metadata.file_type == "txt"
    assert document.metadata.title == "report"
    assert document.metadata.extra["extraction_method"] == "utf-8-sig"


def test_load_markdown_file(
    loader: DocumentFileLoader,
    tmp_path: Path,
) -> None:
    path = tmp_path / "market.md"
    path.write_text("# Market Outlook\n\nGrowth is expected.", encoding="utf-8")

    document = loader.load(path)

    assert document.text == "# Market Outlook\n\nGrowth is expected."
    assert document.metadata.file_type == "md"


def test_loader_handles_utf8_bom(
    loader: DocumentFileLoader,
    tmp_path: Path,
) -> None:
    path = tmp_path / "bom.txt"
    path.write_text("\ufeffFinancial report", encoding="utf-8")

    document = loader.load(path)

    assert document.text == "Financial report"
    assert not document.text.startswith("\ufeff")


def test_loader_preserves_text_whitespace(
    loader: DocumentFileLoader,
    tmp_path: Path,
) -> None:
    original_text = "  Title\n\nBody text.  "
    path = tmp_path / "spacing.txt"
    path.write_text(original_text, encoding="utf-8")

    document = loader.load(path)

    assert document.text == original_text


def test_loader_preserves_unicode(
    loader: DocumentFileLoader,
    tmp_path: Path,
) -> None:
    original_text = "市場 outlook: café, € and ₹"
    path = tmp_path / "unicode.txt"
    path.write_text(original_text, encoding="utf-8")

    document = loader.load(path)

    assert document.text == original_text


def test_loader_sets_absolute_source_path(
    loader: DocumentFileLoader,
    tmp_path: Path,
) -> None:
    path = tmp_path / "report.txt"
    path.write_text("Financial report", encoding="utf-8")

    document = loader.load(path)

    assert document.metadata.source_path == str(path.resolve())


def test_document_id_is_deterministic_for_same_path(
    loader: DocumentFileLoader,
    tmp_path: Path,
) -> None:
    path = tmp_path / "report.txt"
    path.write_text("Financial report", encoding="utf-8")

    first = loader.load(path)
    second = loader.load(path)

    assert first.document_id == second.document_id


def test_document_id_uses_doc_prefix(
    loader: DocumentFileLoader,
    tmp_path: Path,
) -> None:
    path = tmp_path / "report.txt"
    path.write_text("Financial report", encoding="utf-8")

    document = loader.load(path)

    assert document.document_id.startswith("doc-")


def test_same_text_at_different_paths_has_different_ids(
    loader: DocumentFileLoader,
    tmp_path: Path,
) -> None:
    first_path = tmp_path / "first.txt"
    second_path = tmp_path / "second.txt"
    first_path.write_text("Same content", encoding="utf-8")
    second_path.write_text("Same content", encoding="utf-8")

    first = loader.load(first_path)
    second = loader.load(second_path)

    assert first.content_sha256 == second.content_sha256
    assert first.document_id != second.document_id


def test_load_rejects_missing_file(
    loader: DocumentFileLoader,
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError, match="File does not exist"):
        loader.load(tmp_path / "missing.txt")


def test_load_rejects_unsupported_file(
    loader: DocumentFileLoader,
    tmp_path: Path,
) -> None:
    path = tmp_path / "data.csv"
    path.write_text("a,b", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file format"):
        loader.load(path)


def test_load_rejects_directory(
    loader: DocumentFileLoader,
    tmp_path: Path,
) -> None:
    with pytest.raises(IsADirectoryError, match="Path is not a file"):
        loader.load(tmp_path)


def test_load_rejects_invalid_path_argument(
    loader: DocumentFileLoader,
) -> None:
    with pytest.raises(TypeError, match="must be a string or Path"):
        loader.load(123)  # type: ignore[arg-type]


def test_load_rejects_invalid_utf8(
    loader: DocumentFileLoader,
    tmp_path: Path,
) -> None:
    path = tmp_path / "invalid.txt"
    path.write_bytes(b"\xff\xfe\xfa")

    with pytest.raises(UnicodeDecodeError):
        loader.load(path)


class FakePage:
    def __init__(self, text: str | None) -> None:
        self._text = text

    def extract_text(self) -> str | None:
        return self._text


class FakePdfReader:
    def __init__(self, _: str) -> None:
        self.pages = [
            FakePage("Page one financial data."),
            FakePage("Page two market outlook."),
        ]


def test_load_pdf_extracts_pages_in_order(
    loader: DocumentFileLoader,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "report.pdf"
    path.write_bytes(b"fake PDF placeholder")
    monkeypatch.setattr(loader_module, "PdfReader", FakePdfReader)

    document = loader.load(path)

    assert document.text == (
        "Page one financial data.\n\nPage two market outlook."
    )
    assert document.metadata.file_type == "pdf"
    assert document.metadata.extra["extraction_method"] == "pypdf"
    assert document.metadata.extra["page_count"] == 2


def test_pdf_loader_handles_page_without_extractable_text(
    loader: DocumentFileLoader,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class PartiallyReadablePdf:
        def __init__(self, _: str) -> None:
            self.pages = [
                FakePage("First page text."),
                FakePage(None),
                FakePage("Third page text."),
            ]

    path = tmp_path / "partial.pdf"
    path.write_bytes(b"fake PDF placeholder")
    monkeypatch.setattr(
        loader_module,
        "PdfReader",
        PartiallyReadablePdf,
    )

    document = loader.load(path)

    assert document.text == "First page text.\n\n\n\nThird page text."
    assert document.metadata.extra["page_count"] == 3


def test_pdf_loader_rejects_pdf_with_no_extractable_text(
    loader: DocumentFileLoader,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ImageOnlyPdf:
        def __init__(self, _: str) -> None:
            self.pages = [FakePage(None), FakePage("  ")]

    path = tmp_path / "scanned.pdf"
    path.write_bytes(b"fake PDF placeholder")
    monkeypatch.setattr(loader_module, "PdfReader", ImageOnlyPdf)

    with pytest.raises(ValueError, match="No extractable text"):
        loader.load(path)


def test_pdf_loader_propagates_reader_errors(
    loader: DocumentFileLoader,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenPdfReader:
        def __init__(self, _: str) -> None:
            raise RuntimeError("PDF parser failed")

    path = tmp_path / "broken.pdf"
    path.write_bytes(b"fake PDF placeholder")
    monkeypatch.setattr(loader_module, "PdfReader", BrokenPdfReader)

    with pytest.raises(RuntimeError, match="PDF parser failed"):
        loader.load(path)
