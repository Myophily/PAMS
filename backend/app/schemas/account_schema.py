from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal
from typing import Optional


# ========== REQUEST SCHEMAS ==========

class AccountCreateRequest(BaseModel):
    """Create a new account with optional initial balance."""
    name: str
    type: str  # Checking | Brokerage | Foreign | MMF
    currency: str  # KRW | USD | EUR | etc.
    initial_balance: Optional[Decimal] = Decimal("0")
    initial_balance_date: Optional[date] = None  # Defaults to today


class AccountUpdateRequest(BaseModel):
    """Update account (only name can be changed)."""
    name: str


# ========== RESPONSE SCHEMAS ==========

class AccountResponse(BaseModel):
    """Basic account response."""
    id: int
    name: str
    type: str
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class AccountListItemResponse(BaseModel):
    """Account list item with balance summary."""
    id: int
    name: str
    type: str
    currency: str
    balance: Decimal  # Total balance in account's currency
    balance_usd: Decimal  # Converted to USD
    holdings_count: int  # Number of different assets (including CASH)
    created_at: datetime

    class Config:
        from_attributes = True


class HoldingResponse(BaseModel):
    """Holding with current market data."""
    ticker: str
    ticker_name: Optional[str] = None
    quantity: Decimal
    avg_price: Decimal
    current_price: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    cost_basis: Decimal
    unrealized_pl: Optional[Decimal] = None
    unrealized_pl_percent: Optional[Decimal] = None

    class Config:
        from_attributes = True


class AccountSummaryResponse(BaseModel):
    """Account summary statistics."""
    total_value: Decimal  # Current total value
    cash_balance: Decimal  # CASH balance
    invested_amount: Decimal  # Cost basis (non-cash assets)
    unrealized_pl: Decimal  # Total unrealized P/L
    unrealized_pl_percent: Decimal  # Percentage P/L


class AccountDetailResponse(BaseModel):
    """Detailed account response with holdings and summary."""
    account: AccountResponse
    summary: AccountSummaryResponse
    holdings: list[HoldingResponse]
