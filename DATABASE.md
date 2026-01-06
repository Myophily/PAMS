# DATABASE.md - Personal Asset Manager

Comprehensive database schema documentation with relationships and constraints.

---

## Overview

**DBMS:** SQLite 3.35+
**Location:** `asset_data.db` in project root
**ORM:** SQLAlchemy 2.0+

---

## Schema Diagram

```
┌─────────────┐
│   Account   │
├─────────────┤
│ id (PK)     │───┐
│ name        │   │
│ type        │   │
│ currency    │   │
│ created_at  │   │
└─────────────┘   │
                  │
                  ├─────────┐
                  │         │
                  ▼         ▼
         ┌──────────────┐ ┌──────────────────┐
         │   Holding    │ │   Transaction    │
         ├──────────────┤ ├──────────────────┤
         │ id (PK)      │ │ id (PK)          │
         │ account_id ◄─┤ │ account_id ◄─────┤
         │ ticker       │ │ type             │
         │ quantity     │ │ ticker           │
         │ avg_price    │ │ quantity         │
         └──────────────┘ │ price            │
                          │ amount           │
                          │ date             │
                          │ linked_tx_id ◄───┼─┐ Self-referencing
                          │ description      │ │
                          │ created_at       │ │
                          │ deleted_at       │◄┘
                          └──────────────────┘
                                    │
                                    │ ticker reference
                                    ▼
                          ┌──────────────────┐
                          │   MarketData     │
                          ├──────────────────┤
                          │ id (PK)          │
                          │ ticker           │
                          │ date             │
                          │ closing_price    │
                          │ exchange_rate    │
                          │ source           │
                          │ fetched_at       │
                          └──────────────────┘

                          ┌──────────────────┐
                          │  AssetSnapshot   │
                          ├──────────────────┤
                          │ id (PK)          │
                          │ date             │
                          │ total_assets_krw │
                          │ total_assets_usd │
                          │ principal        │
                          │ created_at       │
                          └──────────────────┘
```

---

## Tables

### 1. Account

Represents financial accounts (deposit/withdrawal, securities, foreign currency, money market).

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique account identifier |
| `name` | VARCHAR(100) | NOT NULL, UNIQUE | Account display name (e.g., "Toss Checking") |
| `type` | VARCHAR(20) | NOT NULL, CHECK | Account type: `Deposit`, `Securities`, `ForeignCurrency`, `MoneyMarket` |
| `currency` | VARCHAR(3) | NOT NULL | Base currency: `KRW`, `USD`, `EUR`, etc. |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Account creation timestamp |

**Indexes:**
- `idx_account_type` on `type`
- `idx_account_currency` on `currency`

**SQLAlchemy Model:**
```python
from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

class Account(Base):
    __tablename__ = 'account'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(20), nullable=False)
    currency = Column(String(3), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    holdings = relationship("Holding", back_populates="account", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(type.in_(['Deposit', 'Securities', 'ForeignCurrency', 'MoneyMarket']), name='check_account_type'),
    )
```

**Business Rules:**
- Account name must be unique
- Type cannot be changed after creation (would invalidate transaction history)
- Currency cannot be changed after creation

**Account Type Specifications:**

Each account type has specific restrictions on which assets it can hold:

| Account Type | Base Currency | Allowed Holdings | Purpose |
|--------------|---------------|------------------|---------|
| **Deposit** | `KRW` | `CASH` (KRW only) | Deposit/withdrawal account (입출금통장) for daily spending. Linked to household account book. |
| **MoneyMarket** | `KRW` | `CASH` (KRW only) | Money Market Fund (MMF). Earns interest tracked via `Interest` transactions. |
| **ForeignCurrency** | `USD` | `CASH` (USD only) | Foreign currency account (외화통장). Holds USD and supports currency exchange. |
| **Securities** | `KRW` or `USD` | `CASH` (any currency) + Stocks, ETFs, Gold, Bonds, etc. | Full investment account (증권계좌). Can hold multiple currencies and all security types. |

