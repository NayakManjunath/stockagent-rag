
"""Text splitting utilities for document chunking."""

from __future__ import annotations

import re
from dataclasses import dataclass

from stockagent.chunking.config import ChunkingConfig
from stockagent.chunking.config import ChunkingStrategy


@dataclass(frozen=True)
class TextSegment:
    """A text segment with its original character offsets."""

    text: str
    start_char: int
    end_char: int

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("text must be a string")

        if not self.text:
            raise ValueError("text must not be empty")

        if (
            isinstance(self.start_char, bool)
            or not isinstance(self.start_char, int)
            or self.start_char < 0
        ):
            raise ValueError("start_char must be a non-negative integer")

        if (
            isinstance(self.end_char, bool)
            or not isinstance(self.end_char, int)
            or self.end_char <= self.start_char
        ):
            raise ValueError("end_char must be greater than start_char")

        if self.end_char - self.start_char != len(self.text):
            raise ValueError("Offsets must match the text length")


class TextChunker:
    """Split text into bounded segments using configurable strategies."""

    def __init__(self, config: ChunkingConfig) -> None:
        if not isinstance(config, ChunkingConfig):
            raise TypeError("config must be a ChunkingConfig instance")

        self.config = config

    def split_text(self, text: str) -> list[TextSegment]:
        """Split text while preserving original character positions."""

        if not isinstance(text, str):
            raise TypeError("text must be a string")

        if not text:
            return []

        if len(text) <= self.config.chunk_size:
            return [TextSegment(text, 0, len(text))]

        if self.config.strategy == ChunkingStrategy.FIXED_SIZE:
            spans = self._split_fixed_size(text)

        elif self.config.strategy == ChunkingStrategy.SENTENCE:
            spans = self._split_at_boundaries(
                text,
                boundary_pattern=r"(?<=[.!?])\s+",
            )

        elif self.config.strategy == ChunkingStrategy.PARAGRAPH:
            spans = self._split_at_boundaries(
                text,
                boundary_pattern=r"\n[ \t]*\n+",
            )

        else:
            raise ValueError(
                f"Unsupported chunking strategy: {self.config.strategy}"
            )

        spans = self._rebalance_final_chunk(
            spans=spans,
            text_length=len(text),
        )

        return [
            TextSegment(
                text=text[start:end],
                start_char=start,
                end_char=end,
            )
            for start, end in spans
        ]

    def _split_fixed_size(self, text: str) -> list[tuple[int, int]]:
        """Split text into fixed-size overlapping windows."""

        spans: list[tuple[int, int]] = []

        start = 0
        text_length = len(text)

        step = (
            self.config.chunk_size
            - self.config.chunk_overlap
        )

        while start < text_length:
            end = min(
                start + self.config.chunk_size,
                text_length,
            )

            spans.append((start, end))

            if end == text_length:
                break

            start += step

        return spans

    def _split_at_boundaries(
        self,
        text: str,
        boundary_pattern: str,
    ) -> list[tuple[int, int]]:
        """
        Prefer sentence or paragraph boundaries.

        If no suitable boundary exists within the maximum
        chunk size, fall back to a hard character boundary.
        """

        spans: list[tuple[int, int]] = []

        text_length = len(text)
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap

        boundaries = [
            match.end()
            for match in re.finditer(boundary_pattern, text)
        ]

        start = 0

        while start < text_length:
            hard_end = min(
                start + chunk_size,
                text_length,
            )

            if hard_end == text_length:
                spans.append((start, hard_end))
                break

            minimum_end = start + max(1, chunk_size // 2)

            valid_boundaries = [
                boundary
                for boundary in boundaries
                if minimum_end <= boundary <= hard_end
            ]

            if valid_boundaries:
                end = valid_boundaries[-1]
            else:
                end = hard_end

            spans.append((start, end))

            next_start = end - overlap

            if next_start <= start:
                next_start = end

            start = next_start

        return spans

    def _rebalance_final_chunk(
        self,
        spans: list[tuple[int, int]],
        text_length: int,
    ) -> list[tuple[int, int]]:
        """
        Try to enlarge an undersized final chunk by moving the
        boundary between the last two chunks.

        Preserve the configured overlap and maximum chunk size.
        If a valid adjustment is impossible, return the original
        spans unchanged.
        """

        minimum_size = self.config.min_chunk_size

        if len(spans) < 2:
            return spans

        previous_start, previous_end = spans[-2]
        last_start, last_end = spans[-1]

        if last_end - last_start >= minimum_size:
            return spans

        if text_length < minimum_size:
            return spans

        adjusted_last_start = text_length - minimum_size

        adjusted_previous_end = (
            adjusted_last_start + self.config.chunk_overlap
        )

        adjusted_previous_size = (
            adjusted_previous_end - previous_start
        )

        adjusted_last_size = text_length - adjusted_last_start

        if adjusted_last_start < previous_start:
            return spans

        if adjusted_previous_end <= previous_start:
            return spans

        if adjusted_previous_size < minimum_size:
            return spans

        if adjusted_previous_size > self.config.chunk_size:
            return spans

        if adjusted_last_size > self.config.chunk_size:
            return spans

        adjusted_spans = list(spans)

        adjusted_spans[-2] = (
            previous_start,
            adjusted_previous_end,
        )

        adjusted_spans[-1] = (
            adjusted_last_start,
            text_length,
        )

        return adjusted_spans
