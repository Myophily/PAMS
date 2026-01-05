from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
    """Create a new account with optional initial balance."""
    try:
        account = account_service.create_account(
            name=request.name,
            account_type=request.type,
            currency=request.currency,
            initial_balance=request.initial_balance,
            initial_balance_date=request.initial_balance_date,
            db=db
        )
        return account
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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


@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    """Delete an account (must liquidate first)."""
    try:
        account_service.delete_account(account_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