**Validation:**
- `Deposit` and `MoneyMarket` accounts must have `currency='KRW'`
- `ForeignCurrency` accounts must have `currency='USD'`
- `Securities` accounts can have any base currency
- Holdings must respect the allowed asset types for each account type

**Migration Note:**
For existing databases with old account type values (`Checking`, `Brokerage`, `Foreign`, `MMF`), a migration script is available at `backend/migration_rename_account_types.py` to rename them to the new values (`Deposit`, `Securities`, `ForeignCurrency`, `MoneyMarket`).

---

### 2. Holding

Represents current balances of assets (stocks, cash, etc.) in an account. This is a **computed table** - all values are derivable from `Transaction` history.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique holding identifier |
| `account_id` | INTEGER | NOT NULL, FOREIGN KEY | Reference to `Account.id` |
| `ticker` | VARCHAR(20) | NOT NULL | Stock symbol or special value `CASH` |
| `quantity` | DECIMAL(18, 8) | NOT NULL, DEFAULT 0 | Current quantity held |
| `avg_price` | DECIMAL(18, 4) | NOT NULL, DEFAULT 0 | Average purchase price (cost basis per unit) |

**Indexes:**
- `idx_holding_account` on `account_id`
- `idx_holding_ticker` on `ticker`
- **UNIQUE INDEX** on `(account_id, ticker)` - One holding per ticker per account

**SQLAlchemy Model:**
```python
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

class Holding(Base):
    __tablename__ = 'holding'

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    ticker = Column(String(20), nullable=False)
    quantity = Column(Numeric(18, 8), nullable=False, default=0)
    avg_price = Column(Numeric(18, 4), nullable=False, default=0)

    # Relationships
    account = relationship("Account", back_populates="holdings")

    # Constraints
    __table_args__ = (
        UniqueConstraint('account_id', 'ticker', name='uq_account_ticker'),
    )
```

**Special Cases:**
- **CASH holdings:** `ticker = "CASH"`, `avg_price = 1.0` (always)
- **Zero quantity:** When all shares sold, holding remains with `quantity = 0` (for historical avg_price tracking)

**Calculation Logic:**

**Average Price Calculation (Buy):**
```python
def calculate_avg_price_buy(current_qty, current_avg, buy_qty, buy_price):
    """
    Weighted average price calculation.
    Example: Hold 10 @ $100, buy 5 @ $110
    New avg = (10*100 + 5*110) / (10+5) = 1550/15 = $103.33
    """
    total_value = (current_qty * current_avg) + (buy_qty * buy_price)
    total_qty = current_qty + buy_qty
    return total_value / total_qty if total_qty > 0 else 0
```

**Average Price Calculation (Sell):**
```python
def calculate_avg_price_sell(current_qty, current_avg, sell_qty):
    """
    Average price remains unchanged on sell.
    Only quantity decreases.
    """
    return current_avg  # avg_price does NOT change on sell
```

**Business Rules:**
- Holdings are recalculated from transaction logs when a past transaction is inserted
- Negative quantity is not allowed
- CASH holding must always exist for every account

---

### 3. Transaction

Immutable log of all financial events. This is the **source of truth**.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique transaction identifier |
| `account_id` | INTEGER | NOT NULL, FOREIGN KEY | Reference to `Account.id` |
| `type` | VARCHAR(20) | NOT NULL, CHECK | Transaction type (see below) |
| `ticker` | VARCHAR(20) | NULL | Stock symbol or currency code (NULL for deposits/withdrawals) |
| `quantity` | DECIMAL(18, 8) | NULL | Number of shares/units (NULL for cash-only transactions) |
| `price` | DECIMAL(18, 4) | NULL | Price per unit at transaction time (NULL for transfers) |
| `amount` | DECIMAL(18, 2) | NOT NULL | Cash flow amount (negative for outflow, positive for inflow) |
| `date` | DATE | NOT NULL | Actual transaction date (not entry date) |
| `linked_tx_id` | INTEGER | NULL, FOREIGN KEY | Reference to linked transaction (for transfers/exchanges) |
| `description` | TEXT | NULL | User notes |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Entry timestamp |
| `deleted_at` | TIMESTAMP | NULL | Soft delete timestamp |

