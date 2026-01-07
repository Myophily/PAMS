from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.database import get_db
from app.services.account_service import AccountService
from app.schemas.account_schema import (
    AccountCreateRequest,
    AccountUpdateRequest,
    AccountResponse,
    AccountListItemResponse,
    AccountDetailResponse
)
from typing import List

router = APIRouter(prefix="/api/accounts", tags=["accounts"])
account_service = AccountService()


@router.post("/", response_model=AccountResponse, status_code=201)
def create_account(request: AccountCreateRequest, db: Session = Depends(get_db)):
    """Create a new account with optional initial balance or multiple initial holdings."""
    try:
        account = account_service.create_account(
            name=request.name,
            account_type=request.type,
            initial_balance=request.initial_balance,
            initial_balance_date=request.initial_balance_date,
            initial_holdings=request.initial_holdings,
            db=db
        )
        return account
    except ValueError as e:
        # Business logic validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        # Database constraint violations (unique, foreign key, etc.)
        db.rollback()
        raise HTTPException(status_code=409, detail="Database constraint violation")
    except SQLAlchemyError as e:
        # Database errors (connection, query execution, etc.)
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        # Catch-all for unexpected errors
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/", response_model=List[AccountListItemResponse])
def list_accounts(db: Session = Depends(get_db)):
    """List all accounts with balance summary."""
    accounts = account_service.list_accounts(db)
    return accounts


@router.get("/{account_id}", response_model=AccountDetailResponse)
def get_account_detail(account_id: int, db: Session = Depends(get_db)):
    """Get detailed account information with holdings."""
    try:
        detail = account_service.get_account_detail(account_id, db)
        return detail
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    request: AccountUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update account name."""
    try:
        account = account_service.update_account(account_id, request.name, db)
        return account
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{account_id}", status_code=200)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    """
    Delete an account and all its transactions.

    WARNING: This is a destructive operation that permanently deletes:
    - All transactions for this account
    - All holdings
    - The account itself

    Returns deletion statistics.
    """
    try:
        stats = account_service.delete_account(account_id, db)
        return {
            "message": "Account deleted successfully",
            "stats": stats
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred")
