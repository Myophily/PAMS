"""Asset type inference utility for classifying holdings by asset type."""

from typing import List


# Known crypto ticker symbols (main cryptocurrencies)
CRYPTO_TICKERS = [
    "BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "DOT", "MATIC", "SHIB", "AVAX",
    "LINK", "UNI", "ATOM", "LTC", "BCH", "XLM", "ALGO", "VET", "FIL", "TRX",
    "ETC", "XMR", "BNB", "NEAR", "APT", "OP", "ARB", "INJ", "LDO", "GMX"
]


# Known bond ETF/symbol tickers
# Add Security Deposit as a bond ticker
BOND_TICKERS = [
    "TLT", "BND", "GOVT", "VCIT", "LQD", "HYG", "SHY", "IEF", "EDV", "TIP",
    "BSV", "VGIT", "MBB", "AGG", "SPSB", "SPTI", "SCHO", "SCHR", "SPLB", "S_D"
]


# Known gold/precious metal tickers (including gold ETFs)
GOLD_TICKERS = [
    "GLD", "IAU", "GOLD", "SGOL", "GLDM", "IAUM", "BAR", "OUNZ", "GLTR",
    "SLV", "IAU", "PPLT", "PALL", "SIVR"
]


def classify_asset_type(ticker: str) -> str:
    """
    Classify a ticker into one of 5 asset types:
    - Stock: Individual stocks (including ETFs)
    - Crypto: Cryptocurrencies/coins
    - Cash: Currency tickers (KRW, USD, EUR, etc.)
    - Bond: Bond holdings
    - Gold: Gold/precious metals

    Args:
        ticker: Ticker symbol to classify

    Returns:
        str: Asset type (Stock, Crypto, Cash, Bond, or Gold)

    Examples:
        >>> classify_asset_type("AAPL")
        "Stock"
        >>> classify_asset_type("BTC")
        "Crypto"
        >>> classify_asset_type("KRW")
        "Cash"
        >>> classify_asset_type("GLD")
        "Gold"
        >>> classify_asset_type("TLT")
        "Bond"
    """
    if not ticker:
        return "Stock"

    ticker_upper = ticker.upper()

    # Check if currency (cash)
    from app.utils.currency_inference import is_currency_ticker
    if is_currency_ticker(ticker):
        return "Cash"

    # Check if crypto
    if ticker_upper in CRYPTO_TICKERS:
        return "Crypto"

    # Check if gold
    if ticker_upper in GOLD_TICKERS:
        return "Gold"

    # Check if bond
    if ticker_upper in BOND_TICKERS:
        return "Bond"

    # Default: everything else is a stock (includes ETFs)
    return "Stock"
