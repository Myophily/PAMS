from pydantic import BaseModel, validator, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from app.utils.timezone import parse_iso_to_kst, make_kst_aware


# ========== REQUEST SCHEMAS ==========

class InitialHoldingItem(BaseModel):
    """Single initial holding item for any account type."""
    ticker: str  # "KRW", "USD", "AAPL", "TSLA", "GOLD" (currency or asset ticker)
    quantity: Decimal
    price: Optional[Decimal] = None  # Required for non-currency tickers
    price_currency: Optional[str] = None  # Currency for stock prices (KRW or USD)

    @validator('ticker')
    def validate_ticker_format(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Ticker cannot be empty')

        # Warn on legacy CASH ticker (will be auto-converted)
        ticker_upper = v.upper()
        if ticker_upper == 'CASH':
            import warnings
            warnings.warn(
                "CASH ticker is deprecated. Use explicit currency codes (KRW, USD, etc.)",
                DeprecationWarning
            )

        return ticker_upper

    @validator('price')
    def validate_price_requirement(cls, v, values):
        """Price required for non-currency tickers."""
        from app.utils.currency_inference import is_currency_ticker

        ticker = values.get('ticker')
        if not ticker:
            return v

        # Currency tickers should NOT have price
        if is_currency_ticker(ticker):
            if v is not None:
                raise ValueError(f'Price should not be provided for currency ticker {ticker}')
            return None

        # Non-currency tickers (stocks, commodities) MUST have price
        if v is None:
            raise ValueError(f'Price is required for asset ticker {ticker}')

        return v

    @validator('price_currency', always=True)
    def validate_price_currency_requirement(cls, v, values):
        """price_currency required for non-currency tickers (auto-infer if missing)."""
        from app.utils.currency_inference import is_currency_ticker, infer_price_currency_from_ticker

        ticker = values.get('ticker')
        price = values.get('price')

        if not ticker:
            return v

        # Currency tickers should NOT have price_currency
        if is_currency_ticker(ticker):
            if v is not None:
                raise ValueError(f'price_currency should not be provided for currency ticker {ticker}')
            return None

        # Non-currency tickers with price MUST have price_currency
        if price is not None:
            # Auto-infer if not provided
            if v is None:
                v = infer_price_currency_from_ticker(ticker)
            return v

        return v


class AccountCreateRequest(BaseModel):
    """Create a new account with optional initial balance or multiple initial holdings."""
    name: str
    type: str  # Deposit | Securities | ForeignCurrency | MoneyMarket | Savings
    initial_balance: Optional[Decimal] = None  # DEPRECATED: Use initial_holdings instead
    initial_balance_date: Optional[datetime] = None  # Defaults to current datetime
    initial_holdings: Optional[List[InitialHoldingItem]] = None  # Now for ALL account types

    @field_validator('initial_balance_date', mode='before')
    @classmethod
    def ensure_kst_timezone_for_balance_date(cls, v):
        """Convert naive datetime from frontend to KST-aware datetime."""
        if v is None:
            return v  # None is valid (will default to now_kst in service layer)
        if isinstance(v, str):
            return parse_iso_to_kst(v)
        if isinstance(v, datetime) and v.tzinfo is None:
            return make_kst_aware(v)
        return v

    @validator('initial_holdings')
    def validate_initial_holdings(cls, v, values):
        from app.utils.currency_inference import is_currency_ticker, normalize_ticker, CURRENCY_TICKERS

        account_type = values.get('type')
        initial_balance = values.get('initial_balance')

        # Warn if using deprecated initial_balance
        if initial_balance is not None and initial_balance > 0:
            import warnings
            warnings.warn(
                "initial_balance is deprecated. Use initial_holdings instead.",
                DeprecationWarning
            )
            # Allow both for now (service layer will handle conversion)

        # Cannot use both with positive values
        if v is not None and len(v) > 0 and initial_balance is not None and initial_balance > 0:
            raise ValueError('Cannot use both initial_balance and initial_holdings')

        # Account-type-specific ticker validation
        if v:
            tickers = [item.ticker for item in v]

            # Check for duplicate tickers
            if len(tickers) != len(set(tickers)):
                raise ValueError('Duplicate tickers in initial_holdings')

            # Validate ticker constraints by account type
            for item in v:
                ticker_normalized = item.ticker

                # Normalize CASH for validation
                if ticker_normalized == "CASH":
                    if account_type in ["Deposit", "Savings", "MoneyMarket"]:
                        ticker_normalized = "KRW"
                    else:
                        ticker_normalized = "USD"

                if account_type in ["Deposit", "Savings", "MoneyMarket"]:
                    # Only KRW allowed
                    if ticker_normalized != "KRW":
                        raise ValueError(
                            f'{account_type} accounts can only hold KRW. '
                            f'Found ticker: {item.ticker}'
                        )

                elif account_type == "ForeignCurrency":
                    # Only non-KRW currencies allowed
                    if not is_currency_ticker(ticker_normalized):
                        raise ValueError(
                            f'ForeignCurrency accounts can only hold currencies. '
                            f'Found non-currency ticker: {item.ticker}'
                        )
                    if ticker_normalized == "KRW":
                        raise ValueError(
                            'ForeignCurrency accounts cannot hold KRW. '
                            'Use Deposit account type for KRW.'
                        )

                elif account_type == "Securities":
                    # Any ticker allowed (currencies, stocks, commodities)
                    pass  # No restrictions

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
    balance: Decimal  # Cash only (backward compatibility)
    total_value: Decimal  # NEW: Total portfolio value (cash + stocks) in account currency
    total_value_krw: Decimal  # NEW: Total value converted to KRW for dashboard aggregation
    stock_value: Decimal  # NEW: Stock holdings value in KRW
    balance_usd: Decimal  # CHANGED: Now shows total portfolio USD value (not just cash)
    currency: str  # Inferred primary currency from holdings (e.g., "KRW", "USD")
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
    price_currency: Optional[str] = None  # Currency for stock prices (KRW, USD, etc.)
    current_price: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    cost_basis: Decimal
    unrealized_pl: Optional[Decimal] = None
    unrealized_pl_percent: Optional[Decimal] = None

    class Config:
        from_attributes = True


class AccountSummaryResponse(BaseModel):
    """Account summary statistics."""
    total_value: Decimal  # Current total value in native currency
    total_value_krw: Decimal  # Total value converted to KRW
    cash_balance: Decimal  # CASH balance in native currency
    cash_balance_krw: Decimal  # Cash balance converted to KRW
    invested_amount: Decimal  # Cost basis (non-cash assets)
    unrealized_pl: Decimal  # Total unrealized P/L in native currency
    unrealized_pl_krw: Decimal  # Unrealized P/L converted to KRW
    unrealized_pl_percent: Decimal  # Percentage P/L
    currency: str  # Inferred primary currency from holdings


class AccountDetailResponse(BaseModel):
    """Detailed account response with holdings and summary."""
    account: AccountResponse
    summary: AccountSummaryResponse
    holdings: list[HoldingResponse]
