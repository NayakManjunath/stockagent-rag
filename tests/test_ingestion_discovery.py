
"""Tests for file discovery and supported-format validation."""

from pathlib import Path

import pytest

from stockagent.ingestion import FileDiscovery


@pytest.fixture
def discovery() -> FileDiscovery:
    return FileDiscovery()


@pytest.fixture
def sample_directory(tmp_path: Path) -> Path:
    (tmp_path / "report.pdf").write_text("PDF placeholder", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("Text placeholder", encoding="utf-8")
    (tmp_path / "readme.md").write_text("Markdown placeholder", encoding="utf-8")
    (tmp_path / "data.csv").write_text("a,b", encoding="utf-8")
    (tmp_path / "no_extension").write_text("ignored", encoding="utf-8")
    return tmp_path


def test_default_supported_extensions(discovery: FileDiscovery) -> None:
    assert discovery.supported_extensions == {".pdf", ".txt", ".md"}


def test_discovery_finds_supported_files(
    discovery: FileDiscovery,
    sample_directory: Path,
) -> None:
    found = discovery.discover(sample_directory)

    assert {path.name for path in found} == {
        "report.pdf",
        "notes.txt",
        "readme.md",
    }


def test_discovery_returns_deterministic_sorted_results(
    discovery: FileDiscovery,
    sample_directory: Path,
) -> None:
    first = discovery.discover(sample_directory)
    second = discovery.discover(sample_directory)

    assert first == second
    assert [path.name for path in first] == [
        "notes.txt",
        "readme.md",
        "report.pdf",
    ]


def test_discovery_is_non_recursive_by_default(
    discovery: FileDiscovery,
    sample_directory: Path,
) -> None:
    nested = sample_directory / "nested"
    nested.mkdir()
    (nested / "nested.pdf").write_text("Nested", encoding="utf-8")

    found = discovery.discover(sample_directory)

    assert all(path.parent == sample_directory for path in found)


def test_recursive_discovery_finds_nested_files(
    sample_directory: Path,
) -> None:
    nested = sample_directory / "nested"
    nested.mkdir()
    (nested / "nested.pdf").write_text("Nested", encoding="utf-8")
    (nested / "ignored.csv").write_text("a,b", encoding="utf-8")

    discovery = FileDiscovery(recursive=True)
    found = discovery.discover(sample_directory)

    assert sample_directory / "nested" / "nested.pdf" in found
    assert all(path.suffix.lower() in {".pdf", ".txt", ".md"} for path in found)


def test_discovery_accepts_custom_extensions(tmp_path: Path) -> None:
    (tmp_path / "prices.csv").write_text("price", encoding="utf-8")
    (tmp_path / "report.pdf").write_text("report", encoding="utf-8")

    discovery = FileDiscovery(supported_extensions={"CSV"})
    found = discovery.discover(tmp_path)

    assert [path.name for path in found] == ["prices.csv"]


def test_extension_configuration_accepts_extensions_with_or_without_dot(
    tmp_path: Path,
) -> None:
    (tmp_path / "report.pdf").write_text("report", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("notes", encoding="utf-8")

    discovery = FileDiscovery(supported_extensions={" .PDF "})

    assert [path.name for path in discovery.discover(tmp_path)] == ["report.pdf"]


@pytest.mark.parametrize(
    "extensions",
    [
        set(),
        {""},
        {"."},
        {"/tmp"},
        {"folder\\file"},
    ],
)
def test_rejects_invalid_extension_configuration(
    extensions: set[str],
) -> None:
    with pytest.raises(ValueError):
        FileDiscovery(supported_extensions=extensions)


def test_rejects_string_instead_of_extension_collection() -> None:
    with pytest.raises(TypeError, match="iterable of extensions"):
        FileDiscovery(supported_extensions="pdf")  # type: ignore[arg-type]


def test_rejects_non_string_extension() -> None:
    with pytest.raises(TypeError, match="must be a string"):
        FileDiscovery(supported_extensions={123})  # type: ignore[arg-type]


def test_rejects_empty_extension_collection() -> None:
    with pytest.raises(ValueError, match="At least one"):
        FileDiscovery(supported_extensions=[])


@pytest.mark.parametrize("recursive", [0, 1, "yes", None])
def test_recursive_option_must_be_boolean(recursive: object) -> None:
    with pytest.raises(TypeError, match="must be a boolean"):
        FileDiscovery(recursive=recursive)  # type: ignore[arg-type]


def test_discovery_rejects_missing_directory(
    discovery: FileDiscovery,
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError, match="Directory does not exist"):
        discovery.discover(tmp_path / "missing")


def test_discovery_rejects_file_as_directory(
    discovery: FileDiscovery,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "report.pdf"
    file_path.write_text("report", encoding="utf-8")

    with pytest.raises(NotADirectoryError, match="not a directory"):
        discovery.discover(file_path)


@pytest.mark.parametrize("directory", ["", "   "])
def test_discovery_rejects_empty_directory_path(
    discovery: FileDiscovery,
    directory: str,
) -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        discovery.discover(directory)


def test_discovery_rejects_invalid_directory_argument(
    discovery: FileDiscovery,
) -> None:
    with pytest.raises(TypeError, match="must be a string or Path"):
        discovery.discover(123)  # type: ignore[arg-type]


def test_discovery_rejects_a_regular_file_symlink_as_root(
    discovery: FileDiscovery,
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "directory_link"

    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Directory symlinks are unavailable on this platform.")

    with pytest.raises(ValueError, match="Symbolic-link directories"):
        discovery.discover(link)


def test_discovery_skips_unsupported_files(
    discovery: FileDiscovery,
    sample_directory: Path,
) -> None:
    found = discovery.discover(sample_directory)

    assert all(path.suffix.lower() in discovery.supported_extensions for path in found)
    assert not any(path.name == "data.csv" for path in found)
    assert not any(path.name == "no_extension" for path in found)


def test_validate_file_accepts_supported_file(
    discovery: FileDiscovery,
    sample_directory: Path,
) -> None:
    path = sample_directory / "report.pdf"

    assert discovery.validate_file(path) == path


def test_validate_file_is_case_insensitive(
    discovery: FileDiscovery,
    tmp_path: Path,
) -> None:
    path = tmp_path / "REPORT.PDF"
    path.write_text("report", encoding="utf-8")

    assert discovery.validate_file(path) == path


def test_validate_file_accepts_string_path(
    discovery: FileDiscovery,
    sample_directory: Path,
) -> None:
    path = sample_directory / "notes.txt"

    assert discovery.validate_file(str(path)) == path


def test_validate_file_rejects_missing_file(
    discovery: FileDiscovery,
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError, match="File does not exist"):
        discovery.validate_file(tmp_path / "missing.pdf")


def test_validate_file_rejects_unsupported_format(
    discovery: FileDiscovery,
    sample_directory: Path,
) -> None:
    with pytest.raises(ValueError, match="Unsupported file format"):
        discovery.validate_file(sample_directory / "data.csv")


def test_validate_file_rejects_path_without_extension(
    discovery: FileDiscovery,
    sample_directory: Path,
) -> None:
    with pytest.raises(ValueError, match="Unsupported file format"):
        discovery.validate_file(sample_directory / "no_extension")


def test_validate_file_rejects_directory(
    discovery: FileDiscovery,
    tmp_path: Path,
) -> None:
    with pytest.raises(IsADirectoryError, match="Path is not a file"):
        discovery.validate_file(tmp_path)


def test_validate_file_rejects_empty_path(
    discovery: FileDiscovery,
) -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        discovery.validate_file("  ")


def test_validate_file_rejects_invalid_path_argument(
    discovery: FileDiscovery,
) -> None:
    with pytest.raises(TypeError, match="must be a string or Path"):
        discovery.validate_file(123)  # type: ignore[arg-type]


def test_discovery_skips_file_symlinks(
    discovery: FileDiscovery,
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.pdf"
    target.write_text("report", encoding="utf-8")
    link = tmp_path / "linked.pdf"

    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("File symlinks are unavailable on this platform.")

    found = discovery.discover(tmp_path)

    assert target in found
    assert link not in found


def test_recursive_discovery_does_not_follow_directory_symlinks(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()

    outside_file = outside / "external.pdf"
    outside_file.write_text("external", encoding="utf-8")

    try:
        (root / "external_link").symlink_to(
            outside,
            target_is_directory=True,
        )
    except (OSError, NotImplementedError):
        pytest.skip("Directory symlinks are unavailable on this platform.")

    found = FileDiscovery(recursive=True).discover(root)

    assert found == []