**Transaction Types:**

| Type | Description | Pattern | Fields Used |
|------|-------------|---------|-------------|
| `Deposit` | Income to account | ① | `amount` (positive) |
| `Withdrawal` | Expense from account | ① | `amount` (negative) |
| `Dividend` | Stock dividend received | ① | `ticker`, `amount` (positive) |
| `Buy` | Purchase securities with cash | ③ | `ticker`, `quantity`, `price`, `amount` (negative) |
| `Sell` | Sell securities for cash | ③ | `ticker`, `quantity`, `price`, `amount` (positive) |
| `Transfer_In` | Receive transfer from another account | ② | `amount` (positive), `linked_tx_id` |
| `Transfer_Out` | Send transfer to another account | ② | `amount` (negative), `linked_tx_id` |
| `Exchange` | Currency conversion | ④ | `ticker`, `amount`, `linked_tx_id` |

**Indexes:**
- `idx_transaction_account` on `account_id`
- `idx_transaction_date` on `date`
- `idx_transaction_type` on `type`
- `idx_transaction_ticker` on `ticker`
- `idx_transaction_linked` on `linked_tx_id`

**SQLAlchemy Model:**
```python
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, CheckConstraint, Text
from sqlalchemy.orm import relationship
from datetime import date, datetime

class Transaction(Base):
    __tablename__ = 'transaction'

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(20), nullable=False)
    ticker = Column(String(20), nullable=True)
    quantity = Column(Numeric(18, 8), nullable=True)
    price = Column(Numeric(18, 4), nullable=True)
    amount = Column(Numeric(18, 2), nullable=False)
    date = Column(Date, nullable=False)
    linked_tx_id = Column(Integer, ForeignKey('transaction.id', ondelete='SET NULL'), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    account = relationship("Account", back_populates="transactions")
    linked_transaction = relationship("Transaction", remote_side=[id], uselist=False)

    # Constraints
    __table_args__ = (
        CheckConstraint(
            type.in_(['Deposit', 'Withdrawal', 'Dividend', 'Buy', 'Sell',
                     'Transfer_In', 'Transfer_Out', 'Exchange']),
            name='check_transaction_type'
        ),
    )
```

**Business Rules:**

**Pattern ① Pure Income/Expense:**
```python
# Deposit example
Transaction(
    account_id=1,
    type="Deposit",
    ticker=None,
    quantity=None,
    price=None,
    amount=1000000.00,  # Positive inflow
    date=date(2024, 1, 15),
    linked_tx_id=None
)
```

**Pattern ② Simple Transfer:**
```python
# Transfer $500 from Account 1 to Account 2
tx_out = Transaction(
    account_id=1,
    type="Transfer_Out",
    amount=-500.00,  # Negative outflow
    date=date(2024, 1, 15)
)
tx_in = Transaction(
    account_id=2,
    type="Transfer_In",
    amount=500.00,  # Positive inflow
    date=date(2024, 1, 15)
)
# Link them
tx_out.linked_tx_id = tx_in.id
tx_in.linked_tx_id = tx_out.id
```

**Pattern ③ Asset Form Conversion:**
```python
# Buy 10 shares of AAPL at $150
Transaction(
    account_id=2,
    type="Buy",
    ticker="AAPL",
    quantity=10,
    price=150.00,
    amount=-1500.00,  # Cash decreases
    date=date(2024, 1, 15)
)
# This updates TWO holdings:
# - CASH: -1500
# - AAPL: +10 shares
```

**Pattern ④ Exchange:**
```python
# Exchange 1,300,000 KRW for 1,000 USD
tx_krw = Transaction(
    account_id=3,
    type="Exchange",
    ticker="KRW",
    amount=-1300000.00,
    date=date(2024, 1, 15)
)
tx_usd = Transaction(
    account_id=3,
    type="Exchange",
    ticker="USD",
    amount=1000.00,
    date=date(2024, 1, 15)
)
tx_krw.linked_tx_id = tx_usd.id
tx_usd.linked_tx_id = tx_krw.id
```

