from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./asset_data.db")

# Create engine with SQLite-specific settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
    echo=True  # Log all SQL queries for debugging in Phase 1
)

# Create SessionLocal factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI endpoints.
    Provides database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database schema.
    Creates all tables and configures SQLite pragmas.
    """
    # Import all models to ensure they're registered with Base
    from app.models import account, transaction, holding, market_data, asset_snapshot, recurring_transfer

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Configure SQLite pragmas for better performance and data integrity
    with engine.connect() as conn:
        # Enable foreign key constraints (SQLite defaults to OFF)
        conn.execute(text("PRAGMA foreign_keys = ON;"))

        # Enable WAL mode for better concurrency
        conn.execute(text("PRAGMA journal_mode = WAL;"))

        # Set synchronous mode to NORMAL for better performance
        conn.execute(text("PRAGMA synchronous = NORMAL;"))

        conn.commit()

    print("Database initialized successfully!")
    print(f"Database location: {DATABASE_URL}")


def migrate_account_types(engine):
    """
    Migrate old account type names to new ones.

    Migration mapping:
    - Checking → Deposit
    - Brokerage → Securities
    - Foreign → ForeignCurrency
    - MMF → MoneyMarket

    This migration is idempotent and can be safely run multiple times.
    """
    MIGRATIONS = {
        'Checking': 'Deposit',
        'Brokerage': 'Securities',
        'Foreign': 'ForeignCurrency',
        'MMF': 'MoneyMarket'
    }

    print("\n=== Account Type Migration ===")

    with engine.connect() as conn:
        # Check if there are any accounts to migrate
        total_migrated = 0

        for old_type, new_type in MIGRATIONS.items():
            result = conn.execute(
                text("UPDATE account SET type = :new_type WHERE type = :old_type"),
                {"old_type": old_type, "new_type": new_type}
            )

            if result.rowcount > 0:
                print(f"✓ Migrated {result.rowcount} accounts: {old_type} → {new_type}")
                total_migrated += result.rowcount

        conn.commit()

    if total_migrated == 0:
        print("✓ No accounts to migrate (database already up-to-date or empty)")
    else:
        print(f"✓ Migration complete: {total_migrated} total accounts migrated")

    print("=" * 30 + "\n")


def migrate_date_to_datetime(engine):
    """
    Migrate transaction.date from Date to DateTime.

    Strategy:
    - Existing date-only values are converted to datetime at 09:00 (market open time)
    - This preserves transaction ordering while adding time precision
    - Migration is idempotent and safe to run multiple times

    SQLite doesn't support ALTER COLUMN, so we use table recreation approach.
    """
    print("\n=== Transaction Date to DateTime Migration ===")

    with engine.begin() as conn:
        # Check if migration is needed
        # Try to detect if date column is already datetime by checking if any value has time component
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM "transaction"
            WHERE date LIKE '% %'
        """))
        row = result.fetchone()

        if row and row[0] > 0:
            print("✓ Migration already completed (datetime values detected)")
            print("=" * 30 + "\n")
            return

        # Check if there are any transactions
        result = conn.execute(text('SELECT COUNT(*) FROM "transaction"'))
        row = result.fetchone()
        transaction_count = row[0] if row else 0

        if transaction_count == 0:
            print("✓ No transactions to migrate (database empty)")
            print("=" * 30 + "\n")
            return

        print(f"Migrating {transaction_count} transactions...")

        # Create new transaction table with datetime column
        conn.execute(text("""
            CREATE TABLE transaction_new (
                id INTEGER PRIMARY KEY,
                account_id INTEGER NOT NULL,
                type VARCHAR(20) NOT NULL,
                ticker VARCHAR(20),
                quantity NUMERIC(18, 8),
                price NUMERIC(18, 4),
                amount NUMERIC(18, 2) NOT NULL,
                date DATETIME NOT NULL,
                linked_tx_id INTEGER,
                description TEXT,
                created_at DATETIME NOT NULL,
                deleted_at DATETIME,
                FOREIGN KEY(account_id) REFERENCES account(id) ON DELETE CASCADE,
                FOREIGN KEY(linked_tx_id) REFERENCES "transaction"(id) ON DELETE SET NULL
            )
        """))

        # Copy data, converting date to datetime at 09:00
        conn.execute(text("""
            INSERT INTO transaction_new
            SELECT id, account_id, type, ticker, quantity, price, amount,
                   datetime(date || ' 09:00:00') as date,
                   linked_tx_id, description, created_at, deleted_at
            FROM "transaction"
        """))

        # Drop old table and rename new one
        conn.execute(text('DROP TABLE "transaction"'))
        conn.execute(text('ALTER TABLE transaction_new RENAME TO "transaction"'))

        # Recreate indexes
        conn.execute(text('CREATE INDEX idx_transaction_account ON "transaction"(account_id)'))
        conn.execute(text('CREATE INDEX idx_transaction_date ON "transaction"(date)'))
        conn.execute(text('CREATE INDEX idx_transaction_type ON "transaction"(type)'))
        conn.execute(text('CREATE INDEX idx_transaction_ticker ON "transaction"(ticker)'))
        conn.execute(text('CREATE INDEX idx_transaction_linked ON "transaction"(linked_tx_id)'))

        print(f"✓ Successfully migrated {transaction_count} transactions to datetime format")
        print("✓ All dates converted to 09:00 (market open time)")
        print("✓ Indexes recreated successfully")

    print("=" * 30 + "\n")


