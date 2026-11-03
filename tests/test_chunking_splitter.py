
"""Tests for the text chunking engine."""

import pytest

from stockagent.chunking.config import ChunkingConfig
from stockagent.chunking.config import ChunkingStrategy
from stockagent.chunking.splitter import TextChunker
from stockagent.chunking.splitter import TextSegment


def test_text_segment_valid_offsets():
    segment = TextSegment(
        text="Hello",
        start_char=0,
        end_char=5,
    )

    assert segment.text == "Hello"
    assert segment.start_char == 0
    assert segment.end_char == 5


def test_text_segment_rejects_empty_text():
    with pytest.raises(ValueError, match="must not be empty"):
        TextSegment("", 0, 0)


def test_text_segment_rejects_invalid_offsets():
    with pytest.raises(ValueError, match="Offsets must match"):
        TextSegment("Hello", 0, 4)


def test_text_segment_rejects_negative_start():
    with pytest.raises(ValueError, match="start_char"):
        TextSegment("Hello", -1, 4)


def test_text_segment_rejects_boolean_offset():
    with pytest.raises(ValueError, match="start_char"):
        TextSegment("Hello", True, 6)


def test_chunker_requires_chunking_config():
    with pytest.raises(TypeError, match="ChunkingConfig"):
        TextChunker(config="invalid")


def test_splitter_rejects_non_string_input():
    chunker = TextChunker(ChunkingConfig())

    with pytest.raises(TypeError, match="string"):
        chunker.split_text(123)


def test_empty_text_returns_empty_list():
    chunker = TextChunker(ChunkingConfig())

    assert chunker.split_text("") == []


def test_short_text_returns_single_segment():
    config = ChunkingConfig(
        chunk_size=20,
        chunk_overlap=5,
        min_chunk_size=10,
    )
    chunker = TextChunker(config)

    result = chunker.split_text("Short text")

    assert len(result) == 1
    assert result[0].text == "Short text"
    assert result[0].start_char == 0
    assert result[0].end_char == 10


def test_fixed_size_splitting_without_overlap():
    config = ChunkingConfig(
        chunk_size=5,
        chunk_overlap=0,
        min_chunk_size=1,
        strategy=ChunkingStrategy.FIXED_SIZE,
    )
    chunker = TextChunker(config)

    result = chunker.split_text("ABCDEFGHIJKL")

    assert [segment.text for segment in result] == [
        "ABCDE",
        "FGHIJ",
        "KL",
    ]


def test_fixed_size_splitting_with_overlap():
    config = ChunkingConfig(
        chunk_size=6,
        chunk_overlap=2,
        min_chunk_size=1,
        strategy=ChunkingStrategy.FIXED_SIZE,
    )
    chunker = TextChunker(config)

    result = chunker.split_text("ABCDEFGHIJKL")

    assert [segment.text for segment in result] == [
        "ABCDEF",
        "EFGHIJ",
        "IJKL",
    ]


def test_fixed_size_offsets_are_correct():
    config = ChunkingConfig(
        chunk_size=5,
        chunk_overlap=2,
        min_chunk_size=1,
        strategy=ChunkingStrategy.FIXED_SIZE,
    )
    chunker = TextChunker(config)

    text = "ABCDEFGHIJ"
    result = chunker.split_text(text)

    for segment in result:
        assert segment.text == text[
            segment.start_char:segment.end_char
        ]


def test_sentence_strategy_prefers_sentence_boundaries():
    text = (
        "First sentence. "
        "Second sentence. "
        "Third sentence."
    )

    config = ChunkingConfig(
        chunk_size=35,
        chunk_overlap=0,
        min_chunk_size=1,
        strategy=ChunkingStrategy.SENTENCE,
    )
    chunker = TextChunker(config)

    result = chunker.split_text(text)

    assert len(result) == 2
    assert result[0].text == "First sentence. Second sentence. "
    assert result[1].text == "Third sentence."


def test_sentence_strategy_falls_back_for_long_sentence():
    text = "A" * 30

    config = ChunkingConfig(
        chunk_size=10,
        chunk_overlap=0,
        min_chunk_size=1,
        strategy=ChunkingStrategy.SENTENCE,
    )
    chunker = TextChunker(config)

    result = chunker.split_text(text)

    assert [len(segment.text) for segment in result] == [
        10,
        10,
        10,
    ]


def test_paragraph_strategy_prefers_paragraph_boundaries():
    text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."

    config = ChunkingConfig(
        chunk_size=35,
        chunk_overlap=0,
        min_chunk_size=1,
        strategy=ChunkingStrategy.PARAGRAPH,
    )
    chunker = TextChunker(config)

    result = chunker.split_text(text)

    assert len(result) == 2
    assert result[0].text == "Paragraph one.\n\nParagraph two.\n\n"
    assert result[1].text == "Paragraph three."


