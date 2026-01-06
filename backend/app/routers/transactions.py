from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.transaction_service import TransactionService
from app.schemas.transaction_schema import (
    DepositCreate,
    WithdrawalCreate,
    DividendCreate,
    InterestCreate,
    BuyCreate,
    SellCreate,
    TransferCreate,
    ExchangeCreate,
    TransactionResponse
)
from datetime import date
from typing import List, Optional

router = APIRouter(prefix="/api/transactions", tags=["transactions"])
transaction_service = TransactionService()


# ========== PATTERN ① PURE INCOME/EXPENSE ==========

@router.post("/deposit", response_model=TransactionResponse, status_code=201)
def create_deposit(request: DepositCreate, db: Session = Depends(get_db)):
    """Create deposit transaction (Pattern ①)."""
    try:
        tx = transaction_service.create_deposit(
            account_id=request.account_id,
            amount=request.amount,
            transaction_date=request.date,
            description=request.description,
            db=db
        )
        return tx
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/withdrawal", response_model=TransactionResponse, status_code=201)
def create_withdrawal(request: WithdrawalCreate, db: Session = Depends(get_db)):
    """Create withdrawal transaction (Pattern ①)."""
    try:
        tx = transaction_service.create_withdrawal(
            account_id=request.account_id,
            amount=request.amount,
            transaction_date=request.date,
            description=request.description,
            db=db
        )
        return tx
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/dividend", response_model=TransactionResponse, status_code=201)
def create_dividend(request: DividendCreate, db: Session = Depends(get_db)):
    """Create dividend transaction (Pattern ①)."""
    try:
        tx = transaction_service.create_dividend(
            account_id=request.account_id,
            ticker=request.ticker,
            amount=request.amount,
            transaction_date=request.date,
            description=request.description,
            db=db
        )
        return tx
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/interest", response_model=TransactionResponse, status_code=201)
def create_interest(request: InterestCreate, db: Session = Depends(get_db)):
    """Create interest transaction (Pattern ①) for MoneyMarket accounts."""
    try:
        tx = transaction_service.create_interest(
            account_id=request.account_id,
            amount=request.amount,
            transaction_date=request.date,
            description=request.description,
            db=db
        )
        return tx
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== PATTERN ② SIMPLE TRANSFER ==========

@router.post("/transfer", status_code=201)
def create_transfer(request: TransferCreate, db: Session = Depends(get_db)):
    """Create transfer transactions (Pattern ②)."""
    try:
        tx_out, tx_in = transaction_service.create_transfer(
            from_account_id=request.from_account_id,
            to_account_id=request.to_account_id,
            amount=request.amount,
            transaction_date=request.date,
            description=request.description,
            db=db
        )
        return {
            "status": "success",
            "data": {
                "transaction_out_id": tx_out.id,
                "transaction_in_id": tx_in.id
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== PATTERN ③ ASSET FORM CONVERSION ==========

@router.post("/buy", response_model=TransactionResponse, status_code=201)
def create_buy(request: BuyCreate, db: Session = Depends(get_db)):
    """Create buy transaction (Pattern ③)."""
    try:
        tx = transaction_service.create_buy(
            account_id=request.account_id,
            ticker=request.ticker,
            quantity=request.quantity,
            price=request.price,
            transaction_date=request.date,
            description=request.description,
            db=db
        )
        return tx
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sell", response_model=TransactionResponse, status_code=201)
def create_sell(request: SellCreate, db: Session = Depends(get_db)):
    """Create sell transaction (Pattern ③)."""
    try:
        tx = transaction_service.create_sell(
            account_id=request.account_id,
            ticker=request.ticker,
            quantity=request.quantity,
            price=request.price,
            transaction_date=request.date,
            description=request.description,
            db=db
        )
        return tx
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== PATTERN ④ EXCHANGE ==========

@router.post("/exchange", status_code=201)
def create_exchange(request: ExchangeCreate, db: Session = Depends(get_db)):
    """Create exchange transactions (Pattern ④)."""
    try:
        tx_sell, tx_buy = transaction_service.create_exchange(
            account_id=request.account_id,
            from_ticker=request.from_ticker,
            to_ticker=request.to_ticker,
            from_amount=request.from_amount,
            to_amount=request.to_amount,
            transaction_date=request.date,
            description=request.description,
            db=db
        )
        return {
            "status": "success",
            "data": {
                "transaction_sell_id": tx_sell.id,
                "transaction_buy_id": tx_buy.id
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== QUERY ENDPOINTS ==========

@router.get("/", response_model=List[TransactionResponse])
def list_transactions(
    account_id: Optional[int] = None,
    type: Optional[str] = None,
    ticker: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List transactions with filtering and pagination."""
    transactions = transaction_service.list_transactions(
        db=db,
        account_id=account_id,
        type=type,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Get a single transaction by ID."""
    tx = transaction_service.get_transaction(transaction_id, db)
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
    return tx


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Soft delete a transaction."""
    try:
        transaction_service.delete_transaction(transaction_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{transaction_id}/recalculate", status_code=200)
def trigger_recalculation(transaction_id: int, db: Session = Depends(get_db)):
    """
    Manually trigger recalculation from a transaction's date.

    Useful for:
    - Fixing data inconsistencies
    - After manual database edits
    - Debugging calculation issues

    This will:
    1. Get the transaction date
    2. Rebuild holdings from that date forward
    3. Regenerate snapshots from that date forward

    Args:
        transaction_id: ID of the transaction to use as starting point
        db: Database session

    Returns:
        Success status with recalculation details
    """
    from app.services.recalculation_service import RecalculationService

    tx = transaction_service.get_transaction(transaction_id, db)
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")

    recalc_service = RecalculationService()
    recalc_service.recalculate_from_date(tx.date, db)

    return {
        "status": "success",
        "message": f"Recalculated holdings and snapshots from {tx.date}",
        "recalculation_date": tx.date.isoformat()
    }
