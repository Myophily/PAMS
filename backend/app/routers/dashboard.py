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


@router.get("/candlestick-chart")
def get_candlestick_chart(
    period: str = "daily",
    currency: str = "KRW",
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """
    Get OHLC candlestick data for asset growth chart.

    Args:
        period: Aggregation period ("daily", "monthly", "annual")
        currency: Currency for values ("KRW" or "USD")
        start_date: Optional start date in ISO format (YYYY-MM-DD)
        end_date: Optional end date in ISO format (YYYY-MM-DD)

    Returns:
        Dict with candles array containing OHLC data
    """
    from datetime import datetime
    from fastapi import HTTPException

    # Parse dates if provided
    start = None
    end = None
    if start_date:
        try:
            start = datetime.fromisoformat(start_date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
    if end_date:
        try:
            end = datetime.fromisoformat(end_date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

    # Validate period
    if period not in ["daily", "monthly", "annual"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid period. Must be: daily, monthly, or annual"
        )

    # Validate currency
    if currency not in ["KRW", "USD"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid currency. Must be: KRW or USD"
        )

    # Get candlestick data
    data = dashboard_service.get_candlestick_data(period, currency, db, start, end)

    return {
        "status": "success",
        "data": data
    }
