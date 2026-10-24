
"""Domain model for the simulated stock market."""

from dataclasses import dataclass, field
from decimal import Decimal

from stockagent.models.stock import Stock


@dataclass
class Market:
    """Maintain available stocks and their current market prices."""

    stocks: dict[str, Stock] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and normalize the initial stock collection."""

        if not isinstance(self.stocks, dict):
            raise TypeError("Stocks must be a dictionary.")

        normalized_stocks: dict[str, Stock] = {}

        for symbol, stock in self.stocks.items():
            if not isinstance(symbol, str):
                raise TypeError("Stock dictionary keys must be strings.")

            if not isinstance(stock, Stock):
                raise TypeError("Every market entry must be a Stock.")

            normalized_symbol = symbol.strip().upper()

            if not normalized_symbol:
                raise ValueError("Stock symbol cannot be empty.")

            if normalized_symbol != stock.symbol:
                raise ValueError(
                    "Stock dictionary key must match the stock symbol."
                )

            if normalized_symbol in normalized_stocks:
                raise ValueError(
                    f"Duplicate stock symbol: {normalized_symbol}"
                )

            normalized_stocks[normalized_symbol] = stock

        self.stocks = normalized_stocks

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """Normalize and validate a stock symbol."""

        if not isinstance(symbol, str):
            raise TypeError("Stock symbol must be a string.")

        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError("Stock symbol cannot be empty.")

        return normalized_symbol

    def add_stock(self, stock: Stock) -> None:
        """Add a stock if its symbol is not already registered."""

        if not isinstance(stock, Stock):
            raise TypeError("Only Stock objects can be added to the market.")

        symbol = stock.symbol

        if symbol in self.stocks:
            raise ValueError(f"Stock already exists: {symbol}")

        self.stocks[symbol] = stock

    def get_stock(self, symbol: str) -> Stock:
        """Return a registered stock or raise KeyError."""

        normalized_symbol = self._normalize_symbol(symbol)

        try:
            return self.stocks[normalized_symbol]
        except KeyError:
            raise KeyError(
                f"Stock not found in market: {normalized_symbol}"
            ) from None

    def get_price(self, symbol: str) -> Decimal:
        """Return the current price of a registered stock."""

        return self.get_stock(symbol).price

    def update_price(self, symbol: str, price: Decimal) -> None:
        """Update a stock price after validating the new value."""

        stock = self.get_stock(symbol)

        if not isinstance(price, Decimal):
            raise TypeError("Market price must be a Decimal.")

        if not price.is_finite() or price <= Decimal("0"):
            raise ValueError("Market price must be finite and positive.")

        # Construct a validated replacement instead of directly mutating
        # the existing Stock object's price.
        updated_stock = Stock(
            symbol=stock.symbol,
            name=stock.name,
            price=price,
            currency=stock.currency,
        )

        self.stocks[stock.symbol] = updated_stock
