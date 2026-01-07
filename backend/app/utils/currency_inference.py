"""Currency inference utility for dynamically determining account currency from holdings."""

from typing import List
from app.models.holding import Holding


# Currency tickers that represent cash holdings in different currencies
CURRENCY_TICKERS = ["CASH", "KRW", "USD", "EUR", "JPY", "GBP", "CHF", "CNY", "HKD", "SGD"]


def infer_currency_from_holdings(holdings: List[Holding], account_type: str = None) -> str:
    """
    Infer account currency from holdings.

    Priority order:
    1. First CASH holding → returns "KRW" (CASH is treated as KRW)
    2. First currency ticker (KRW, USD, EUR, JPY, etc.)
    3. Fallback: "KRW"

    Args:
        holdings: List of Holding objects for an account
        account_type: Optional account type for better fallback inference

    Returns:
        str: Inferred currency code (e.g., "KRW", "USD", "EUR")
    """
    for holding in holdings:
        if holding.ticker in CURRENCY_TICKERS:
            # CASH is treated as KRW by default unless we know better?
            # Actually, if we have account_type, we might want to override CASH=KRW assumption
            # But for now, let's keep existing logic and only change fallback
            if holding.ticker == "CASH":
                # If it's a Securities/Foreign account with CASH, assume USD
                if account_type in ["Securities", "ForeignCurrency"]:
                    return "USD"
                return "KRW"
            # Other currency tickers return as-is
            return holding.ticker

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
