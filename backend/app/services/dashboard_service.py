"""
Dashboard service for providing summary statistics and chart data.
"""

from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.asset_snapshot import AssetSnapshot
from app.services.holding_service import HoldingService
from app.services.market_data_service import MarketDataService
from app.services.snapshot_service import SnapshotService
from app.utils.decimal_helpers import to_decimal
from app.utils.currency_inference import infer_currency_from_holdings
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Dict, List
from app.utils.timezone import now_kst, now_kst_truncated


class DashboardService:
    """
    Service for dashboard data (summary, charts, statistics).
    """

    def __init__(self):
        self.holding_service = HoldingService()
        self.market_data_service = MarketDataService()
        self.snapshot_service = SnapshotService()

    def get_summary(self, db: Session) -> Dict:
        """
        Get dashboard summary with total assets, changes, and allocation.

        Returns:
            Dict with summary statistics

        Example response:
        {
            "total_assets": {"krw": 10000000, "usd": 7692.31},
            "current_exchange_rate": {"usd_to_krw": 1300, "updated_at": "2024-01-15"},
            "changes": {
                "day": {"amount_krw": 50000, "amount_usd": 38.46, "percent": 0.5},
                "month": {"amount_krw": 200000, "amount_usd": 153.85, "percent": 2.0},
                "year": {"amount_krw": 1000000, "amount_usd": 769.23, "percent": 10.0}
            },
            "allocation": {
                "by_type": [
                    {"type": "Cash", "value_krw": 3000000, "percent": 30.0},
                    {"type": "Stocks", "value_krw": 6000000, "percent": 60.0}
                ]
            }
        }
        """
        # Get current datetime snapshot (or regenerate if stale)
        now = now_kst().replace(minute=0, second=0, microsecond=0)
        current_snapshot = self.snapshot_service.get_snapshot(now, db)

        # CRITICAL FIX: Always regenerate today's snapshot to use latest market data
        # This ensures dashboard always shows current market prices
        if current_snapshot:
            # Delete existing snapshot and regenerate it with fresh data
            db.delete(current_snapshot)
            db.flush()

        # Generate fresh snapshot for today
        current_snapshot = self.snapshot_service.generate_snapshot(now, db)
        db.commit()

        # Get exchange rate (exchange rates are daily, not hourly)
        usd_krw_rate = self.market_data_service.get_exchange_rate("USD", "KRW", now.date(), db)
        if not usd_krw_rate:
            usd_krw_rate = to_decimal(1300, precision=4)  # Fallback

        # Calculate changes (using hours: 1 day=24h, 30 days=720h, 365 days=8760h)
        day_amount, day_percent = self.snapshot_service.calculate_period_change(now, 24, db)
        month_amount, month_percent = self.snapshot_service.calculate_period_change(now, 720, db)
        year_amount, year_percent = self.snapshot_service.calculate_period_change(now, 8760, db)

        # Get allocation by type
        allocation_result = self._calculate_allocation_by_type(db, current_snapshot.total_assets_krw)

        # Calculate top assets
        top_assets = self._calculate_top_assets(db, current_snapshot.total_assets_krw)

        return {
            "total_assets": {
                "krw": current_snapshot.total_assets_krw,
                "usd": current_snapshot.total_assets_usd
            },
            "current_exchange_rate": {
                "usd_to_krw": usd_krw_rate,
                "updated_at": now.date().isoformat()
            },
            "changes": {
                "day": {
                    "amount_krw": day_amount,
                    "amount_usd": (day_amount / usd_krw_rate).quantize(Decimal("0.01")),
                    "percent": day_percent
                },
                "month": {
                    "amount_krw": month_amount,
                    "amount_usd": (month_amount / usd_krw_rate).quantize(Decimal("0.01")),
                    "percent": month_percent
                },
                "year": {
                    "amount_krw": year_amount,
                    "amount_usd": (year_amount / usd_krw_rate).quantize(Decimal("0.01")),
                    "percent": year_percent
                }
            },
            "allocation": allocation_result["allocation"],
            "risk_summary": allocation_result["risk_summary"],
            "top_assets": top_assets
        }

    def get_chart_data(
        self,
        period: str,
        currency: str,
        db: Session
    ) -> Dict:
        """
        Get asset volatility time series data for charts.

        Args:
            period: Time period ("1W", "1M", "3M", "6M", "1Y", "ALL")
            currency: Currency for values ("KRW" or "USD")
            db: Database session

        Returns:
            Dict with chart data

        Example response:
        {
            "chart_data": [
                {
                    "date": "2024-01-01",
                    "total_assets": 9500000,
                    "principal": 9000000,
                    "gain_loss": 500000
                },
                ...
            ],
            "period": "1M",
            "currency": "KRW"
        }
        """
        # Calculate date range based on period
        end_date = date.today()

        if period == "1W":
            start_date = end_date - timedelta(days=7)
        elif period == "1M":
            start_date = end_date - timedelta(days=30)
        elif period == "3M":
            start_date = end_date - timedelta(days=90)
        elif period == "6M":
            start_date = end_date - timedelta(days=180)
        elif period == "1Y":
            start_date = end_date - timedelta(days=365)
        else:  # "ALL"
            # Get earliest snapshot date
            earliest = db.query(AssetSnapshot).order_by(AssetSnapshot.snapshot_datetime).first()
            start_date = earliest.snapshot_datetime.date() if earliest else end_date - timedelta(days=365)

        # Get snapshots for date range (convert date to datetime)
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        snapshots = self.snapshot_service.get_snapshots_range(start_datetime, end_datetime, db)

        # Build chart data
        chart_data = []
        for snapshot in snapshots:
            if currency == "USD":
                total_assets = snapshot.total_assets_usd
                principal = snapshot.principal / to_decimal(1300, precision=4)  # Convert to USD
            else:  # KRW
                total_assets = snapshot.total_assets_krw
                principal = snapshot.principal

            gain_loss = total_assets - principal

            chart_data.append({
                "date": snapshot.snapshot_datetime.date().isoformat(),
                "total_assets": total_assets,
                "principal": principal,
                "gain_loss": gain_loss
            })

        return {
            "chart_data": chart_data,
            "period": period,
            "currency": currency
        }

    def _calculate_allocation_by_type(
        self,
        db: Session,
        total_assets_krw: Decimal
    ) -> Dict:
        """
        Calculate asset allocation by type (Stock, Crypto, Cash, Bond, Gold).

        Returns:
            Dict with allocation and risk summary

        Example:
            {
                "allocation": [
                    {"type": "Stock", "value_krw": 6000000, "percent": 60.0},
                    {"type": "Cash", "value_krw": 3000000, "percent": 30.0}
                ],
                "risk_summary": {
                    "risk_assets_percent": 70.0,
                    "safe_assets_percent": 30.0
                }
            }
        """
        from app.utils.asset_type_inference import classify_asset_type
        from app.utils.currency_inference import infer_price_currency_from_ticker

        accounts = db.query(Account).all()

        stock_value = Decimal("0")
        crypto_value = Decimal("0")
        cash_value = Decimal("0")
        bond_value = Decimal("0")
        gold_value = Decimal("0")

        today_date = date.today()

        for account in accounts:
            holdings = self.holding_service.get_all_holdings_for_account(account.id, db, include_zero=False)

            for holding in holdings:
                asset_type = classify_asset_type(holding.ticker)

                if asset_type == "Cash":
                    if holding.ticker == "KRW":
                        cash_value += holding.quantity
                    else:
                        krw_rate = self.market_data_service.get_exchange_rate(holding.ticker, "KRW", today_date, db)
                        if not krw_rate:
                            krw_rate = self._get_fallback_exchange_rate(holding.ticker)
                        if krw_rate:
                            cash_value += holding.quantity * krw_rate
                elif asset_type == "Crypto":
                    current_price = self.market_data_service.get_latest_price(holding.ticker, db)
                    if current_price is None:
                        current_price = holding.avg_price
                    value = holding.quantity * current_price

                    price_currency = holding.price_currency or infer_price_currency_from_ticker(holding.ticker)
                    if price_currency and price_currency != "KRW":
                        krw_rate = self.market_data_service.get_exchange_rate(price_currency, "KRW", today_date, db)
                        if not krw_rate:
                            krw_rate = self._get_fallback_exchange_rate(price_currency)
                        if krw_rate:
                            value = value * krw_rate
                    crypto_value += value
                elif asset_type == "Gold":
                    current_price = self.market_data_service.get_latest_price(holding.ticker, db)
                    if current_price is None:
                        current_price = holding.avg_price
                    value = holding.quantity * current_price

                    price_currency = holding.price_currency or infer_price_currency_from_ticker(holding.ticker)
                    if price_currency and price_currency != "KRW":
                        krw_rate = self.market_data_service.get_exchange_rate(price_currency, "KRW", today_date, db)
                        if not krw_rate:
                            krw_rate = self._get_fallback_exchange_rate(price_currency)
                        if krw_rate:
                            value = value * krw_rate
                    gold_value += value
                elif asset_type == "Bond":
                    current_price = self.market_data_service.get_latest_price(holding.ticker, db)
                    if current_price is None:
                        current_price = holding.avg_price
                    value = holding.quantity * current_price

                    price_currency = holding.price_currency or infer_price_currency_from_ticker(holding.ticker)
                    if price_currency and price_currency != "KRW":
                        krw_rate = self.market_data_service.get_exchange_rate(price_currency, "KRW", today_date, db)
                        if not krw_rate:
                            krw_rate = self._get_fallback_exchange_rate(price_currency)
                        if krw_rate:
                            value = value * krw_rate
                    bond_value += value
                else:  # Stock
                    current_price = self.market_data_service.get_latest_price(holding.ticker, db)
                    if current_price is None:
                        current_price = holding.avg_price

                    # Calculate this holding's value
                    holding_value = holding.quantity * current_price

                    # Convert to KRW based on price currency
                    if holding.price_currency:
                        if holding.price_currency == "USD":
                            usd_krw_rate = self.market_data_service.get_exchange_rate("USD", "KRW", today_date, db)
                            if not usd_krw_rate:
                                usd_krw_rate = to_decimal(1300, precision=4)
                            holding_value = holding_value * usd_krw_rate
                        elif holding.price_currency == "EUR":
                            eur_krw_rate = self.market_data_service.get_exchange_rate("EUR", "KRW", today_date, db)
                            if not eur_krw_rate:
                                eur_krw_rate = to_decimal(1400, precision=4)
                            holding_value = holding_value * eur_krw_rate
                    else:
                        # Infer currency from ticker
                        stock_price_currency = infer_price_currency_from_ticker(holding.ticker)
                        if stock_price_currency == "USD":
                            usd_krw_rate = self.market_data_service.get_exchange_rate("USD", "KRW", today_date, db)
                            if not usd_krw_rate:
                                usd_krw_rate = to_decimal(1300, precision=4)
                            holding_value = holding_value * usd_krw_rate
                        elif stock_price_currency == "EUR":
                            eur_krw_rate = self.market_data_service.get_exchange_rate("EUR", "KRW", today_date, db)
                            if not eur_krw_rate:
                                eur_krw_rate = to_decimal(1400, precision=4)
                            holding_value = holding_value * eur_krw_rate

                    # Accumulate into total stock value
                    stock_value += holding_value

        allocation = []

        if total_assets_krw > 0:
            if stock_value > 0:
                allocation.append({
                    "type": "Stock",
                    "value_krw": stock_value,
                    "percent": (stock_value / total_assets_krw * 100).quantize(Decimal("0.01"))
                })
            if crypto_value > 0:
                allocation.append({
                    "type": "Crypto",
                    "value_krw": crypto_value,
                    "percent": (crypto_value / total_assets_krw * 100).quantize(Decimal("0.01"))
                })
            if cash_value > 0:
                allocation.append({
                    "type": "Cash",
                    "value_krw": cash_value,
                    "percent": (cash_value / total_assets_krw * 100).quantize(Decimal("0.01"))
                })
            if bond_value > 0:
                allocation.append({
                    "type": "Bond",
                    "value_krw": bond_value,
                    "percent": (bond_value / total_assets_krw * 100).quantize(Decimal("0.01"))
                })
            if gold_value > 0:
                allocation.append({
                    "type": "Gold",
                    "value_krw": gold_value,
                    "percent": (gold_value / total_assets_krw * 100).quantize(Decimal("0.01"))
                })

        risk_assets_value = stock_value + crypto_value
        safe_assets_value = cash_value + bond_value + gold_value

        risk_percent = (risk_assets_value / total_assets_krw * 100).quantize(Decimal("0.01")) if total_assets_krw > 0 else Decimal("0")
        safe_percent = (safe_assets_value / total_assets_krw * 100).quantize(Decimal("0.01")) if total_assets_krw > 0 else Decimal("0")

        return {
            "allocation": allocation,
            "risk_summary": {
                "risk_assets_percent": risk_percent,
                "safe_assets_percent": safe_percent
            }
        }

    def _get_fallback_exchange_rate(self, from_currency: str) -> Decimal:
        """
        Get fallback exchange rate to KRW when market data is unavailable.

        Args:
            from_currency: Source currency code (e.g., "USD", "EUR")

        Returns:
            Decimal: Exchange rate to KRW, or None if currency not found

        Fallback rates (as of typical values):
            USD: 1300, EUR: 1400, JPY: 9, GBP: 1650,
            CHF: 1450, CNY: 180, HKD: 167, SGD: 970
        """
        fallback_rates = {
            "USD": to_decimal(1300, precision=4),
            "EUR": to_decimal(1400, precision=4),
            "JPY": to_decimal(9, precision=4),
            "GBP": to_decimal(1650, precision=4),
            "CHF": to_decimal(1450, precision=4),
            "CNY": to_decimal(180, precision=4),
            "HKD": to_decimal(167, precision=4),
            "SGD": to_decimal(970, precision=4),
        }
        return fallback_rates.get(from_currency)

    def _calculate_top_assets(
        self,
        db: Session,
        total_assets_krw: Decimal,
        limit: int = 10
    ) -> List[Dict]:
        """
        Calculate top assets by value across all accounts.

        Aggregates holdings by ticker (excluding CASH), calculates total
        value in KRW, and returns top N assets sorted by value.

        Args:
            db: Database session
            total_assets_krw: Total assets in KRW for percentage calculation
            limit: Number of top assets to return (default: 10)

        Returns:
            List of dicts with ticker, name, value_krw, percent
        """
        from collections import defaultdict

        # Get all accounts
        accounts = db.query(Account).all()

        # Aggregate holdings by ticker
        ticker_data = defaultdict(lambda: {
            'quantity': Decimal("0"),
            'total_value_krw': Decimal("0")
        })

        # Track aggregated cash separately by currency (converted to KRW value)
        cash_krw_value = Decimal("0")
        cash_usd_value_in_krw = Decimal("0")

        today = date.today()
        usd_krw_rate = self.market_data_service.get_exchange_rate("USD", "KRW", today, db)
        if not usd_krw_rate:
            usd_krw_rate = to_decimal(1300, precision=4)  # Fallback

        for account in accounts:
            holdings = self.holding_service.get_all_holdings_for_account(
                account.id, db, include_zero=False
            )

            # Infer currency from holdings since Account doesn't store it
            inferred_currency = infer_currency_from_holdings(holdings, account.type)

            from app.utils.currency_inference import is_currency_ticker

            for holding in holdings:
                # Handle all currency tickers (KRW, USD, EUR, etc.)
                if is_currency_ticker(holding.ticker):
                    if holding.ticker == "KRW":
                        cash_krw_value += holding.quantity
                    elif holding.ticker == "USD":
                        cash_usd_value_in_krw += holding.quantity * usd_krw_rate
                    elif holding.ticker == "EUR":
                        # Skip EUR for now as we don't have exchange rate logic here
                        pass
                    else:
                        # Other currencies - skip for now
                        pass
                    continue

                # Get current price (fallback to avg_price if market data unavailable)
                current_price = self.market_data_service.get_latest_price(holding.ticker, db)
                if not current_price:
                    current_price = holding.avg_price

                # Calculate value in price currency
                value_in_price_currency = holding.quantity * current_price

                # CRITICAL FIX: Convert to KRW based on stock's price_currency, NOT account currency
                if holding.price_currency:
                    if holding.price_currency == "USD":
                        value_krw = value_in_price_currency * usd_krw_rate
                    elif holding.price_currency == "EUR":
                        eur_krw_rate = self.market_data_service.get_exchange_rate("EUR", "KRW", today, db)
                        if not eur_krw_rate:
                            eur_krw_rate = to_decimal(1400, precision=4)
                        value_krw = value_in_price_currency * eur_krw_rate
                    else:
                        # KRW and others - no conversion needed
                        value_krw = value_in_price_currency
                else:
                    # Fallback: infer price currency from ticker
                    from app.utils.currency_inference import infer_price_currency_from_ticker
                    stock_price_currency = infer_price_currency_from_ticker(holding.ticker)

                    if stock_price_currency == "USD":
                        value_krw = value_in_price_currency * usd_krw_rate
                    elif stock_price_currency == "EUR":
                        eur_krw_rate = self.market_data_service.get_exchange_rate("EUR", "KRW", today, db)
                        if not eur_krw_rate:
                            eur_krw_rate = to_decimal(1400, precision=4)
                        value_krw = value_in_price_currency * eur_krw_rate
                    else:
                        # KRW and others - no conversion needed
                        value_krw = value_in_price_currency

                # Aggregate by ticker
                ticker_data[holding.ticker]['quantity'] += holding.quantity
                ticker_data[holding.ticker]['total_value_krw'] += value_krw

        # Build result list
        top_assets = []

        # Add Cash (KRW) entry if positive
        if cash_krw_value > 0:
            if total_assets_krw > 0:
                percent = (cash_krw_value / total_assets_krw * 100).quantize(Decimal("0.01"))
            else:
                percent = Decimal("0")

            top_assets.append({
                "ticker": "Cash (KRW)",
                "name": "Korean Won",
                "value_krw": cash_krw_value.quantize(Decimal("1")),
                "percent": percent
            })

        # Add Cash (USD) entry if positive
        if cash_usd_value_in_krw > 0:
            if total_assets_krw > 0:
                percent = (cash_usd_value_in_krw / total_assets_krw * 100).quantize(Decimal("0.01"))
            else:
                percent = Decimal("0")

            top_assets.append({
                "ticker": "Cash (USD)",
                "name": "US Dollar",
                "value_krw": cash_usd_value_in_krw.quantize(Decimal("1")),
                "percent": percent
            })

        for ticker, data in ticker_data.items():
            value_krw = data['total_value_krw']

            # Calculate percentage of total assets
            if total_assets_krw > 0:
                percent = (value_krw / total_assets_krw * 100).quantize(Decimal("0.01"))
            else:
                percent = Decimal("0")

            top_assets.append({
                "ticker": ticker,
                "name": None,  # TODO: Add ticker name lookup later
                "value_krw": value_krw.quantize(Decimal("1")),  # No decimals for KRW
                "percent": percent
            })

        # Sort by value descending and take top N
        top_assets.sort(key=lambda x: x['value_krw'], reverse=True)
        return top_assets[:limit]

    def get_candlestick_data(
        self,
        period: str,
        currency: str,
        db: Session,
        start_datetime: datetime = None,
        end_datetime: datetime = None
    ) -> Dict:
        """
        Generate OHLC candlestick data from AssetSnapshot table (now with hourly support).

        Args:
            period: Aggregation period ("hourly", "daily", "monthly", "annual")
            currency: Currency for values ("KRW" or "USD")
            db: Database session
            start_datetime: Optional start datetime (defaults based on period)
            end_datetime: Optional end datetime (defaults to now)

        Returns:
            Dict with candles array containing OHLC data

        Aggregation logic:
            - Hourly: Each snapshot = one candle (O=H=L=C since one value per hour)
            - Daily: Each snapshot = one candle (O=H=L=C since one value per day)
            - Monthly: Group by month, calculate O (1st), H (max), L (min), C (last)
            - Annual: Group by year, calculate O (1st), H (max), L (min), C (last)
        """
        # Determine datetime range
        if not end_datetime:
            end_datetime = now_kst()

        if not start_datetime:
            if period == "hourly":
                start_datetime = end_datetime - timedelta(hours=168)  # Default: 7 days (168 hours)
            elif period == "daily":
                start_datetime = end_datetime - timedelta(days=90)  # Default: 90 days
            elif period == "monthly":
                start_datetime = end_datetime - timedelta(days=365)  # Default: 1 year
            else:  # annual
                start_datetime = end_datetime - timedelta(days=365 * 5)  # Default: 5 years

        # Get snapshots from DB
        snapshots = self.snapshot_service.get_snapshots_range(start_datetime, end_datetime, db)

        if not snapshots:
            return {
                "candles": [],
                "period": period,
                "currency": currency,
                "data_points": 0
            }

        # Select value field based on currency
        value_field = "total_assets_krw" if currency == "KRW" else "total_assets_usd"

        # Aggregate based on period
        if period == "hourly":
            candles = self._aggregate_hourly(snapshots, value_field)
        elif period == "daily":
            candles = self._aggregate_daily(snapshots, value_field)
        elif period == "monthly":
            candles = self._aggregate_monthly(snapshots, value_field)
        else:  # annual
            candles = self._aggregate_annual(snapshots, value_field)

        return {
            "candles": candles,
            "period": period,
            "currency": currency,
            "data_points": len(candles)
        }

    def _aggregate_hourly(self, snapshots: List[AssetSnapshot], value_field: str) -> List[Dict]:
        """
        Hourly aggregation: Each snapshot becomes one candle where O=H=L=C.

        Since we only have one value per hour, all OHLC values are the same.
        The variation is shown between consecutive hours.

        Args:
            snapshots: List of AssetSnapshot records
            value_field: Field to use for values ("total_assets_krw" or "total_assets_usd")

        Returns:
            List of dicts with time, open, high, low, close
        """
        candles = []
        for snapshot in snapshots:
            value = getattr(snapshot, value_field)
            candles.append({
                "time": snapshot.snapshot_datetime.isoformat(),
                "open": value,
                "high": value,
                "low": value,
                "close": value
            })
        return candles

    def _aggregate_daily(self, snapshots: List[AssetSnapshot], value_field: str) -> List[Dict]:
        """
        Daily aggregation: Group hourly snapshots by day, calculate OHLC.

        - Open: First hourly value in the day
        - High: Maximum hourly value during the day
        - Low: Minimum hourly value during the day
        - Close: Last hourly value in the day

        Args:
            snapshots: List of AssetSnapshot records (hourly granularity)
            value_field: Field to use for values ("total_assets_krw" or "total_assets_usd")

        Returns:
            List of dicts with time, open, high, low, close
        """
        from collections import defaultdict

        # Group by date
        daily_data = defaultdict(list)
        for snapshot in snapshots:
            date_key = snapshot.snapshot_datetime.date().isoformat()
            value = getattr(snapshot, value_field)
            daily_data[date_key].append({
                "datetime": snapshot.snapshot_datetime,
                "value": value
            })

        # Calculate OHLC for each day
        candles = []
        for date_key in sorted(daily_data.keys()):
            values = daily_data[date_key]
            # Sort by datetime
            values.sort(key=lambda x: x["datetime"])

            open_val = values[0]["value"]  # First hour
            close_val = values[-1]["value"]  # Last hour
            high_val = max(v["value"] for v in values)
            low_val = min(v["value"] for v in values)

            candles.append({
                "time": date_key,
                "open": open_val,
                "high": high_val,
                "low": low_val,
                "close": close_val
            })

        return candles

    def _aggregate_monthly(self, snapshots: List[AssetSnapshot], value_field: str) -> List[Dict]:
        """
        Monthly aggregation: Group by month, calculate OHLC.

        - Open: First day's value in the month
        - High: Maximum value during the month
        - Low: Minimum value during the month
        - Close: Last day's value in the month

        Args:
            snapshots: List of AssetSnapshot records
            value_field: Field to use for values ("total_assets_krw" or "total_assets_usd")

        Returns:
            List of dicts with time, open, high, low, close
        """
        from collections import defaultdict

        # Group by year-month
        monthly_data = defaultdict(list)
        for snapshot in snapshots:
            month_key = snapshot.snapshot_datetime.strftime("%Y-%m")
            value = getattr(snapshot, value_field)
            monthly_data[month_key].append({
                "date": snapshot.snapshot_datetime.date(),
                "value": value
            })

        # Calculate OHLC for each month
        candles = []
        for month_key in sorted(monthly_data.keys()):
            values = monthly_data[month_key]
            # Sort by date
            values.sort(key=lambda x: x["date"])

            open_val = values[0]["value"]  # First day
            close_val = values[-1]["value"]  # Last day
            high_val = max(v["value"] for v in values)
            low_val = min(v["value"] for v in values)

            # Use last day of the month as time
            candles.append({
                "time": values[-1]["date"].isoformat(),
                "open": open_val,
                "high": high_val,
                "low": low_val,
                "close": close_val
            })

        return candles

    def _aggregate_annual(self, snapshots: List[AssetSnapshot], value_field: str) -> List[Dict]:
        """
        Annual aggregation: Group by year, calculate OHLC.

        - Open: First day's value in the year
        - High: Maximum value during the year
        - Low: Minimum value during the year
        - Close: Last day's value in the year

        Args:
            snapshots: List of AssetSnapshot records
            value_field: Field to use for values ("total_assets_krw" or "total_assets_usd")

        Returns:
            List of dicts with time, open, high, low, close
        """
        from collections import defaultdict

        # Group by year
        yearly_data = defaultdict(list)
        for snapshot in snapshots:
            year_key = snapshot.snapshot_datetime.strftime("%Y")
            value = getattr(snapshot, value_field)
            yearly_data[year_key].append({
                "date": snapshot.snapshot_datetime.date(),
                "value": value
            })

        # Calculate OHLC for each year
        candles = []
        for year_key in sorted(yearly_data.keys()):
            values = yearly_data[year_key]
            # Sort by date
            values.sort(key=lambda x: x["date"])

            open_val = values[0]["value"]  # First day
            close_val = values[-1]["value"]  # Last day
            high_val = max(v["value"] for v in values)
            low_val = min(v["value"] for v in values)

            # Use last day of the year as time
            candles.append({
                "time": values[-1]["date"].isoformat(),
                "open": open_val,
                "high": high_val,
                "low": low_val,
                "close": close_val
            })

        return candles
