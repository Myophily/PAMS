"""
Pydantic schemas for market data API responses.

These schemas match the frontend TypeScript interfaces exactly.
"""

from pydantic import BaseModel


class StockPriceResponse(BaseModel):
    """
    Stock price response matching frontend StockPrice interface.

    Fields:
        price: Stock price as string (Decimal from backend converted to string)
        currency: Currency code (e.g., "USD", "KRW")
        source: Data source ("yahoo_finance", "cache", "manual")
        is_cached: True if returned from database cache
        date: Date in ISO format (YYYY-MM-DD)

    Examples:
        {
            "price": "185.50",
            "currency": "USD",
            "source": "yahoo_finance",
            "is_cached": false,
            "date": "2024-01-15"
        }
    """
    price: str  # Decimal as string (e.g., "185.50")
    currency: str  # "USD", "KRW", etc.
    source: str  # "yahoo_finance", "cache", "manual"
    is_cached: bool  # True if from database cache
    date: str  # "2024-01-15" (ISO format)

    class Config:
        from_attributes = True


class ExchangeRateResponse(BaseModel):
    """
    Exchange rate response matching frontend ExchangeRate interface.

    Format: 1 from_currency = X to_currency
    Example: USD/KRW returns "1300.0000" (1 USD = 1300 KRW)

    Fields:
        rate: Exchange rate as string (Decimal from backend converted to string)
        source: Data source ("yahoo_finance", "cache", "manual")
        date: Date in ISO format (YYYY-MM-DD)
        is_cached: True if returned from database cache

    Examples:
        {
            "rate": "1300.0000",
            "source": "yahoo_finance",
            "date": "2024-01-15",
            "is_cached": false
        }
    """
    rate: str  # Decimal as string (e.g., "1300.5000")
    source: str  # "yahoo_finance", "cache", "manual"
    date: str  # "2024-01-15" (ISO format)
    is_cached: bool  # True if from database cache

    class Config:
        from_attributes = True
