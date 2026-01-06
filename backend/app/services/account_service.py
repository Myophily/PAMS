"""
Account service for account management operations.
"""

from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.holding import Holding
from app.services.transaction_service import TransactionService
from app.services.holding_service import HoldingService
from app.services.market_data_service import MarketDataService
from app.utils.calculation_engine import calculate_unrealized_pl, calculate_total_value, calculate_cost_basis
from app.utils.decimal_helpers import to_decimal
from app.schemas.account_schema import (
    AccountResponse,
    AccountListItemResponse,
    AccountDetailResponse,
    AccountSummaryResponse,
    HoldingResponse
)
from decimal import Decimal
from datetime import date, datetime
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
        currency: str,
        initial_balance: Decimal,
        initial_balance_date: Optional[date],
        db: Session
    ) -> Account:
        """
        Create a new account.

        If initial_balance > 0, creates a Deposit transaction.

        Args:
            name: Account name
            account_type: Account type (Deposit, Securities, ForeignCurrency, MoneyMarket)
            currency: Currency code (KRW, USD, EUR, etc.)
            initial_balance: Initial balance (default: 0)
            initial_balance_date: Date for initial balance (default: today)
            db: Database session

        Returns:
            Created account

        Raises:
            ValueError: If validation fails
        """
        # Validate account type
        valid_types = ["Deposit", "Securities", "ForeignCurrency", "MoneyMarket"]
        if account_type not in valid_types:
            raise ValueError(f"Invalid account type. Must be one of: {valid_types}")

        # Check for duplicate name
        existing = db.query(Account).filter(Account.name == name).first()
        if existing:
            raise ValueError(f"Account with name '{name}' already exists")

        # Create account
        account = Account(
            name=name,
            type=account_type,
            currency=currency
        )
        db.add(account)
        db.flush()

        # If initial balance > 0, create deposit transaction
        if initial_balance > 0:
            balance_date = initial_balance_date or date.today()

            self.transaction_service.create_deposit(
                account_id=account.id,
                amount=initial_balance,
                transaction_date=balance_date,
                description="Initial balance",
                db=db,
                auto_commit=False  # Let parent handle commit
            )

        # Refresh to ensure account is bound to session
        db.refresh(account)
        db.commit()
        return account

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

            # Calculate total balance in account's currency
            balance_raw = sum(h.quantity for h in holdings if h.ticker in ["CASH", account.currency])

            # Quantize based on currency type
            if account.currency == "KRW":
                balance = balance_raw.quantize(Decimal("1"))  # 0 decimals
            else:
                balance = balance_raw.quantize(Decimal("0.01"))  # 2 decimals for USD/EUR

            # Convert to USD for comparison
            if account.currency == "KRW":
                balance_usd = balance / usd_krw_rate
            elif account.currency == "USD":
                balance_usd = balance
            else:
                # TODO: Handle other currencies
                balance_usd = balance

            account_list.append(AccountListItemResponse(
                id=account.id,
                name=account.name,
                type=account.type,
                currency=account.currency,
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
                currency=account.currency,
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

    def delete_account(self, account_id: int, db: Session) -> None:
        """
        Delete an account.

        If account has non-zero holdings, raise error (must liquidate first).
        If account has only zero holdings, hard delete.

        Args:
            account_id: Account ID
            db: Database session

        Raises:
            ValueError: If account not found or has active holdings
        """
        account = db.query(Account).get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Check for active holdings
        holdings = self.holding_service.get_all_holdings_for_account(account_id, db, include_zero=False)

        if holdings:
            # Check if only CASH with zero balance
            if len(holdings) == 1 and holdings[0].ticker == "CASH" and holdings[0].quantity == 0:
                # Allow deletion
                pass
            else:
                raise ValueError(
                    f"Cannot delete account with active holdings. "
                    f"Please liquidate all assets first."
                )

        # Delete holdings
        db.query(Holding).filter(Holding.account_id == account_id).delete()

        # Delete account
        db.delete(account)
        db.commit()

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