def test_paragraph_strategy_falls_back_for_long_paragraph():
    text = "A" * 25

    config = ChunkingConfig(
        chunk_size=10,
        chunk_overlap=0,
        min_chunk_size=1,
        strategy=ChunkingStrategy.PARAGRAPH,
    )
    chunker = TextChunker(config)

    result = chunker.split_text(text)

    assert [len(segment.text) for segment in result] == [
        10,
        10,
        5,
    ]


def test_boundary_strategy_applies_overlap():
    text = "First sentence. Second sentence. Third sentence."

    config = ChunkingConfig(
        chunk_size=35,
        chunk_overlap=5,
        min_chunk_size=1,
        strategy=ChunkingStrategy.SENTENCE,
    )
    chunker = TextChunker(config)

    result = chunker.split_text(text)

    assert len(result) >= 2

    for previous, current in zip(result, result[1:]):
        assert current.start_char < previous.end_char


def test_segments_preserve_original_offsets():
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."

    config = ChunkingConfig(
        chunk_size=25,
        chunk_overlap=5,
        min_chunk_size=1,
        strategy=ChunkingStrategy.PARAGRAPH,
    )
    chunker = TextChunker(config)

    result = chunker.split_text(text)

    for segment in result:
        assert segment.text == text[
            segment.start_char:segment.end_char
        ]


def test_chunks_do_not_exceed_configured_size():
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 5

    config = ChunkingConfig(
        chunk_size=20,
        chunk_overlap=5,
        min_chunk_size=1,
        strategy=ChunkingStrategy.FIXED_SIZE,
    )
    chunker = TextChunker(config)

    result = chunker.split_text(text)

    assert all(
        len(segment.text) <= config.chunk_size
        for segment in result
    )


def test_consecutive_segments_have_no_uncovered_gaps():
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 3

    config = ChunkingConfig(
        chunk_size=15,
        chunk_overlap=4,
        min_chunk_size=1,
        strategy=ChunkingStrategy.FIXED_SIZE,
    )
    chunker = TextChunker(config)

    result = chunker.split_text(text)

    for previous, current in zip(result, result[1:]):
        assert current.start_char <= previous.end_char


def test_final_segment_reaches_end_of_original_text():
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    config = ChunkingConfig(
        chunk_size=10,
        chunk_overlap=3,
        min_chunk_size=1,
        strategy=ChunkingStrategy.FIXED_SIZE,
    )
    chunker = TextChunker(config)

    result = chunker.split_text(text)

    assert result[-1].end_char == len(text)


# Minimum chunk size refinement tests


def test_rebalances_undersized_final_chunk():
    text = "ABCDEFGHIJKLMNOPQRS"

    config = ChunkingConfig(
        chunk_size=10,
        chunk_overlap=2,
        min_chunk_size=5,
        strategy=ChunkingStrategy.FIXED_SIZE,
    )
    chunker = TextChunker(config)

    result = chunker.split_text(text)

    assert [len(segment.text) for segment in result] == [
        10,
        8,
        5,
    ]

    assert [segment.text for segment in result] == [
        "ABCDEFGHIJ",
        "IJKLMNOP",
        "OPQRS",
    ]


def test_rebalancing_preserves_configured_overlap():
    text = "ABCDEFGHIJKLMNOPQRS"

    config = ChunkingConfig(
        chunk_size=10,
        chunk_overlap=2,
        min_chunk_size=5,
        strategy=ChunkingStrategy.FIXED_SIZE,
    )
    chunker = TextChunker(config)

    result = chunker.split_text(text)

    for previous, current in zip(result, result[1:]):
        overlap = previous.end_char - current.start_char

        assert overlap == config.chunk_overlap


def test_does_not_rebalance_when_constraints_cannot_be_satisfied():
    text = "ABCDEFGHIJKLMNOPQRS"

    config = ChunkingConfig(
        chunk_size=10,
        chunk_overlap=2,
        min_chunk_size=8,
        strategy=ChunkingStrategy.FIXED_SIZE,
    )
    chunker = TextChunker(config)

    result = chunker.split_text(text)

    assert len(result[-1].text) == 3

    assert all(
        len(segment.text) <= config.chunk_size
        for segment in result
    )

    assert result[-1].end_char == len(text)


def test_short_document_is_not_rebalanced():
    text = "ABC"

    config = ChunkingConfig(
        chunk_size=10,
        chunk_overlap=2,
        min_chunk_size=5,
        strategy=ChunkingStrategy.FIXED_SIZE,
    )
    chunker = TextChunker(config)

    result = chunker.split_text(text)

    assert len(result) == 1
    assert result[0].text == text
    assert result[0].start_char == 0
    assert result[0].end_char == len(text)


def test_rebalanced_segments_preserve_original_offsets():
    text = "ABCDEFGHIJKLMNOPQRS"

    config = ChunkingConfig(
        chunk_size=10,
        chunk_overlap=2,
        min_chunk_size=5,
        strategy=ChunkingStrategy.FIXED_SIZE,
    )
    chunker = TextChunker(config)

    result = chunker.split_text(text)

    for segment in result:
        assert segment.text == text[
            segment.start_char:segment.end_char
        ]
