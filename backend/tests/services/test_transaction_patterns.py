"""
Service layer tests for the 4 core transaction patterns.

These tests verify that transaction creation follows the correct patterns
and maintains data integrity invariants.

Pattern ① Income/Expense: 1 tx → 1 holding → total assets CHANGE
Pattern ② Transfer: 2 linked tx → 2 holdings → total assets UNCHANGED
Pattern ③ Buy/Sell: 1 tx → 2 holdings → total assets UNCHANGED (at tx time)
Pattern ④ Exchange: 2 linked tx (same account) → 2 holdings → total assets UNCHANGED
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from freezegun import freeze_time

from app.services.transaction_service import TransactionService
from app.models.transaction import Transaction
from app.models.holding import Holding


# =============================================================================
# PATTERN ① PURE INCOME/EXPENSE TESTS
# =============================================================================

class TestPattern1IncomeExpense:
    """Test Pattern ① - Single account, total assets CHANGE."""

    def test_deposit_increases_cash_balance(self, db_session, checking_account, get_cash_balance):
        """Deposit should increase CASH holding."""
        service = TransactionService()

        # Create deposit
        tx = service.create_deposit(
            account_id=checking_account.id,
            amount=Decimal("1000000"),
            transaction_date=date.today(),
            description="Test deposit",
            db=db_session
        )

        # Verify transaction created
        assert tx.type == "Deposit"
        assert tx.amount == Decimal("1000000.00")

        # Verify CASH holding increased
        balance = get_cash_balance(checking_account)
        assert balance == Decimal("1000000.00")

    def test_multiple_deposits_accumulate(self, db_session, checking_account, get_cash_balance):
        """Multiple deposits should accumulate."""
        service = TransactionService()

        # First deposit
        service.create_deposit(
            account_id=checking_account.id,
            amount=Decimal("500000"),
            transaction_date=date.today(),
            description="First",
            db=db_session
        )

        # Second deposit
        service.create_deposit(
            account_id=checking_account.id,
            amount=Decimal("300000"),
            transaction_date=date.today(),
            description="Second",
            db=db_session
        )

        # Total should be sum
        balance = get_cash_balance(checking_account)
        assert balance == Decimal("800000.00")

    def test_withdrawal_decreases_cash_balance(self, db_session, checking_account, create_deposit, get_cash_balance):
        """Withdrawal should decrease CASH holding."""
        service = TransactionService()

        # Setup: deposit first
        create_deposit(checking_account, "1000000")

        # Withdraw
        tx = service.create_withdrawal(
            account_id=checking_account.id,
            amount=Decimal("300000"),
            transaction_date=date.today(),
            description="Test withdrawal",
            db=db_session
        )

        # Verify transaction created (amount stored as negative)
        assert tx.type == "Withdrawal"
        assert tx.amount == Decimal("-300000.00")

        # Verify CASH holding decreased
        balance = get_cash_balance(checking_account)
        assert balance == Decimal("700000.00")

    def test_withdrawal_insufficient_balance_fails(self, db_session, checking_account, create_deposit):
        """Withdrawal exceeding balance should fail."""
        service = TransactionService()

        # Setup: small deposit
        create_deposit(checking_account, "100000")

        # Attempt large withdrawal
        with pytest.raises(ValueError, match="Insufficient.*balance"):
            service.create_withdrawal(
                account_id=checking_account.id,
                amount=Decimal("200000"),  # More than balance
                transaction_date=date.today(),
                description="Over-withdrawal",
                db=db_session
            )

    def test_dividend_increases_cash_and_records_ticker(self, db_session, brokerage_account, create_deposit, get_cash_balance):
        """Dividend should increase CASH and record ticker."""
        service = TransactionService()

        # Setup: initial balance
        create_deposit(brokerage_account, "100000")

        # Receive dividend
        tx = service.create_dividend(
            account_id=brokerage_account.id,
            ticker="AAPL",
            amount=Decimal("5000"),
            transaction_date=date.today(),
            description="Q4 dividend",
            db=db_session
        )

        # Verify transaction
        assert tx.type == "Dividend"
        assert tx.ticker == "AAPL"
        assert tx.amount == Decimal("5000.00")

        # Verify CASH increased
        balance = get_cash_balance(brokerage_account)
        assert balance == Decimal("105000.00")


# =============================================================================
# PATTERN ② SIMPLE TRANSFER TESTS
# =============================================================================

class TestPattern2Transfer:
    """Test Pattern ② - Two accounts, total assets UNCHANGED."""

    def test_transfer_creates_two_linked_transactions(self, db_session, account_pair, create_deposit):
        """Transfer should create two bidirectionally linked transactions."""
        service = TransactionService()
        account_a, account_b = account_pair

        # Setup: add cash to account_a
        create_deposit(account_a, "1000000")

        # Transfer
        tx_out, tx_in = service.create_transfer(
            from_account_id=account_a.id,
            to_account_id=account_b.id,
            amount=Decimal("300000"),
            transaction_date=date.today(),
            description="Transfer test",
            db=db_session
        )

        # Verify two transactions created
        assert tx_out.type == "Transfer_Out"
        assert tx_in.type == "Transfer_In"

        # Verify bidirectional linking
        assert tx_out.linked_tx_id == tx_in.id
        assert tx_in.linked_tx_id == tx_out.id

    def test_transfer_amounts_balance_to_zero(self, db_session, account_pair, create_deposit):
        """Transfer amounts should sum to zero."""
        service = TransactionService()
        account_a, account_b = account_pair

        # Setup
        create_deposit(account_a, "1000000")

        # Transfer
        tx_out, tx_in = service.create_transfer(
            from_account_id=account_a.id,
            to_account_id=account_b.id,
            amount=Decimal("300000"),
            transaction_date=date.today(),
            description="Balance test",
            db=db_session
        )

        # Verify amounts balance
        assert tx_out.amount == Decimal("-300000.00")
        assert tx_in.amount == Decimal("300000.00")
        assert tx_out.amount + tx_in.amount == Decimal("0")

    def test_transfer_updates_both_account_balances(self, db_session, account_pair, create_deposit, get_cash_balance):
        """Transfer should update both account balances."""
        service = TransactionService()
        account_a, account_b = account_pair

        # Setup: initial balances
        create_deposit(account_a, "1000000")
        create_deposit(account_b, "500000")

        # Transfer 300,000 from A to B
        service.create_transfer(
            from_account_id=account_a.id,
            to_account_id=account_b.id,
            amount=Decimal("300000"),
            transaction_date=date.today(),
            description="Balance update test",
            db=db_session
        )

        # Verify balances
        assert get_cash_balance(account_a) == Decimal("700000.00")   # 1M - 300K
        assert get_cash_balance(account_b) == Decimal("800000.00")   # 500K + 300K

    def test_transfer_total_assets_unchanged(self, db_session, account_pair, create_deposit, get_total_assets):
        """CRITICAL: Transfer should NOT change total assets."""
        service = TransactionService()
        account_a, account_b = account_pair

        # Setup
        create_deposit(account_a, "1000000")
        create_deposit(account_b, "500000")

        # Get initial total
        initial_total = get_total_assets()
        assert initial_total == Decimal("1500000")

        # Transfer
        service.create_transfer(
            from_account_id=account_a.id,
            to_account_id=account_b.id,
            amount=Decimal("300000"),
            transaction_date=date.today(),
            description="Total assets test",
            db=db_session
        )

        # Verify total unchanged
        final_total = get_total_assets()
        assert final_total == initial_total  # MUST BE UNCHANGED

    def test_transfer_insufficient_balance_fails(self, db_session, account_pair, create_deposit):
        """Transfer exceeding source balance should fail."""
        service = TransactionService()
        account_a, account_b = account_pair

        # Setup: small balance
        create_deposit(account_a, "100000")

        # Attempt large transfer
        with pytest.raises(ValueError, match="Insufficient.*balance"):
            service.create_transfer(
                from_account_id=account_a.id,
                to_account_id=account_b.id,
                amount=Decimal("200000"),
                transaction_date=date.today(),
                description="Over-transfer",
                db=db_session
            )

    def test_transfer_to_same_account_fails(self, db_session, checking_account, create_deposit):
        """Transfer to same account should fail validation."""
        service = TransactionService()

        # Setup
        create_deposit(checking_account, "1000000")

        # Attempt transfer to self
        with pytest.raises(ValueError, match="same account"):
            service.create_transfer(
                from_account_id=checking_account.id,
                to_account_id=checking_account.id,  # Same as from
                amount=Decimal("300000"),
                transaction_date=date.today(),
                description="Self-transfer",
                db=db_session
            )


# =============================================================================
# PATTERN ③ BUY/SELL TESTS
# =============================================================================

class TestPattern3BuySell:
    """Test Pattern ③ - Asset form conversion, total assets UNCHANGED at tx time."""

    def test_buy_creates_stock_holding_and_decreases_cash(self, db_session, brokerage_account, create_deposit, get_cash_balance, get_holding):
        """Buy should create stock holding and decrease CASH."""
        service = TransactionService()

        # Setup: deposit cash
        create_deposit(brokerage_account, "2000")

        # Buy stock
        tx = service.create_buy(
            account_id=brokerage_account.id,
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("150.00"),
            transaction_date=date.today(),
            description="Buy test",
            db=db_session
        )

        # Verify transaction
        assert tx.type == "Buy"
        assert tx.ticker == "AAPL"
        assert tx.quantity == Decimal("10.00000000")
        assert tx.price == Decimal("150.0000")

        # Verify CASH decreased
        cash = get_cash_balance(brokerage_account)
        assert cash == Decimal("500.00")  # 2000 - 1500

        # Verify stock holding created
        holding = get_holding(brokerage_account, "AAPL")
        assert holding is not None
        assert holding.quantity == Decimal("10.00000000")
        assert holding.avg_price == Decimal("150.0000")

    def test_buy_weighted_average_price(self, db_session, brokerage_account, create_deposit, get_holding):
        """Multiple buys should calculate weighted average price."""
        service = TransactionService()

        # Setup
        create_deposit(brokerage_account, "3000")

        # First buy: 10 @ $100
        service.create_buy(
            account_id=brokerage_account.id,
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("100.00"),
            transaction_date=date.today(),
            description="First buy",
            db=db_session
        )

        holding = get_holding(brokerage_account, "AAPL")
        assert holding.avg_price == Decimal("100.0000")

        # Second buy: 5 @ $120
        service.create_buy(
            account_id=brokerage_account.id,
            ticker="AAPL",
            quantity=Decimal("5"),
            price=Decimal("120.00"),
            transaction_date=date.today(),
            description="Second buy",
            db=db_session
        )

        # Verify weighted average
        holding = get_holding(brokerage_account, "AAPL")
        # (10 × 100 + 5 × 120) / 15 = 106.6667
        assert holding.avg_price == Decimal("106.6667")
        assert holding.quantity == Decimal("15.00000000")

    def test_sell_preserves_average_price(self, db_session, brokerage_account, create_deposit, get_holding):
        """CRITICAL: Selling should NOT change average price."""
        service = TransactionService()

        # Setup: deposit and buy
        create_deposit(brokerage_account, "2000")
        service.create_buy(
            account_id=brokerage_account.id,
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("100.00"),
            transaction_date=date.today(),
            description="Setup",
            db=db_session
        )

        original_avg_price = get_holding(brokerage_account, "AAPL").avg_price

        # Sell half at different price
        service.create_sell(
            account_id=brokerage_account.id,
            ticker="AAPL",
            quantity=Decimal("5"),
            price=Decimal("150.00"),  # Selling at profit
            transaction_date=date.today(),
            description="Sell test",
            db=db_session
        )

        # Verify average price UNCHANGED
        holding = get_holding(brokerage_account, "AAPL")
        assert holding.avg_price == original_avg_price  # MUST NOT CHANGE
        assert holding.quantity == Decimal("5.00000000")  # Half sold

    def test_sell_increases_cash(self, db_session, brokerage_account, create_deposit, get_cash_balance):
        """Sell should increase CASH holding."""
        service = TransactionService()

        # Setup: deposit and buy
        create_deposit(brokerage_account, "1500")
        service.create_buy(
            account_id=brokerage_account.id,
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("100.00"),
            transaction_date=date.today(),
            description="Setup",
            db=db_session
        )

        # CASH after buy: 1500 - 1000 = 500
        assert get_cash_balance(brokerage_account) == Decimal("500.00")

        # Sell
        service.create_sell(
            account_id=brokerage_account.id,
            ticker="AAPL",
            quantity=Decimal("5"),
            price=Decimal("120.00"),
            transaction_date=date.today(),
            description="Sell",
            db=db_session
        )

        # CASH after sell: 500 + 600 = 1100
        assert get_cash_balance(brokerage_account) == Decimal("1100.00")

    def test_sell_insufficient_quantity_fails(self, db_session, brokerage_account, create_deposit):
        """Selling more than owned should fail."""
        service = TransactionService()

        # Setup: deposit and buy small amount
        create_deposit(brokerage_account, "1000")
        service.create_buy(
            account_id=brokerage_account.id,
            ticker="AAPL",
            quantity=Decimal("5"),
            price=Decimal("100.00"),
            transaction_date=date.today(),
            description="Setup",
            db=db_session
        )

        # Attempt to sell more than owned
        with pytest.raises(ValueError, match="Insufficient.*balance"):
            service.create_sell(
                account_id=brokerage_account.id,
                ticker="AAPL",
                quantity=Decimal("10"),  # More than 5 owned
                price=Decimal("120.00"),
                transaction_date=date.today(),
                description="Over-sell",
                db=db_session
            )


# =============================================================================
# PATTERN ④ EXCHANGE TESTS
# =============================================================================

class TestPattern4Exchange:
    """Test Pattern ④ - Currency conversion, same account, total assets UNCHANGED."""

    def test_exchange_creates_two_linked_transactions_same_account(self, db_session, foreign_account, create_deposit):
        """Exchange should create two linked transactions for same account."""
        service = TransactionService()

        # Setup: add CASH which is default currency
        create_deposit(foreign_account, "1300000")

        # Exchange CASH → USD (using CASH as from_ticker since that's what deposit creates)
        tx_sell, tx_buy = service.create_exchange(
            account_id=foreign_account.id,
            from_ticker="CASH",
            to_ticker="USD",
            from_amount=Decimal("1300000"),
            to_amount=Decimal("1000"),
            transaction_date=date.today(),
            description="Exchange test",
            db=db_session
        )

        # Verify both transactions for SAME account
        assert tx_sell.account_id == foreign_account.id
        assert tx_buy.account_id == foreign_account.id

        # Verify bidirectional linking
        assert tx_sell.linked_tx_id == tx_buy.id
        assert tx_buy.linked_tx_id == tx_sell.id

    def test_exchange_updates_currency_holdings(self, db_session, foreign_account, create_deposit, get_holding):
        """Exchange should update both currency holdings."""
        service = TransactionService()

        # Setup: add CASH
        create_deposit(foreign_account, "1300000")

        # Exchange CASH → USD
        service.create_exchange(
            account_id=foreign_account.id,
            from_ticker="CASH",
            to_ticker="USD",
            from_amount=Decimal("1300000"),
            to_amount=Decimal("1000"),
            transaction_date=date.today(),
            description="Currency exchange",
            db=db_session
        )

        # Verify CASH decreased (should be deleted or zero)
        cash_holding = get_holding(foreign_account, "CASH")
        if cash_holding:
            assert cash_holding.quantity == Decimal("0")

        # Verify USD increased
        usd_holding = get_holding(foreign_account, "USD")
        assert usd_holding is not None
        assert usd_holding.quantity == Decimal("1000.00000000")


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestTransactionValidation:
    """Test common validation rules across all patterns."""

    def test_future_date_rejected(self, db_session, checking_account):
        """Future transaction dates should be rejected."""
        service = TransactionService()
        future_date = date.today() + timedelta(days=1)

        with pytest.raises(ValueError, match="cannot be in the future"):
            service.create_deposit(
                account_id=checking_account.id,
                amount=Decimal("100000"),
                transaction_date=future_date,
                description="Future date test",
                db=db_session
            )

    def test_negative_amount_rejected(self, db_session, checking_account):
        """Negative amounts should be rejected."""
        service = TransactionService()

        with pytest.raises(ValueError, match="must be positive"):
            service.create_deposit(
                account_id=checking_account.id,
                amount=Decimal("-100000"),  # Negative
                transaction_date=date.today(),
                description="Negative amount test",
                db=db_session
            )

    def test_zero_amount_rejected(self, db_session, checking_account):
        """Zero amounts should be rejected."""
        service = TransactionService()

        with pytest.raises(ValueError, match="must be positive"):
            service.create_deposit(
                account_id=checking_account.id,
                amount=Decimal("0"),  # Zero
                transaction_date=date.today(),
                description="Zero amount test",
                db=db_session
            )

    def test_invalid_account_id_rejected(self, db_session):
        """Invalid account ID should be rejected."""
        service = TransactionService()

        with pytest.raises(ValueError, match="not found"):
            service.create_deposit(
                account_id=99999,  # Non-existent
                amount=Decimal("100000"),
                transaction_date=date.today(),
                description="Invalid account test",
                db=db_session
            )
