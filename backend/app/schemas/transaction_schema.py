from pydantic import BaseModel, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.utils.timezone import parse_iso_to_kst, make_kst_aware


# ========== BASE CLASS WITH KST TIMEZONE VALIDATION ==========

class TransactionCreateBase(BaseModel):
    """Base class for transaction creation with automatic KST timezone handling."""

    @field_validator('date', mode='before', check_fields=False)
    @classmethod
    def ensure_kst_timezone(cls, v):
        """Convert naive datetime from frontend to KST-aware datetime."""
        if isinstance(v, str):
            # Parse ISO string from frontend (e.g., "2024-01-15T14:30")
            return parse_iso_to_kst(v)
        if isinstance(v, datetime) and v.tzinfo is None:
            # Convert naive datetime to KST-aware
            return make_kst_aware(v)
        # Already timezone-aware, return as-is
        return v


# ========== PATTERN ① PURE INCOME/EXPENSE ==========

class DepositCreate(TransactionCreateBase):
    """Create deposit transaction."""
    account_id: int
    amount: Decimal
    date: datetime
    description: Optional[str] = None


class WithdrawalCreate(TransactionCreateBase):
    """Create withdrawal transaction."""
    account_id: int
    amount: Decimal
    date: datetime
    description: Optional[str] = None


class DividendCreate(TransactionCreateBase):
    """Create dividend transaction."""
    account_id: int
    ticker: str
    amount: Decimal
    date: datetime
    description: Optional[str] = None


class InterestCreate(TransactionCreateBase):
    """Create interest transaction for MoneyMarket accounts."""
    account_id: int
    amount: Decimal
    date: datetime
    description: Optional[str] = None


# ========== PATTERN ② SIMPLE TRANSFER ==========

class TransferCreate(TransactionCreateBase):
    """Create transfer transaction."""
    from_account_id: int
    to_account_id: int
    amount: Decimal
    date: datetime
    description: Optional[str] = None


# ========== PATTERN ③ ASSET FORM CONVERSION ==========

class BuyCreate(TransactionCreateBase):
    """Create buy transaction."""
    account_id: int
    ticker: str
    quantity: Decimal
    price: Decimal
    price_currency: str = 'USD'  # Currency of the price (USD, KRW, JPY, EUR, etc.)
    date: datetime
    description: Optional[str] = None


class SellCreate(TransactionCreateBase):
    """Create sell transaction."""
    account_id: int
    ticker: str
    quantity: Decimal
    price: Decimal
    price_currency: str = 'USD'  # Currency of the price (USD, KRW, JPY, EUR, etc.)
    date: datetime
    description: Optional[str] = None


# ========== PATTERN ④+② CROSS-ACCOUNT EXCHANGE ==========

class ExchangeCreate(TransactionCreateBase):
    """Create cross-account exchange transaction (Pattern ④+②)."""
    account_id: int
    from_ticker: str
    to_ticker: str
    from_amount: Decimal
    to_amount: Decimal
    date: datetime
    description: Optional[str] = None
    to_account_id: int  # Required for cross-account exchange-transfer


# ========== RESPONSE SCHEMAS ==========

class TransactionResponse(BaseModel):
    """Basic transaction response."""
    id: int
    account_id: int
    type: str
    ticker: Optional[str] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    price_currency: Optional[str] = None
    amount: Decimal
    date: datetime
    linked_tx_id: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransactionDetailResponse(BaseModel):
    """Detailed transaction response with account name."""
    id: int
    account_id: int
    account_name: str
    type: str
    ticker: Optional[str] = None
    ticker_name: Optional[str] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    price_currency: Optional[str] = None
    amount: Decimal
    date: datetime
    linked_tx_id: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Response for transaction list endpoint."""
    transactions: list[TransactionDetailResponse]
    total: int
    limit: int
    offset: int
