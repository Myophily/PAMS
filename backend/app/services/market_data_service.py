"""
Market data service for fetching and caching stock prices and exchange rates.

PHASE 4: External API integration with Yahoo Finance (yfinance)
"""

from sqlalchemy.orm import Session
from app.models.market_data import MarketData
from app.utils.decimal_helpers import to_decimal
from app.utils.date_helpers import get_previous_business_day, is_weekend
from decimal import Decimal
from datetime import date, timedelta
from typing import Optional
import yfinance as yf
import pandas as pd


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
        Fetch stock price from Yahoo Finance.

        Handles both US tickers (AAPL) and Korean tickers (005930).
        Korean numeric tickers are automatically converted to .KS format.

        Args:
            ticker: Stock ticker
            target_date: Date

        Returns:
            Stock price or None

        Examples:
            >>> price = service._fetch_stock_price_from_api("AAPL", date(2024, 1, 15))
            >>> price
            Decimal('185.50')
        """
        try:
            # Normalize ticker format (Korean stocks need .KS suffix)
            normalized_ticker = self._normalize_ticker(ticker)

            # Fetch data from yfinance
            stock = yf.Ticker(normalized_ticker)

            # Get historical data (request 5 days window to handle weekends)
            end_date = target_date + timedelta(days=1)
            start_date = target_date - timedelta(days=5)

            hist = stock.history(start=start_date, end=end_date)

            if hist.empty:
                return None

            # Get closest date (handles weekends automatically)
            # Convert to timezone-naive for comparison
            target_timestamp = pd.Timestamp(target_date).tz_localize(None)
            hist_index_naive = hist.index.tz_localize(None)

            closest_dates = hist_index_naive[hist_index_naive <= target_timestamp]
            if len(closest_dates) == 0:
                return None

            # Use the index position to get the price from original hist
            closest_idx = len(closest_dates) - 1
            price = hist.iloc[closest_idx]['Close']

            return to_decimal(price, precision=4)

        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")
            return None

    def _fetch_exchange_rate_from_api(
        self,
        from_currency: str,
        to_currency: str,
        target_date: date
    ) -> Optional[Decimal]:
        """
        Fetch exchange rate from Yahoo Finance.

        Format: 1 from_currency = X to_currency
        Example: USD/KRW returns 1300 (1 USD = 1300 KRW)

        Tries direct pair first (USDKRW=X), then inverse if not available.

        Args:
            from_currency: Source currency
            to_currency: Target currency
            target_date: Date

        Returns:
            Exchange rate or None

        Examples:
            >>> rate = service._fetch_exchange_rate_from_api("USD", "KRW", date.today())
            >>> rate
            Decimal('1300.0000')
        """
        # Same currency pair always has rate of 1.0
        if from_currency == to_currency:
            return to_decimal(1.0, precision=6)

        try:
            # Construct forex pair symbol for yfinance
            pair_symbol = f"{from_currency}{to_currency}=X"

            # Fetch data
            pair = yf.Ticker(pair_symbol)

            end_date = target_date + timedelta(days=1)
            start_date = target_date - timedelta(days=5)

            hist = pair.history(start=start_date, end=end_date)

            if hist.empty:
                # Try inverse pair
                inverse_symbol = f"{to_currency}{from_currency}=X"
                pair = yf.Ticker(inverse_symbol)
                hist = pair.history(start=start_date, end=end_date)

                if hist.empty:
                    return None

                # Get closest date and invert the rate
                # Convert to timezone-naive for comparison
                target_timestamp = pd.Timestamp(target_date).tz_localize(None)
                hist_index_naive = hist.index.tz_localize(None)

                closest_dates = hist_index_naive[hist_index_naive <= target_timestamp]
                if len(closest_dates) == 0:
                    return None

                # Use the index position to get the rate from original hist
                closest_idx = len(closest_dates) - 1
                inverse_rate = hist.iloc[closest_idx]['Close']
                return to_decimal(1 / inverse_rate, precision=6)

            # Direct pair found
            # Convert to timezone-naive for comparison
            target_timestamp = pd.Timestamp(target_date).tz_localize(None)
            hist_index_naive = hist.index.tz_localize(None)

            closest_dates = hist_index_naive[hist_index_naive <= target_timestamp]
            if len(closest_dates) == 0:
                return None

            # Use the index position to get the rate from original hist
            closest_idx = len(closest_dates) - 1
            rate = hist.iloc[closest_idx]['Close']
            return to_decimal(rate, precision=6)

        except Exception as e:
            print(f"Error fetching rate for {from_currency}/{to_currency}: {e}")
            return None

    def get_latest_price(self, ticker: str, db: Session) -> Optional[Decimal]:
        """
        Get the most recent price for a ticker.

        NEW: If not found in cache, automatically fetches from API.

        Args:
            ticker: Stock ticker
            db: Database session

        Returns:
            Latest price or None
        """
        from datetime import date

        # Check cache first
        latest = db.query(MarketData).filter(
            MarketData.ticker == ticker,
            MarketData.closing_price.isnot(None)
        ).order_by(MarketData.date.desc()).first()

        if latest:
            return latest.closing_price

        # NEW: Auto-fetch if not in cache
        print(f"[AUTO-FETCH] Price for {ticker} not in cache, fetching from API...")
        price = self._fetch_stock_price_from_api(ticker, date.today())

        if price:
            # Cache it
            self._cache_stock_price(ticker, date.today(), price, "api", db)
            try:
                db.commit()
            except Exception as e:
                print(f"[WARN] Failed to cache price for {ticker}: {e}")
                db.rollback()
            return price

        return None

    def get_latest_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        db: Session
    ) -> Optional[Decimal]:
        """
        Get the most recent exchange rate.

        NEW: If not found in cache, automatically fetches from API.

        Args:
            from_currency: Source currency
            to_currency: Target currency
            db: Database session

        Returns:
            Latest exchange rate or None
        """
        from datetime import date

        ticker_symbol = f"{from_currency}_{to_currency}"

        # Check cache first
        latest = db.query(MarketData).filter(
            MarketData.ticker == ticker_symbol,
            MarketData.exchange_rate.isnot(None)
        ).order_by(MarketData.date.desc()).first()

        if latest:
            return latest.exchange_rate

        # NEW: Auto-fetch if not in cache
        print(f"[AUTO-FETCH] Exchange rate {from_currency}/{to_currency} not in cache, fetching from API...")
        rate = self._fetch_exchange_rate_from_api(from_currency, to_currency, date.today())

        if rate:
            # Cache it
            self._cache_exchange_rate(from_currency, to_currency, date.today(), rate, "api", db)
            try:
                db.commit()
            except Exception as e:
                print(f"[WARN] Failed to cache exchange rate for {from_currency}/{to_currency}: {e}")
                db.rollback()
            return rate

        return None

    def _normalize_ticker(self, ticker: str) -> str:
        """
        Normalize ticker format for yfinance.

        Korean stocks: numeric code → add .KS suffix (KOSPI)
        US stocks: use as-is

        Args:
            ticker: Stock ticker symbol

        Returns:
            Normalized ticker for yfinance

        Examples:
            >>> service._normalize_ticker("AAPL")
            'AAPL'
            >>> service._normalize_ticker("005930")
            '005930.KS'
        """
        if ticker.isdigit() and len(ticker) == 6:
            return f"{ticker}.KS"  # KOSPI stocks
        return ticker.upper()
