
"""Domain model for investment portfolios."""

from dataclasses import dataclass, field
from decimal import Decimal

from stockagent.models.position import Position


@dataclass
class Portfolio:
    """Represent and validate an investment portfolio."""

    portfolio_id: str
    name: str
    positions: list[Position] = field(default_factory=list)
    cash_balance: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        """Normalize fields and enforce portfolio business rules."""

        # Normalize identifiers and names.
        if not isinstance(self.portfolio_id, str):
            raise TypeError("Portfolio ID must be a string.")

        if not isinstance(self.name, str):
            raise TypeError("Portfolio name must be a string.")

        self.portfolio_id = self.portfolio_id.strip()
        self.name = self.name.strip()

        if not self.portfolio_id:
            raise ValueError("Portfolio ID cannot be empty.")

        if not self.name:
            raise ValueError("Portfolio name cannot be empty.")

        # Validate positions collection.
        if not isinstance(self.positions, list):
            raise TypeError("Positions must be a list.")

        if not all(isinstance(position, Position) for position in self.positions):
            raise TypeError("Every portfolio position must be a Position.")

        # A portfolio can have only one position per stock symbol.
        symbols = [position.symbol for position in self.positions]

        if len(symbols) != len(set(symbols)):
            raise ValueError(
                "A portfolio cannot contain duplicate stock symbols."
            )

        # Validate cash balance.
        if not isinstance(self.cash_balance, Decimal):
            raise TypeError("Cash balance must be a Decimal.")

        if (
            not self.cash_balance.is_finite()
            or self.cash_balance < Decimal("0")
        ):
            raise ValueError(
                "Cash balance must be finite and non-negative."
            )
