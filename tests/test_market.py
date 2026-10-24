
"""Tests for the Market domain model."""

from decimal import Decimal

import pytest

from stockagent.models.market import Market
from stockagent.models.stock import Stock


def make_stock(
    symbol: str = "AAPL",
    name: str = "Apple Inc.",
    price: Decimal = Decimal("250.00"),
    currency: str = "USD",
) -> Stock:
    return Stock(
        symbol=symbol,
        name=name,
        price=price,
        currency=currency,
    )


def test_market_starts_empty() -> None:
    market = Market()

    assert market.stocks == {}


def test_markets_have_independent_stock_dictionaries() -> None:
    first = Market()
    second = Market()

    first.add_stock(make_stock())

    assert len(first.stocks) == 1
    assert second.stocks == {}


def test_market_accepts_initial_stocks() -> None:
    stock = make_stock()

    market = Market(stocks={"AAPL": stock})

    assert market.get_stock("AAPL") == stock


def test_market_normalizes_initial_dictionary_keys() -> None:
    stock = make_stock()

    market = Market(stocks={"aapl": stock})

    assert list(market.stocks) == ["AAPL"]


def test_market_rejects_non_dictionary_stocks() -> None:
    with pytest.raises(TypeError, match="must be a dictionary"):
        Market(stocks=[])  # type: ignore[arg-type]


def test_market_rejects_non_string_dictionary_key() -> None:
    with pytest.raises(TypeError, match="keys must be strings"):
        Market(stocks={123: make_stock()})  # type: ignore[dict-item]


def test_market_rejects_non_stock_entry() -> None:
    with pytest.raises(TypeError, match="must be a Stock"):
        Market(stocks={"AAPL": "not a stock"})  # type: ignore[dict-item]


def test_market_rejects_mismatched_dictionary_key() -> None:
    with pytest.raises(ValueError, match="key must match"):
        Market(stocks={"MSFT": make_stock("AAPL")})


def test_market_adds_stock() -> None:
    market = Market()
    stock = make_stock()

    market.add_stock(stock)

    assert market.stocks["AAPL"] == stock


def test_market_rejects_duplicate_stock() -> None:
    market = Market()
    market.add_stock(make_stock())

    with pytest.raises(ValueError, match="already exists"):
        market.add_stock(make_stock())


def test_market_rejects_non_stock_object() -> None:
    market = Market()

    with pytest.raises(TypeError, match="Only Stock objects"):
        market.add_stock("AAPL")  # type: ignore[arg-type]


def test_market_get_stock_is_case_insensitive() -> None:
    market = Market()
    stock = make_stock()
    market.add_stock(stock)

    assert market.get_stock(" aapl ") == stock


def test_market_rejects_empty_lookup_symbol() -> None:
    market = Market()

    with pytest.raises(ValueError, match="cannot be empty"):
        market.get_stock("   ")


def test_market_rejects_non_string_lookup_symbol() -> None:
    market = Market()

    with pytest.raises(TypeError, match="must be a string"):
        market.get_stock(123)  # type: ignore[arg-type]


def test_market_raises_key_error_for_unknown_stock() -> None:
    market = Market()

    with pytest.raises(KeyError, match="Stock not found"):
        market.get_stock("UNKNOWN")


def test_market_returns_current_price() -> None:
    market = Market()
    market.add_stock(make_stock(price=Decimal("250.00")))

    assert market.get_price("AAPL") == Decimal("250.00")


def test_market_updates_price() -> None:
    market = Market()
    market.add_stock(make_stock(price=Decimal("250.00")))

    market.update_price("AAPL", Decimal("275.50"))

    assert market.get_price("AAPL") == Decimal("275.50")


def test_market_price_update_preserves_stock_information() -> None:
    market = Market()
    original = make_stock()
    market.add_stock(original)

    market.update_price("AAPL", Decimal("275.50"))

    updated = market.get_stock("AAPL")

    assert updated.symbol == original.symbol
    assert updated.name == original.name
    assert updated.currency == original.currency
    assert updated.price == Decimal("275.50")


@pytest.mark.parametrize("price", [0, 10.0, "100.00"])
def test_market_rejects_non_decimal_price(price: object) -> None:
    market = Market()
    market.add_stock(make_stock())

    with pytest.raises(TypeError, match="must be a Decimal"):
        market.update_price("AAPL", price)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "price",
    [
        Decimal("0"),
        Decimal("-1"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_market_rejects_invalid_price(price: Decimal) -> None:
    market = Market()
    market.add_stock(make_stock())

    with pytest.raises(ValueError, match="finite and positive"):
        market.update_price("AAPL", price)


def test_failed_price_update_preserves_existing_price() -> None:
    market = Market()
    market.add_stock(make_stock(price=Decimal("250.00")))

    with pytest.raises(ValueError):
        market.update_price("AAPL", Decimal("-1"))

    assert market.get_price("AAPL") == Decimal("250.00")


def test_market_does_not_mutate_original_stock_on_price_update() -> None:
    market = Market()
    original = make_stock(price=Decimal("250.00"))
    market.add_stock(original)

    market.update_price("AAPL", Decimal("275.50"))

    assert original.price == Decimal("250.00")
    assert market.get_price("AAPL") == Decimal("275.50")
