"""
Recalculation service for time-travel functionality.

CRITICAL: When past transactions are inserted, modified, or deleted,
          we must recalculate holdings and snapshots from that date forward.
"""

from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.models.holding import Holding
from app.models.account import Account
from app.models.asset_snapshot import AssetSnapshot
from app.utils.calculation_engine import calculate_avg_price_on_buy
from app.utils.date_helpers import get_date_range
from decimal import Decimal
from datetime import datetime, date
from typing import List, Dict
from collections import defaultdict


class RecalculationService:
    """
    Service for recalculating holdings and snapshots when past transactions are modified.

    Algorithm:
    1. Get all transactions from start_date to present (ordered by date)
    2. Get all affected accounts
    3. For each account, rebuild holdings by replaying transactions
    4. Regenerate asset snapshots from start_date to present
    """

    def recalculate_from_date(self, start_date: datetime, db: Session) -> None:
        """
        Recalculate all holdings and snapshots from a specific date.

        This is called when a past transaction is inserted, edited, or deleted.

        Args:
            start_date: Date to start recalculation from
            db: Database session

        Examples:
            >>> service = RecalculationService()
            >>> # User inserted a transaction dated 2024-01-01
            >>> service.recalculate_from_date(date(2024, 1, 1), db)
            # All holdings and snapshots from 2024-01-01 to present are recalculated
        """
        print(f"[Recalculation] Starting recalculation from {start_date}")

        # Get all transactions from start_date to present, ordered by date
        transactions = db.query(Transaction).filter(
            Transaction.date >= start_date,
            Transaction.deleted_at.is_(None)  # Exclude soft-deleted
        ).order_by(Transaction.date, Transaction.id).all()

        if not transactions:
            print(f"[Recalculation] No transactions found from {start_date}")
            return

        # Get unique accounts affected
        affected_accounts = set(tx.account_id for tx in transactions)
        print(f"[Recalculation] Affected accounts: {affected_accounts}")

        # For each account, rebuild holdings
        for account_id in affected_accounts:
            self._rebuild_holdings_for_account(account_id, start_date, db)

        # Regenerate snapshots from start_date to present
        self._regenerate_snapshots_from_date(start_date, db)

        db.commit()
        print(f"[Recalculation] Completed")

    def _rebuild_holdings_for_account(
        self,
        account_id: int,
        start_date: datetime,
        db: Session
    ) -> None:
        """
        Rebuild holdings for an account by replaying transactions.

        Algorithm:
        1. Get holdings state at (start_date - 1)
        2. Get all transactions from start_date to present for this account
        3. Replay transactions chronologically to rebuild holdings

        Args:
            account_id: Account ID
            start_date: Date to start rebuilding from
            db: Database session
        """
        print(f"[Recalculation] Rebuilding holdings for account {account_id}")

        # Get current holdings for this account
        holdings = db.query(Holding).filter(
            Holding.account_id == account_id
        ).all()

        # Create holding lookup: {ticker: Holding}
        holding_map: Dict[str, Holding] = {h.ticker: h for h in holdings}

        # Reset holdings to state before start_date
        # (We need to "undo" transactions from start_date onward, then replay them)
        # For MVP, we'll use a simpler approach: reset all holdings to zero, then replay ALL transactions
        # This is less efficient but correct and simpler to implement
        for holding in holdings:
            holding.quantity = Decimal("0")
            if holding.ticker != "CASH":
                holding.avg_price = Decimal("0")

        # Get ALL transactions for this account (from beginning), ordered by date
        all_transactions = db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.deleted_at.is_(None)
        ).order_by(Transaction.date, Transaction.id).all()

        # Replay transactions
        for tx in all_transactions:
            self._apply_transaction_to_holdings(tx, holding_map, db)

        db.flush()
        print(f"[Recalculation] Rebuilt {len(holding_map)} holdings for account {account_id}")

    def _apply_transaction_to_holdings(
        self,
        tx: Transaction,
        holding_map: Dict[str, Holding],
        db: Session
    ) -> None:
        """
        Apply a single transaction to holdings (without creating new transaction records).

        This replicates the logic from transaction_service but only updates holdings.

        Args:
            tx: Transaction to apply
            holding_map: Dict of {ticker: Holding}
            db: Database session
        """
        # Pattern ① - Income/Expense (Deposit, Withdrawal, Dividend)
        if tx.type in ["Deposit", "Withdrawal", "Dividend"]:
            cash = holding_map.get("CASH")
            if not cash:
                cash = Holding(
                    account_id=tx.account_id,
                    ticker="CASH",
                    quantity=Decimal("0"),
                    avg_price=Decimal("1.0")
                )
                holding_map["CASH"] = cash
                db.add(cash)

            cash.quantity += tx.amount

        # Pattern ② - Transfer (handled separately, not in this loop)
        elif tx.type in ["Transfer_Out", "Transfer_In"]:
            cash = holding_map.get("CASH")
            if not cash:
                cash = Holding(
                    account_id=tx.account_id,
                    ticker="CASH",
                    quantity=Decimal("0"),
                    avg_price=Decimal("1.0")
                )
                holding_map["CASH"] = cash
                db.add(cash)

            cash.quantity += tx.amount

        # Pattern ③ - Buy
        elif tx.type == "Buy":
            # Update CASH
            cash = holding_map.get("CASH")
            if not cash:
                cash = Holding(
                    account_id=tx.account_id,
                    ticker="CASH",
                    quantity=Decimal("0"),
                    avg_price=Decimal("1.0")
                )
                holding_map["CASH"] = cash
                db.add(cash)

            cash.quantity += tx.amount  # Negative amount (decrease cash)

            # Update stock holding
            stock = holding_map.get(tx.ticker)
            if not stock:
                stock = Holding(
                    account_id=tx.account_id,
                    ticker=tx.ticker,
                    quantity=Decimal("0"),
                    avg_price=Decimal("0")
                )
                holding_map[tx.ticker] = stock
                db.add(stock)

            # Calculate new average price
            new_avg_price = calculate_avg_price_on_buy(
                stock.quantity,
                stock.avg_price,
                tx.quantity,
                tx.price
            )

            stock.quantity += tx.quantity
            stock.avg_price = new_avg_price

        # Pattern ③ - Sell
        elif tx.type == "Sell":
            # Update CASH
            cash = holding_map.get("CASH")
            if not cash:
                cash = Holding(
                    account_id=tx.account_id,
                    ticker="CASH",
                    quantity=Decimal("0"),
                    avg_price=Decimal("1.0")
                )
                holding_map["CASH"] = cash
                db.add(cash)

            cash.quantity += tx.amount  # Positive amount (increase cash)

            # Update stock holding
            stock = holding_map.get(tx.ticker)
            if stock:
                stock.quantity -= tx.quantity
                # avg_price stays the same

        # Pattern ④ - Exchange
        elif tx.type == "Exchange":
            # Update currency holding
            currency = holding_map.get(tx.ticker)
            if not currency:
                currency = Holding(
                    account_id=tx.account_id,
                    ticker=tx.ticker,
                    quantity=Decimal("0"),
                    avg_price=Decimal("1.0")
                )
                holding_map[tx.ticker] = currency
                db.add(currency)

            currency.quantity += tx.amount

    def _regenerate_snapshots_from_date(
        self,
        start_date: datetime,
        db: Session
    ) -> None:
        """
        Regenerate asset snapshots from start_date to today.

        For each date:
        1. Fetch market data for all holdings
        2. Call SnapshotService.generate_snapshot()
        3. This updates existing snapshots or creates new ones

        Args:
            start_date: Date to start regenerating from
            db: Database session
        """
        from app.services.snapshot_service import SnapshotService
        from app.services.market_data_service import MarketDataService

        snapshot_service = SnapshotService()
        market_service = MarketDataService()

        # Get date range from start_date to today
        today = date.today()
        dates = get_date_range(start_date, today)

        print(f"[Recalculation] Regenerating {len(dates)} snapshots from {start_date} to {today}")

        for snapshot_date in dates:
            # Fetch USD/KRW rate for this date
            usd_krw_rate = market_service.get_exchange_rate("USD", "KRW", snapshot_date, db)

            # Generate snapshot (this will fetch all needed market data internally)
            snapshot_service.generate_snapshot(snapshot_date, db, usd_krw_rate)

        print(f"[Recalculation] Completed snapshot regeneration")

    def recalculate_all_holdings(self, db: Session) -> None:
        """
        Recalculate ALL holdings from the beginning of time.

        This is a nuclear option for fixing inconsistencies.
        Should only be used for maintenance/debugging.

        Args:
            db: Database session
        """
        print("[Recalculation] Starting FULL recalculation of all holdings")

        # Get all accounts
        accounts = db.query(Account).all()

        for account in accounts:
            # Delete all holdings for this account
            db.query(Holding).filter(Holding.account_id == account.id).delete()

            # Replay all transactions
            self._rebuild_holdings_for_account(account.id, date(1900, 1, 1), db)

        db.commit()
        print("[Recalculation] Full recalculation completed")
