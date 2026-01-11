#!/usr/bin/env python3
"""
Database reset script for development.

WARNING: This will delete ALL data and DROP ALL tables!
Use this for a clean slate before major schema changes.
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import init_db, engine
from sqlalchemy import text


def reset_database():
    """Drop all tables and recreate schema."""

    print("\n" + "=" * 50)
    print("DATABASE RESET SCRIPT")
    print("=" * 50)
    print("\n⚠️  WARNING: This will DELETE ALL DATA and DROP ALL TABLES!")
    print("This includes:")
    print("  - All accounts, transactions, and holdings")
    print("  - All asset snapshots")
    print("  - All market data cache")
    print("  - All recurring transfers")
    print("  - APScheduler job data")
    print("\nYou will need to re-enter or import all data after this.")
    print("\n" + "=" * 50)

    confirm = input("\nType 'yes' to confirm database reset: ")
    if confirm.lower() != "yes":
        print("Aborted.")
        return

    print("\n🗑️  Dropping all tables...")

    with engine.begin() as conn:
        # Get all table names
        result = conn.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """))

        tables = [row[0] for row in result.fetchall()]

        if not tables:
            print("  No tables to drop (database already empty)")
        else:
            # Drop each table (quote table names to handle reserved keywords like "transaction")
            for table in tables:
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}"'))
                print(f"  ✓ Dropped {table}")

    print("\n🔧 Recreating schema...")
    init_db()

    print("\n✅ Database reset complete!")
    print(f"   Location: {os.getenv('DATABASE_URL', 'sqlite:///./asset_data.db')}")
    print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    try:
        reset_database()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
