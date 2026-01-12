"""
Backfill snapshots for existing transactions.

This script creates snapshots at the exact transaction times for all existing transactions
that don't have corresponding snapshots.
"""

from datetime import datetime
from app.database import SessionLocal
from app.services.recalculation_service import RecalculationService
from app.models.transaction import Transaction

def backfill_snapshots():
    """Backfill snapshots for all existing transactions."""
    db = SessionLocal()
    try:
        print("\n" + "="*80)
        print("BACKFILLING ASSET SNAPSHOTS")
        print("="*80)

        # Get all transactions
        transactions = db.query(Transaction).filter(
            Transaction.deleted_at.is_(None)
        ).order_by(Transaction.date).all()

        if not transactions:
            print("\n No transactions found. Nothing to backfill.")
            return

        print(f"\nFound {len(transactions)} transactions")

        # Get the earliest transaction date
        earliest_date = transactions[0].date
        print(f"Earliest transaction: {earliest_date}")

        # Trigger recalculation from the earliest transaction
        print(f"\nTriggering recalculation from {earliest_date}...")
        recalc_service = RecalculationService()
        recalc_service.recalculate_from_date(earliest_date, db)

        print("\n✅ Backfill complete!")
        print("\nVerifying snapshots...")

        # Verify snapshots were created
        from app.models.asset_snapshot import AssetSnapshot
        snapshots = db.query(AssetSnapshot).order_by(AssetSnapshot.snapshot_datetime).all()

        print(f"\nTotal snapshots: {len(snapshots)}")

        # Show transaction-time snapshots
        tx_times = set(tx.date.replace(second=0, microsecond=0) for tx in transactions)
        tx_snapshots = [s for s in snapshots if s.snapshot_datetime in tx_times]

        print(f"Transaction-time snapshots: {len(tx_snapshots)}")
        for snap in tx_snapshots[:5]:
            print(f"  - {snap.snapshot_datetime} ({snap.total_assets_krw:,.2f} KRW)")
        if len(tx_snapshots) > 5:
            print(f"  ... and {len(tx_snapshots) - 5} more")

        # Show hourly snapshots
        hourly_snapshots = [s for s in snapshots if s.snapshot_datetime.minute == 0]
        print(f"\nHourly snapshots: {len(hourly_snapshots)}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    backfill_snapshots()
