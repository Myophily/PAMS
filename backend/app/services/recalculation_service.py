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
from app.utils.currency_inference import is_currency_ticker, normalize_ticker, CURRENCY_TICKERS
from decimal import Decimal
from datetime import datetime, date
from typing import List, Dict, Union
from collections import defaultdict
from app.utils.timezone import now_kst_truncated


class RecalculationService:
    """
    Service for recalculating holdings and snapshots when past transactions are modified.

    Algorithm:
    1. Get all transactions from start_date to present (ordered by date)
    2. Get all affected accounts
    3. For each account, rebuild holdings by replaying transactions
    4. Regenerate asset snapshots from start_date to present
    """

    def recalculate_from_date(self, start_date: Union[date, datetime], db: Session) -> None:
        """
        Recalculate all holdings and hourly snapshots from a specific date/datetime.

        This is called when a past transaction is inserted, edited, or deleted.

        Args:
            start_date: Date or datetime to start recalculation from
            db: Database session

        Examples:
            >>> from datetime import datetime
            >>> service = RecalculationService()
            >>> # User inserted a transaction dated 2024-01-01 14:00
            >>> service.recalculate_from_date(datetime(2024, 1, 1, 14, 0), db)
            # All holdings and hourly snapshots from 2024-01-01 14:00 to present are recalculated
        """
        # Convert date to datetime at 00:00 if needed
        if isinstance(start_date, date) and not isinstance(start_date, datetime):
            start_datetime = datetime.combine(start_date, datetime.min.time())
        else:
            start_datetime = start_date

        print(f"[Recalculation] Starting recalculation from {start_datetime}")

        # Get all transactions from start_datetime to present, ordered by datetime
        transactions = db.query(Transaction).filter(
            Transaction.date >= start_datetime,
            Transaction.deleted_at.is_(None)  # Exclude soft-deleted
        ).order_by(Transaction.date, Transaction.id).all()

        if not transactions:
            print(f"[Recalculation] No transactions found from {start_datetime}")
            return

        # Get unique accounts affected
        affected_accounts = set(tx.account_id for tx in transactions)
        print(f"[Recalculation] Affected accounts: {affected_accounts}")

        # For each account, rebuild holdings
        # Note: Holdings are account-level, not time-based, so we still use date for comparison
        start_date_only = start_datetime.date() if isinstance(start_datetime, datetime) else start_datetime
        for account_id in affected_accounts:
            self._rebuild_holdings_for_account(account_id, start_date_only, db)

        # Regenerate hourly snapshots from start_datetime to present
        self._regenerate_snapshots_from_datetime(start_datetime, db)

        db.commit()
        print(f"[Recalculation] Completed")

    def _rebuild_holdings_for_account(
        self,
        account_id: int,
        start_date: date,
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
            # Currency holdings always have avg_price of 1.0
            if not is_currency_ticker(holding.ticker):
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
            # CRITICAL FIX: Handle ticker=None for Withdrawal/Deposit transactions
            # Infer default currency ticker based on account type
            if tx.ticker is None:
                account = db.query(Account).get(tx.account_id)
                ticker = normalize_ticker("CASH", account.type) if account else "KRW"
            else:
                ticker = tx.ticker

            # CRITICAL FIX: Distinguish between currency deposits and stock deposits
            # - Currency deposits: Deposit with ticker="USD"/"KRW" (cash transactions)
            # - Stock deposits: Deposit with ticker="AAPL" + quantity + price (initial stock holdings)
            #
            # Background: account_service.py creates "Deposit" transactions for initial stock holdings
            # with ticker, quantity, price, AND amount fields. These must be processed differently
            # from true currency deposits to prevent quantity/price corruption.

            if is_currency_ticker(ticker):
                # PATH A: Currency deposit/withdrawal (KRW, USD, etc.)
                # This is a true cash transaction - use tx.amount and avg_price=1.0
                currency_holding = holding_map.get(ticker)
                if not currency_holding:
                    currency_holding = Holding(
                        account_id=tx.account_id,
                        ticker=ticker,
                        quantity=Decimal("0"),
                        avg_price=Decimal("1.0")
                    )
                    holding_map[ticker] = currency_holding
                    db.add(currency_holding)

                currency_holding.quantity += tx.amount

            else:
                # PATH B: Stock deposit (initial holdings created by account_service)
                # These transactions have ticker (e.g., "AAPL"), quantity, price, AND amount
                # We must use quantity/price fields, NOT amount

                # Only process as stock deposit if quantity and price are present
                if tx.quantity is not None and tx.price is not None:
                    # Update stock holding using quantity and price (NOT amount!)
                    stock_holding = holding_map.get(ticker)
                    if not stock_holding:
                        stock_holding = Holding(
                            account_id=tx.account_id,
                            ticker=ticker,
                            quantity=Decimal("0"),
                            avg_price=Decimal("0")
                        )
                        holding_map[ticker] = stock_holding
                        db.add(stock_holding)

                    # Calculate weighted average price (same logic as Buy transactions)
                    new_avg_price = calculate_avg_price_on_buy(
                        stock_holding.quantity,
                        stock_holding.avg_price,
                        tx.quantity,  # CRITICAL: Use quantity, NOT amount
                        tx.price      # CRITICAL: Use actual price, NOT 1.0
                    )

                    stock_holding.quantity += tx.quantity
                    stock_holding.avg_price = new_avg_price

                    # Store price currency if available
                    if tx.price_currency:
                        stock_holding.price_currency = tx.price_currency
                else:
                    # Fallback: treat as currency if no quantity/price (edge case)
                    # This handles malformed transactions gracefully
                    currency_holding = holding_map.get(ticker)
                    if not currency_holding:
                        currency_holding = Holding(
                            account_id=tx.account_id,
                            ticker=ticker,
                            quantity=Decimal("0"),
                            avg_price=Decimal("1.0")
                        )
                        holding_map[ticker] = currency_holding
                        db.add(currency_holding)

                    currency_holding.quantity += tx.amount

        # Pattern ② - Transfer (handled separately, not in this loop)
        elif tx.type in ["Transfer_Out", "Transfer_In"]:
            # Use the currency ticker from the transaction (KRW, USD, etc.)
            ticker = tx.ticker
            currency_holding = holding_map.get(ticker)
            if not currency_holding:
                currency_holding = Holding(
                    account_id=tx.account_id,
                    ticker=ticker,
                    quantity=Decimal("0"),
                    avg_price=Decimal("1.0")
                )
                holding_map[ticker] = currency_holding
                db.add(currency_holding)

            currency_holding.quantity += tx.amount

        # Pattern ③ - Buy
        elif tx.type == "Buy":
            # Determine cash currency from transaction price_currency
            # If not specified, infer from account type
            if tx.price_currency:
                cash_ticker = tx.price_currency
            else:
                # Fallback: infer from account type
                account = db.query(Account).get(tx.account_id)
                cash_ticker = normalize_ticker("CASH", account.type) if account else "KRW"

            # Update cash holding
            currency_holding = holding_map.get(cash_ticker)
            if not currency_holding:
                currency_holding = Holding(
                    account_id=tx.account_id,
                    ticker=cash_ticker,
                    quantity=Decimal("0"),
                    avg_price=Decimal("1.0")
                )
                holding_map[cash_ticker] = currency_holding
                db.add(currency_holding)

            currency_holding.quantity += tx.amount  # Negative amount (decrease cash)

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
            # Determine cash currency from transaction price_currency
            # If not specified, infer from account type
            if tx.price_currency:
                cash_ticker = tx.price_currency
            else:
                # Fallback: infer from account type
                account = db.query(Account).get(tx.account_id)
                cash_ticker = normalize_ticker("CASH", account.type) if account else "KRW"

            # Update cash holding
            currency_holding = holding_map.get(cash_ticker)
            if not currency_holding:
                currency_holding = Holding(
                    account_id=tx.account_id,
                    ticker=cash_ticker,
                    quantity=Decimal("0"),
                    avg_price=Decimal("1.0")
                )
                holding_map[cash_ticker] = currency_holding
                db.add(currency_holding)

            currency_holding.quantity += tx.amount  # Positive amount (increase cash)

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

    def _regenerate_snapshots_from_datetime(
        self,
        start_datetime: datetime,
        db: Session
    ) -> None:
        """
        Regenerate asset snapshots from start_datetime to now.

        Creates TWO types of snapshots:
        1. Transaction-time snapshots: At exact transaction times (any minute)
        2. Hourly snapshots: At top of each hour (:00)

        Algorithm:
        1. Get all transaction datetimes from start_datetime to now
        2. Create set of datetimes to regenerate (transactions + hourly)
        3. Delete existing snapshots for those datetimes
        4. Regenerate all snapshots

        Args:
            start_datetime: Datetime to start regenerating from
            db: Database session
        """
        from app.services.snapshot_service import SnapshotService
        from datetime import timedelta

        snapshot_service = SnapshotService()

        # Truncate to minute precision
        start_dt = start_datetime.replace(second=0, microsecond=0)
        now = now_kst_truncated()

        # Step 1: Get all transaction datetimes from start_dt to now
        transactions = db.query(Transaction).filter(
            Transaction.date >= start_dt,
            Transaction.date <= now,
            Transaction.deleted_at.is_(None)
        ).all()

        transaction_datetimes = set()
        for tx in transactions:
            # Truncate to minute precision
            tx_dt = tx.date.replace(second=0, microsecond=0)
            transaction_datetimes.add(tx_dt)

        print(f"[Recalculation] Found {len(transaction_datetimes)} unique transaction times")

        # Step 2: Generate hourly datetimes (:00 of each hour)
        hourly_datetimes = set()
        current_hour = start_dt.replace(minute=0, second=0, microsecond=0)
        end_hour = now.replace(minute=0, second=0, microsecond=0)

        while current_hour <= end_hour:
            hourly_datetimes.add(current_hour)
            current_hour += timedelta(hours=1)

        print(f"[Recalculation] Generated {len(hourly_datetimes)} hourly times")

        # Step 3: Combine transaction times and hourly times
        all_snapshot_times = transaction_datetimes.union(hourly_datetimes)
        all_snapshot_times = sorted(all_snapshot_times)

        print(f"[Recalculation] Total snapshots to regenerate: {len(all_snapshot_times)}")

        # Step 4: Delete existing snapshots for these times
        db.query(AssetSnapshot).filter(
            AssetSnapshot.snapshot_datetime.in_(all_snapshot_times)
        ).delete(synchronize_session=False)

        # Step 5: Regenerate all snapshots
        regenerated = 0
        for snapshot_dt in all_snapshot_times:
            snapshot_service.generate_snapshot(snapshot_dt, db)
            regenerated += 1

            # Batch commit every 24 snapshots for performance
            if regenerated % 24 == 0:
                db.commit()
                print(f"[Recalculation] Regenerated {regenerated}/{len(all_snapshot_times)} snapshots...")

        db.commit()
        print(f"[Recalculation] Regenerated {regenerated} snapshots ({len(transaction_datetimes)} tx times + {len(hourly_datetimes)} hourly)")

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
