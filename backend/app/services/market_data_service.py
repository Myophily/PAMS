"""
Market data service for fetching and caching stock prices and exchange rates.

PHASE 2: Manual entry only (MVP)
PHASE 8: External API integration (Yahoo Finance / Alpha Vantage)
"""

from sqlalchemy.orm import Session
from app.models.market_data import MarketData
from app.utils.decimal_helpers import to_decimal
from app.utils.date_helpers import get_previous_business_day, is_weekend
from decimal import Decimal
from datetime import date
from typing import Optional


class MarketDataService:
    """
    Service for fetching and caching market data (stock prices and exchange rates).

    Caching Strategy:
    1. Check MarketData table first
    2. If not cached, fetch from external API (Phase 8)
    3. Store in MarketData table
    4. Return cached data
    """

    def get_stock_price(
        self,
        ticker: str,
        target_date: date,
        db: Session
    ) -> Optional[Decimal]:
        """
        Get stock price for a specific date.

        First checks cache, then fetches from external API if needed.
        For weekends, automatically falls back to previous business day.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL", "005930.KS")
            target_date: Date to get price for
            db: Database session

        Returns:
            Stock price or None if not available

        Examples:
            >>> price = service.get_stock_price("AAPL", date(2024, 1, 15), db)
            >>> price
            Decimal('185.50')

            >>> # Weekend date automatically falls back to Friday
            >>> price = service.get_stock_price("AAPL", date(2024, 1, 14), db)  # Sunday
            # Returns Friday's price
        """
        # Check cache first
        cached = db.query(MarketData).filter(
            MarketData.ticker == ticker,
            MarketData.date == target_date
        ).first()

        if cached and cached.closing_price:
            return cached.closing_price

        # If weekend, try previous business day
        if is_weekend(target_date):
            prev_day = get_previous_business_day(target_date)
            if prev_day:
                return self.get_stock_price(ticker, prev_day, db)

        # Fetch from external API
        price = self._fetch_stock_price_from_api(ticker, target_date)

        if price:
            # Cache it
            self._cache_stock_price(ticker, target_date, price, "api", db)
            return price

        return None

    def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        target_date: date,
        db: Session
    ) -> Optional[Decimal]:
        """
        Get exchange rate for a specific date.

        Format: 1 from_currency = X to_currency
        Example: from=USD, to=KRW returns 1300 (1 USD = 1300 KRW)

        Args:
            from_currency: Source currency (e.g., "USD")
            to_currency: Target currency (e.g., "KRW")
            target_date: Date to get rate for
            db: Database session

        Returns:
            Exchange rate or None

        Examples:
            >>> rate = service.get_exchange_rate("USD", "KRW", date.today(), db)
            >>> rate
            Decimal('1300.0000')
        """
        # Check cache
        ticker_symbol = f"{from_currency}_{to_currency}"

        cached = db.query(MarketData).filter(
            MarketData.ticker == ticker_symbol,
            MarketData.date == target_date
        ).first()

        if cached and cached.exchange_rate:
            return cached.exchange_rate

        # Fetch from external API
        rate = self._fetch_exchange_rate_from_api(from_currency, to_currency, target_date)

        if rate:
            # Cache it
            self._cache_exchange_rate(from_currency, to_currency, target_date, rate, "api", db)
            return rate

        return None

    def manually_enter_price(
        self,
        ticker: str,
        price: Decimal,
        target_date: date,
        db: Session
    ) -> MarketData:
        """
        Manually enter a stock price (fallback when API unavailable).

        Args:
            ticker: Stock ticker symbol
            price: Stock price
            target_date: Date for this price
            db: Database session

        Returns:
            MarketData record

        Examples:
            >>> data = service.manually_enter_price(
            ...     "AAPL",
            ...     Decimal("185.50"),
            ...     date.today(),
            ...     db
            ... )
            >>> data.source
            'manual'
        """
        return self._cache_stock_price(ticker, target_date, price, "manual", db)

    def manually_enter_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate: Decimal,
        target_date: date,
        db: Session
    ) -> MarketData:
        """
        Manually enter an exchange rate (fallback when API unavailable).

        Args:
            from_currency: Source currency
            to_currency: Target currency
            rate: Exchange rate
            target_date: Date for this rate
            db: Database session

        Returns:
            MarketData record
        """
        return self._cache_exchange_rate(from_currency, to_currency, target_date, rate, "manual", db)

    def _cache_stock_price(
        self,
        ticker: str,
        target_date: date,
        price: Decimal,
        source: str,
        db: Session
    ) -> MarketData:
        """
        Cache a stock price in the database.

        Args:
            ticker: Stock ticker
            target_date: Date
            price: Price to cache
            source: Source of data ("api", "manual", etc.)
            db: Database session

        Returns:
            MarketData record
        """
        # Check if already exists
        market_data = db.query(MarketData).filter(
            MarketData.ticker == ticker,
            MarketData.date == target_date
        ).first()

        if market_data:
            # Update existing
            market_data.closing_price = to_decimal(price, precision=4)
            market_data.source = source
        else:
            # Create new
            market_data = MarketData(
                ticker=ticker,
                date=target_date,
                closing_price=to_decimal(price, precision=4),
                exchange_rate=None,
                source=source
            )
            db.add(market_data)

        db.flush()
        return market_data

    def _cache_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        target_date: date,
        rate: Decimal,
        source: str,
        db: Session
    ) -> MarketData:
        """
        Cache an exchange rate in the database.

        Args:
            from_currency: Source currency
            to_currency: Target currency
            target_date: Date
            rate: Exchange rate to cache
            source: Source of data
            db: Database session

        Returns:
            MarketData record
        """
        ticker_symbol = f"{from_currency}_{to_currency}"

        # Check if already exists
        market_data = db.query(MarketData).filter(
            MarketData.ticker == ticker_symbol,
            MarketData.date == target_date
        ).first()

        if market_data:
            # Update existing
            market_data.exchange_rate = to_decimal(rate, precision=4)
            market_data.source = source
        else:
            # Create new
            market_data = MarketData(
                ticker=ticker_symbol,
                date=target_date,
                closing_price=None,
                exchange_rate=to_decimal(rate, precision=4),
                source=source
            )
            db.add(market_data)

        db.flush()
        return market_data

    def _fetch_stock_price_from_api(
        self,
        ticker: str,
        target_date: date
    ) -> Optional[Decimal]:
        """
        Fetch stock price from external API (Yahoo Finance or Alpha Vantage).

        PHASE 2: Returns None (manual entry required)
        PHASE 8: Full external API integration

        Args:
            ticker: Stock ticker
            target_date: Date

        Returns:
            Stock price or None
        """
        # TODO: Implement external API integration in Phase 8
        return None

    def _fetch_exchange_rate_from_api(
        self,
        from_currency: str,
        to_currency: str,
        target_date: date
    ) -> Optional[Decimal]:
        """
        Fetch exchange rate from external API.

        PHASE 2: Returns None (manual entry required)
        PHASE 8: Full external API integration

        Args:
            from_currency: Source currency
            to_currency: Target currency
            target_date: Date

        Returns:
            Exchange rate or None
        """
        # TODO: Implement external API integration in Phase 8
        return None

    def get_latest_price(self, ticker: str, db: Session) -> Optional[Decimal]:
        """
        Get the most recent price for a ticker.

        Args:
            ticker: Stock ticker
            db: Database session

        Returns:
            Latest price or None
        """
        latest = db.query(MarketData).filter(
            MarketData.ticker == ticker,
            MarketData.closing_price.isnot(None)
        ).order_by(MarketData.date.desc()).first()

        return latest.closing_price if latest else None

    def get_latest_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        db: Session
    ) -> Optional[Decimal]:
        """
        Get the most recent exchange rate.

        Args:
            from_currency: Source currency
            to_currency: Target currency
            db: Database session

        Returns:
            Latest exchange rate or None
        """
        ticker_symbol = f"{from_currency}_{to_currency}"

        latest = db.query(MarketData).filter(
            MarketData.ticker == ticker_symbol,
            MarketData.exchange_rate.isnot(None)
        ).order_by(MarketData.date.desc()).first()

        return latest.exchange_rate if latest else None
