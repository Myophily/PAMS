"""
Account service for account management operations.
"""

from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.holding import Holding
from app.models.transaction import Transaction
from app.services.transaction_service import TransactionService
from app.services.holding_service import HoldingService
from app.services.market_data_service import MarketDataService
from app.services.recalculation_service import RecalculationService
from app.utils.calculation_engine import calculate_unrealized_pl, calculate_total_value, calculate_cost_basis
from app.utils.decimal_helpers import to_decimal
from app.utils.currency_inference import infer_currency_from_holdings, get_decimal_places
from app.schemas.account_schema import (
    AccountResponse,
    AccountListItemResponse,
    AccountDetailResponse,
    AccountSummaryResponse,
    HoldingResponse
)
from decimal import Decimal
from datetime import datetime
from typing import List, Optional


class AccountService:
    """
    Service for managing accounts.
    """

    def __init__(self):
        self.transaction_service = TransactionService()
        self.holding_service = HoldingService()
        self.market_data_service = MarketDataService()

    def create_account(
        self,
        name: str,
        account_type: str,
        initial_balance: Optional[Decimal],
        initial_balance_date: Optional[datetime],
        initial_holdings: Optional[List],
        db: Session
    ) -> Account:
        """
        Create a new account with optional initial balance or multiple initial holdings.

        For Securities accounts with initial_holdings:
        - Creates multiple Buy/Deposit transactions for each holding
        For other accounts with initial_balance > 0:
        - Creates a single Deposit transaction

        Args:
            name: Account name
            account_type: Account type (Deposit, Securities, ForeignCurrency, MoneyMarket)
            initial_balance: Simple initial balance (for non-Securities or backwards compat)
            initial_balance_date: Date for initial transactions (default: now)
            initial_holdings: List of initial holdings with per-stock price_currency
            db: Database session

        Returns:
            Created account

        Raises:
            ValueError: If validation fails
        """
        # Validate account type
        valid_types = ["Deposit", "Securities", "ForeignCurrency", "MoneyMarket", "Savings"]
        if account_type not in valid_types:
            raise ValueError(f"Invalid account type. Must be one of: {valid_types}")

        # Check for duplicate name
        existing = db.query(Account).filter(Account.name == name).first()
        if existing:
            raise ValueError(f"Account with name '{name}' already exists")

        # Create account
        account = Account(
            name=name,
            type=account_type
        )
        db.add(account)
        db.flush()

        # Determine which initialization method to use
        balance_date = initial_balance_date or datetime.now().replace(second=0, microsecond=0)

        # Convert deprecated initial_balance to initial_holdings format
        if initial_balance and initial_balance > 0 and (not initial_holdings or len(initial_holdings) == 0):
            from app.schemas.account_schema import InitialHoldingItem

            # Determine appropriate currency ticker
            if account_type in ["Deposit", "Savings", "MoneyMarket"]:
                ticker = "KRW"
            elif account_type in ["Securities", "ForeignCurrency"]:
                ticker = "USD"  # Default for foreign currency/securities
            else:
                ticker = "KRW"

            # Convert to holdings format
            initial_holdings = [
                InitialHoldingItem(
                    ticker=ticker,
                    quantity=initial_balance,
                    price=None
                )
            ]

            print(f"[DEPRECATED] Converted initial_balance to initial_holdings with ticker {ticker}")

        if initial_holdings and len(initial_holdings) > 0:
            # Create initial holdings (now for ALL account types)
            self._create_initial_holdings(
                account_id=account.id,
                account_type=account_type,  # Pass account type for validation
                holdings=initial_holdings,
                transaction_date=balance_date,
                db=db
            )

        # Refresh to ensure account is bound to session
        db.refresh(account)
        db.commit()
        return account

    def _create_initial_holdings(
        self,
        account_id: int,
        account_type: str,
        holdings: List,
        transaction_date: datetime,
        db: Session
    ) -> None:
        """
        Create initial holdings for any account type.

        Account type determines transaction types and ticker normalization:
        - Deposit/Savings/MoneyMarket: Creates Deposit transactions for KRW only
        - ForeignCurrency: Creates Deposit transactions for foreign currencies
        - Securities: Creates Deposit for currencies, Buy for stocks/commodities

        Handles legacy CASH ticker by auto-converting to appropriate currency.

        Args:
            account_id: Account ID
            account_type: Account type for validation and normalization
            holdings: List of InitialHoldingItem objects
            transaction_date: Date for all transactions
            db: Database session

        Raises:
            ValueError: If validation fails
        """
        from app.utils.currency_inference import normalize_ticker, is_currency_ticker
        from app.schemas.account_schema import InitialHoldingItem

        # Normalize all tickers (convert legacy CASH)
        normalized_holdings = []
        for h in holdings:
            normalized_ticker = normalize_ticker(h.ticker, account_type)
            normalized_holdings.append(
                InitialHoldingItem(
                    ticker=normalized_ticker,
                    quantity=h.quantity,
                    price=h.price
                )
            )

        holdings = normalized_holdings

        # For Securities accounts: Auto-inject cash if needed
        if account_type == "Securities":
            has_cash = any(is_currency_ticker(h.ticker) for h in holdings)

            if not has_cash:
                # Calculate total cost of non-currency assets
                total_buy_cost = sum(
                    h.quantity * h.price for h in holdings
                    if not is_currency_ticker(h.ticker) and h.price is not None
                )

                if total_buy_cost > 0:
                    # Inject KRW cash to cover purchases
                    cash_holding = InitialHoldingItem(
                        ticker='KRW',
                        quantity=total_buy_cost,
                        price=None
                    )
                    holdings = [cash_holding] + list(holdings)

        # Sort: Currencies first, then stocks alphabetically
        sorted_holdings = sorted(
            holdings,
            key=lambda h: (not is_currency_ticker(h.ticker), h.ticker)
        )

        for holding in sorted_holdings:
            if is_currency_ticker(holding.ticker):
                # Create Deposit transaction for currency holdings
                self.transaction_service.create_deposit(
                    account_id=account_id,
                    amount=holding.quantity,
                    transaction_date=transaction_date,
                    description=f"Initial {holding.ticker} balance",
                    db=db,
                    auto_commit=False,
                    ticker=holding.ticker  # NEW: Pass ticker to create_deposit
                )
            else:
                # Create Buy transaction for non-currency assets (stocks, commodities)
                # Only valid for Securities accounts (validation already done in schema)
                price_currency = holding.price_currency or 'USD'  # Default to USD
                self.transaction_service.create_buy(
                    account_id=account_id,
                    ticker=holding.ticker,
                    quantity=holding.quantity,
                    price=holding.price,
                    price_currency=price_currency,
                    transaction_date=transaction_date,
                    description=f"Initial holding: {holding.ticker}",
                    db=db,
                    auto_commit=False
                )

    def list_accounts(self, db: Session) -> List[AccountListItemResponse]:
        """
        List all accounts with balance summary.

        Args:
            db: Database session

        Returns:
            List of accounts with balance info
        """
        accounts = db.query(Account).all()

        # Get default exchange rate (USD/KRW)
        usd_krw_rate = to_decimal(1300, precision=4)  # Placeholder

        account_list = []
        for account in accounts:
            # Get holdings for this account
            holdings = self.holding_service.get_all_holdings_for_account(account.id, db, include_zero=False)

            # Infer currency from holdings
            inferred_currency = infer_currency_from_holdings(holdings, account.type)

            # Calculate total balance in account's currency
            balance_raw = sum((h.quantity for h in holdings if h.ticker in ["CASH", inferred_currency]), Decimal("0"))

            # Quantize based on currency type
            decimal_places = get_decimal_places(inferred_currency)
            balance = balance_raw.quantize(Decimal(decimal_places))

            # Convert to USD for comparison
            if inferred_currency == "KRW":
                balance_usd = balance / usd_krw_rate
            elif inferred_currency == "USD":
                balance_usd = balance
            else:
                # TODO: Handle other currencies
                balance_usd = balance

            account_list.append(AccountListItemResponse(
                id=account.id,
                name=account.name,
                type=account.type,
                balance=balance,
                balance_usd=balance_usd.quantize(Decimal("0.01")),
                holdings_count=len(holdings),
                created_at=account.created_at
            ))

        return account_list

    def get_account_detail(
        self,
        account_id: int,
        db: Session
    ) -> AccountDetailResponse:
        """
        Get detailed account information with holdings and summary.

        Args:
            account_id: Account ID
            db: Database session

        Returns:
            Detailed account response

        Raises:
            ValueError: If account not found
        """
        account = db.query(Account).get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Get all holdings
        holdings = self.holding_service.get_all_holdings_for_account(account_id, db, include_zero=False)

        # Infer currency from holdings
        inferred_currency = infer_currency_from_holdings(holdings, account.type)

        # Build holding responses with market data
        holding_responses = []
        total_value = Decimal("0")
        cash_balance = Decimal("0")
        total_cost_basis = Decimal("0")
        total_unrealized_pl = Decimal("0")

        for holding in holdings:
            if holding.ticker == "CASH":
                # CASH holding
                cash_balance = holding.quantity
                total_value += holding.quantity

                holding_responses.append(HoldingResponse(
                    id=holding.id,
                    account_id=holding.account_id,
                    ticker="CASH",
                    ticker_name="Cash",
                    quantity=holding.quantity,
                    avg_price=Decimal("1.0"),
                    current_price=Decimal("1.0"),
                    current_value=holding.quantity,
                    cost_basis=holding.quantity,
                    unrealized_pl=Decimal("0"),
                    unrealized_pl_percent=Decimal("0")
                ))
            else:
                # Stock/currency holding
                # Get current price (placeholder - use avg_price for now)
                current_price = self.market_data_service.get_latest_price(holding.ticker, db)
                if not current_price:
                    current_price = holding.avg_price  # Fallback

                # Calculate values
                cost_basis = calculate_cost_basis(holding.quantity, holding.avg_price)
                current_value = calculate_total_value(holding.quantity, current_price)
                unrealized_pl, unrealized_pl_percent = calculate_unrealized_pl(
                    holding.quantity,
                    holding.avg_price,
                    current_price
                )

                total_value += current_value
                total_cost_basis += cost_basis
                total_unrealized_pl += unrealized_pl

                holding_responses.append(HoldingResponse(
                    id=holding.id,
                    account_id=holding.account_id,
                    ticker=holding.ticker,
                    ticker_name=None,  # TODO: Add ticker name lookup
                    quantity=holding.quantity,
                    avg_price=holding.avg_price,
                    current_price=current_price,
                    current_value=current_value,
                    cost_basis=cost_basis,
                    unrealized_pl=unrealized_pl,
                    unrealized_pl_percent=unrealized_pl_percent
                ))

        # Calculate invested amount (non-cash cost basis)
        invested_amount = total_cost_basis

        # Calculate overall P/L percentage
        if invested_amount > 0:
            unrealized_pl_percent = (total_unrealized_pl / invested_amount * 100).quantize(Decimal("0.01"))
        else:
            unrealized_pl_percent = Decimal("0")

        # Build response
        return AccountDetailResponse(
            account=AccountResponse(
                id=account.id,
                name=account.name,
                type=account.type,
                created_at=account.created_at
            ),
            summary=AccountSummaryResponse(
                total_value=total_value,
                cash_balance=cash_balance,
                invested_amount=invested_amount,
                unrealized_pl=total_unrealized_pl,
                unrealized_pl_percent=unrealized_pl_percent
            ),
            holdings=holding_responses
        )

    def update_account(
        self,
        account_id: int,
        name: str,
        db: Session
    ) -> Account:
        """
        Update account name.

        Type and currency cannot be changed after creation.

        Args:
            account_id: Account ID
            name: New name
            db: Database session

        Returns:
            Updated account

        Raises:
            ValueError: If account not found or name already exists
        """
        account = db.query(Account).get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Check for duplicate name
        existing = db.query(Account).filter(
            Account.name == name,
            Account.id != account_id
        ).first()
        if existing:
            raise ValueError(f"Account with name '{name}' already exists")

        account.name = name
        db.commit()
        return account

    def _collect_deletion_stats(self, account_id: int, db: Session) -> dict:
        """
        Collect statistics about what will be deleted.

        Args:
            account_id: Account ID
            db: Database session

        Returns:
            Dictionary with deletion statistics
        """
        # Count transactions (excluding soft-deleted)
        transactions = db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.deleted_at.is_(None)
        ).all()

        # Count holdings
        holdings = self.holding_service.get_all_holdings_for_account(
            account_id, db, include_zero=False
        )

        # Count linked transactions that will be orphaned
        linked_tx_count = sum(1 for tx in transactions if tx.linked_tx_id is not None)

        return {
            'account_id': account_id,
            'transactions_deleted': len(transactions),
            'holdings_deleted': len(holdings),
            'linked_transactions_broken': linked_tx_count
        }

    def _find_affected_accounts(self, account_id: int, db: Session) -> set:
        """
        Find accounts that have transactions linked to this account.

        These accounts will have their linked_tx_id set to NULL,
        so they need recalculation if they were Pattern ② (Transfer) or
        Pattern ④ (Exchange) transactions.

        Args:
            account_id: Account ID being deleted
            db: Database session

        Returns:
            Set of affected account IDs
        """
        # Get all transaction IDs from the account being deleted
        this_account_tx_ids = db.query(Transaction.id).filter(
            Transaction.account_id == account_id,
            Transaction.deleted_at.is_(None)
        ).subquery()

        # Find transactions in OTHER accounts that link to these
        affected_txs = db.query(Transaction).filter(
            Transaction.account_id != account_id,
            Transaction.linked_tx_id.in_(this_account_tx_ids),
            Transaction.deleted_at.is_(None)
        ).all()

        return set(tx.account_id for tx in affected_txs)

    def _get_earliest_transaction_date(self, account_id: int, db: Session) -> Optional[datetime]:
        """
        Get the earliest transaction date for recalculation.

        Args:
            account_id: Account ID
            db: Database session

        Returns:
            Earliest transaction date or None if no transactions
        """
        earliest_tx = db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.deleted_at.is_(None)
        ).order_by(Transaction.date.asc()).first()

        return earliest_tx.date if earliest_tx else None

    def delete_account(self, account_id: int, db: Session) -> dict:
        """
        Delete an account and all its transactions.

        DESTRUCTIVE: This permanently deletes:
        - All transactions for this account
        - All holdings (via CASCADE)
        - The account itself

        SIDE EFFECTS:
        - Transactions in OTHER accounts linked to this account's transactions
          will have their linked_tx_id set to NULL (via ondelete='SET NULL')
        - May trigger recalculation for affected accounts

        Args:
            account_id: Account ID to delete
            db: Database session

        Returns:
            Dictionary with deletion statistics

        Raises:
            ValueError: If account not found
        """
        account = db.query(Account).get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Collect deletion statistics BEFORE deletion
        stats = self._collect_deletion_stats(account_id, db)

        # Find accounts that have linked transactions with this account
        affected_account_ids = self._find_affected_accounts(account_id, db)

        # Get the earliest transaction date (for recalculation)
        earliest_tx_date = self._get_earliest_transaction_date(account_id, db)

        # Hard delete account (CASCADE will handle holdings and transactions)
        # linked_tx_id will be set to NULL automatically via ondelete='SET NULL'
        db.delete(account)
        db.flush()  # Execute deletion before recalculation

        # Trigger recalculation for affected accounts if needed
        if affected_account_ids and earliest_tx_date:
            recalc_service = RecalculationService()
            recalc_service.recalculate_from_date(earliest_tx_date, db)

        db.commit()
        return stats

    def get_account(self, account_id: int, db: Session) -> Optional[Account]:
        """
        Get a single account by ID.

        Args:
            account_id: Account ID
            db: Database session

        Returns:
            Account or None
        """
        return db.query(Account).get(account_id)
