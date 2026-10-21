# StockAgent Domain Design

## 1. Domain Overview

StockAgent is a simulated trading system in which an agent analyzes market information and proposes trading decisions.

The core financial simulation must be deterministic and independent of the LLM and RAG components.

## 2. Core Entities

### Stock

Represents a tradable financial instrument.

Responsibilities:
- Store the stock symbol and identifying information.
- Represent the current market price.
- Validate stock properties.

### Market

Represents the trading environment.

Responsibilities:
- Maintain the available stocks.
- Provide current market prices.
- Supply market information required for order execution.
- Coordinate the processing of accepted orders.

### Order

Represents a request to buy or sell a stock.

Responsibilities:
- Store the stock symbol, trade side, and quantity.
- Record relevant order pricing information.
- Represent the order's lifecycle status.
- Provide the information required for validation and execution.

### Position

Represents ownership of a stock within a portfolio.

Responsibilities:
- Track the stock symbol.
- Track the quantity held.
- Track the average acquisition price.

### Portfolio

Represents an agent's financial state.

Responsibilities:
- Track available cash.
- Track stock positions.
- Calculate portfolio value.
- Apply successful trade results consistently.

### Agent

Represents an autonomous market participant.

Responsibilities:
- Observe market state.
- Observe portfolio state.
- Analyze available information.
- Propose trading decisions and corresponding orders.

## 3. Core Relationships

- An Agent owns a Portfolio.
- A Portfolio contains zero or more Positions.
- A Market maintains available Stocks.
- An Agent proposes Orders.
- The system validates proposed Orders before execution.
- The Market or execution component processes valid Orders.
- The Portfolio reflects successfully executed trades.

## 4. Initial Business Invariants

- A stock symbol cannot be empty.
- A stock price must be greater than zero.
- An order quantity must be greater than zero.
- An order must identify a valid trade side.
- An order must reference a stock known to the trading system.
- Portfolio cash cannot become negative.
- Position quantity cannot become negative.
- An agent cannot sell more shares than it owns.
- An agent cannot buy shares without sufficient cash.
- Cash and position changes from a successful trade must remain consistent.
- A failed trade must not leave the portfolio partially updated.

## 5. Illustrative Transaction Flow

1. The agent observes the market and its portfolio.
2. The agent proposes an order.
3. The system validates the order's structure and business constraints.
4. The execution component determines whether the order can be executed.
5. A successful execution produces an execution result, including the executed quantity and price.
6. The portfolio applies the execution result consistently to cash and positions.
7. The updated state becomes available for subsequent decisions.

Invalid or unexecutable orders must be rejected without changing the portfolio's financial state.

## 6. Portfolio Valuation

Portfolio value is calculated as:

Total Portfolio Value = Available Cash + Total Market Value of Positions

For each position:

Market Value = Quantity Held * Current Market Price

Unrealized profit or loss may be calculated by comparing a position's market value with its cost basis.

The initial implementation must define how current prices are obtained and handle missing prices explicitly.

## 7. Architectural Boundaries

- Financial business rules are enforced by deterministic application code.
- The LLM may support analysis and propose trading decisions.
- RAG retrieves relevant information from financial documents.
- Retrieved text and LLM output must not bypass order validation or execution rules.
- Retrieval and generation are separate concerns from financial state management.
- Portfolio updates must preserve financial consistency.

## 8. Open Design Decisions

The following decisions will be finalized during implementation:

- Whether the initial simulation supports market orders only or both market and limit orders.
- How historical and current market prices are represented.
- How order statuses, rejected orders, and execution failures are recorded.
- How transaction costs and price slippage are handled.
- How floating-point precision and monetary amounts are represented.
- How portfolio valuation and realized or unrealized profit/loss are calculated in edge cases.