**Validation Rules:**
- `date` cannot be in the future
- For `Buy`/`Sell`: `ticker`, `quantity`, `price` must be provided
- For `Transfer`: `linked_tx_id` must reference another transaction
- For `Deposit`/`Withdrawal`: `amount` must be non-zero
- `amount` for `Buy` must be negative, for `Sell` must be positive

---

### 4. MarketData

Cached external market data (stock prices, exchange rates).

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `ticker` | VARCHAR(20) | NOT NULL | Stock symbol or "USD_KRW" for exchange rates |
| `date` | DATE | NOT NULL | Market data date |
| `closing_price` | DECIMAL(18, 4) | NULL | Stock closing price |
| `exchange_rate` | DECIMAL(18, 6) | NULL | Currency exchange rate |
| `source` | VARCHAR(50) | NOT NULL | Data source: `yahoo_finance`, `alpha_vantage`, `manual` |
| `fetched_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When data was cached |

**Indexes:**
- **UNIQUE INDEX** on `(ticker, date)` - One price per ticker per date

**SQLAlchemy Model:**
```python
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, UniqueConstraint

class MarketData(Base):
    __tablename__ = 'market_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    closing_price = Column(Numeric(18, 4), nullable=True)
    exchange_rate = Column(Numeric(18, 6), nullable=True)
    source = Column(String(50), nullable=False)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('ticker', 'date', name='uq_ticker_date'),
    )
```

**Business Rules:**
- Exchange rates stored as `{BASE}_{QUOTE}` (e.g., `USD_KRW` = 1300 means 1 USD = 1300 KRW)
- Weekend/holiday prices use the previous trading day's closing price
- Manual entries have `source = "manual"`
- Data is never deleted (only appended)

**Example Queries:**
```python
# Get latest USD/KRW exchange rate
latest_rate = db.query(MarketData).filter(
    MarketData.ticker == "USD_KRW"
).order_by(MarketData.date.desc()).first()

# Get stock price for specific date
price = db.query(MarketData).filter(
    MarketData.ticker == "AAPL",
    MarketData.date == date(2024, 1, 15)
).first()
```

---

### 5. AssetSnapshot

Daily total asset value records for charting and performance tracking.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `date` | DATE | NOT NULL, UNIQUE | Snapshot date |
| `total_assets_krw` | DECIMAL(18, 2) | NOT NULL | Total asset value in KRW |
| `total_assets_usd` | DECIMAL(18, 2) | NOT NULL | Total asset value in USD |
| `principal` | DECIMAL(18, 2) | NOT NULL | Total deposited - withdrawn (cost basis) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Snapshot creation time |

**Indexes:**
- **UNIQUE INDEX** on `date`
- `idx_snapshot_date` on `date` for range queries

**SQLAlchemy Model:**
```python
from sqlalchemy import Column, Integer, Numeric, Date, DateTime, UniqueConstraint

