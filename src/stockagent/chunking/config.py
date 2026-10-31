
"""Configuration models for document chunking."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ChunkingStrategy(str, Enum):
    """Supported document chunking strategies."""

    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"


@dataclass(frozen=True)
class ChunkingConfig:
    """Store and validate document chunking parameters.

    All size-related parameters are measured in characters, not tokens.
    """

    chunk_size: int = 1000
    chunk_overlap: int = 150
    min_chunk_size: int = 100
    strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""

        self._validate_integer(
            "chunk_size",
            self.chunk_size,
        )
        self._validate_integer(
            "chunk_overlap",
            self.chunk_overlap,
        )
        self._validate_integer(
            "min_chunk_size",
            self.min_chunk_size,
        )

        if self.chunk_size <= 0:
            raise ValueError("Chunk size must be greater than zero.")

        if self.chunk_overlap < 0:
            raise ValueError("Chunk overlap cannot be negative.")

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                "Chunk overlap must be smaller than chunk size."
            )

        if self.min_chunk_size <= 0:
            raise ValueError(
                "Minimum chunk size must be greater than zero."
            )

        if self.min_chunk_size > self.chunk_size:
            raise ValueError(
                "Minimum chunk size cannot exceed chunk size."
            )

        if isinstance(self.strategy, str):
            try:
                object.__setattr__(
                    self,
                    "strategy",
                    ChunkingStrategy(self.strategy),
                )
            except ValueError as exc:
                supported = ", ".join(
                    strategy.value for strategy in ChunkingStrategy
                )
                raise ValueError(
                    f"Unsupported chunking strategy: {self.strategy!r}. "
                    f"Supported strategies: {supported}"
                ) from exc

        elif not isinstance(self.strategy, ChunkingStrategy):
            raise TypeError(
                "Strategy must be a ChunkingStrategy or a valid "
                "strategy string."
            )

    @staticmethod
    def _validate_integer(name: str, value: int) -> None:
        """Reject non-integer values and booleans."""

        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(
                f"{name} must be an integer."
            )
