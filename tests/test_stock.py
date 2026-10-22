
from decimal import Decimal

import pytest

from stockagent.models.stock import Stock


def test_stock_normalizes_fields_and_uses_default_currency():
    stock = Stock(
        symbol=" aapl ",
        name=" Apple Inc. ",
        price=Decimal("250.00"),
    )

    assert stock.symbol == "AAPL"
    assert stock.name == "Apple Inc."
    assert stock.price == Decimal("250.00")
    assert stock.currency == "USD"


def test_stock_accepts_custom_currency():
    stock = Stock(
        symbol="infy",
        name="Infosys",
        price=Decimal("1500.00"),
        currency="inr",
    )

    assert stock.currency == "INR"


@pytest.mark.parametrize("symbol", ["", "   "])
def test_stock_rejects_empty_symbol(symbol):
    with pytest.raises(ValueError, match="symbol cannot be empty"):
        Stock(
            symbol=symbol,
            name="Apple Inc.",
            price=Decimal("250.00"),
        )


@pytest.mark.parametrize("name", ["", "   "])
def test_stock_rejects_empty_name(name):
    with pytest.raises(ValueError, match="name cannot be empty"):
        Stock(
            symbol="AAPL",
            name=name,
            price=Decimal("250.00"),
        )


def test_stock_rejects_float_price():
    with pytest.raises(TypeError, match="must be a Decimal"):
        Stock(
            symbol="AAPL",
            name="Apple Inc.",
            price=250.00,
        )


@pytest.mark.parametrize(
    "price",
    [
        Decimal("0"),
        Decimal("-10.00"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_stock_rejects_invalid_price(price):
    with pytest.raises(ValueError, match="finite positive"):
        Stock(
            symbol="AAPL",
            name="Apple Inc.",
            price=price,
        )


@pytest.mark.parametrize("currency", ["US", "US1", "US-D"])
def test_stock_rejects_invalid_currency_format(currency):
    with pytest.raises(ValueError, match="three-letter code"):
        Stock(
            symbol="AAPL",
            name="Apple Inc.",
            price=Decimal("250.00"),
            currency=currency,
        )
