
"""Tests for chunking configuration and strategy selection."""

from dataclasses import FrozenInstanceError

import pytest

from stockagent.chunking import ChunkingConfig, ChunkingStrategy


class TestChunkingConfig:
    """Tests for chunking configuration."""

    def test_default_configuration(self) -> None:
        config = ChunkingConfig()

        assert config.chunk_size == 1000
        assert config.chunk_overlap == 150
        assert config.min_chunk_size == 100
        assert config.strategy == ChunkingStrategy.FIXED_SIZE

    def test_custom_configuration(self) -> None:
        config = ChunkingConfig(
            chunk_size=500,
            chunk_overlap=50,
            min_chunk_size=40,
            strategy=ChunkingStrategy.SENTENCE,
        )

        assert config.chunk_size == 500
        assert config.chunk_overlap == 50
        assert config.min_chunk_size == 40
        assert config.strategy == ChunkingStrategy.SENTENCE

    @pytest.mark.parametrize(
        "strategy",
        list(ChunkingStrategy),
    )
    def test_accepts_all_supported_strategies(
        self,
        strategy: ChunkingStrategy,
    ) -> None:
        config = ChunkingConfig(strategy=strategy)

        assert config.strategy == strategy

    @pytest.mark.parametrize(
        ("strategy_value", "expected_strategy"),
        [
            ("fixed_size", ChunkingStrategy.FIXED_SIZE),
            ("sentence", ChunkingStrategy.SENTENCE),
            ("paragraph", ChunkingStrategy.PARAGRAPH),
        ],
    )
    def test_accepts_valid_strategy_strings(
        self,
        strategy_value: str,
        expected_strategy: ChunkingStrategy,
    ) -> None:
        config = ChunkingConfig(strategy=strategy_value)

        assert config.strategy is expected_strategy

    def test_rejects_unsupported_strategy(self) -> None:
        with pytest.raises(
            ValueError,
            match="Unsupported chunking strategy",
        ):
            ChunkingConfig(strategy="semantic")

    def test_rejects_invalid_strategy_type(self) -> None:
        with pytest.raises(TypeError, match="Strategy must be"):
            ChunkingConfig(strategy=123)  # type: ignore[arg-type]

    @pytest.mark.parametrize("chunk_size", [0, -1])
    def test_rejects_non_positive_chunk_size(
        self,
        chunk_size: int,
    ) -> None:
        with pytest.raises(
            ValueError,
            match="Chunk size must be greater than zero",
        ):
            ChunkingConfig(chunk_size=chunk_size)

    @pytest.mark.parametrize(
        "chunk_size",
        [1.5, True, "1000"],
    )
    def test_rejects_non_integer_chunk_size(
        self,
        chunk_size: int,
    ) -> None:
        with pytest.raises(TypeError, match="chunk_size"):
            ChunkingConfig(chunk_size=chunk_size)  # type: ignore[arg-type]

    def test_accepts_zero_overlap(self) -> None:
        config = ChunkingConfig(chunk_overlap=0)

        assert config.chunk_overlap == 0

    def test_rejects_negative_overlap(self) -> None:
        with pytest.raises(
            ValueError,
            match="Chunk overlap cannot be negative",
        ):
            ChunkingConfig(chunk_overlap=-1)

    @pytest.mark.parametrize("overlap", [1000, 1200])
    def test_rejects_overlap_equal_to_or_greater_than_chunk_size(
        self,
        overlap: int,
    ) -> None:
        with pytest.raises(
            ValueError,
            match="smaller than chunk size",
        ):
            ChunkingConfig(
                chunk_size=1000,
                chunk_overlap=overlap,
            )

    @pytest.mark.parametrize("overlap", [1.5, True, "100"])
    def test_rejects_non_integer_overlap(
        self,
        overlap: int,
    ) -> None:
        with pytest.raises(TypeError, match="chunk_overlap"):
            ChunkingConfig(
                chunk_overlap=overlap,  # type: ignore[arg-type]
            )

    @pytest.mark.parametrize("min_size", [0, -1])
    def test_rejects_non_positive_minimum_chunk_size(
        self,
        min_size: int,
    ) -> None:
        with pytest.raises(
            ValueError,
            match="Minimum chunk size must be greater than zero",
        ):
            ChunkingConfig(min_chunk_size=min_size)

    def test_rejects_minimum_size_greater_than_chunk_size(self) -> None:
        with pytest.raises(
            ValueError,
            match="cannot exceed chunk size",
        ):
            ChunkingConfig(
                chunk_size=500,
                min_chunk_size=600,
            )

    @pytest.mark.parametrize("min_size", [1.5, True, "100"])
    def test_rejects_non_integer_minimum_chunk_size(
        self,
        min_size: int,
    ) -> None:
        with pytest.raises(TypeError, match="min_chunk_size"):
            ChunkingConfig(
                min_chunk_size=min_size,  # type: ignore[arg-type]
            )

    def test_configuration_is_immutable(self) -> None:
        config = ChunkingConfig()

        with pytest.raises(FrozenInstanceError):
            config.chunk_size = 500  # type: ignore[misc]

    def test_accepts_minimum_size_equal_to_chunk_size(self) -> None:
        config = ChunkingConfig(
            chunk_size=500,
            chunk_overlap=0,
            min_chunk_size=500,
        )

        assert config.min_chunk_size == config.chunk_size
