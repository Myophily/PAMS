from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import accounts, transactions, dashboard, market_data, snapshots, recurring_transfers
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Personal Asset Manager API",
    version="1.0.0",
    description="Local-first financial dashboard API"
)

# Initialize APScheduler for recurring transfers
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///asset_data.db')
}
executors = {
    'default': ThreadPoolExecutor(1)  # Single thread to avoid race conditions
}
job_defaults = {
    'coalesce': True,  # Combine missed runs into single execution
    'max_instances': 1,  # Prevent concurrent execution of same job
    'misfire_grace_time': 3600  # 1 hour grace period for missed executions
}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults
)

# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(market_data.router)
app.include_router(snapshots.router)
app.include_router(recurring_transfers.router)


def generate_hourly_snapshot():
    """Background job to generate hourly snapshot."""
    from app.services.snapshot_service import SnapshotService
    from datetime import datetime

    db = SessionLocal()
    try:
        snapshot_service = SnapshotService()
        now = datetime.now().replace(minute=0, second=0, microsecond=0)

        snapshot = snapshot_service.generate_snapshot(now, db)
        db.commit()

        print(f"[Snapshot] Generated hourly snapshot: {now}")
    except Exception as e:
        db.rollback()
        print(f"[Snapshot] Error generating hourly snapshot: {e}")
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    """Initialize database, run migrations, and start scheduler on startup."""
    from app.database import (
        init_db, migrate_account_types, migrate_date_to_datetime,
        migrate_recurring_transfer_nullable_to_account, migrate_snapshot_date_to_datetime,
        engine, SessionLocal
    )
    from app.services.recurring_transfer_service import RecurringTransferService

    # Initialize database schema
    init_db()

    # Run account type migration
    migrate_account_types(engine)

    # Run date to datetime migration
    migrate_date_to_datetime(engine)

    # Run recurring transfer external support migration
    migrate_recurring_transfer_nullable_to_account(engine)

    # Run snapshot date to datetime migration
    migrate_snapshot_date_to_datetime(engine)

    # Backfill missing hourly snapshots (gap detection)
    from app.services.snapshot_service import SnapshotService
    snapshot_service = SnapshotService()
    db = SessionLocal()
    try:
        filled = snapshot_service.detect_and_fill_gaps(db)
        if filled > 0:
            print(f"[Snapshot] Backfilled {filled} missing hourly snapshots")
    except Exception as e:
        print(f"[Snapshot] Error during gap detection: {e}")
    finally:
        db.close()

    # Start APScheduler
    scheduler.start()
    print("[Scheduler] APScheduler started")

    # Schedule hourly snapshot generation
    scheduler.add_job(
        func=generate_hourly_snapshot,
        trigger='cron',
        minute=0,  # Run at top of every hour (00:00, 01:00, 02:00, ...)
        id='hourly_snapshot_generation',
        replace_existing=True
    )
    print("[Scheduler] Hourly snapshot generation scheduled")

    # Load and schedule recurring transfers
    db = SessionLocal()
    try:
        recurring_service = RecurringTransferService()
        recurring_service.load_and_schedule_all(db, scheduler)
    except Exception as e:
        print(f"[Scheduler] Error loading recurring transfers: {e}")
    finally:
        db.close()


@app.on_event("shutdown")
def on_shutdown():
    """Gracefully shutdown scheduler on app shutdown."""
    scheduler.shutdown(wait=True)
    print("[Scheduler] APScheduler shutdown")


@app.get("/api/health")
def health_check():
    """Health check endpoint to verify API and database connection."""
    from app.database import SessionLocal
    from app.models import Account

    db = SessionLocal()
    try:
        # Test database connection
        count = db.query(Account).count()
        db.close()
        return {
            "status": "healthy",
            "database": "connected",
            "accounts_count": count
        }
    except Exception as e:
        db.close()
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e)
        }
