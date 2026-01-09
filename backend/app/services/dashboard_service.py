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
from datetime import date, timedelta
from typing import Dict, List


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
        # Get current date snapshot (or generate if not exists)
        today = date.today()
        current_snapshot = self.snapshot_service.get_snapshot(today, db)

        if not current_snapshot:
            # Generate snapshot for today
            current_snapshot = self.snapshot_service.generate_snapshot(today, db)
            db.commit()

        # Get exchange rate
        usd_krw_rate = self.market_data_service.get_exchange_rate("USD", "KRW", today, db)
        if not usd_krw_rate:
            usd_krw_rate = to_decimal(1300, precision=4)  # Fallback

        # Calculate changes
        day_amount, day_percent = self.snapshot_service.calculate_period_change(today, 1, db)
        month_amount, month_percent = self.snapshot_service.calculate_period_change(today, 30, db)
        year_amount, year_percent = self.snapshot_service.calculate_period_change(today, 365, db)

        # Get allocation by type
        allocation_by_type = self._calculate_allocation_by_type(db, current_snapshot.total_assets_krw)

        # Calculate top assets
        top_assets = self._calculate_top_assets(db, current_snapshot.total_assets_krw)

        return {
            "total_assets": {
                "krw": current_snapshot.total_assets_krw,
                "usd": current_snapshot.total_assets_usd
            },
            "current_exchange_rate": {
                "usd_to_krw": usd_krw_rate,
                "updated_at": today.isoformat()
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
            "allocation": {
                "by_type": allocation_by_type
            },
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
            earliest = db.query(AssetSnapshot).order_by(AssetSnapshot.date).first()
            start_date = earliest.date if earliest else end_date - timedelta(days=365)

        # Get snapshots for date range
        snapshots = self.snapshot_service.get_snapshots_range(start_date, end_date, db)

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
                "date": snapshot.date.isoformat(),
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
    ) -> List[Dict]:
        """
        Calculate asset allocation by type (Cash, Stocks, Foreign Currency).

        Args:
            db: Database session
            total_assets_krw: Total assets in KRW

        Returns:
            List of allocation items
        """
        # Get all accounts
        accounts = db.query(Account).all()

        cash_value = Decimal("0")
        stocks_value = Decimal("0")
        foreign_currency_value = Decimal("0")

        from app.utils.currency_inference import is_currency_ticker

        for account in accounts:
            holdings = self.holding_service.get_all_holdings_for_account(account.id, db, include_zero=False)

            for holding in holdings:
                if is_currency_ticker(holding.ticker):
                    # All currencies (KRW, USD, EUR, etc.)
                    if holding.ticker == "KRW":
                        cash_value += holding.quantity
                    else:
                        foreign_currency_value += holding.quantity
                else:
                    # Stock
                    # TODO: Get current price and convert to KRW
                    stocks_value += holding.quantity * holding.avg_price

        # Calculate percentages
        allocation = []

        if total_assets_krw > 0:
            allocation.append({
                "type": "Cash",
                "value_krw": cash_value,
                "percent": (cash_value / total_assets_krw * 100).quantize(Decimal("0.01"))
            })

            allocation.append({
                "type": "Stocks",
                "value_krw": stocks_value,
                "percent": (stocks_value / total_assets_krw * 100).quantize(Decimal("0.01"))
            })

            allocation.append({
                "type": "Foreign Currency",
                "value_krw": foreign_currency_value,
                "percent": (foreign_currency_value / total_assets_krw * 100).quantize(Decimal("0.01"))
            })

        return allocation

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

                # Calculate value in account currency
                value_in_account_currency = holding.quantity * current_price

                # Convert to KRW if needed
                if inferred_currency == "USD":
                    value_krw = value_in_account_currency * usd_krw_rate
                elif inferred_currency == "KRW":
                    value_krw = value_in_account_currency
                else:
                    value_krw = value_in_account_currency  # TODO: Handle EUR, etc.

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
