"""Currency inference utility for dynamically determining account currency from holdings."""

from typing import List
from app.models.holding import Holding


# Currency tickers that represent cash holdings in different currencies
# Note: "CASH" is deprecated in favor of explicit currency codes (KRW, USD, etc.)
CURRENCY_TICKERS = ["KRW", "USD", "EUR", "JPY", "GBP", "CHF", "CNY", "HKD", "SGD"]


def is_currency_ticker(ticker: str) -> bool:
    """
    Check if ticker is a currency code.

    Args:
        ticker: Ticker symbol to check

    Returns:
        bool: True if ticker is a recognized currency

    Examples:
        >>> is_currency_ticker("KRW")
        True
        >>> is_currency_ticker("AAPL")
        False
        >>> is_currency_ticker("CASH")  # Legacy
        True  # For backward compatibility only
    """
    if not ticker:
        return False

    ticker_upper = ticker.upper()

    # Accept legacy CASH during transition
    if ticker_upper == "CASH":
        return True

    return ticker_upper in CURRENCY_TICKERS


def normalize_ticker(ticker: str, account_type: str = None) -> str:
    """
    Normalize legacy CASH ticker to explicit currency.

    Args:
        ticker: Original ticker
        account_type: Account type for context

    Returns:
        str: Normalized ticker (CASH → KRW/USD based on account type)

    Examples:
        >>> normalize_ticker("CASH", "Deposit")
        "KRW"
        >>> normalize_ticker("CASH", "Securities")
        "USD"
        >>> normalize_ticker("USD", "Securities")
        "USD"
    """
    if not ticker:
        return ticker

    ticker_upper = ticker.upper()

    if ticker_upper != "CASH":
        return ticker_upper

    # Auto-convert CASH based on account type
    if account_type in ["Deposit", "Savings", "MoneyMarket"]:
        return "KRW"
    elif account_type in ["Securities", "ForeignCurrency"]:
        return "USD"
    else:
        # Fallback to KRW
        return "KRW"


def infer_currency_from_holdings(holdings: List[Holding], account_type: str = None) -> str:
    """
    Infer account currency from holdings.

    Priority order:
    1. First currency ticker (KRW, USD, EUR, etc.) - explicit currencies preferred
    2. Legacy CASH → normalized to KRW/USD based on account_type
    3. Fallback: "KRW" for Deposit/Savings/MoneyMarket, "USD" for others

    Args:
        holdings: List of Holding objects for an account
        account_type: Account type for better inference

    Returns:
        str: Inferred currency code (e.g., "KRW", "USD")
    """
    for holding in holdings:
        # Normalize ticker (handles legacy CASH)
        ticker_normalized = normalize_ticker(holding.ticker, account_type)

        if ticker_normalized in CURRENCY_TICKERS:
            return ticker_normalized

    # Fallback if no currency holdings found
    if account_type in ["Securities", "ForeignCurrency"]:
        return "USD"

    return "KRW"


def get_decimal_places(currency: str) -> str:
    """
    Get decimal quantization string for a currency.

    Args:
        currency: Currency code (e.g., "KRW", "USD")

    Returns:
        str: Decimal quantization string for use with Decimal.quantize()

    Examples:
        >>> get_decimal_places("KRW")
        '1'

        >>> get_decimal_places("USD")
        '0.01'
    """
    # KRW uses 0 decimal places (integers)
    if currency == "KRW":
        return "1"
    # All other currencies use 2 decimal places
    return "0.01"
