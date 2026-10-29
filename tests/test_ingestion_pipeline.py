
"""Tests for ingestion validation, error handling, and orchestration."""

from pathlib import Path

import pytest

from stockagent.ingestion import (
    DocumentMetadata,
    DocumentValidationError,
    DocumentValidator,
    IngestedDocument,
    IngestionPipeline,
    IngestionReport,
)


def make_document(
    source_path: str = "report.txt",
    file_type: str = "txt",
    text: str = "Revenue increased by 10%.",
    document_id: str = "doc-001",
) -> IngestedDocument:
    """Build a document for validation tests."""

    return IngestedDocument(
        document_id=document_id,
        text=text,
        metadata=DocumentMetadata(
            source_path=source_path,
            file_type=file_type,
            title="Financial Report",
        ),
    )


class TestDocumentValidator:
    """Tests for document contract validation."""

    def setup_method(self) -> None:
        self.validator = DocumentValidator()

    def test_accepts_valid_document(self) -> None:
        document = make_document()

        result = self.validator.validate(document)

        assert result is document

    def test_rejects_wrong_document_type(self) -> None:
        with pytest.raises(
            TypeError,
            match="IngestedDocument",
        ):
            self.validator.validate("not a document")  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("source_path", "file_type"),
        [
            ("report.csv", "csv"),
            ("report.docx", "docx"),
            ("report", "txt"),
        ],
    )
    def test_rejects_unsupported_source_extension(
        self,
        source_path: str,
        file_type: str,
    ) -> None:
        document = make_document(
            source_path=source_path,
            file_type=file_type,
        )

        with pytest.raises(
            DocumentValidationError,
            match="Unsupported source file extension",
        ):
            self.validator.validate(document)

    def test_rejects_mismatched_metadata_file_type(self) -> None:
        document = make_document(
            source_path="report.txt",
            file_type="pdf",
        )

        with pytest.raises(
            DocumentValidationError,
            match="does not match",
        ):
            self.validator.validate(document)

    def test_accepts_pdf_extension_case_insensitively(self) -> None:
        document = make_document(
            source_path="report.PDF",
            file_type="pdf",
        )

        assert self.validator.validate(document) is document

    def test_preserves_document_metadata(self) -> None:
        document = make_document()
        original_metadata = document.metadata

        result = self.validator.validate(document)

        assert result.metadata is original_metadata
        assert result.metadata.title == "Financial Report"


class TestIngestionPipeline:
    """Tests for the resilient batch ingestion pipeline."""

    def test_ingests_and_normalizes_text_file(
        self,
        tmp_path: Path,
    ) -> None:
        source = tmp_path / "report.txt"
        source.write_text(
            "  Revenue   increased by 10%.  \r\n",
            encoding="utf-8",
        )

        report = IngestionPipeline().ingest_paths([source])

        assert report.discovered_count == 1
        assert report.succeeded_count == 1
        assert report.failed_count == 0
        assert report.is_successful is True
        assert report.documents[0].text == "  Revenue increased by 10%."
        assert report.documents[0].metadata.file_type == "txt"

    def test_continues_after_a_file_failure(
        self,
        tmp_path: Path,
    ) -> None:
        first = tmp_path / "first.txt"
        missing = tmp_path / "missing.txt"
        third = tmp_path / "third.md"

        first.write_text("First financial document.", encoding="utf-8")
        third.write_text("Third financial document.", encoding="utf-8")

        report = IngestionPipeline().ingest_paths(
            [first, missing, third]
        )

        assert report.discovered_count == 3
        assert report.succeeded_count == 2
        assert report.failed_count == 1
        assert report.is_successful is False
        assert [doc.metadata.title for doc in report.documents] == [
            "first",
            "third",
        ]
        assert report.failures[0].source_path == str(missing)
        assert report.failures[0].error_type == "FileNotFoundError"
        assert "does not exist" in report.failures[0].message

    def test_records_invalid_path_item_and_continues(
        self,
        tmp_path: Path,
    ) -> None:
        source = tmp_path / "valid.txt"
        source.write_text("Valid content.", encoding="utf-8")

        report = IngestionPipeline().ingest_paths(
            [42, source]  # type: ignore[list-item]
        )

        assert report.discovered_count == 2
        assert report.succeeded_count == 1
        assert report.failed_count == 1
        assert report.failures[0].error_type == "TypeError"

    def test_rejects_a_single_path_instead_of_an_iterable(
        self,
        tmp_path: Path,
    ) -> None:
        source = tmp_path / "report.txt"
        source.write_text("Content.", encoding="utf-8")

        with pytest.raises(TypeError, match="not a single path"):
            IngestionPipeline().ingest_paths(source)

    def test_rejects_non_iterable_input(self) -> None:
        with pytest.raises(TypeError, match="iterable"):
            IngestionPipeline().ingest_paths(123)  # type: ignore[arg-type]

    def test_empty_batch_returns_empty_successful_report(self) -> None:
        report = IngestionPipeline().ingest_paths([])

        assert isinstance(report, IngestionReport)
        assert report.discovered_count == 0
        assert report.succeeded_count == 0
        assert report.failed_count == 0
        assert report.is_successful is True

    def test_rejects_duplicate_document_ids(
        self,
        tmp_path: Path,
    ) -> None:
        source = tmp_path / "report.txt"
        source.write_text("Financial content.", encoding="utf-8")

        report = IngestionPipeline().ingest_paths([source, source])

        assert report.discovered_count == 2
        assert report.succeeded_count == 1
        assert report.failed_count == 1
        assert "Duplicate document ID" in report.failures[0].message

    def test_ingests_supported_files_from_directory(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "report.txt").write_text(
            "Quarterly revenue.",
            encoding="utf-8",
        )
        (tmp_path / "notes.md").write_text(
            "# Financial notes",
            encoding="utf-8",
        )
        (tmp_path / "ignored.csv").write_text(
            "a,b\n1,2",
            encoding="utf-8",
        )

        report = IngestionPipeline().ingest_directory(tmp_path)

        assert report.discovered_count == 2
        assert report.succeeded_count == 2
        assert report.failed_count == 0
        assert report.is_successful is True
        assert {
            document.metadata.file_type
            for document in report.documents
        } == {"txt", "md"}

    def test_directory_errors_are_propagated(
        self,
        tmp_path: Path,
    ) -> None:
        missing_directory = tmp_path / "missing"

        with pytest.raises(FileNotFoundError):
            IngestionPipeline().ingest_directory(missing_directory)

    def test_failure_contains_structured_error_information(
        self,
        tmp_path: Path,
    ) -> None:
        missing = tmp_path / "absent.pdf"

        report = IngestionPipeline().ingest_paths([missing])
        failure = report.failures[0]

        assert failure.source_path == str(missing)
        assert failure.error_type == "FileNotFoundError"
        assert failure.message
