from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional


# ========== PATTERN ① PURE INCOME/EXPENSE ==========

class DepositCreate(BaseModel):
    """Create deposit transaction."""
    account_id: int
    amount: Decimal
    date: datetime
    description: Optional[str] = None


class WithdrawalCreate(BaseModel):
    """Create withdrawal transaction."""
    account_id: int
    amount: Decimal
    date: datetime
    description: Optional[str] = None


class DividendCreate(BaseModel):
    """Create dividend transaction."""
    account_id: int
    ticker: str
    amount: Decimal
    date: datetime
    description: Optional[str] = None


class InterestCreate(BaseModel):
    """Create interest transaction for MoneyMarket accounts."""
    account_id: int
    amount: Decimal
    date: datetime
    description: Optional[str] = None


# ========== PATTERN ② SIMPLE TRANSFER ==========

class TransferCreate(BaseModel):
    """Create transfer transaction."""
    from_account_id: int
    to_account_id: int
    amount: Decimal
    date: datetime
    description: Optional[str] = None


# ========== PATTERN ③ ASSET FORM CONVERSION ==========

class BuyCreate(BaseModel):
    """Create buy transaction."""
    account_id: int
    ticker: str
    quantity: Decimal
    price: Decimal
    date: datetime
    description: Optional[str] = None


class SellCreate(BaseModel):
    """Create sell transaction."""
    account_id: int
    ticker: str
    quantity: Decimal
    price: Decimal
    date: datetime
    description: Optional[str] = None


# ========== PATTERN ④ EXCHANGE ==========

class ExchangeCreate(BaseModel):
    """Create exchange transaction."""
    account_id: int
    from_ticker: str
    to_ticker: str
    from_amount: Decimal
    to_amount: Decimal
    date: datetime
    description: Optional[str] = None


# ========== RESPONSE SCHEMAS ==========

class TransactionResponse(BaseModel):
    """Basic transaction response."""
    id: int
    account_id: int
    type: str
    ticker: Optional[str] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
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
