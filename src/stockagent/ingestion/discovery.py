
"""File discovery and supported-format validation for ingestion."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


DEFAULT_SUPPORTED_EXTENSIONS = frozenset({".pdf", ".txt", ".md"})


class FileDiscovery:
    """Discover supported document files without extracting their content."""

    def __init__(
        self,
        supported_extensions: Iterable[str] = DEFAULT_SUPPORTED_EXTENSIONS,
        recursive: bool = False,
    ) -> None:
        """Configure supported extensions and recursive discovery."""

        if isinstance(supported_extensions, (str, bytes)):
            raise TypeError(
                "Supported extensions must be an iterable of extensions."
            )

        if not isinstance(recursive, bool):
            raise TypeError("Recursive must be a boolean.")

        normalized_extensions: set[str] = set()

        for extension in supported_extensions:
            if not isinstance(extension, str):
                raise TypeError("Every supported extension must be a string.")

            normalized = extension.strip().lower()

            if normalized and not normalized.startswith("."):
                normalized = f".{normalized}"

            if (
                not normalized
                or normalized == "."
                or "/" in normalized
                or "\\" in normalized
            ):
                raise ValueError(f"Invalid file extension: {extension!r}")

            normalized_extensions.add(normalized)

        if not normalized_extensions:
            raise ValueError("At least one supported extension is required.")

        self.supported_extensions = frozenset(normalized_extensions)
        self.recursive = recursive

    @staticmethod
    def _validate_path_argument(directory: str | Path) -> Path:
        """Validate and convert a directory argument to Path."""

        if not isinstance(directory, (str, Path)):
            raise TypeError("Directory must be a string or Path.")

        if isinstance(directory, str) and not directory.strip():
            raise ValueError("Directory path cannot be empty.")

        return Path(directory)

    def validate_file(self, file_path: str | Path) -> Path:
        """Return a valid supported file path or raise an informative error."""

        if not isinstance(file_path, (str, Path)):
            raise TypeError("File path must be a string or Path.")

        if isinstance(file_path, str) and not file_path.strip():
            raise ValueError("File path cannot be empty.")

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")

        if path.is_symlink():
            raise ValueError(f"Symbolic links are not supported: {path}")

        if not path.is_file():
            raise IsADirectoryError(f"Path is not a file: {path}")

        if path.suffix.lower() not in self.supported_extensions:
            supported = ", ".join(sorted(self.supported_extensions))
            raise ValueError(
                f"Unsupported file format: {path.suffix or '<no extension>'}. "
                f"Supported extensions: {supported}"
            )

        return path

    def discover(self, directory: str | Path) -> list[Path]:
        """Find supported files and return them in deterministic order."""

        root = self._validate_path_argument(directory)

        if not root.exists():
            raise FileNotFoundError(f"Directory does not exist: {root}")

        if root.is_symlink():
            raise ValueError(f"Symbolic-link directories are not supported: {root}")

        if not root.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {root}")

        discovered: list[Path] = []

        if self.recursive:
            for current_root, directory_names, file_names in os.walk(
                root,
                followlinks=False,
            ):
                current_path = Path(current_root)

                # Do not descend into directory symlinks.
                directory_names[:] = sorted(
                    name
                    for name in directory_names
                    if not (current_path / name).is_symlink()
                )

                for file_name in sorted(file_names):
                    path = current_path / file_name

                    if path.is_symlink() or not path.is_file():
                        continue

                    if path.suffix.lower() in self.supported_extensions:
                        discovered.append(path)
        else:
            for path in root.iterdir():
                if path.is_symlink() or not path.is_file():
                    continue

                if path.suffix.lower() in self.supported_extensions:
                    discovered.append(path)

        return sorted(
            discovered,
            key=lambda path: path.relative_to(root).as_posix().casefold(),
        )
