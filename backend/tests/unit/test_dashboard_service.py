import pytest
from decimal import Decimal
from datetime import date
from app.services.dashboard_service import DashboardService
from app.models.holding import Holding
from app.utils.decimal_helpers import to_decimal

def test_top_assets_includes_cash_separately(db_session, checking_account, brokerage_account, mock_market_data):
    """
    Verify that Cash (KRW) and Cash (USD) are displayed separately in Top Assets.
    """
    from app.utils.currency_inference import normalize_ticker

    # Setup
    dashboard_service = DashboardService()

    # 1. Add KRW Cash to checking account (1,000,000 KRW)
    # CASH normalized to KRW for Deposit accounts
    krw_ticker = normalize_ticker("CASH", checking_account.type)
    krw_cash = Holding(
        account_id=checking_account.id,
        ticker=krw_ticker,
        quantity=to_decimal(1000000, precision=2),
        avg_price=to_decimal(1, precision=4)
    )
    db_session.add(krw_cash)

    # 2. Add USD Cash to brokerage account (100 USD)
    # CASH normalized to USD for Securities accounts
    # USD/KRW rate is mocked at 1300 in mock_market_data fixture
    usd_ticker = normalize_ticker("CASH", brokerage_account.type)
    usd_cash = Holding(
        account_id=brokerage_account.id,
        ticker=usd_ticker,
        quantity=to_decimal(100, precision=2),
        avg_price=to_decimal(1, precision=4)
    )
    db_session.add(usd_cash)

    # 3. Add a Stock holding (Samsung Electronics)
    # 10 shares @ 50,000 KRW = 500,000 KRW
    stock = Holding(
        account_id=checking_account.id,
        ticker="005930.KS",
        quantity=to_decimal(10, precision=8),
        avg_price=to_decimal(50000, precision=4)
    )
    db_session.add(stock)
    
    db_session.commit()

    # Calculate Total Assets for percentage check
    # Cash KRW: 1,000,000
    # Cash USD: 100 * 1300 = 130,000
    # Stock: 10 * 50,000 = 500,000 (Assuming market price matches or using avg_price fallback)
    # Total = 1,630,000 KRW
    total_assets_krw = Decimal("1630000")

    # Execute
    top_assets = dashboard_service._calculate_top_assets(db_session, total_assets_krw)

    # Verify
    assert len(top_assets) > 0
    
    # Check for "Cash (KRW)"
    cash_krw_entry = next((item for item in top_assets if item["ticker"] == "Cash (KRW)"), None)
    assert cash_krw_entry is not None
    assert cash_krw_entry["value_krw"] == Decimal("1000000")
    assert cash_krw_entry["name"] == "Korean Won"
    
    # Check for "Cash (USD)"
    cash_usd_entry = next((item for item in top_assets if item["ticker"] == "Cash (USD)"), None)
    assert cash_usd_entry is not None
    assert cash_usd_entry["value_krw"] == Decimal("100") * Decimal("1300")
    assert cash_usd_entry["name"] == "US Dollar"
    
    # Verify Stock entry
    stock_entry = next((item for item in top_assets if item["ticker"] == "005930.KS"), None)
    assert stock_entry is not None
    # Depending on mock_market_data, price might be different. 
    # mock_market_data says 005930.KS is 75,000.
    # So stock value = 10 * 75,000 = 750,000.
    # If calculate_top_assets uses market price:
    expected_stock_value = Decimal("10") * Decimal("75000")
    assert stock_entry["value_krw"] == expected_stock_value