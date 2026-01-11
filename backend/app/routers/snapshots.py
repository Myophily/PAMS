"""
Snapshot router for accessing hourly asset snapshots.

Asset snapshots are used for:
- Dashboard charts showing portfolio value over time (with hourly granularity)
- Performance tracking
- Historical analysis
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.snapshot_service import SnapshotService
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter(prefix="/api/snapshots", tags=["snapshots"])
snapshot_service = SnapshotService()


@router.get("/")
def get_snapshots(
    start_datetime: Optional[datetime] = None,
    end_datetime: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get hourly snapshots for a datetime range.

    If no datetimes provided, defaults to last 30 days.

    Args:
        start_datetime: Start datetime (inclusive)
        end_datetime: End datetime (inclusive)
        db: Database session

    Returns:
        List of asset snapshots ordered by datetime
    """
    if not start_datetime:
        start_datetime = datetime.now() - timedelta(days=30)
    if not end_datetime:
        end_datetime = datetime.now()

    snapshots = snapshot_service.get_snapshots_range(start_datetime, end_datetime, db)
    return snapshots


@router.get("/latest")
def get_latest_snapshot(db: Session = Depends(get_db)):
    """
    Get the most recent snapshot.

    Returns:
        Latest asset snapshot

    Raises:
        HTTPException: 404 if no snapshots exist
    """
    snapshot = snapshot_service.get_latest_snapshot(db)
    if not snapshot:
        raise HTTPException(status_code=404, detail="No snapshots found")
    return snapshot


@router.post("/backfill", status_code=200)
def backfill_snapshots(
    start_datetime: datetime = Query(..., description="Start datetime for backfill"),
    end_datetime: datetime = Query(default=None, description="End datetime (defaults to now)"),
    db: Session = Depends(get_db)
):
    """
    Backfill historical hourly snapshots for a datetime range.

    This generates snapshots for any hours that don't already have one.
    Useful for:
    - Initial setup after importing historical transactions
    - Fixing gaps in snapshot data after server downtime
    - Regenerating snapshots after data corrections

    Args:
        start_datetime: Start datetime
        end_datetime: End datetime (defaults to now)
        db: Database session

    Returns:
        Success status with count of snapshots created
    """
    if not end_datetime:
        end_datetime = datetime.now()

    count = snapshot_service.backfill_hourly_snapshots(start_datetime, end_datetime, db)
    return {
        "status": "success",
        "snapshots_created": count,
        "datetime_range": f"{start_datetime} to {end_datetime}"
    }
