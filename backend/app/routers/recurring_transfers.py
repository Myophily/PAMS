from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.recurring_transfer_service import RecurringTransferService
from app.schemas.recurring_transfer_schema import (
    RecurringTransferCreate,
    RecurringTransferUpdate,
    RecurringTransferResponse
)
from typing import List, Optional


router = APIRouter(prefix="/api/recurring-transfers", tags=["recurring-transfers"])
service = RecurringTransferService()


@router.post("/", response_model=RecurringTransferResponse, status_code=201)
def create_recurring_transfer(
    request: RecurringTransferCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new recurring transfer rule.

    Args:
        request: RecurringTransferCreate schema with transfer details
        db: Database session

    Returns:
        Created RecurringTransfer with account names and next execution date

    Raises:
        HTTPException 400: Validation failed (accounts not found, invalid account types, etc.)
        HTTPException 500: Database error
    """
    try:
        recurring = service.create_recurring_transfer(
            from_account_id=request.from_account_id,
            to_account_id=request.to_account_id,
            amount=request.amount,
            day_of_month=request.day_of_month,
            description=request.description,
            db=db
        )

        # Build response with account names and next execution date
        response = RecurringTransferResponse(
            id=recurring.id,
            from_account_id=recurring.from_account_id,
            from_account_name=recurring.from_account.name,
            to_account_id=recurring.to_account_id,
            to_account_name=recurring.to_account.name if recurring.to_account else "External",
            amount=recurring.amount,
            day_of_month=recurring.day_of_month,
            description=recurring.description,
            is_active=recurring.is_active,
            last_executed_date=recurring.last_executed_date,
            created_at=recurring.created_at,
            next_execution_date=service._calculate_next_execution(recurring)
        )
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create recurring transfer: {str(e)}")


@router.get("/", response_model=List[RecurringTransferResponse])
def list_recurring_transfers(
    account_id: Optional[int] = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """
    List all recurring transfers.

    Args:
        account_id: Optional account ID to filter by (returns transfers from or to this account)
        include_inactive: Whether to include inactive/paused transfers (default: False)
        db: Database session

    Returns:
        List of RecurringTransfer objects with account names and next execution dates
    """
    recurring_list = service.list_recurring_transfers(db, account_id, include_inactive)

    responses = []
    for recurring in recurring_list:
        responses.append(RecurringTransferResponse(
            id=recurring.id,
            from_account_id=recurring.from_account_id,
            from_account_name=recurring.from_account.name,
            to_account_id=recurring.to_account_id,
            to_account_name=recurring.to_account.name if recurring.to_account else "External",
            amount=recurring.amount,
            day_of_month=recurring.day_of_month,
            description=recurring.description,
            is_active=recurring.is_active,
            last_executed_date=recurring.last_executed_date,
            created_at=recurring.created_at,
            next_execution_date=service._calculate_next_execution(recurring)
        ))

    return responses


@router.get("/{recurring_id}", response_model=RecurringTransferResponse)
def get_recurring_transfer(recurring_id: int, db: Session = Depends(get_db)):
    """
    Get a single recurring transfer by ID.

    Args:
        recurring_id: RecurringTransfer ID
        db: Database session

    Returns:
        RecurringTransfer object with account names and next execution date

    Raises:
        HTTPException 404: Recurring transfer not found
    """
    from app.models.recurring_transfer import RecurringTransfer

    recurring = db.query(RecurringTransfer).filter(
        RecurringTransfer.id == recurring_id,
        RecurringTransfer.deleted_at.is_(None)
    ).first()

    if not recurring:
        raise HTTPException(status_code=404, detail=f"Recurring transfer {recurring_id} not found")

    return RecurringTransferResponse(
        id=recurring.id,
        from_account_id=recurring.from_account_id,
        from_account_name=recurring.from_account.name,
        to_account_id=recurring.to_account_id,
        to_account_name=recurring.to_account.name if recurring.to_account else "External",
        amount=recurring.amount,
        day_of_month=recurring.day_of_month,
        description=recurring.description,
        is_active=recurring.is_active,
        last_executed_date=recurring.last_executed_date,
        created_at=recurring.created_at,
        next_execution_date=service._calculate_next_execution(recurring)
    )


@router.patch("/{recurring_id}", response_model=RecurringTransferResponse)
def update_recurring_transfer(
    recurring_id: int,
    request: RecurringTransferUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing recurring transfer.

    Args:
        recurring_id: RecurringTransfer ID
        request: RecurringTransferUpdate schema with fields to update
        db: Database session

    Returns:
        Updated RecurringTransfer object

    Raises:
        HTTPException 404: Recurring transfer not found
        HTTPException 400: Validation error
        HTTPException 500: Database error
    """
    try:
        recurring = service.update_recurring_transfer(
            recurring_id=recurring_id,
            amount=request.amount,
            day_of_month=request.day_of_month,
            description=request.description,
            is_active=request.is_active,
            db=db
        )

        response = RecurringTransferResponse(
            id=recurring.id,
            from_account_id=recurring.from_account_id,
            from_account_name=recurring.from_account.name,
            to_account_id=recurring.to_account_id,
            to_account_name=recurring.to_account.name if recurring.to_account else "External",
            amount=recurring.amount,
            day_of_month=recurring.day_of_month,
            description=recurring.description,
            is_active=recurring.is_active,
            last_executed_date=recurring.last_executed_date,
            created_at=recurring.created_at,
            next_execution_date=service._calculate_next_execution(recurring)
        )
        return response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update: {str(e)}")


@router.delete("/{recurring_id}", status_code=204)
def delete_recurring_transfer(recurring_id: int, db: Session = Depends(get_db)):
    """
    Delete (soft delete) a recurring transfer.

    This only deletes the recurring transfer rule. Historical transactions
    created by this recurring transfer are preserved (immutable).

    Args:
        recurring_id: RecurringTransfer ID
        db: Database session

    Raises:
        HTTPException 404: Recurring transfer not found
    """
    try:
        service.delete_recurring_transfer(recurring_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