class AssetSnapshot(Base):
    __tablename__ = 'asset_snapshot'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True)
    total_assets_krw = Column(Numeric(18, 2), nullable=False)
    total_assets_usd = Column(Numeric(18, 2), nullable=False)
    principal = Column(Numeric(18, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('date', name='uq_snapshot_date'),
    )
```

**Business Rules:**
- Snapshots are generated daily (can be backfilled for historical dates)
- When a past transaction is inserted, snapshots from that date forward are regenerated
- `principal` = sum of all deposits - sum of all withdrawals (excludes market gains/losses)
- Unrealized P/L = `total_assets_krw` - `principal`

**Calculation Logic:**
```python
def generate_snapshot(date: date, db: Session) -> AssetSnapshot:
    """
    Generate asset snapshot for a specific date.
    """
    # Get all holdings as of this date
    all_holdings = get_holdings_at_date(date, db)

    # Calculate total value
    total_krw = 0
    for holding in all_holdings:
        if holding.ticker == "CASH":
            value = holding.quantity  # Cash value is face value
        else:
            price = get_market_price(holding.ticker, date, db)
            value = holding.quantity * price

        # Convert to KRW if needed
        if holding.account.currency != "KRW":
            rate = get_exchange_rate(holding.account.currency, "KRW", date, db)
            value *= rate

        total_krw += value

    # Calculate principal
    principal = calculate_principal(date, db)

    # Convert to USD
    usd_krw_rate = get_exchange_rate("USD", "KRW", date, db)
    total_usd = total_krw / usd_krw_rate

    return AssetSnapshot(
        date=date,
        total_assets_krw=total_krw,
        total_assets_usd=total_usd,
        principal=principal
    )
```

---

## Database Initialization

**SQLite Configuration:**
```sql
-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;

-- Set synchronous mode
PRAGMA synchronous = NORMAL;
```

**SQLAlchemy Configuration:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "sqlite:///./asset_data.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=True  # Log SQL queries (disable in production)
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize database (create tables)
def init_db():
    Base.metadata.create_all(bind=engine)
```

---

## Backup & Recovery

**Backup (SQLite):**
```bash
# Simple file copy
cp asset_data.db asset_data_backup_$(date +%Y%m%d).db

# Or use SQLite backup command
sqlite3 asset_data.db ".backup asset_data_backup.db"
```

**Recovery:**
```bash
# Restore from backup
cp asset_data_backup.db asset_data.db
```

**Cloud Sync:**
- Place `asset_data.db` in Dropbox/Google Drive/iCloud folder
- Automatic versioning and sync across devices

---

## Performance Optimization

**Indexes:**
```sql
-- Account queries
CREATE INDEX idx_account_type ON account(type);
CREATE INDEX idx_account_currency ON account(currency);

-- Transaction queries
CREATE INDEX idx_transaction_account ON transaction(account_id);
CREATE INDEX idx_transaction_date ON transaction(date);
CREATE INDEX idx_transaction_type ON transaction(type);
CREATE INDEX idx_transaction_ticker ON transaction(ticker);

-- Holding queries
CREATE INDEX idx_holding_account ON holding(account_id);
CREATE INDEX idx_holding_ticker ON holding(ticker);
CREATE UNIQUE INDEX uq_account_ticker ON holding(account_id, ticker);

-- Market data queries
CREATE UNIQUE INDEX uq_ticker_date ON market_data(ticker, date);

-- Snapshot queries
CREATE UNIQUE INDEX uq_snapshot_date ON asset_snapshot(date);
```

**Query Optimization Tips:**
- Use `date` range filters with indexes
- Avoid `SELECT *` - specify needed columns
- Use joins instead of multiple queries
- Paginate large result sets (transactions)
- Cache frequently accessed data (current exchange rates)

---

## Data Integrity Checks

**Validation Queries:**

**Check for orphaned holdings:**
```sql
SELECT * FROM holding
WHERE account_id NOT IN (SELECT id FROM account);
```

**Check for broken transaction links:**
```sql
SELECT * FROM transaction
WHERE linked_tx_id IS NOT NULL
AND linked_tx_id NOT IN (SELECT id FROM transaction);
```

**Check for duplicate holdings:**
```sql
SELECT account_id, ticker, COUNT(*) as count
FROM holding
GROUP BY account_id, ticker
HAVING count > 1;
```

**Verify total assets calculation:**
```sql
-- Sum of all holdings should match latest snapshot
SELECT SUM(quantity * avg_price) as calculated_total
FROM holding
WHERE ticker != 'CASH';
```

---

## Migration Strategy

For schema changes:

1. Create backup: `cp asset_data.db asset_data_pre_migration.db`
2. Run ALTER TABLE statements
3. Trigger full recalculation
4. Validate data integrity
5. Test application functionality

**Example Migration (Adding new column):**
```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('transaction', sa.Column('fee', sa.Numeric(18, 2), nullable=True))

def downgrade():
    op.drop_column('transaction', 'fee')
```