def migrate_recurring_transfer_nullable_to_account(engine):
    """
    Migrate recurring_transfer table to make to_account_id nullable.

    This enables external recurring transfers (withdrawals) where to_account_id is NULL.
    - NULL = External withdrawal (Pattern ①)
    - NOT NULL = Internal transfer (Pattern ②)

    Strategy:
    - Drop old check_different_accounts constraint
    - Make to_account_id nullable
    - Validation moved to application layer to handle NULL properly

    SQLite doesn't support ALTER COLUMN, so we use table recreation approach.
    """
    print("\n=== Recurring Transfer External Support Migration ===")

    with engine.begin() as conn:
        # Check if recurring_transfer table exists
        result = conn.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='recurring_transfer'
        """))

        if not result.fetchone():
            print("✓ Table recurring_transfer doesn't exist yet (fresh database)")
            print("=" * 30 + "\n")
            return

        # Check if migration is needed by inspecting table schema
        # SQLite stores NOT NULL constraint in the sql column of sqlite_master
        result = conn.execute(text("""
            SELECT sql FROM sqlite_master
            WHERE type='table' AND name='recurring_transfer'
        """))

        row = result.fetchone()
        table_sql = row[0] if row else ""

        # Check if to_account_id is already nullable (doesn't have NOT NULL)
        # Look for "to_account_id INTEGER," without "NOT NULL"
        if "to_account_id INTEGER," in table_sql or "to_account_id INTEGER)" in table_sql:
            print("✓ Migration already completed (to_account_id is nullable)")
            print("=" * 30 + "\n")
            return

        # Get count of existing recurring transfers
        result = conn.execute(text('SELECT COUNT(*) FROM recurring_transfer'))
        row = result.fetchone()
        transfer_count = row[0] if row else 0

        print(f"Migrating {transfer_count} recurring transfers...")

        # Create new table with nullable to_account_id
        conn.execute(text("""
            CREATE TABLE recurring_transfer_new (
                id INTEGER PRIMARY KEY,
                from_account_id INTEGER NOT NULL,
                to_account_id INTEGER,
                amount NUMERIC(18, 2) NOT NULL,
                day_of_month INTEGER NOT NULL,
                description TEXT,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                last_executed_date DATETIME,
                created_at DATETIME NOT NULL,
                deleted_at DATETIME,
                FOREIGN KEY(from_account_id) REFERENCES account(id) ON DELETE CASCADE,
                FOREIGN KEY(to_account_id) REFERENCES account(id) ON DELETE CASCADE,
                CHECK(day_of_month >= 1 AND day_of_month <= 31),
                CHECK(amount > 0)
            )
        """))

        # Copy all existing data (all will have to_account_id NOT NULL since they're internal transfers)
        conn.execute(text("""
            INSERT INTO recurring_transfer_new
            SELECT * FROM recurring_transfer
        """))

        # Drop old table and rename new one
        conn.execute(text('DROP TABLE recurring_transfer'))
        conn.execute(text('ALTER TABLE recurring_transfer_new RENAME TO recurring_transfer'))

        # Recreate indexes
        conn.execute(text('CREATE INDEX idx_recurring_transfer_from_account ON recurring_transfer(from_account_id)'))
        conn.execute(text('CREATE INDEX idx_recurring_transfer_to_account ON recurring_transfer(to_account_id)'))
        conn.execute(text('CREATE INDEX idx_recurring_transfer_active ON recurring_transfer(is_active)'))

        print(f"✓ Successfully migrated {transfer_count} recurring transfers")
        print("✓ to_account_id is now nullable (NULL = external transfer)")
        print("✓ Indexes recreated successfully")

    print("=" * 30 + "\n")
