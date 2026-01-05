"""
Dashboard router for summary statistics and chart data.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
dashboard_service = DashboardService()


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Get dashboard summary with total assets, changes, and allocation.

    Returns:
        Dict with:
        - total_assets (KRW and USD)
        - current_exchange_rate
        - changes (day, month, year)
        - allocation (by type)
    """
    summary = dashboard_service.get_summary(db)
    return {
        "status": "success",
        "data": summary
    }


@router.get("/chart")
def get_dashboard_chart(
    period: str = "1M",
    currency: str = "KRW",
    db: Session = Depends(get_db)
):
    """
    Get asset volatility time series data for charts.

    Args:
        period: Time period ("1W", "1M", "3M", "6M", "1Y", "ALL")
        currency: Currency for values ("KRW" or "USD")

    Returns:
        Dict with chart_data array containing:
        - date
        - total_assets
        - principal
        - gain_loss
    """
    chart_data = dashboard_service.get_chart_data(period, currency, db)
    return {
        "status": "success",
        "data": chart_data
    }
