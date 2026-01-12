"""
Snapshot service for generating and managing hourly asset snapshots.

Asset snapshots capture the total asset value at a specific point in time,
used for dashboard charts and performance tracking.
"""

from sqlalchemy.orm import Session
from app.models.asset_snapshot import AssetSnapshot
from app.models.holding import Holding
from app.models.account import Account
from app.models.transaction import Transaction
from app.utils.decimal_helpers import to_decimal, safe_divide
from app.utils.currency_inference import infer_currency_from_holdings
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Optional, List
from app.utils.timezone import now_kst


class SnapshotService:
    """
    Service for managing asset snapshots.

    Snapshots are generated hourly and store:
    - Total assets in KRW
    - Total assets in USD
    - Principal (total deposits - withdrawals)
    """

    def generate_snapshot(
        self,
        snapshot_datetime: datetime,
        db: Session,
        usd_krw_rate: Optional[Decimal] = None
    ) -> AssetSnapshot:
        """
        Generate asset snapshot for a specific datetime (hourly granularity).

        Algorithm:
        1. Get all holdings as of snapshot_datetime
        2. Fetch hourly market prices for snapshot_datetime (from MarketData)
        3. Calculate total assets in KRW and USD
        4. Calculate principal (total deposits - withdrawals)
        5. Create or update AssetSnapshot record

        Args:
            snapshot_datetime: Datetime to generate snapshot for (hour precision)
            db: Database session
            usd_krw_rate: Optional USD/KRW exchange rate (if None, fetches from API)

        Returns:
            Created or updated AssetSnapshot

        Examples:
            >>> from datetime import datetime
            >>> service = SnapshotService()
            >>> snapshot = service.generate_snapshot(datetime(2024, 1, 15, 14, 0), db)
            >>> snapshot.total_assets_krw
            Decimal('10000000.00')
        """
        # Import market service for fetching exchange rates and prices
        from app.services.market_data_service import MarketDataService
        market_service = MarketDataService()

        # Get date component for exchange rates (updated daily, not hourly)
        snapshot_date = snapshot_datetime.date()

        # Fetch USD/KRW rate if not provided
        if usd_krw_rate is None:
            usd_krw_rate = market_service.get_exchange_rate("USD", "KRW", snapshot_date, db)
            if usd_krw_rate is None:
                # Fallback to default only if API fails
                usd_krw_rate = to_decimal(1300, precision=4)

        # Get all accounts
        accounts = db.query(Account).all()

        total_krw = Decimal("0")

        for account in accounts:
            # Get holdings for this account
            holdings = db.query(Holding).filter(
                Holding.account_id == account.id
            ).all()

            # Infer currency from holdings
            inferred_currency = infer_currency_from_holdings(holdings, account.type)

            from app.utils.currency_inference import is_currency_ticker

            for holding in holdings:
                # Calculate value
                if is_currency_ticker(holding.ticker):
                    # For all currency holdings (KRW, USD, EUR, etc.), value = quantity
                    value = holding.quantity

                    # Convert to KRW if needed
                    if holding.ticker == "USD":
                        value = value * usd_krw_rate
                    elif holding.ticker == "EUR":
                        # Fetch EUR/KRW rate from market data service
                        eur_krw_rate = market_service.get_exchange_rate("EUR", "KRW", snapshot_date, db)
                        if eur_krw_rate is None:
                            eur_krw_rate = to_decimal(1400, precision=4)  # Fallback
                        value = value * eur_krw_rate
                    # KRW stays as-is (no conversion needed)

                else:
                    # For stocks, fetch hourly price for snapshot_datetime
                    current_price = market_service.get_stock_price_hourly(holding.ticker, snapshot_datetime, db)

                    if current_price is None:
                        # Fallback to avg_price if market data unavailable
                        current_price = holding.avg_price
                        print(f"[Snapshot] No market data for {holding.ticker} at {snapshot_datetime}, using avg_price")

                    value = holding.quantity * current_price

                    # CRITICAL FIX: Convert to KRW based on stock's price_currency, NOT account currency
                    # Each stock has its own price currency (e.g., AAPL=USD, 005930=KRW)
                    if holding.price_currency:
                        if holding.price_currency == "USD":
                            value = value * usd_krw_rate
                        elif holding.price_currency == "EUR":
                            # Fetch EUR/KRW rate
                            eur_krw_rate = market_service.get_exchange_rate("EUR", "KRW", snapshot_date, db)
                            if eur_krw_rate is None:
                                eur_krw_rate = to_decimal(1400, precision=4)
                            value = value * eur_krw_rate
                        # KRW stocks don't need conversion
                    else:
                        # Fallback: infer price currency from ticker if price_currency is not set
                        from app.utils.currency_inference import infer_price_currency_from_ticker
                        stock_price_currency = infer_price_currency_from_ticker(holding.ticker)

                        if stock_price_currency == "USD":
                            value = value * usd_krw_rate
                        elif stock_price_currency == "EUR":
                            eur_krw_rate = market_service.get_exchange_rate("EUR", "KRW", snapshot_date, db)
                            if eur_krw_rate is None:
                                eur_krw_rate = to_decimal(1400, precision=4)
                            value = value * eur_krw_rate
                        # KRW stocks don't need conversion

                total_krw += value

        # Calculate principal
        principal = self._calculate_principal(snapshot_datetime, db)

        # Calculate USD equivalent
        total_usd = safe_divide(total_krw, usd_krw_rate, precision=2)

        # Create or update snapshot
        snapshot = db.query(AssetSnapshot).filter(
            AssetSnapshot.snapshot_datetime == snapshot_datetime
        ).first()

        if snapshot:
            snapshot.total_assets_krw = to_decimal(total_krw, precision=2)
            snapshot.total_assets_usd = total_usd
            snapshot.principal = to_decimal(principal, precision=2)
        else:
            snapshot = AssetSnapshot(
                snapshot_datetime=snapshot_datetime,
                total_assets_krw=to_decimal(total_krw, precision=2),
                total_assets_usd=total_usd,
                principal=to_decimal(principal, precision=2)
            )
            db.add(snapshot)

        db.flush()
        return snapshot

    def _calculate_principal(self, up_to_datetime: datetime, db: Session) -> Decimal:
        """
        Calculate principal (total deposits - withdrawals) up to a datetime.

        Principal represents the net amount of money put into the system.

        Args:
            up_to_datetime: Calculate principal up to this datetime (inclusive)
            db: Database session

        Returns:
            Principal amount

        Examples:
            >>> from datetime import datetime
            >>> # Deposited 1M, withdrew 200K
            >>> principal = service._calculate_principal(datetime(2024, 1, 15, 14, 0), db)
            >>> principal
            Decimal('800000.00')
        """
        # Sum all deposits and withdrawals up to datetime
        transactions = db.query(Transaction).filter(
            Transaction.date <= up_to_datetime,
            Transaction.type.in_(["Deposit", "Withdrawal"]),
            Transaction.deleted_at.is_(None)
        ).all()

        principal = sum(tx.amount for tx in transactions)
        return to_decimal(principal, precision=2)

    def get_snapshot(self, snapshot_datetime: datetime, db: Session) -> Optional[AssetSnapshot]:
        """
        Get snapshot for a specific datetime.

        Args:
            snapshot_datetime: Datetime to get snapshot for
            db: Database session

        Returns:
            AssetSnapshot or None
        """
        return db.query(AssetSnapshot).filter(
            AssetSnapshot.snapshot_datetime == snapshot_datetime
        ).first()

    def get_snapshots_range(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        db: Session
    ) -> List[AssetSnapshot]:
        """
        Get all snapshots within a datetime range (hourly granularity).

        Args:
            start_datetime: Start datetime (inclusive)
            end_datetime: End datetime (inclusive)
            db: Session

        Returns:
            List of snapshots ordered by datetime

        Examples:
            >>> from datetime import datetime
            >>> snapshots = service.get_snapshots_range(
            ...     datetime(2024, 1, 1, 0, 0),
            ...     datetime(2024, 1, 7, 23, 0),
            ...     db
            ... )
            >>> len(snapshots)
            168  # 7 days * 24 hours
        """
        return db.query(AssetSnapshot).filter(
            AssetSnapshot.snapshot_datetime >= start_datetime,
            AssetSnapshot.snapshot_datetime <= end_datetime
        ).order_by(AssetSnapshot.snapshot_datetime).all()

    def backfill_hourly_snapshots(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        db: Session
    ) -> int:
        """
        Backfill hourly snapshots for a datetime range.

        This is useful for generating historical hourly snapshots from transaction history
        or filling gaps after server downtime.

        Args:
            start_datetime: Start datetime
            end_datetime: End datetime
            db: Database session

        Returns:
            Number of snapshots created

        Examples:
            >>> from datetime import datetime
            >>> # Generate hourly snapshots for 7 days
            >>> count = service.backfill_hourly_snapshots(
            ...     datetime(2024, 1, 1, 0, 0),
            ...     datetime(2024, 1, 7, 23, 0),
            ...     db
            ... )
            >>> count
            168  # 7 days * 24 hours
        """
        # Round to hour boundaries
        current_dt = start_datetime.replace(minute=0, second=0, microsecond=0)
        end_dt = end_datetime.replace(minute=0, second=0, microsecond=0)
        created_count = 0

        while current_dt <= end_dt:
            # Skip if snapshot already exists
            existing = self.get_snapshot(current_dt, db)
            if not existing:
                self.generate_snapshot(current_dt, db)
                created_count += 1

                # Batch commit every 24 hours for performance
                if created_count % 24 == 0:
                    db.commit()

            current_dt += timedelta(hours=1)

        db.commit()
        print(f"[SnapshotService] Backfilled {created_count} hourly snapshots")
        return created_count

    def detect_and_fill_gaps(self, db: Session) -> int:
        """
        Detect missing hourly snapshots and backfill them.

        Called on application startup to catch up after server downtime.

        Algorithm:
        1. Get latest snapshot datetime
        2. If gap > 1 hour from now, backfill from latest to now
        3. If no snapshots exist, backfill last 30 days

        Args:
            db: Database session

        Returns:
            Number of snapshots created

        Examples:
            >>> # Server was down for 10 hours
            >>> filled = service.detect_and_fill_gaps(db)
            >>> filled
            10  # Filled 10 missing hourly snapshots
        """
        latest = self.get_latest_snapshot(db)
        now = now_kst().replace(minute=0, second=0, microsecond=0)

        if not latest:
            # No snapshots exist - backfill last 30 days
            print("[SnapshotService] No snapshots found, backfilling last 30 days")
            start_dt = now - timedelta(days=30)
            return self.backfill_hourly_snapshots(start_dt, now, db)

        # Check for gap
        hours_gap = (now - latest.snapshot_datetime).total_seconds() / 3600

        if hours_gap > 1:
            print(f"[SnapshotService] Gap detected: {hours_gap:.1f} hours missing")
            # Backfill from latest + 1 hour to now
            start_dt = latest.snapshot_datetime + timedelta(hours=1)
            return self.backfill_hourly_snapshots(start_dt, now, db)

        print("[SnapshotService] No gaps detected")
        return 0

    def get_latest_snapshot(self, db: Session) -> Optional[AssetSnapshot]:
        """
        Get the most recent snapshot.

        Args:
            db: Database session

        Returns:
            Latest snapshot or None
        """
        return db.query(AssetSnapshot).order_by(
            AssetSnapshot.snapshot_datetime.desc()
        ).first()

    def calculate_period_change(
        self,
        current_datetime: datetime,
        hours_ago: int,
        db: Session
    ) -> tuple[Decimal, Decimal]:
        """
        Calculate asset change over a period (hourly granularity).

        Args:
            current_datetime: Current datetime
            hours_ago: Number of hours to look back
            db: Database session

        Returns:
            Tuple of (amount_change, percent_change)

        Examples:
            >>> from datetime import datetime
            >>> # Calculate change over last 24 hours
            >>> amount, percent = service.calculate_period_change(
            ...     datetime(2024, 1, 15, 14, 0),
            ...     24,
            ...     db
            ... )
            >>> percent
            Decimal('2.50')  # 2.5% increase
        """
        past_datetime = current_datetime - timedelta(hours=hours_ago)

        current_snapshot = self.get_snapshot(current_datetime, db)
        past_snapshot = self.get_snapshot(past_datetime, db)

        if not current_snapshot or not past_snapshot:
            return Decimal("0"), Decimal("0")

        amount_change = current_snapshot.total_assets_krw - past_snapshot.total_assets_krw

        if past_snapshot.total_assets_krw == 0:
            percent_change = Decimal("0")
        else:
            percent_change = (amount_change / past_snapshot.total_assets_krw * 100)
            percent_change = percent_change.quantize(Decimal("0.01"))

        return amount_change, percent_change
