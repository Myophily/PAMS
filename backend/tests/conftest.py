"""
Shared pytest fixtures for Personal Asset Manager testing.

This module provides database fixtures, sample data factories, and utilities
for testing the PAM application with isolated in-memory databases.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from decimal import Decimal
from datetime import date, timedelta
from typing import Generator

from app.database import Base, get_db
from app.main import app
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.holding import Holding
from app.models.market_data import MarketData
from app.models.asset_snapshot import AssetSnapshot


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_engine():
    """
    Create an in-memory SQLite database engine for testing.
    Each test function gets a fresh database.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Required for in-memory SQLite
        echo=False  # Set to True for debugging SQL queries
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Enable foreign key constraints
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON;"))
        conn.commit()

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    Provide a transactional database session for testing.
    Automatically rolls back after each test for isolation.
    """
    connection = test_engine.connect()
    transaction = connection.begin()

    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection
    )
    session = TestSessionLocal()

    yield session

    # Rollback and cleanup
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_client(db_session):
    """
    Provide a FastAPI TestClient with overridden database dependency.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup handled by db_session fixture

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ============================================================================
# ACCOUNT FIXTURES
# ============================================================================

@pytest.fixture
def checking_account(db_session) -> Account:
    """Create a KRW checking account for testing."""
    account = Account(
        name="Test Checking Account",
        type="Deposit",
        currency="KRW"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def brokerage_account(db_session) -> Account:
    """Create a USD brokerage account for testing."""
    account = Account(
        name="Test Brokerage Account",
        type="Securities",
        currency="USD"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def foreign_account(db_session) -> Account:
    """Create a foreign currency account for testing."""
    account = Account(
        name="Test Foreign Account",
        type="ForeignCurrency",
        currency="USD"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def mmf_account(db_session) -> Account:
    """Create an MMF account for testing."""
    account = Account(
        name="Test MMF Account",
        type="MoneyMarket",
        currency="KRW"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def account_pair(db_session) -> tuple[Account, Account]:
    """Create two checking accounts for transfer testing."""
    account_a = Account(
        name="Account A",
        type="Deposit",
        currency="KRW"
    )
    account_b = Account(
        name="Account B",
        type="Deposit",
        currency="KRW"
    )
    db_session.add_all([account_a, account_b])
    db_session.commit()
    db_session.refresh(account_a)
    db_session.refresh(account_b)
    return account_a, account_b


# ============================================================================
# MARKET DATA FIXTURES
# ============================================================================

@pytest.fixture
def mock_market_data(db_session, monkeypatch):
    """
    Mock market data to avoid external API calls during testing.
    Provides pre-defined prices for common test tickers.
    """
    def mock_fetch_stock_price(ticker: str, target_date: date):
        """Return mock stock prices."""
        mock_prices = {
            "AAPL": Decimal("150.00"),
            "GOOGL": Decimal("2800.00"),
            "TSLA": Decimal("200.00"),
            "MSFT": Decimal("380.00"),
            "005930.KS": Decimal("75000.00"),  # Samsung Electronics
        }
        return mock_prices.get(ticker, Decimal("100.00"))

    def mock_fetch_exchange_rate(from_currency: str, to_currency: str, target_date: date):
        """Return mock exchange rates."""
        if from_currency == "USD" and to_currency == "KRW":
            return Decimal("1300.00")
        elif from_currency == "KRW" and to_currency == "USD":
            return Decimal("0.00076923")  # 1/1300
        return Decimal("1.00")

    # Monkey patch market data service
    from app.services import market_data_service
    monkeypatch.setattr(
        market_data_service,
        "fetch_stock_price",
        mock_fetch_stock_price
    )
    monkeypatch.setattr(
        market_data_service,
        "fetch_exchange_rate",
        mock_fetch_exchange_rate
    )

    return {
        "stock_price": mock_fetch_stock_price,
        "exchange_rate": mock_fetch_exchange_rate
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@pytest.fixture
def create_deposit(db_session):
    """
    Factory function to create deposit transactions for testing.
    """
    def _create_deposit(
        account: Account,
        amount: Decimal | float | str,
        transaction_date: date = None
    ) -> Transaction:
        """Create a deposit transaction and update holdings."""
        if transaction_date is None:
            transaction_date = date.today()

        amount = Decimal(str(amount))

        # Create transaction
        transaction = Transaction(
            account_id=account.id,
            type="Deposit",
            ticker="CASH",
            quantity=amount,
            price=Decimal("1.0000"),
            amount=amount,
            date=transaction_date,
            description=f"Test deposit of {amount}"
        )
        db_session.add(transaction)

        # Update or create CASH holding
        holding = db_session.query(Holding).filter(
            Holding.account_id == account.id,
            Holding.ticker == "CASH"
        ).first()

        if holding:
            holding.quantity += amount
        else:
            holding = Holding(
                account_id=account.id,
                ticker="CASH",
                quantity=amount,
                avg_price=Decimal("1.0000")
            )
            db_session.add(holding)

        db_session.commit()
        db_session.refresh(transaction)
        return transaction

    return _create_deposit


@pytest.fixture
def get_cash_balance(db_session):
    """
    Helper to get CASH balance for an account.
    """
    def _get_cash_balance(account: Account) -> Decimal:
        """Return the CASH balance of an account."""
        holding = db_session.query(Holding).filter(
            Holding.account_id == account.id,
            Holding.ticker == "CASH"
        ).first()
        return holding.quantity if holding else Decimal("0")

    return _get_cash_balance


@pytest.fixture
def get_holding(db_session):
    """
    Helper to get a specific holding for an account.
    """
    def _get_holding(account: Account, ticker: str) -> Holding | None:
        """Return the holding for a specific ticker."""
        return db_session.query(Holding).filter(
            Holding.account_id == account.id,
            Holding.ticker == ticker
        ).first()

    return _get_holding


@pytest.fixture
def get_total_assets(db_session):
    """
    Helper to calculate total assets across all accounts.
    Simplified for testing (assumes all in KRW or same currency).
    """
    def _get_total_assets() -> Decimal:
        """Sum all holdings' values."""
        holdings = db_session.query(Holding).all()
        total = Decimal("0")
        for holding in holdings:
            # Simplified: just sum quantity (assumes all same currency)
            # In real app, would convert to base currency
            if holding.ticker == "CASH" or holding.ticker in ["KRW", "USD"]:
                total += holding.quantity
            else:
                # For stocks, use quantity * avg_price as proxy
                total += holding.quantity * holding.avg_price
        return total

    return _get_total_assets


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_transactions(db_session, checking_account, create_deposit):
    """
    Create a set of sample transactions for complex testing scenarios.
    """
    transactions = []

    # Day 1: Initial deposit
    tx1 = create_deposit(checking_account, "10000000", date(2024, 1, 1))
    transactions.append(tx1)

    # Day 2: Another deposit
    tx2 = create_deposit(checking_account, "5000000", date(2024, 1, 2))
    transactions.append(tx2)

    return transactions


@pytest.fixture
def today():
    """Return today's date for consistent testing."""
    return date.today()


@pytest.fixture
def yesterday():
    """Return yesterday's date."""
    return date.today() - timedelta(days=1)


@pytest.fixture
def last_week():
    """Return date from one week ago."""
    return date.today() - timedelta(days=7)
