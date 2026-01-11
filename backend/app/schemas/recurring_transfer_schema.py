from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from datetime import datetime
from typing import Optional


class RecurringTransferCreate(BaseModel):
    """Schema for creating a new recurring transfer."""
    from_account_id: int = Field(..., gt=0, description="Source account ID")
    to_account_id: int = Field(..., gt=0, description="Target account ID")
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Transfer amount")
    day_of_month: int = Field(..., ge=1, le=31, description="Day of month (1-31)")
    description: Optional[str] = Field(None, max_length=500)

    @field_validator('to_account_id')
    @classmethod
    def validate_different_accounts(cls, v, info):
        from_id = info.data.get('from_account_id')
        if from_id and v == from_id:
            raise ValueError("from_account_id and to_account_id must be different")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "from_account_id": 1,
                "to_account_id": 2,
                "amount": "100000.00",
                "day_of_month": 15,
                "description": "Monthly savings transfer"
            }
        }


class RecurringTransferUpdate(BaseModel):
    """Schema for updating an existing recurring transfer."""
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "amount": "150000.00",
                "day_of_month": 20,
                "is_active": True
            }
        }


class RecurringTransferResponse(BaseModel):
    """Schema for recurring transfer responses."""
    id: int
    from_account_id: int
    from_account_name: str
    to_account_id: int
    to_account_name: str
    amount: Decimal
    day_of_month: int
    description: Optional[str]
    is_active: bool
    last_executed_date: Optional[datetime]
    created_at: datetime
    next_execution_date: Optional[datetime] = Field(
        None,
        description="Calculated next execution date"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "from_account_id": 1,
                "from_account_name": "Checking Account",
                "to_account_id": 2,
                "to_account_name": "Savings Account",
                "amount": "100000.00",
                "day_of_month": 15,
                "description": "Monthly savings transfer",
                "is_active": True,
                "last_executed_date": "2025-12-15T00:00:00",
                "created_at": "2025-11-01T10:30:00",
                "next_execution_date": "2026-01-15T00:00:00"
            }
        }
