"""
Pydantic schemas for dashboard API responses.
"""

from pydantic import BaseModel
from decimal import Decimal
from typing import List


class CandlestickData(BaseModel):
    """Single candlestick OHLC data point."""
    time: str  # ISO date format (e.g., "2024-01-15")
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal

    class Config:
        json_encoders = {
            Decimal: str  # Serialize Decimal as string to prevent float precision issues
        }


class CandlestickChartResponse(BaseModel):
    """Response schema for candlestick chart endpoint."""
    candles: List[CandlestickData]
    period: str  # "daily", "monthly", or "annual"
    currency: str  # "KRW" or "USD"
    data_points: int  # Number of candles

    class Config:
        json_encoders = {
            Decimal: str
        }
