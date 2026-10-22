
"""Domain model for stock orders."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import re


class OrderSide(Enum):
    """Direction of a stock order."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Execution instruction for a stock order."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(Enum):
    """Lifecycle status of a stock order."""

    NEW = "NEW"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"


@dataclass
class Order:
    """Represent and validate a stock order."""

    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    limit_price: Decimal | None = None
    status: OrderStatus = OrderStatus.NEW

    def __post_init__(self) -> None:
        """Normalize fields and enforce order business rules."""

        # Normalize text identifiers.
        self.order_id = self.order_id.strip()
        self.symbol = self.symbol.strip().upper()

        # Validate required identifiers.
        if not self.order_id:
            raise ValueError("Order ID cannot be empty.")

        if not self.symbol:
            raise ValueError("Stock symbol cannot be empty.")

        if not re.fullmatch(r"[A-Z0-9.-]+", self.symbol):
            raise ValueError("Stock symbol contains invalid characters.")

        # Validate enum fields.
        if not isinstance(self.side, OrderSide):
            raise TypeError("Side must be an OrderSide value.")

        if not isinstance(self.order_type, OrderType):
            raise TypeError("Order type must be an OrderType value.")

        if not isinstance(self.status, OrderStatus):
            raise TypeError("Status must be an OrderStatus value.")

        # Require a positive whole-share quantity.
        # bool is a subclass of int in Python, so reject it explicitly.
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int):
            raise TypeError("Quantity must be an integer.")

        if self.quantity <= 0:
            raise ValueError("Quantity must be positive.")

        # Enforce the price rules for each order type.
        if self.order_type is OrderType.MARKET:
            if self.limit_price is not None:
                raise ValueError(
                    "Market orders must not specify a limit price."
                )

        elif self.order_type is OrderType.LIMIT:
            if not isinstance(self.limit_price, Decimal):
                raise TypeError(
                    "Limit orders require a Decimal limit price."
                )

            if (
                not self.limit_price.is_finite()
                or self.limit_price <= Decimal("0")
            ):
                raise ValueError(
                    "Limit price must be finite and positive."
                )
