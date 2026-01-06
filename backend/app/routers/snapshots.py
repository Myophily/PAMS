"""
Snapshot router for accessing daily asset snapshots.

Asset snapshots are used for:
- Dashboard charts showing portfolio value over time
- Performance tracking
- Historical analysis
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.snapshot_service import SnapshotService
from datetime import date, timedelta
from typing import Optional

router = APIRouter(prefix="/api/snapshots", tags=["snapshots"])
snapshot_service = SnapshotService()


@router.get("/")
def get_snapshots(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get snapshots for a date range.

    If no dates provided, defaults to last 365 days.

    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        db: Database session

    Returns:
        List of asset snapshots ordered by date
    """
    if not start_date:
        start_date = date.today() - timedelta(days=365)
    if not end_date:
        end_date = date.today()

    snapshots = snapshot_service.get_snapshots_range(start_date, end_date, db)
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
    start_date: date = Query(..., description="Start date for backfill"),
    end_date: date = Query(default=None, description="End date (defaults to today)"),
    db: Session = Depends(get_db)
):
    """
    Backfill historical snapshots for a date range.

    This generates snapshots for any dates that don't already have one.
    Useful for:
    - Initial setup after importing historical transactions
    - Fixing gaps in snapshot data
    - Regenerating snapshots after data corrections

    Args:
        start_date: Start date
        end_date: End date (defaults to today)
        db: Database session

    Returns:
        Success status with count of snapshots created
    """
    if not end_date:
        end_date = date.today()

    count = snapshot_service.backfill_snapshots(start_date, end_date, db)
    return {
        "status": "success",
        "snapshots_created": count,
        "date_range": f"{start_date} to {end_date}"
    }
