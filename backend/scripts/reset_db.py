#!/usr/bin/env python3
"""
Reset the database by clearing all user data.
Deletes data from:
- account (cascades to transaction, holding)
- asset_snapshot

Keeps:
- market_data
"""

import sys
import argparse
from pathlib import Path
from sqlalchemy import create_engine, text

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import DATABASE_URL


def reset_db(dry_run: bool = False, force: bool = False):
    """Reset the database."""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        print("Checking data counts...")
        
        # Check current counts
        tables = ['account', 'transaction', 'holding', 'asset_snapshot']
        counts = {}
        for table in tables:
            # Handle reserved word "transaction"
            table_name = f"`{table}`" if table == "transaction" else table
            res = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            counts[table] = res.scalar()
            
        print("\nCurrent data:")
        for table, count in counts.items():
            print(f"  {table}: {count}")
            
        if dry_run:
            print("\n[DRY RUN] Would delete all records from the above tables.")
            return

        # Confirm
        if not force:
            confirm = input("\n⚠️  ARE YOU SURE YOU WANT TO DELETE ALL USER DATA? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Aborted.")
                return

        print("\nDeleting data...")
        
        # Disable foreign keys temporarily for SQLite if needed, but CASCADE should handle it.
        # However, deleting from child tables explicitly is clearer.
        # But since we have CASCADE on account->transactions/holdings, deleting account is enough for those.
        # AssetSnapshot is separate.
        
        try:
            # Delete Asset Snapshots
            conn.execute(text("DELETE FROM asset_snapshot"))
            print("  Deleted asset_snapshot")
            
            # Delete Accounts (cascades to transactions and holdings)
            conn.execute(text("DELETE FROM account"))
            print("  Deleted account (and cascaded to transaction, holding)")
            
            conn.commit()
            print("\n✅ Database reset successfully.")
            
        except Exception as e:
            print(f"\n❌ Error resetting database: {e}")
            conn.rollback()
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset database (clear user data)")
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without executing')
    args = parser.parse_args()

    try:
        reset_db(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\nAborted.")
