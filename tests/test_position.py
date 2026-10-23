
"""Tests for the Position domain model."""

from decimal import Decimal

import pytest

from stockagent.models.position import Position


def test_valid_position() -> None:
    position = Position("aapl", 10, Decimal("180.00"))

    assert position.symbol == "AAPL"
    assert position.quantity == 10
    assert position.average_cost == Decimal("180.00")


def test_position_normalizes_symbol_whitespace() -> None:
    position = Position("  msft  ", 5, Decimal("400.00"))

    assert position.symbol == "MSFT"


@pytest.mark.parametrize("symbol", ["", "   "])
def test_position_rejects_empty_symbol(symbol: str) -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        Position(symbol, 1, Decimal("10.00"))


@pytest.mark.parametrize("symbol", ["AAPL$", "AA PL", "AAPL/US"])
def test_position_rejects_invalid_symbol(symbol: str) -> None:
    with pytest.raises(ValueError, match="invalid characters"):
        Position(symbol, 1, Decimal("10.00"))


def test_position_rejects_non_string_symbol() -> None:
    with pytest.raises(TypeError, match="must be a string"):
        Position(123, 1, Decimal("10.00"))  # type: ignore[arg-type]


@pytest.mark.parametrize("quantity", [0, -1, -100])
def test_position_rejects_non_positive_quantity(quantity: int) -> None:
    with pytest.raises(ValueError, match="must be positive"):
        Position("AAPL", quantity, Decimal("10.00"))


@pytest.mark.parametrize("quantity", [1.5, "10", True, False])
def test_position_rejects_invalid_quantity_type(quantity: object) -> None:
    with pytest.raises(TypeError, match="must be an integer"):
        Position("AAPL", quantity, Decimal("10.00"))  # type: ignore[arg-type]


@pytest.mark.parametrize("cost", [10.0, 10, "10.00"])
def test_position_rejects_non_decimal_average_cost(cost: object) -> None:
    with pytest.raises(TypeError, match="must be a Decimal"):
        Position("AAPL", 1, cost)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "cost",
    [
        Decimal("0"),
        Decimal("-1"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_position_rejects_invalid_average_cost(cost: Decimal) -> None:
    with pytest.raises(ValueError, match="finite and positive"):
        Position("AAPL", 1, cost)
