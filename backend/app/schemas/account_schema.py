from pydantic import BaseModel, validator
from datetime import datetime
from decimal import Decimal
from typing import Optional, List


# ========== REQUEST SCHEMAS ==========

class InitialHoldingItem(BaseModel):
    """Single initial holding item for Securities accounts."""
    ticker: str  # "AAPL", "TSLA", or "CASH"
    quantity: Decimal
    price: Optional[Decimal] = None  # Required for stocks, ignored for CASH

    @validator('ticker')
    def validate_ticker_format(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Ticker cannot be empty')
        return v.upper()

    @validator('price')
    def validate_price_required_for_stocks(cls, v, values):
        ticker = values.get('ticker')
        if ticker and ticker != 'CASH' and v is None:
            raise ValueError('Price is required for stock holdings')
        if ticker == 'CASH' and v is not None:
            raise ValueError('Price should not be provided for CASH')
        return v


class AccountCreateRequest(BaseModel):
    """Create a new account with optional initial balance or multiple initial holdings."""
    name: str
    type: str  # Deposit | Securities | ForeignCurrency | MoneyMarket | Savings
    initial_balance: Optional[Decimal] = None
    initial_balance_date: Optional[datetime] = None  # Defaults to current datetime
    initial_holdings: Optional[List[InitialHoldingItem]] = None  # For Securities accounts

    @validator('initial_holdings')
    def validate_initial_holdings(cls, v, values):
        account_type = values.get('type')
        initial_balance = values.get('initial_balance')

        # Only Securities accounts can use initial_holdings
        if v is not None and account_type != 'Securities':
            raise ValueError('initial_holdings can only be used with Securities accounts')

        # Cannot use both initial_balance and initial_holdings
        if v is not None and initial_balance is not None and initial_balance > 0:
            raise ValueError('Cannot use both initial_balance and initial_holdings')

        # Check for duplicate tickers
        if v:
            tickers = [item.ticker for item in v]
            if len(tickers) != len(set(tickers)):
                raise ValueError('Duplicate tickers in initial_holdings')

        return v


class AccountUpdateRequest(BaseModel):
    """Update account (only name can be changed)."""
    name: str


# ========== RESPONSE SCHEMAS ==========

class AccountResponse(BaseModel):
    """Basic account response."""
    id: int
    name: str
    type: str
    created_at: datetime

    class Config:
        from_attributes = True


class AccountListItemResponse(BaseModel):
    """Account list item with balance summary."""
    id: int
    name: str
    type: str
    balance: Decimal  # Total balance in account's currency
    balance_usd: Decimal  # Converted to USD
    holdings_count: int  # Number of different assets (including CASH)
    created_at: datetime

    class Config:
        from_attributes = True


class HoldingResponse(BaseModel):
    """Holding with current market data."""
    id: int
    account_id: int
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
