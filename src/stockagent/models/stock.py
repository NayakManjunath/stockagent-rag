
from dataclasses import dataclass
from decimal import Decimal
import re


@dataclass
class Stock:
    """Represent a stock and its current market price."""

    symbol: str
    name: str
    price: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        # Normalize text fields to avoid inconsistent representations.
        self.symbol = self.symbol.strip().upper()
        self.name = self.name.strip()
        self.currency = self.currency.strip().upper()

        # Validate required text fields.
        if not self.symbol:
            raise ValueError("Stock symbol cannot be empty.")

        if not self.name:
            raise ValueError("Stock name cannot be empty.")

        # Require Decimal to avoid silently accepting float prices.
        if not isinstance(self.price, Decimal):
            raise TypeError("Stock price must be a Decimal.")

        if not self.price.is_finite() or self.price <= Decimal("0"):
            raise ValueError("Stock price must be a finite positive value.")

        # Validate the three-letter currency-code format.
        if not re.fullmatch(r"[A-Z]{3}", self.currency):
            raise ValueError("Currency must be a three-letter code.")
