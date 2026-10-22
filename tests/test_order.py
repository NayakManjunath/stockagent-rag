
from decimal import Decimal

import pytest

from stockagent.models.order import (
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
)


def test_limit_order_is_created_successfully():
    order = Order(
        order_id="ORD-001",
        symbol=" aapl ",
        side=OrderSide.BUY,
        quantity=10,
        order_type=OrderType.LIMIT,
        limit_price=Decimal("250.00"),
    )

    assert order.order_id == "ORD-001"
    assert order.symbol == "AAPL"
    assert order.side is OrderSide.BUY
    assert order.quantity == 10
    assert order.order_type is OrderType.LIMIT
    assert order.limit_price == Decimal("250.00")
    assert order.status is OrderStatus.NEW


def test_market_order_has_no_limit_price():
    order = Order(
        order_id="ORD-002",
        symbol="msft",
        side=OrderSide.SELL,
        quantity=5,
        order_type=OrderType.MARKET,
    )

    assert order.symbol == "MSFT"
    assert order.limit_price is None
    assert order.status is OrderStatus.NEW


@pytest.mark.parametrize("order_id", ["", "   "])
def test_order_rejects_empty_order_id(order_id):
    with pytest.raises(ValueError, match="Order ID cannot be empty"):
        Order(
            order_id=order_id,
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=1,
            order_type=OrderType.MARKET,
        )


@pytest.mark.parametrize("symbol", ["", "   "])
def test_order_rejects_empty_symbol(symbol):
    with pytest.raises(ValueError, match="Stock symbol cannot be empty"):
        Order(
            order_id="ORD-001",
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=1,
            order_type=OrderType.MARKET,
        )


@pytest.mark.parametrize("symbol", ["AAPL!", "AA PL", "AAPL/US"])
def test_order_rejects_invalid_symbol_characters(symbol):
    with pytest.raises(ValueError, match="invalid characters"):
        Order(
            order_id="ORD-001",
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=1,
            order_type=OrderType.MARKET,
        )


@pytest.mark.parametrize("quantity", [0, -1])
def test_order_rejects_nonpositive_quantity(quantity):
    with pytest.raises(ValueError, match="Quantity must be positive"):
        Order(
            order_id="ORD-001",
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=quantity,
            order_type=OrderType.MARKET,
        )


@pytest.mark.parametrize("quantity", [True, False, 1.5, "10"])
def test_order_rejects_noninteger_quantity(quantity):
    with pytest.raises(TypeError, match="Quantity must be an integer"):
        Order(
            order_id="ORD-001",
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=quantity,
            order_type=OrderType.MARKET,
        )


def test_order_rejects_invalid_side():
    with pytest.raises(TypeError, match="Side must be an OrderSide"):
        Order(
            order_id="ORD-001",
            symbol="AAPL",
            side="BUY",
            quantity=1,
            order_type=OrderType.MARKET,
        )


def test_order_rejects_invalid_order_type():
    with pytest.raises(TypeError, match="Order type must be an OrderType"):
        Order(
            order_id="ORD-001",
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=1,
            order_type="MARKET",
        )


def test_order_rejects_invalid_status():
    with pytest.raises(TypeError, match="Status must be an OrderStatus"):
        Order(
            order_id="ORD-001",
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=1,
            order_type=OrderType.MARKET,
            status="NEW",
        )


def test_market_order_rejects_limit_price():
    with pytest.raises(ValueError, match="must not specify a limit price"):
        Order(
            order_id="ORD-001",
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=1,
            order_type=OrderType.MARKET,
            limit_price=Decimal("250.00"),
        )


def test_limit_order_requires_decimal_price():
    with pytest.raises(TypeError, match="require a Decimal limit price"):
        Order(
            order_id="ORD-001",
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=1,
            order_type=OrderType.LIMIT,
        )


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
def test_limit_order_rejects_invalid_price(price):
    with pytest.raises(ValueError, match="finite and positive"):
        Order(
            order_id="ORD-001",
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=1,
            order_type=OrderType.LIMIT,
            limit_price=price,
        )
