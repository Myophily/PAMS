"""
Test script to verify the asset snapshot fix.

Tests:
1. Current transaction creates immediate snapshot at exact time
2. Past transaction regenerates both transaction-time and hourly snapshots
"""

from datetime import datetime, timedelta
from decimal import Decimal
from app.database import SessionLocal
from app.services.transaction_service import TransactionService
from app.services.snapshot_service import SnapshotService
from app.models.account import Account
from app.models.asset_snapshot import AssetSnapshot

def test_current_transaction_snapshot():
    """Test that a current transaction creates a snapshot at the exact time."""
    db = SessionLocal()
    try:
        print("\n" + "="*80)
        print("TEST 1: Current Transaction Snapshot")
        print("="*80)

        # Clean up any existing test accounts
        db.query(Account).filter(Account.name.like("Test %")).delete(synchronize_session=False)
        db.commit()

        # Create a test account
        account = Account(
            name="Test Deposit Account",
            type="Deposit"
        )
        db.add(account)
        db.commit()
        print(f"✓ Created test account: {account.name} (ID: {account.id})")

        # Create transaction at current time (use current minute, just ensure it's not :00)
        now = datetime.now()
        transaction_time = now.replace(second=0, microsecond=0)

        # If we're exactly at :00, add 1 minute to test non-hourly snapshot
        if transaction_time.minute == 0:
            transaction_time = transaction_time.replace(minute=1)

        print(f"\n📝 Creating deposit at {transaction_time}")

        service = TransactionService()
        transaction = service.create_deposit(
            account_id=account.id,
            amount=Decimal("1000000"),
            transaction_date=transaction_time,
            description="Test current transaction",
            db=db,
            ticker="KRW"
        )

        print(f"✓ Transaction created: {transaction.type} {transaction.amount} KRW")

        # Check if snapshot exists at transaction time
        snapshot_service = SnapshotService()
        snapshot = snapshot_service.get_snapshot(transaction_time, db)

        if snapshot:
            print(f"✅ SUCCESS: Snapshot exists at transaction time {snapshot.snapshot_datetime}")
            print(f"   Total assets: {snapshot.total_assets_krw:,.2f} KRW")
            print(f"   Total assets: ${snapshot.total_assets_usd:,.2f} USD")
        else:
            print(f"❌ FAIL: No snapshot found at transaction time {transaction_time}")

        # Check if hourly snapshot will be created next hour
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        print(f"\n💡 Next hourly snapshot should be created at {next_hour} by cron job")

        # Cleanup
        db.query(AssetSnapshot).filter(AssetSnapshot.snapshot_datetime >= transaction_time).delete()
        db.delete(transaction)
        db.delete(account)
        db.commit()
        print(f"\n🧹 Test cleanup completed")

        return snapshot is not None

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def test_past_transaction_regeneration():
    """Test that a past transaction regenerates both transaction-time and hourly snapshots."""
    db = SessionLocal()
    try:
        print("\n" + "="*80)
        print("TEST 2: Past Transaction Regeneration")
        print("="*80)

        # Clean up any existing test accounts
        db.query(Account).filter(Account.name.like("Test %")).delete(synchronize_session=False)
        db.commit()

        # Create a test account
        account = Account(
            name="Test Past Transaction Account",
            type="Deposit"
        )
        db.add(account)
        db.commit()
        print(f"✓ Created test account: {account.name} (ID: {account.id})")

        # Create a past transaction (2 hours ago at :24 minutes)
        past_time = datetime.now() - timedelta(hours=2)
        past_time = past_time.replace(minute=24, second=0, microsecond=0)

        print(f"\n📝 Creating past deposit at {past_time} (2 hours ago)")

        service = TransactionService()
        transaction = service.create_deposit(
            account_id=account.id,
            amount=Decimal("500000"),
            transaction_date=past_time,
            description="Test past transaction",
            db=db,
            ticker="KRW"
        )

        print(f"✓ Transaction created: {transaction.type} {transaction.amount} KRW")

        # Check if snapshot exists at transaction time (14:24)
        snapshot_service = SnapshotService()
        tx_snapshot = snapshot_service.get_snapshot(past_time, db)

        if tx_snapshot:
            print(f"\n✅ SUCCESS: Transaction-time snapshot exists at {tx_snapshot.snapshot_datetime}")
            print(f"   Total assets: {tx_snapshot.total_assets_krw:,.2f} KRW")
        else:
            print(f"\n❌ FAIL: No snapshot found at transaction time {past_time}")

        # Check if hourly snapshots exist
        hour_after = past_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        hourly_snapshot = snapshot_service.get_snapshot(hour_after, db)

        if hourly_snapshot:
            print(f"✅ SUCCESS: Hourly snapshot exists at {hourly_snapshot.snapshot_datetime}")
            print(f"   Total assets: {hourly_snapshot.total_assets_krw:,.2f} KRW")
        else:
            print(f"❌ FAIL: No hourly snapshot found at {hour_after}")

        # Query all snapshots in the range
        start_range = past_time.replace(minute=0, second=0, microsecond=0)
        end_range = datetime.now().replace(minute=0, second=0, microsecond=0)

        all_snapshots = db.query(AssetSnapshot).filter(
            AssetSnapshot.snapshot_datetime >= start_range,
            AssetSnapshot.snapshot_datetime <= end_range
        ).order_by(AssetSnapshot.snapshot_datetime).all()

        print(f"\n📊 All snapshots in range ({len(all_snapshots)} total):")
        for snap in all_snapshots:
            minute_marker = "TX" if snap.snapshot_datetime.minute != 0 else "HR"
            print(f"   [{minute_marker}] {snap.snapshot_datetime} - {snap.total_assets_krw:,.2f} KRW")

        # Cleanup
        db.query(AssetSnapshot).filter(AssetSnapshot.snapshot_datetime >= start_range).delete()
        db.delete(transaction)
        db.delete(account)
        db.commit()
        print(f"\n🧹 Test cleanup completed")

        return tx_snapshot is not None and hourly_snapshot is not None

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Run all tests."""
    print("\n" + "🚀 ASSET SNAPSHOT FIX VERIFICATION" + "\n")

    test1_passed = test_current_transaction_snapshot()
    test2_passed = test_past_transaction_regeneration()

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Test 1 (Current Transaction):  {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Test 2 (Past Transaction):      {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print()

    if test1_passed and test2_passed:
        print("🎉 All tests passed! The snapshot fix is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit(main())
