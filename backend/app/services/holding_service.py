"""
Holding service for managing account holdings (computed state).

CRITICAL: Holdings are ALWAYS computed from transaction history.
         Never manually modify holding quantities or avg_price.
"""

from sqlalchemy.orm import Session
from app.models.holding import Holding
from app.utils.decimal_helpers import to_decimal
from decimal import Decimal
from typing import List, Optional


class HoldingService:
    """
    Service for managing holdings (computed state derived from transactions).

    Holdings represent the current state of assets in an account.
    They are ALWAYS computed from the transaction log, never manually edited.
    """

    def get_or_create_cash_holding(self, account_id: int, db: Session) -> Holding:
        """
        DEPRECATED: Get CASH holding (auto-converted to KRW).

        Use get_or_create_holding(account_id, "KRW", db) instead.

        Args:
            account_id: Account ID
            db: Database session

        Returns:
            KRW Holding record

        Examples:
            >>> holding = service.get_or_create_cash_holding(1, db)
            >>> holding.ticker
            'KRW'  # Auto-converted from legacy CASH
        """
        import warnings
        warnings.warn(
            "get_or_create_cash_holding is deprecated. Use get_or_create_holding with explicit ticker.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_or_create_holding(account_id, "KRW", db)

    def get_or_create_holding(
        self,
        account_id: int,
        ticker: str,
        db: Session
    ) -> Holding:
        """
        Get holding for account + ticker, create if not exists.

        Automatically normalizes legacy CASH ticker to appropriate currency
        based on account type.

        Args:
            account_id: Account ID
            ticker: Ticker symbol (stock, currency, etc.)
            db: Database session

        Returns:
            Holding record

        Examples:
            >>> holding = service.get_or_create_holding(1, "AAPL", db)
            >>> holding.ticker
            'AAPL'
            >>> holding.quantity
            Decimal('0')  # Initially zero

            >>> # Legacy CASH auto-converted
            >>> holding = service.get_or_create_holding(1, "CASH", db)
            >>> holding.ticker
            'KRW'  # Auto-normalized for Deposit account
        """
        from app.utils.currency_inference import normalize_ticker
        from app.models.account import Account

        # Get account for normalization context
        account = db.query(Account).get(account_id)
        if account:
            ticker = normalize_ticker(ticker, account.type)

        holding = db.query(Holding).filter(
            Holding.account_id == account_id,
            Holding.ticker == ticker
        ).first()

        if not holding:
            holding = Holding(
                account_id=account_id,
                ticker=ticker,
                quantity=to_decimal(0, precision=8),
                avg_price=to_decimal(0, precision=4)
            )
            db.add(holding)
            db.flush()

        return holding

    def get_all_holdings_for_account(
        self,
        account_id: int,
        db: Session,
        include_zero: bool = False
    ) -> List[Holding]:
        """
        Get all holdings for an account.

        Args:
            account_id: Account ID
            db: Database session
            include_zero: If True, include holdings with zero quantity (default: False)

        Returns:
            List of holdings

        Examples:
            >>> holdings = service.get_all_holdings_for_account(1, db)
            >>> len(holdings)
            3  # CASH, AAPL, TSLA (non-zero holdings only)

            >>> all_holdings = service.get_all_holdings_for_account(1, db, include_zero=True)
            >>> len(all_holdings)
            5  # Includes holdings that were sold completely
        """
        query = db.query(Holding).filter(Holding.account_id == account_id)

        if not include_zero:
            query = query.filter(Holding.quantity != 0)

        return query.all()

    def get_holding(
        self,
        account_id: int,
        ticker: str,
        db: Session
    ) -> Optional[Holding]:
        """
        Get a specific holding (returns None if not exists).

        Args:
            account_id: Account ID
            ticker: Ticker symbol
            db: Database session

        Returns:
            Holding record or None

        Examples:
            >>> holding = service.get_holding(1, "AAPL", db)
            >>> if holding:
            ...     print(holding.quantity)
            ... else:
            ...     print("Holding not found")
        """
        return db.query(Holding).filter(
            Holding.account_id == account_id,
            Holding.ticker == ticker
        ).first()

    def validate_sufficient_balance(
        self,
        account_id: int,
        ticker: str,
        required_qty: Decimal,
        db: Session
    ) -> None:
        """
        Validate that an account has sufficient balance for a transaction.

        Args:
            account_id: Account ID
            ticker: Ticker symbol
            required_qty: Required quantity
            db: Database session

        Raises:
            ValueError: If insufficient balance

        Examples:
            >>> # This will succeed if balance >= 1000
            >>> service.validate_sufficient_balance(1, "CASH", Decimal("1000"), db)

            >>> # This will raise ValueError if balance < 1000
            >>> service.validate_sufficient_balance(1, "CASH", Decimal("1000"), db)
            ValueError: Insufficient CASH balance. Required: 1000, Available: 500
        """
        holding = self.get_or_create_holding(account_id, ticker, db)

        if holding.quantity < required_qty:
            raise ValueError(
                f"Insufficient {ticker} balance. "
                f"Required: {required_qty}, Available: {holding.quantity}"
            )

    def get_total_holdings_value(
        self,
        account_id: int,
        current_prices: dict,
        db: Session
    ) -> Decimal:
        """
        Calculate total value of all holdings in an account.

        Args:
            account_id: Account ID
            current_prices: Dict of {ticker: current_price}
            db: Database session

        Returns:
            Total value of all holdings

        Examples:
            >>> prices = {"CASH": Decimal("1"), "AAPL": Decimal("150"), "TSLA": Decimal("200")}
            >>> total = service.get_total_holdings_value(1, prices, db)
            >>> total
            Decimal('15000.00')  # Example: 1000 cash + 10 AAPL + 20 TSLA
        """
        holdings = self.get_all_holdings_for_account(account_id, db, include_zero=False)

        total_value = Decimal("0")
        for holding in holdings:
            if holding.ticker == "CASH":
                # CASH has value = quantity (1:1)
                total_value += holding.quantity
            elif holding.ticker in current_prices:
                # Stock/currency has value = quantity × price
                total_value += holding.quantity * current_prices[holding.ticker]

        return total_value.quantize(Decimal("0.01"))

    def delete_zero_holdings(self, account_id: int, db: Session) -> int:
        """
        Delete holdings with zero quantity (cleanup).

        This is optional cleanup - holdings with zero quantity don't affect calculations.

        Args:
            account_id: Account ID
            db: Database session

        Returns:
            Number of holdings deleted

        Examples:
            >>> count = service.delete_zero_holdings(1, db)
            >>> print(f"Deleted {count} zero-quantity holdings")
        """
        result = db.query(Holding).filter(
            Holding.account_id == account_id,
            Holding.quantity == 0,
            Holding.ticker != "CASH"  # Never delete CASH holding
        ).delete()

        db.flush()
        return result
