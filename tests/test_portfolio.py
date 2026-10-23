
"""Tests for the Portfolio domain model."""

from decimal import Decimal

import pytest

from stockagent.models.portfolio import Portfolio
from stockagent.models.position import Position


def make_position(
    symbol: str = "AAPL",
    quantity: int = 10,
    average_cost: Decimal = Decimal("180.00"),
) -> Position:
    return Position(symbol, quantity, average_cost)


def test_valid_portfolio() -> None:
    position = make_position()
    portfolio = Portfolio(
        portfolio_id="P001",
        name="Long-Term Portfolio",
        positions=[position],
        cash_balance=Decimal("5000.00"),
    )

    assert portfolio.portfolio_id == "P001"
    assert portfolio.name == "Long-Term Portfolio"
    assert portfolio.positions == [position]
    assert portfolio.cash_balance == Decimal("5000.00")


def test_portfolio_normalizes_identifier_and_name() -> None:
    portfolio = Portfolio(" P001 ", " Growth Portfolio ")

    assert portfolio.portfolio_id == "P001"
    assert portfolio.name == "Growth Portfolio"


def test_portfolio_defaults_to_empty_positions_and_zero_cash() -> None:
    portfolio = Portfolio("P001", "Empty Portfolio")

    assert portfolio.positions == []
    assert portfolio.cash_balance == Decimal("0")


def test_portfolios_have_independent_position_lists() -> None:
    first = Portfolio("P001", "First")
    second = Portfolio("P002", "Second")

    first.positions.append(make_position())

    assert len(first.positions) == 1
    assert second.positions == []


@pytest.mark.parametrize("portfolio_id", ["", "   "])
def test_portfolio_rejects_empty_id(portfolio_id: str) -> None:
    with pytest.raises(ValueError, match="ID cannot be empty"):
        Portfolio(portfolio_id, "Portfolio")


@pytest.mark.parametrize("name", ["", "   "])
def test_portfolio_rejects_empty_name(name: str) -> None:
    with pytest.raises(ValueError, match="name cannot be empty"):
        Portfolio("P001", name)


@pytest.mark.parametrize(
    ("portfolio_id", "name"),
    [(123, "Portfolio"), ("P001", 123)],
)
def test_portfolio_rejects_non_string_id_or_name(
    portfolio_id: object,
    name: object,
) -> None:
    with pytest.raises(TypeError):
        Portfolio(portfolio_id, name)  # type: ignore[arg-type]


def test_portfolio_rejects_non_list_positions() -> None:
    with pytest.raises(TypeError, match="must be a list"):
        Portfolio("P001", "Portfolio", positions=())  # type: ignore[arg-type]


def test_portfolio_rejects_invalid_position_item() -> None:
    with pytest.raises(TypeError, match="must be a Position"):
        Portfolio(
            "P001",
            "Portfolio",
            positions=["AAPL"],  # type: ignore[list-item]
        )


def test_portfolio_rejects_duplicate_symbols() -> None:
    positions = [
        make_position("AAPL"),
        make_position("aapl", quantity=5),
    ]

    with pytest.raises(ValueError, match="duplicate stock symbols"):
        Portfolio("P001", "Portfolio", positions=positions)


def test_portfolio_accepts_different_symbols() -> None:
    portfolio = Portfolio(
        "P001",
        "Portfolio",
        positions=[
            make_position("AAPL"),
            make_position("MSFT"),
        ],
    )

    assert len(portfolio.positions) == 2


@pytest.mark.parametrize("cash", [10, 10.0, "100.00"])
def test_portfolio_rejects_non_decimal_cash(cash: object) -> None:
    with pytest.raises(TypeError, match="must be a Decimal"):
        Portfolio("P001", "Portfolio", cash_balance=cash)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "cash",
    [
        Decimal("-0.01"),
        Decimal("-100"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_portfolio_rejects_invalid_cash_balance(cash: Decimal) -> None:
    with pytest.raises(ValueError, match="finite and non-negative"):
        Portfolio("P001", "Portfolio", cash_balance=cash)


def test_portfolio_accepts_zero_cash() -> None:
    portfolio = Portfolio(
        "P001",
        "Portfolio",
        cash_balance=Decimal("0"),
    )

    assert portfolio.cash_balance == Decimal("0")
