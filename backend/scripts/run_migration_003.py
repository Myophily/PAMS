#!/usr/bin/env python3
"""
Run migration 003: CASH → KRW/USD conversion.

Usage:
    python scripts/run_migration_003.py [--dry-run]
"""

import sys
import argparse
from pathlib import Path
from sqlalchemy import create_engine, text

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import DATABASE_URL


def run_migration(dry_run: bool = False):
    """Run the migration script."""
    engine = create_engine(DATABASE_URL)

    migration_file = Path(__file__).parent.parent / "migrations" / "003_cash_to_krw_migration.sql"

    with open(migration_file) as f:
        migration_sql = f.read()

    with engine.connect() as conn:
        if dry_run:
            print("[DRY RUN] Would execute migration:")
            print(migration_sql)
            print("\n" + "="*80 + "\n")

            # Show what would change
            result = conn.execute(text(
                "SELECT 'Holdings' as table_name, ticker, COUNT(*) as count "
                "FROM holding WHERE ticker = 'CASH' GROUP BY ticker "
                "UNION ALL "
                "SELECT 'Transactions', ticker, COUNT(*) "
                "FROM `transaction` WHERE ticker = 'CASH' GROUP BY ticker"
            ))

            print("Current CASH ticker counts:")
            rows = result.fetchall()
            if rows:
                for row in rows:
                    print(f"  {row[0]}: {row[1]} = {row[2]}")
            else:
                print("  No CASH tickers found in database")

            print("\n" + "="*80)
            print("\nTo execute this migration, run without --dry-run flag")

        else:
            print("Executing migration...")
            print("="*80)

            # Execute migration
            # Split by semicolon but handle PRAGMA and BEGIN/COMMIT properly
            statements = []
            current_statement = []

            for line in migration_sql.split('\n'):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('--'):
                    continue

                current_statement.append(line)

                # Execute when we hit a semicolon
                if line.endswith(';'):
                    statement = ' '.join(current_statement)
                    if statement and not statement.startswith('--'):
                        try:
                            conn.execute(text(statement))
                        except Exception as e:
                            print(f"Error executing statement: {statement[:100]}...")
                            print(f"Error: {e}")
                            raise
                    current_statement = []

            conn.commit()

            # Verify
            print("\nVerifying migration...")
            result = conn.execute(text(
                "SELECT ticker, COUNT(*) as count FROM holding "
                "WHERE ticker IN ('CASH', 'KRW', 'USD') GROUP BY ticker"
            ))

            print("\nPost-migration ticker counts (Holdings):")
            for row in result:
                print(f"  {row[0]}: {row[1]}")

            result = conn.execute(text(
                "SELECT ticker, COUNT(*) as count FROM `transaction` "
                "WHERE ticker IN ('CASH', 'KRW', 'USD') GROUP BY ticker"
            ))

            print("\nPost-migration ticker counts (Transactions):")
            for row in result:
                print(f"  {row[0]}: {row[1]}")

            # Check for any remaining CASH
            result = conn.execute(text(
                "SELECT COUNT(*) as count FROM holding WHERE ticker = 'CASH'"
            ))
            cash_count = result.fetchone()[0]

            if cash_count > 0:
                print(f"\n⚠️  WARNING: {cash_count} CASH holdings remain!")
            else:
                print("\n✅ Migration completed successfully! No CASH tickers remain.")

            print("="*80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CASH to KRW migration")
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would change without executing')
    args = parser.parse_args()

    try:
        run_migration(dry_run=args.dry_run)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
