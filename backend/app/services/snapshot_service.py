"""
Snapshot service for generating and managing daily asset snapshots.

Asset snapshots capture the total asset value at a specific point in time,
used for dashboard charts and performance tracking.
"""

from sqlalchemy.orm import Session
from app.models.asset_snapshot import AssetSnapshot
from app.models.holding import Holding
from app.models.account import Account
from app.models.transaction import Transaction
from app.utils.decimal_helpers import to_decimal, safe_divide
from decimal import Decimal
from datetime import date
from typing import Optional


class SnapshotService:
    """
    Service for managing asset snapshots.

    Snapshots are generated daily and store:
    - Total assets in KRW
    - Total assets in USD
    - Principal (total deposits - withdrawals)
    """

    def generate_snapshot(
        self,
        snapshot_date: date,
        db: Session,
        usd_krw_rate: Optional[Decimal] = None
    ) -> AssetSnapshot:
        """
        Generate asset snapshot for a specific date.

        Algorithm:
        1. Get all holdings as of snapshot_date
        2. Fetch market prices for snapshot_date (from MarketData)
        3. Calculate total assets in KRW and USD
        4. Calculate principal (total deposits - withdrawals)
        5. Create or update AssetSnapshot record

        Args:
            snapshot_date: Date to generate snapshot for
            db: Database session
            usd_krw_rate: Optional USD/KRW exchange rate (if None, uses default 1300)

        Returns:
            Created or updated AssetSnapshot

        Examples:
            >>> service = SnapshotService()
            >>> snapshot = service.generate_snapshot(date.today(), db)
            >>> snapshot.total_assets_krw
            Decimal('10000000.00')
        """
        # Use default exchange rate if not provided
        # TODO: Fetch from market_data_service in Phase 8
        if usd_krw_rate is None:
            usd_krw_rate = to_decimal(1300, precision=4)

        # Get all accounts
        accounts = db.query(Account).all()

        total_krw = Decimal("0")

        for account in accounts:
            # Get holdings for this account
            holdings = db.query(Holding).filter(
                Holding.account_id == account.id
            ).all()

            for holding in holdings:
                # Calculate value
                if holding.ticker == "CASH" or holding.ticker in ["KRW", "USD", "EUR"]:
                    # For cash and currencies, value = quantity
                    value = holding.quantity

                    # Convert to KRW if needed
                    if holding.ticker == "USD":
                        value = value * usd_krw_rate
                    elif holding.ticker == "EUR":
                        # TODO: Fetch EUR/KRW rate from market_data_service
                        value = value * to_decimal(1400, precision=4)  # Placeholder
                    # KRW and CASH stay as-is

                else:
                    # For stocks, value = quantity × current_price
                    # TODO: Fetch current price from market_data_service
                    # For now, use avg_price as placeholder
                    value = holding.quantity * holding.avg_price

                    # Convert to KRW based on account currency
                    if account.currency == "USD":
                        value = value * usd_krw_rate
                    elif account.currency == "EUR":
                        value = value * to_decimal(1400, precision=4)

                total_krw += value

        # Calculate principal
        principal = self._calculate_principal(snapshot_date, db)

        # Calculate USD equivalent
        total_usd = safe_divide(total_krw, usd_krw_rate, precision=2)

        # Create or update snapshot
        snapshot = db.query(AssetSnapshot).filter(
            AssetSnapshot.date == snapshot_date
        ).first()

        if snapshot:
            snapshot.total_assets_krw = to_decimal(total_krw, precision=2)
            snapshot.total_assets_usd = total_usd
            snapshot.principal = to_decimal(principal, precision=2)
        else:
            snapshot = AssetSnapshot(
                date=snapshot_date,
                total_assets_krw=to_decimal(total_krw, precision=2),
                total_assets_usd=total_usd,
                principal=to_decimal(principal, precision=2)
            )
            db.add(snapshot)

        db.flush()
        return snapshot

    def _calculate_principal(self, up_to_date: date, db: Session) -> Decimal:
        """
        Calculate principal (total deposits - withdrawals) up to a date.

        Principal represents the net amount of money put into the system.

        Args:
            up_to_date: Calculate principal up to this date (inclusive)
            db: Database session

        Returns:
            Principal amount

        Examples:
            >>> # Deposited 1M, withdrew 200K
            >>> principal = service._calculate_principal(date.today(), db)
            >>> principal
            Decimal('800000.00')
        """
        # Sum all deposits and withdrawals up to date
        transactions = db.query(Transaction).filter(
            Transaction.date <= up_to_date,
            Transaction.type.in_(["Deposit", "Withdrawal"]),
            Transaction.deleted_at.is_(None)
        ).all()

        principal = sum(tx.amount for tx in transactions)
        return to_decimal(principal, precision=2)

    def get_snapshot(self, snapshot_date: date, db: Session) -> Optional[AssetSnapshot]:
        """
        Get snapshot for a specific date.

        Args:
            snapshot_date: Date to get snapshot for
            db: Database session

        Returns:
            AssetSnapshot or None
        """
        return db.query(AssetSnapshot).filter(
            AssetSnapshot.date == snapshot_date
        ).first()

    def get_snapshots_range(
        self,
        start_date: date,
        end_date: date,
        db: Session
    ) -> list[AssetSnapshot]:
        """
        Get all snapshots within a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            db: Session

        Returns:
            List of snapshots ordered by date

        Examples:
            >>> snapshots = service.get_snapshots_range(
            ...     date(2024, 1, 1),
            ...     date(2024, 1, 31),
            ...     db
            ... )
            >>> len(snapshots)
            31  # One snapshot per day
        """
        return db.query(AssetSnapshot).filter(
            AssetSnapshot.date >= start_date,
            AssetSnapshot.date <= end_date
        ).order_by(AssetSnapshot.date).all()

    def backfill_snapshots(
        self,
        start_date: date,
        end_date: date,
        db: Session
    ) -> int:
        """
        Backfill snapshots for a date range.

        This is useful for generating historical snapshots from transaction history.

        Args:
            start_date: Start date
            end_date: End date
            db: Database session

        Returns:
            Number of snapshots created

        Examples:
            >>> # Generate snapshots for the entire year
            >>> count = service.backfill_snapshots(
            ...     date(2024, 1, 1),
            ...     date(2024, 12, 31),
            ...     db
            ... )
            >>> count
            366  # Leap year
        """
        from app.utils.date_helpers import get_date_range

        dates = get_date_range(start_date, end_date)
        count = 0

        for snapshot_date in dates:
            # Skip if snapshot already exists
            existing = self.get_snapshot(snapshot_date, db)
            if not existing:
                self.generate_snapshot(snapshot_date, db)
                count += 1

        db.commit()
        return count

    def get_latest_snapshot(self, db: Session) -> Optional[AssetSnapshot]:
        """
        Get the most recent snapshot.

        Args:
            db: Database session

        Returns:
            Latest snapshot or None
        """
        return db.query(AssetSnapshot).order_by(
            AssetSnapshot.date.desc()
        ).first()

    def calculate_period_change(
        self,
        current_date: date,
        days_ago: int,
        db: Session
    ) -> tuple[Decimal, Decimal]:
        """
        Calculate asset change over a period.

        Args:
            current_date: Current date
            days_ago: Number of days to look back
            db: Database session

        Returns:
            Tuple of (amount_change, percent_change)

        Examples:
            >>> # Calculate change over last 30 days
            >>> amount, percent = service.calculate_period_change(
            ...     date.today(),
            ...     30,
            ...     db
            ... )
            >>> percent
            Decimal('5.50')  # 5.5% increase
        """
        from datetime import timedelta

        past_date = current_date - timedelta(days=days_ago)

        current_snapshot = self.get_snapshot(current_date, db)
        past_snapshot = self.get_snapshot(past_date, db)

        if not current_snapshot or not past_snapshot:
            return Decimal("0"), Decimal("0")

        amount_change = current_snapshot.total_assets_krw - past_snapshot.total_assets_krw

        if past_snapshot.total_assets_krw == 0:
            percent_change = Decimal("0")
        else:
            percent_change = (amount_change / past_snapshot.total_assets_krw * 100)
            percent_change = percent_change.quantize(Decimal("0.01"))

        return amount_change, percent_change
