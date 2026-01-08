"""
Migration script to convert CASH holdings to explicit currency tickers (KRW, USD, etc.)

This fixes the issue where "CASH" ticker loses currency information.
After this migration, all cash holdings will have explicit currency tickers.
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.account import Account
from app.models.holding import Holding


def migrate_cash_holdings(db: Session):
    """Convert CASH holdings to explicit currency tickers."""

    # Find all CASH holdings
    cash_holdings = db.query(Holding).filter(Holding.ticker == "CASH").all()

    print(f"Found {len(cash_holdings)} CASH holdings to migrate")

    migrated_count = 0

    for holding in cash_holdings:
        # Get the account
        account = db.query(Account).filter(Account.id == holding.account_id).first()

        if not account:
            print(f"WARNING: Holding {holding.id} has no account, skipping")
            continue

        # Determine what currency this should be based on account type
        if account.type in ["Deposit", "Savings", "MoneyMarket"]:
            new_ticker = "KRW"
        elif account.type == "ForeignCurrency":
            new_ticker = "USD"
        elif account.type == "Securities":
            # Check other holdings to determine primary currency
            other_holdings = db.query(Holding).filter(
                Holding.account_id == account.id,
                Holding.ticker != "CASH"
            ).all()

            # If has KRW-priced stocks, assume KRW cash
            has_krw_stocks = any(h.price_currency == "KRW" for h in other_holdings if h.price_currency)
            new_ticker = "KRW" if has_krw_stocks else "USD"
        else:
            print(f"WARNING: Unknown account type {account.type}, defaulting to KRW")
            new_ticker = "KRW"

        # Check if there's already a holding with the new ticker
        existing = db.query(Holding).filter(
            Holding.account_id == account.id,
            Holding.ticker == new_ticker
        ).first()

        old_ticker = holding.ticker

        if existing and existing.id != holding.id:
            # Merge: add CASH quantity to existing currency holding
            print(f"  Account {account.id} ({account.type}): Merging {old_ticker} ({holding.quantity}) into {new_ticker} ({existing.quantity})")
            existing.quantity += holding.quantity
            # Delete the CASH holding
            db.delete(holding)
        else:
            # Simple rename
            holding.ticker = new_ticker
            holding.price_currency = None  # Currency holdings don't have price_currency
            print(f"  Account {account.id} ({account.type}): {old_ticker} → {new_ticker}")

        migrated_count += 1

    # Commit changes
    db.commit()

    print(f"\nMigration complete! Migrated {migrated_count} holdings")

    # Verify
    remaining_cash = db.query(Holding).filter(Holding.ticker == "CASH").count()
    if remaining_cash > 0:
        print(f"WARNING: {remaining_cash} CASH holdings still remain!")
    else:
        print("✓ All CASH holdings successfully migrated")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        migrate_cash_holdings(db)
    finally:
        db.close()
