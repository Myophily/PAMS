"""
Transaction service implementing the 4 core transaction patterns.

CRITICAL: This is the heart of the application. All financial operations flow through here.

Pattern ① Pure Income/Expense: 1 transaction → 1 holding → total assets CHANGE
Pattern ② Simple Transfer: 2 linked transactions → 2 holdings → total assets UNCHANGED
Pattern ③ Asset Form Conversion: 1 transaction → 2 holdings → total assets UNCHANGED at tx time
Pattern ④ Exchange: 2 linked transactions (same account) → 2 holdings → total assets UNCHANGED at tx time
"""

from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.models.account import Account
from app.services.holding_service import HoldingService
from app.services.transaction_validation import validate_transaction_type
from app.utils.decimal_helpers import to_decimal, validate_positive
from app.utils.date_helpers import validate_transaction_date, is_past_transaction
from app.utils.calculation_engine import (
    calculate_avg_price_on_buy,
    calculate_avg_price_on_sell
)
from decimal import Decimal
from datetime import datetime
from typing import Tuple, Optional, List
from app.utils.timezone import now_kst


class TransactionService:
    """
    Business logic for transaction operations.

    All transaction creation methods follow one of the 4 core patterns.
    """

    def __init__(self):
        self.holding_service = HoldingService()

    # ========== PATTERN ① PURE INCOME/EXPENSE ==========

    def create_deposit(
        self,
        account_id: int,
        amount: Decimal,
        transaction_date: datetime,
        description: Optional[str],
        db: Session,
        auto_commit: bool = True,
        ticker: Optional[str] = None  # NEW: Optional ticker (defaults to "KRW")
    ) -> Transaction:
        """
        Create deposit transaction (Pattern ①).

        Money enters the financial system. Total assets increase.

        Args:
            account_id: Account ID
            amount: Deposit amount (must be positive)
            transaction_date: Date of transaction
            description: Optional user notes
            db: Database session
            auto_commit: Whether to commit the transaction (default: True)
            ticker: Currency ticker (default: "KRW" for backward compatibility)

        Returns:
            Created transaction

        Raises:
            ValueError: If validation fails

        Examples:
            >>> tx = service.create_deposit(
            ...     account_id=1,
            ...     amount=Decimal("1000000"),
            ...     transaction_date=date.today(),
            ...     description="Monthly salary",
            ...     db=db,
            ...     ticker="KRW"
            ... )
            >>> tx.type
            'Deposit'
            >>> tx.ticker
            'KRW'
            >>> tx.amount
            Decimal('1000000.00')
        """
        from app.utils.currency_inference import normalize_ticker, is_currency_ticker

        # Validate
        validate_transaction_date(transaction_date)
        validate_positive(amount, "Deposit amount")

        account = db.query(Account).get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Validate transaction type allowed for account type
        validate_transaction_type(account.type, "Deposit")

        # Determine ticker (default to KRW for backward compatibility)
        if ticker is None:
            ticker = "KRW"

        # Normalize ticker (handle legacy CASH)
        ticker = normalize_ticker(ticker, account.type)

        # Validate ticker is a currency
        if not is_currency_ticker(ticker):
            raise ValueError(f"Deposit ticker must be a currency. Got: {ticker}")

        # Create transaction
        transaction = Transaction(
            account_id=account_id,
            type="Deposit",
            ticker=ticker,  # NOW: Store currency ticker
            quantity=None,
            price=None,
            amount=to_decimal(amount, precision=2),
            date=transaction_date,
            linked_tx_id=None,
            description=description
        )
        db.add(transaction)
        db.flush()

        # Update currency holding (not hardcoded "CASH")
        holding = self.holding_service.get_or_create_holding(account_id, ticker, db)
        holding.quantity += transaction.amount

        # Create snapshot at transaction time
        self._create_transaction_snapshot(transaction_date, db)

        # Trigger recalculation if past transaction
        if is_past_transaction(transaction_date):
            self._trigger_recalculation(transaction_date, db)

        if auto_commit:
            db.commit()
        return transaction

    def create_withdrawal(
        self,
        account_id: int,
        amount: Decimal,
        transaction_date: datetime,
        description: Optional[str],
        db: Session
    ) -> Transaction:
        """
        Create withdrawal transaction (Pattern ①).

        Money leaves the financial system. Total assets decrease.

        Args:
            account_id: Account ID
            amount: Withdrawal amount (must be positive, stored as negative)
            transaction_date: Date of transaction
            description: Optional user notes
            db: Database session

        Returns:
            Created transaction

        Raises:
            ValueError: If validation fails or insufficient balance
        """
        # Validate
        validate_transaction_date(transaction_date)
        validate_positive(amount, "Withdrawal amount")

        # Check sufficient balance
        self.holding_service.validate_sufficient_balance(
            account_id, "CASH", amount, db
        )

        account = db.query(Account).get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Validate transaction type allowed for account type
        validate_transaction_type(account.type, "Withdrawal")

        # Create transaction (negative amount)
        transaction = Transaction(
            account_id=account_id,
            type="Withdrawal",
            ticker=None,
            quantity=None,
            price=None,
            amount=-to_decimal(amount, precision=2),
            date=transaction_date,
            linked_tx_id=None,
            description=description
        )
        db.add(transaction)
        db.flush()

        # Update CASH holding
        cash_holding = self.holding_service.get_or_create_cash_holding(account_id, db)
        cash_holding.quantity += transaction.amount  # Add negative amount

        # Create snapshot at transaction time
        self._create_transaction_snapshot(transaction_date, db)

        # Trigger recalculation if past transaction
        if is_past_transaction(transaction_date):
            self._trigger_recalculation(transaction_date, db)

        db.commit()
        return transaction

    def create_dividend(
        self,
        account_id: int,
        ticker: str,
        amount: Decimal,
        transaction_date: datetime,
        description: Optional[str],
        db: Session
    ) -> Transaction:
        """
        Create dividend transaction (Pattern ①).

        Stock dividend received. Total assets increase.

        Args:
            account_id: Account ID
            ticker: Stock ticker that paid dividend
            amount: Dividend amount received
            transaction_date: Date of transaction
            description: Optional user notes
            db: Database session

        Returns:
            Created transaction

        Raises:
            ValueError: If validation fails
        """
        # Validate
        validate_transaction_date(transaction_date)
        validate_positive(amount, "Dividend amount")

        account = db.query(Account).get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Validate transaction type allowed for account type
        validate_transaction_type(account.type, "Dividend")

        # Create transaction
        transaction = Transaction(
            account_id=account_id,
            type="Dividend",
            ticker=ticker,
            quantity=None,
            price=None,
            amount=to_decimal(amount, precision=2),
            date=transaction_date,
            linked_tx_id=None,
            description=description
        )
        db.add(transaction)
        db.flush()

        # Update CASH holding
        cash_holding = self.holding_service.get_or_create_cash_holding(account_id, db)
        cash_holding.quantity += transaction.amount

        # Create snapshot at transaction time
        self._create_transaction_snapshot(transaction_date, db)

        if is_past_transaction(transaction_date):
            self._trigger_recalculation(transaction_date, db)

        db.commit()
        return transaction

    # ========== PATTERN ② SIMPLE TRANSFER ==========

    def create_transfer(
        self,
        from_account_id: int,
        to_account_id: int,
        amount: Decimal,
        transaction_date: datetime,
        description: Optional[str],
        db: Session
    ) -> Tuple[Transaction, Transaction]:
        """
        Create transfer transactions (Pattern ②).

        Two linked transactions, total assets unchanged.

        Args:
            from_account_id: Source account ID
            to_account_id: Target account ID
            amount: Transfer amount (must be positive)
            transaction_date: Date of transaction
            description: Optional user notes
            db: Database session

        Returns:
            Tuple of (outflow_transaction, inflow_transaction)

        Raises:
            ValueError: If validation fails

        Examples:
            >>> tx_out, tx_in = service.create_transfer(
            ...     from_account_id=1,
            ...     to_account_id=2,
            ...     amount=Decimal("500000"),
            ...     transaction_date=date.today(),
            ...     description="Fund brokerage",
            ...     db=db
            ... )
            >>> tx_out.type
            'Transfer_Out'
            >>> tx_in.type
            'Transfer_In'
            >>> tx_out.linked_tx_id == tx_in.id
            True
            >>> tx_in.linked_tx_id == tx_out.id
            True
        """
        # Validate
        validate_transaction_date(transaction_date)
        validate_positive(amount, "Transfer amount")

        if from_account_id == to_account_id:
            raise ValueError("Cannot transfer to the same account")

        # Check accounts exist
        from_account = db.query(Account).get(from_account_id)
        to_account = db.query(Account).get(to_account_id)

        if not from_account:
            raise ValueError(f"From account {from_account_id} not found")
        if not to_account:
            raise ValueError(f"To account {to_account_id} not found")

        # Validate transaction types allowed for both accounts
        validate_transaction_type(from_account.type, "Transfer_Out")
        validate_transaction_type(to_account.type, "Transfer_In")

        # Check sufficient KRW balance (KRW-only transfer constraint)
        self.holding_service.validate_sufficient_balance(
            from_account_id, "KRW", amount, db
        )

        # Create outflow transaction
        tx_out = Transaction(
            account_id=from_account_id,
            type="Transfer_Out",
            ticker="KRW",
            quantity=None,
            price=None,
            amount=-to_decimal(amount, precision=2),
            date=transaction_date,
            linked_tx_id=None,  # Set after creating tx_in
            description=description or f"Transfer to {to_account.name}"
        )
        db.add(tx_out)
        db.flush()

        # Create inflow transaction
        tx_in = Transaction(
            account_id=to_account_id,
            type="Transfer_In",
            ticker="KRW",
            quantity=None,
            price=None,
            amount=to_decimal(amount, precision=2),
            date=transaction_date,
            linked_tx_id=None,
            description=description or f"Transfer from {from_account.name}"
        )
        db.add(tx_in)
        db.flush()

        # CRITICAL: Link transactions bidirectionally
        tx_out.linked_tx_id = tx_in.id
        tx_in.linked_tx_id = tx_out.id

        # Update KRW holdings (KRW-only transfer constraint)
        cash_out = self.holding_service.get_or_create_krw_cash_holding(from_account_id, db)
        cash_in = self.holding_service.get_or_create_krw_cash_holding(to_account_id, db)

        cash_out.quantity += tx_out.amount  # Decrease
        cash_in.quantity += tx_in.amount    # Increase

        # Verify invariant: total change = 0
        if tx_out.amount + tx_in.amount != 0:
            raise ValueError("Transfer amounts do not balance")

        # Create snapshot at transaction time
        self._create_transaction_snapshot(transaction_date, db)

        if is_past_transaction(transaction_date):
            self._trigger_recalculation(transaction_date, db)

        db.commit()
        return tx_out, tx_in

    # ========== PATTERN ③ ASSET FORM CONVERSION ==========

    def create_buy(
        self,
        account_id: int,
        ticker: str,
        quantity: Decimal,
        price: Decimal,
        price_currency: str = 'USD',
        transaction_date: datetime = None,
        description: Optional[str] = None,
        db: Session = None,
        auto_commit: bool = True
    ) -> Transaction:
        """
        Create buy transaction (Pattern ③).

        Cash decreases, stock quantity increases. Total assets unchanged at transaction time.

        Args:
            account_id: Account ID
            ticker: Stock ticker symbol
            quantity: Number of shares to buy
            price: Price per share
            transaction_date: Date of transaction
            description: Optional user notes
            db: Database session
            auto_commit: If True, commits the transaction (default: True)

        Returns:
            Created transaction

        Raises:
            ValueError: If validation fails or insufficient cash

        Examples:
            >>> tx = service.create_buy(
            ...     account_id=2,
            ...     ticker="AAPL",
            ...     quantity=Decimal("10"),
            ...     price=Decimal("150"),
            ...     transaction_date=date.today(),
            ...     description="Buy Apple",
            ...     db=db
            ... )
            >>> tx.type
            'Buy'
            >>> tx.amount
            Decimal('-1500.00')  # Negative (cash outflow)
        """
        # Validate
        validate_transaction_date(transaction_date)
        validate_positive(quantity, "Quantity")
        validate_positive(price, "Price")

        account = db.query(Account).get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Validate transaction type allowed for account type
        validate_transaction_type(account.type, "Buy")

        # Calculate total cost
        total_cost = quantity * price

        # Check sufficient cash
        self.holding_service.validate_sufficient_balance(
            account_id, "CASH", total_cost, db
        )

        # Create transaction
        transaction = Transaction(
            account_id=account_id,
            type="Buy",
            ticker=ticker,
            quantity=to_decimal(quantity, precision=8),
            price=to_decimal(price, precision=4),
            price_currency=price_currency,
            amount=-to_decimal(total_cost, precision=2),  # Negative (cash outflow)
            date=transaction_date,
            linked_tx_id=None,
            description=description
        )
        db.add(transaction)
        db.flush()

        # Update CASH holding
        cash_holding = self.holding_service.get_or_create_cash_holding(account_id, db)
        cash_holding.quantity += transaction.amount  # Decrease cash

        # Update stock holding
        stock_holding = self.holding_service.get_or_create_holding(account_id, ticker, db)

        # Calculate new average price
        new_avg_price = calculate_avg_price_on_buy(
            stock_holding.quantity,
            stock_holding.avg_price,
            transaction.quantity,
            transaction.price
        )

        stock_holding.quantity += transaction.quantity
        stock_holding.avg_price = new_avg_price
        stock_holding.price_currency = price_currency  # Store price currency with holding

        # Create snapshot at transaction time
        self._create_transaction_snapshot(transaction_date, db)

        if is_past_transaction(transaction_date):
            self._trigger_recalculation(transaction_date, db)

        if auto_commit:
            db.commit()
        return transaction

    def create_sell(
        self,
        account_id: int,
        ticker: str,
        quantity: Decimal,
        price: Decimal,
        price_currency: str = 'USD',
        transaction_date: datetime = None,
        description: Optional[str] = None,
        db: Session = None
    ) -> Transaction:
        """
        Create sell transaction (Pattern ③).

        Stock quantity decreases, cash increases. Average price UNCHANGED.

        Args:
            account_id: Account ID
            ticker: Stock ticker symbol
            quantity: Number of shares to sell
            price: Price per share
            price_currency: Currency of the price (default: USD)
            transaction_date: Date of transaction
            description: Optional user notes
            db: Database session

        Returns:
            Created transaction

        Raises:
            ValueError: If validation fails or insufficient shares
        """
        # Validate
        validate_transaction_date(transaction_date)
        validate_positive(quantity, "Quantity")
        validate_positive(price, "Price")

        account = db.query(Account).get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Validate transaction type allowed for account type
        validate_transaction_type(account.type, "Sell")

        # Check sufficient stock
        self.holding_service.validate_sufficient_balance(
            account_id, ticker, quantity, db
        )

        # Calculate proceeds
        proceeds = quantity * price

        # Create transaction
        transaction = Transaction(
            account_id=account_id,
            type="Sell",
            ticker=ticker,
            quantity=to_decimal(quantity, precision=8),
            price=to_decimal(price, precision=4),
            price_currency=price_currency,
            amount=to_decimal(proceeds, precision=2),  # Positive (cash inflow)
            date=transaction_date,
            linked_tx_id=None,
            description=description
        )
        db.add(transaction)
        db.flush()

        # Update CASH holding
        cash_holding = self.holding_service.get_or_create_cash_holding(account_id, db)
        cash_holding.quantity += transaction.amount  # Increase cash

        # Update stock holding
        stock_holding = self.holding_service.get_or_create_holding(account_id, ticker, db)

        # CRITICAL: Average price UNCHANGED on sell (for cost basis tracking)
        stock_holding.quantity -= transaction.quantity
        # stock_holding.avg_price stays the same!

        # Create snapshot at transaction time
        self._create_transaction_snapshot(transaction_date, db)

        if is_past_transaction(transaction_date):
            self._trigger_recalculation(transaction_date, db)

        db.commit()
        return transaction

    # ========== PATTERN ④ EXCHANGE ==========

    def _create_exchange_pair(
        self,
        account_id: int,
        from_ticker: str,
        to_ticker: str,
        from_amount: Decimal,
        to_amount: Decimal,
        transaction_date: datetime,
        description: Optional[str],
        db: Session
    ) -> Tuple[Transaction, Transaction]:
        """
        Create a pair of linked exchange transactions for same account (Pattern ④).

        Internal helper method that creates two linked Exchange transactions
        within the same account for different currencies.

        Args:
            account_id: Account ID
            from_ticker: Currency being sold
            to_ticker: Currency being bought
            from_amount: Amount of source currency
            to_amount: Amount of target currency
            transaction_date: Date of transaction
            description: Optional user notes
            db: Database session

        Returns:
            Tuple of (sell_transaction, buy_transaction)

        Note:
            This method does NOT commit. Caller must commit.
        """
        # Validate
        validate_transaction_date(transaction_date)
        validate_positive(from_amount, "From amount")
        validate_positive(to_amount, "To amount")

        if from_ticker == to_ticker:
            raise ValueError("Cannot exchange same currency")

        account = db.query(Account).get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Validate transaction type allowed for account type
        validate_transaction_type(account.type, "Exchange")

        # Check sufficient balance in source currency
        self.holding_service.validate_sufficient_balance(
            account_id, from_ticker, from_amount, db
        )

        # Create outflow transaction (currency being sold)
        tx_sell = Transaction(
            account_id=account_id,
            type="Exchange",
            ticker=from_ticker,
            quantity=None,
            price=None,
            amount=-to_decimal(from_amount, precision=2),
            date=transaction_date,
            linked_tx_id=None,
            description=description or f"Exchange {from_ticker} to {to_ticker}"
        )
        db.add(tx_sell)
        db.flush()

        # Create inflow transaction (currency being bought)
        tx_buy = Transaction(
            account_id=account_id,
            type="Exchange",
            ticker=to_ticker,
            quantity=None,
            price=None,
            amount=to_decimal(to_amount, precision=2),
            date=transaction_date,
            linked_tx_id=None,
            description=description or f"Exchange {from_ticker} to {to_ticker}"
        )
        db.add(tx_buy)
        db.flush()

        # Link transactions bidirectionally
        tx_sell.linked_tx_id = tx_buy.id
        tx_buy.linked_tx_id = tx_sell.id

        # Update holdings
        from_holding = self.holding_service.get_or_create_holding(account_id, from_ticker, db)
        to_holding = self.holding_service.get_or_create_holding(account_id, to_ticker, db)

        from_holding.quantity += tx_sell.amount  # Decrease
        to_holding.quantity += tx_buy.amount      # Increase

        return tx_sell, tx_buy

    def create_exchange(
        self,
        account_id: int,
        from_ticker: str,
        to_ticker: str,
        from_amount: Decimal,
        to_amount: Decimal,
        transaction_date: datetime,
        description: Optional[str],
        to_account_id: int,
        db: Session = None
    ) -> Tuple[Transaction, Transaction, Transaction, Transaction]:
        """
        Create cross-account exchange transactions (Pattern ④+②).

        Exchanges always require a target account - same-account exchanges are not supported.
        Creates 4 transactions: Exchange in source account + Transfer between accounts.

        Args:
            account_id: Source account ID
            from_ticker: Currency being sold (e.g., "USD" or "KRW")
            to_ticker: Currency being bought (e.g., "KRW" or "USD")
            from_amount: Amount of source currency
            to_amount: Amount of target currency
            transaction_date: Date of transaction
            description: Optional user notes
            to_account_id: Target account for cross-account transfer (REQUIRED)
            db: Database session

        Returns:
            Tuple of (tx1, tx2, tx3, tx4) - Always 4 transactions

        Raises:
            ValueError: If validation fails (same account, Foreign→Foreign, etc.)

        Example:
            # Cross-account exchange-transfer (Foreign -> Deposit)
            >>> tx1, tx2, tx3, tx4 = service.create_exchange(
            ...     account_id=3,
            ...     from_ticker="USD",
            ...     to_ticker="KRW",
            ...     from_amount=Decimal("100"),
            ...     to_amount=Decimal("130000"),
            ...     transaction_date=date.today(),
            ...     description="Transfer USD to Deposit account",
            ...     to_account_id=2,
            ...     db=db
            ... )
        """
        # Validate that to_account_id is different from account_id
        if to_account_id == account_id:
            raise ValueError(
                "Cross-account exchange required. Cannot exchange within same account. "
                "Exchange must transfer between different accounts."
            )

        # Cross-account exchange-transfer (4 transactions)
        source_account = db.query(Account).get(account_id)
        target_account = db.query(Account).get(to_account_id)

        if not source_account:
            raise ValueError(f"Source account {account_id} not found")
        if not target_account:
            raise ValueError(f"Target account {to_account_id} not found")

        # Disallow Foreign → Foreign
        if (source_account.type == 'ForeignCurrency' and
            target_account.type == 'ForeignCurrency'):
            raise ValueError(
                "Transfer between Foreign Currency accounts not supported. "
                "Please use separate Exchange and Transfer operations."
            )

        # Determine transaction order based on account types
        if source_account.type == 'ForeignCurrency':
            # Foreign → Non-Foreign: Exchange first, then Transfer
            if to_ticker != 'KRW':
                raise ValueError(
                    "Must convert to KRW before transferring to non-Foreign Currency account"
                )

            # Step 1: Exchange foreign currency to KRW in source account
            tx1, tx2 = self._create_exchange_pair(
                account_id=account_id,
                from_ticker=from_ticker,
                to_ticker='KRW',
                from_amount=from_amount,
                to_amount=to_amount,
                transaction_date=transaction_date,
                description=f"Exchange for transfer: {description or ''}",
                db=db
            )

            # Step 2: Transfer KRW from source to target (direct creation, no validation)
            # Create outflow transaction
            tx3 = Transaction(
                account_id=account_id,
                type="Transfer_Out",
                ticker="KRW",
                quantity=None,
                price=None,
                amount=-to_decimal(to_amount, precision=2),
                date=transaction_date,
                linked_tx_id=None,
                description=description or f"Transfer to {target_account.name}"
            )
            db.add(tx3)
            db.flush()

            # Create inflow transaction
            tx4 = Transaction(
                account_id=to_account_id,
                type="Transfer_In",
                ticker="KRW",
                quantity=None,
                price=None,
                amount=to_decimal(to_amount, precision=2),
                date=transaction_date,
                linked_tx_id=None,
                description=description or f"Transfer from {source_account.name}"
            )
            db.add(tx4)
            db.flush()

            # Link transactions bidirectionally
            tx3.linked_tx_id = tx4.id
            tx4.linked_tx_id = tx3.id

            # Update KRW holdings
            cash_out = self.holding_service.get_or_create_krw_cash_holding(account_id, db)
            cash_in = self.holding_service.get_or_create_krw_cash_holding(to_account_id, db)
            cash_out.quantity += tx3.amount
            cash_in.quantity += tx4.amount

            # Create snapshot at transaction time
            self._create_transaction_snapshot(transaction_date, db)

            if is_past_transaction(transaction_date):
                self._trigger_recalculation(transaction_date, db)

            db.commit()
            return tx1, tx2, tx3, tx4

        else:
            # Non-Foreign → Foreign: Transfer first, then Exchange
            if from_ticker != 'KRW':
                raise ValueError(
                    "Must transfer KRW to Foreign Currency account before exchange"
                )

            # Step 1: Transfer KRW from source to target (direct creation, no validation)
            # Create outflow transaction
            tx1 = Transaction(
                account_id=account_id,
                type="Transfer_Out",
                ticker="KRW",
                quantity=None,
                price=None,
                amount=-to_decimal(from_amount, precision=2),
                date=transaction_date,
                linked_tx_id=None,
                description=description or f"Transfer to {target_account.name}"
            )
            db.add(tx1)
            db.flush()

            # Create inflow transaction
            tx2 = Transaction(
                account_id=to_account_id,
                type="Transfer_In",
                ticker="KRW",
                quantity=None,
                price=None,
                amount=to_decimal(from_amount, precision=2),
                date=transaction_date,
                linked_tx_id=None,
                description=description or f"Transfer from {source_account.name}"
            )
            db.add(tx2)
            db.flush()

            # Link transactions bidirectionally
            tx1.linked_tx_id = tx2.id
            tx2.linked_tx_id = tx1.id

            # Update KRW holdings
            cash_out = self.holding_service.get_or_create_krw_cash_holding(account_id, db)
            cash_in = self.holding_service.get_or_create_krw_cash_holding(to_account_id, db)
            cash_out.quantity += tx1.amount
            cash_in.quantity += tx2.amount

            # Step 2: Exchange KRW to foreign currency in target
            tx3, tx4 = self._create_exchange_pair(
                account_id=to_account_id,
                from_ticker='KRW',
                to_ticker=to_ticker,
                from_amount=from_amount,
                to_amount=to_amount,
                transaction_date=transaction_date,
                description=f"Exchange after transfer: {description or ''}",
                db=db
            )

            # Create snapshot at transaction time
            self._create_transaction_snapshot(transaction_date, db)

            if is_past_transaction(transaction_date):
                self._trigger_recalculation(transaction_date, db)

            db.commit()
            return tx1, tx2, tx3, tx4

    def create_interest(
        self,
        account_id: int,
        amount: Decimal,
        transaction_date: datetime,
        description: Optional[str],
        db: Session
    ) -> Transaction:
        """
        Create interest transaction (Pattern ①) for MoneyMarket accounts.

        Interest income from money market or savings accounts. Total assets increase.

        Args:
            account_id: Account ID (must be MoneyMarket type)
            amount: Interest amount (must be positive)
            transaction_date: Date of transaction
            description: Optional user notes
            db: Database session

        Returns:
            Created transaction

        Raises:
            ValueError: If validation fails

        Examples:
            >>> tx = service.create_interest(
            ...     account_id=4,
            ...     amount=Decimal("5000"),
            ...     transaction_date=date.today(),
            ...     description="Monthly interest",
            ...     db=db
            ... )
            >>> tx.type
            'Interest'
            >>> tx.amount
            Decimal('5000.00')
        """
        # Validate
        validate_transaction_date(transaction_date)
        validate_positive(amount, "Interest amount")

        account = db.query(Account).get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Validate transaction type allowed for account type
        validate_transaction_type(account.type, "Interest")

        # Create transaction
        transaction = Transaction(
            account_id=account_id,
            type="Interest",
            ticker=None,
            quantity=None,
            price=None,
            amount=to_decimal(amount, precision=2),
            date=transaction_date,
            linked_tx_id=None,
            description=description
        )
        db.add(transaction)
        db.flush()

        # Update CASH holding (same as deposit)
        cash_holding = self.holding_service.get_or_create_cash_holding(account_id, db)
        cash_holding.quantity += transaction.amount

        # Create snapshot at transaction time
        self._create_transaction_snapshot(transaction_date, db)

        # Trigger recalculation if past transaction
        if is_past_transaction(transaction_date):
            self._trigger_recalculation(transaction_date, db)

        db.commit()
        return transaction

    # ========== HELPER METHODS ==========

    def _create_transaction_snapshot(self, transaction_date: datetime, db: Session):
        """
        Create a snapshot at the exact transaction time.

        This creates a "transaction-time snapshot" in addition to regular hourly snapshots.
        Used when transactions occur at non-hourly times (e.g., 2:24 PM).

        Args:
            transaction_date: Exact datetime of transaction (minute precision)
            db: Database session
        """
        from app.services.snapshot_service import SnapshotService

        snapshot_service = SnapshotService()

        # Truncate to minute precision (remove seconds/microseconds)
        snapshot_datetime = transaction_date.replace(second=0, microsecond=0)

        # Create or update snapshot (handles multiple transactions in same minute)
        print(f"[TransactionService] Creating snapshot at transaction time: {snapshot_datetime}")
        snapshot_service.generate_snapshot(snapshot_datetime, db)

    def _trigger_recalculation(self, start_date: datetime, db: Session):
        """
        Trigger recalculation of holdings and snapshots from a date.

        This is called when a past transaction is inserted, modified, or deleted.

        Args:
            start_date: Date to start recalculation from
            db: Database session
        """
        from app.services.recalculation_service import RecalculationService

        print(f"[TransactionService] Triggering recalculation from {start_date}")
        recalc_service = RecalculationService()
        recalc_service.recalculate_from_date(start_date, db)

    def list_transactions(
        self,
        db: Session,
        account_id: Optional[int] = None,
        type: Optional[str] = None,
        ticker: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Transaction]:
        """
        List transactions with filtering and pagination.

        Args:
            db: Database session
            account_id: Filter by account ID
            type: Filter by transaction type
            ticker: Filter by ticker
            start_date: Filter by date range (inclusive)
            end_date: Filter by date range (inclusive)
            limit: Number of results per page
            offset: Pagination offset

        Returns:
            List of transactions
        """
        query = db.query(Transaction).filter(Transaction.deleted_at.is_(None))

        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        if type:
            query = query.filter(Transaction.type == type)
        if ticker:
            query = query.filter(Transaction.ticker == ticker)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)

        query = query.order_by(Transaction.date.desc(), Transaction.id.desc())
        query = query.limit(limit).offset(offset)

        return query.all()

    def get_transaction(self, transaction_id: int, db: Session) -> Optional[Transaction]:
        """
        Get a single transaction by ID.

        Args:
            transaction_id: Transaction ID
            db: Database session

        Returns:
            Transaction or None
        """
        return db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.deleted_at.is_(None)
        ).first()

    def delete_transaction(self, transaction_id: int, db: Session) -> None:
        """
        Soft delete a transaction.

        Args:
            transaction_id: Transaction ID
            db: Database session

        Raises:
            ValueError: If transaction not found
        """
        from datetime import datetime

        transaction = self.get_transaction(transaction_id, db)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        # Soft delete
        transaction.deleted_at = now_kst()

        # If linked transaction exists, soft delete it too
        if transaction.linked_tx_id:
            linked_tx = self.get_transaction(transaction.linked_tx_id, db)
            if linked_tx:
                linked_tx.deleted_at = now_kst()

        # Trigger recalculation from this date
        self._trigger_recalculation(transaction.date, db)

        db.commit()
