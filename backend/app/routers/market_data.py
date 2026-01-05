"""
Market data router for stock prices and exchange rates.

Endpoints:
- GET /api/market-data/price - Get stock price for ticker and date
- GET /api/market-data/exchange-rate - Get exchange rate for currency pair and date
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.market_data_service import MarketDataService
from app.schemas.market_data_schema import StockPriceResponse, ExchangeRateResponse
from app.models.market_data import MarketData
from app.utils.date_helpers import validate_transaction_date
from datetime import date, datetime
from typing import Optional

router = APIRouter(prefix="/api/market-data", tags=["market_data"])
market_data_service = MarketDataService()


@router.get("/price", response_model=StockPriceResponse)
def get_stock_price(
    ticker: str = Query(..., description="Stock ticker symbol (e.g., AAPL, 005930)"),
    date_param: Optional[str] = Query(None, alias="date", description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """
    Get stock price for a specific ticker and date.

    - **ticker**: Stock symbol (e.g., AAPL for Apple, 005930 for Samsung)
    - **date**: Optional date in YYYY-MM-DD format (defaults to today)

    Returns price with currency, source, and cache status.

    Examples:
        GET /api/market-data/price?ticker=AAPL&date=2024-01-15
        Response: {"price": "185.50", "currency": "USD", "source": "yahoo_finance", "is_cached": false, "date": "2024-01-15"}

        GET /api/market-data/price?ticker=005930&date=2024-01-15
        Response: {"price": "75000", "currency": "KRW", "source": "yahoo_finance", "is_cached": false, "date": "2024-01-15"}
    """
    try:
        # Parse date (default to today)
        target_date = date.fromisoformat(date_param) if date_param else date.today()

        # Validate date is not in future
        validate_transaction_date(target_date)

        # Fetch price from service (includes caching logic)
        price = market_data_service.get_stock_price(ticker, target_date, db)

        if price is None:
            raise LookupError(f"Price data not available for {ticker} on {target_date}")

        # Check if data came from cache
        cached_data = db.query(MarketData).filter(
            MarketData.ticker == ticker,
            MarketData.date == target_date
        ).first()

        # Data is considered cached if it existed before this request (>5 seconds old)
        is_cached = cached_data is not None and (
            datetime.now() - (cached_data.fetched_at or datetime.now())
        ).total_seconds() > 5

        # Determine currency from ticker format
        # Korean stocks are numeric (6 digits), US/international use letters
        currency = "KRW" if ticker.isdigit() else "USD"

        return StockPriceResponse(
            price=str(price),
            currency=currency,
            source=cached_data.source if cached_data else "yahoo_finance",
            is_cached=is_cached,
            date=str(target_date)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Market data service temporarily unavailable"
        )


@router.get("/exchange-rate", response_model=ExchangeRateResponse)
def get_exchange_rate(
    from_currency: str = Query(..., alias="from", min_length=3, max_length=3, description="Source currency code"),
    to_currency: str = Query(..., alias="to", min_length=3, max_length=3, description="Target currency code"),
    date_param: Optional[str] = Query(None, alias="date", description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """
    Get exchange rate for a currency pair and date.

    - **from**: Source currency code (e.g., USD, KRW, EUR)
    - **to**: Target currency code (e.g., KRW, USD, JPY)
    - **date**: Optional date in YYYY-MM-DD format (defaults to today)

    Returns exchange rate (1 from_currency = X to_currency).

    Examples:
        GET /api/market-data/exchange-rate?from=USD&to=KRW&date=2024-01-15
        Response: {"rate": "1300.0000", "source": "yahoo_finance", "date": "2024-01-15", "is_cached": false}

        GET /api/market-data/exchange-rate?from=EUR&to=USD
        Response: {"rate": "1.0850", "source": "yahoo_finance", "date": "2026-01-05", "is_cached": false}
    """
    try:
        # Parse date (default to today)
        target_date = date.fromisoformat(date_param) if date_param else date.today()

        # Validate date is not in future
        validate_transaction_date(target_date)

        # Normalize currency codes to uppercase
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        # Fetch rate from service (includes caching logic)
        rate = market_data_service.get_exchange_rate(
            from_currency, to_currency, target_date, db
        )

        if rate is None:
            raise LookupError(
                f"Exchange rate not available for {from_currency}/{to_currency} on {target_date}"
            )

        # Check cache status
        ticker_symbol = f"{from_currency}_{to_currency}"
        cached_data = db.query(MarketData).filter(
            MarketData.ticker == ticker_symbol,
            MarketData.date == target_date
        ).first()

        # Data is considered cached if it existed before this request (>5 seconds old)
        is_cached = cached_data is not None and (
            datetime.now() - (cached_data.fetched_at or datetime.now())
        ).total_seconds() > 5

        return ExchangeRateResponse(
            rate=str(rate),
            source=cached_data.source if cached_data else "yahoo_finance",
            date=str(target_date),
            is_cached=is_cached
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Market data service temporarily unavailable"
        )
