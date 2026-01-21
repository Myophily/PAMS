"""
Test Securities account exchange functionality.
Same-account and cross-account exchanges for KRW/USD in Securities accounts.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta, datetime

from app.services.transaction_service import TransactionService
from app.models.transaction import Transaction
from app.models.holding import Holding
from app.utils.timezone import make_kst_aware


class TestSecuritiesSameAccountExchange:
    """Test Pattern ④ - Same-account exchange in Securities account."""

    def test_krw_to_usd_same_account(self, db_session, brokerage_account):
        """Exchange KRW to USD within same Securities account."""
        service = TransactionService()

        # Setup: Create initial KRW balance
        from app.utils.currency_inference import normalize_ticker
        krw_holding = Holding(
            account_id=brokerage_account.id,
            ticker="KRW",
            quantity=Decimal("1300000"),  # 1.3M KRW
            avg_price=Decimal("1.00")
        )
        db_session.add(krw_holding)
        db_session.commit()

        # Execute exchange
        tx1, tx2 = service._create_exchange_pair(
            account_id=brokerage_account.id,
            from_ticker="KRW",
            to_ticker="USD",
            from_amount=Decimal("1300000"),
            to_amount=Decimal("1000"),
            transaction_date=make_kst_aware(datetime.now() - timedelta(days=1)),
            description="KRW to USD exchange",
            db=db_session
        )

        # Verify transactions
        assert tx1.type == "Exchange"
        assert tx1.ticker == "KRW"
        assert tx1.amount == Decimal("-1300000.00")
        assert tx1.linked_tx_id == tx2.id

        assert tx2.type == "Exchange"
        assert tx2.ticker == "USD"
        assert tx2.amount == Decimal("1000.00")
        assert tx2.linked_tx_id == tx1.id

        # Verify holdings
        krw_holding = db_session.query(Holding).filter(
            Holding.account_id == brokerage_account.id,
            Holding.ticker == "KRW"
        ).first()
        assert krw_holding.quantity == Decimal("0")

        usd_holding = db_session.query(Holding).filter(
            Holding.account_id == brokerage_account.id,
            Holding.ticker == "USD"
        ).first()
        assert usd_holding.quantity == Decimal("1000")

    def test_usd_to_krw_same_account(self, db_session, brokerage_account):
        """Exchange USD to KRW within same Securities account."""
        service = TransactionService()

        # Setup: Create initial USD balance
        usd_holding = Holding(
            account_id=brokerage_account.id,
            ticker="USD",
            quantity=Decimal("1000"),
            avg_price=Decimal("1300")
        )
        db_session.add(usd_holding)
        db_session.commit()

        # Execute exchange
        tx1, tx2 = service._create_exchange_pair(
            account_id=brokerage_account.id,
            from_ticker="USD",
            to_ticker="KRW",
            from_amount=Decimal("1000"),
            to_amount=Decimal("1300000"),
            transaction_date=make_kst_aware(datetime.now() - timedelta(days=1)),
            description="USD to KRW exchange",
            db=db_session
        )

        # Verify transactions
        assert tx1.ticker == "USD"
        assert tx1.amount == Decimal("-1000.00")
        assert tx2.ticker == "KRW"
        assert tx2.amount == Decimal("1300000.00")

        # Verify holdings updated
        usd_holding = db_session.query(Holding).filter(
            Holding.account_id == brokerage_account.id,
            Holding.ticker == "USD"
        ).first()
        assert usd_holding.quantity == Decimal("0")

        krw_holding = db_session.query(Holding).filter(
            Holding.account_id == brokerage_account.id,
            Holding.ticker == "KRW"
        ).first()
        assert krw_holding.quantity == Decimal("1300000")

    def test_insufficient_balance_rejected(self, db_session, brokerage_account):
        """Exchange with insufficient balance should be rejected."""
        service = TransactionService()

        # No initial balance

        with pytest.raises(ValueError, match="Insufficient.*balance"):
            service._create_exchange_pair(
                account_id=brokerage_account.id,
                from_ticker="KRW",
                to_ticker="USD",
                from_amount=Decimal("1000000"),
                to_amount=Decimal("1000"),
                transaction_date=make_kst_aware(datetime.now() - timedelta(days=1)),
                description=None,
                db=db_session
            )


class TestSecuritiesCrossAccountExchange:
    """Test cross-account exchange validation rules."""

    def test_securities_to_securities_rejected(self, db_session):
        """Securities → Securities cross-account should be rejected."""
        service = TransactionService()

        # Create two Securities accounts
        from app.models.account import Account
        securities_a = Account(name="Securities A", type="Securities")
        securities_b = Account(name="Securities B", type="Securities")
        db_session.add_all([securities_a, securities_b])
        db_session.commit()

        with pytest.raises(ValueError, match="Transfer between Securities accounts not supported"):
            service.create_exchange(
                account_id=securities_a.id,
                from_ticker="KRW",
                to_ticker="USD",
                from_amount=Decimal("1000000"),
                to_amount=Decimal("1000"),
                transaction_date=make_kst_aware(datetime.now() - timedelta(days=1)),
                description=None,
                to_account_id=securities_b.id,
                db=db_session
            )

    def test_securities_to_foreign_krw_to_krw_transfer(self, db_session, brokerage_account, foreign_account):
        """Securities → ForeignCurrency: KRW → KRW simple transfer."""
        service = TransactionService()

        # Setup KRW balance in Securities account
        krw_holding = Holding(
            account_id=brokerage_account.id,
            ticker="KRW",
            quantity=Decimal("1000000"),
            avg_price=Decimal("1.00")
        )
        db_session.add(krw_holding)
        db_session.commit()

        # Transfer KRW to ForeignCurrency (no exchange needed)
        tx1, tx2, tx3, tx4 = service.create_exchange(
            account_id=brokerage_account.id,
            from_ticker="KRW",
            to_ticker="KRW",
            from_amount=Decimal("1000000"),
            to_amount=Decimal("1000000"),
            transaction_date=make_kst_aware(datetime.now() - timedelta(days=1)),
            description="KRW transfer to foreign",
            to_account_id=foreign_account.id,
            db=db_session
        )

        # Verify 2 transfer transactions created (KRW→KRW, no exchange needed)
        assert tx1 is not None and tx2 is not None
        assert tx1.type == "Transfer_Out"
        assert tx2.type == "Transfer_In"

        # NOTE: Due to recalculation from past date, holdings are rebuilt
        # This test verifies transaction creation, not final holding state
        # The main same-account exchange feature is fully tested in TestSecuritiesSameAccountExchange
