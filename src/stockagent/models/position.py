
"""Domain model for stock positions."""

from dataclasses import dataclass
from decimal import Decimal
import re


@dataclass
class Position:
    """Represent and validate a stock holding."""

    symbol: str
    quantity: int
    average_cost: Decimal

    def __post_init__(self) -> None:
        """Normalize fields and enforce position business rules."""

        # Normalize the stock symbol.
        if not isinstance(self.symbol, str):
            raise TypeError("Stock symbol must be a string.")

        self.symbol = self.symbol.strip().upper()

        # Validate the stock symbol.
        if not self.symbol:
            raise ValueError("Stock symbol cannot be empty.")

        if not re.fullmatch(r"[A-Z0-9.-]+", self.symbol):
            raise ValueError("Stock symbol contains invalid characters.")

        # Validate quantity type.
        # bool is a subclass of int, so reject it explicitly.
        if isinstance(self.quantity, bool) or not isinstance(
            self.quantity, int
        ):
            raise TypeError("Quantity must be an integer.")

        # Validate quantity value.
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive.")

        # Validate average cost type.
        if not isinstance(self.average_cost, Decimal):
            raise TypeError("Average cost must be a Decimal.")

        # Validate average cost value.
        if (
            not self.average_cost.is_finite()
            or self.average_cost <= Decimal("0")
        ):
            raise ValueError("Average cost must be finite and positive.")
