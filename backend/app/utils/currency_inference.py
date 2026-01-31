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
    # Collect all currency holdings
    currency_holdings = []
    for holding in holdings:
        # Normalize ticker (handles legacy CASH)
        ticker_normalized = normalize_ticker(holding.ticker, account_type)

        if ticker_normalized in CURRENCY_TICKERS:
            currency_holdings.append(ticker_normalized)

    # If single currency found, use it
    if len(currency_holdings) == 1:
        return currency_holdings[0]

    # If multiple currencies, prefer KRW if present, else first one
    if len(currency_holdings) > 1:
        if "KRW" in currency_holdings:
            return "KRW"
        return currency_holdings[0]

    # Handle empty accounts - use account type to determine default
    if len(holdings) == 0:
        if account_type == "Securities":
            # Securities accounts can hold multiple currencies, default to KRW for Korean users
            return "KRW"
        elif account_type == "ForeignCurrency":
            # ForeignCurrency accounts default to USD
            return "USD"
        else:
            # Deposit/Savings/MoneyMarket default to KRW
            return "KRW"

    # Fallback: Check price_currency of stock holdings
    for holding in holdings:
        if not is_currency_ticker(holding.ticker) and hasattr(holding, 'price_currency'):
            if holding.price_currency:
                return holding.price_currency

    # Last resort fallback for non-empty accounts without currency holdings
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


def infer_price_currency_from_ticker(ticker: str) -> str:
    """
    Infer price currency from ticker symbol.

    Korean stocks (numeric or .KS suffix) → KRW
    Korean bonds (S_D, etc.) → KRW
    Japanese stocks (.T suffix) → JPY
    Hong Kong stocks (.HK suffix) → HKD
    US stocks and others → USD

    Args:
        ticker: Stock ticker symbol

    Returns:
        Inferred currency code (USD, KRW, JPY, etc.)

    Examples:
        >>> infer_price_currency_from_ticker("AAPL")
        "USD"
        >>> infer_price_currency_from_ticker("005930")
        "KRW"
        >>> infer_price_currency_from_ticker("005930.KS")
        "KRW"
        >>> infer_price_currency_from_ticker("7203.T")
        "JPY"
        >>> infer_price_currency_from_ticker("S_D")
        "KRW"
    """
    if not ticker:
        return "USD"

    ticker_upper = ticker.upper()

    # Korean stocks: 6-digit numeric or .KS/.KQ suffix
    if ticker_upper.isdigit() and len(ticker_upper) == 6:
        return "KRW"
    if ticker_upper.endswith('.KS') or ticker_upper.endswith('.KQ'):
        return "KRW"

    # Korean bonds (S_D, etc.)
    from app.utils.asset_type_inference import KOREAN_BOND_TICKERS
    if ticker_upper in KOREAN_BOND_TICKERS:
        return "KRW"

    # Japanese stocks: .T suffix
    if ticker_upper.endswith('.T'):
        return "JPY"

    # Hong Kong stocks: .HK suffix
    if ticker_upper.endswith('.HK'):
        return "HKD"

    # Default to USD for US and international stocks
    return "USD"
