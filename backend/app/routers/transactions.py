from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
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
    TransactionResponse,
    TransactionListResponse
)
from app.utils.date_helpers import is_past_transaction
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
        # Business logic validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        # Database constraint violations
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
        # Business logic validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        # Database constraint violations
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
        # Business logic validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        # Database constraint violations
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
        # Business logic validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        # Database constraint violations
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
        # Business logic validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        # Database constraint violations
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
            price_currency=request.price_currency,
            transaction_date=request.date,
            description=request.description,
            db=db
        )
        return tx
    except ValueError as e:
        # Business logic validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        # Database constraint violations
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


@router.post("/sell", response_model=TransactionResponse, status_code=201)
def create_sell(request: SellCreate, db: Session = Depends(get_db)):
    """Create sell transaction (Pattern ③)."""
    try:
        tx = transaction_service.create_sell(
            account_id=request.account_id,
            ticker=request.ticker,
            quantity=request.quantity,
            price=request.price,
            price_currency=request.price_currency,
            transaction_date=request.date,
            description=request.description,
            db=db
        )
        return tx
    except ValueError as e:
        # Business logic validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        # Database constraint violations
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


# ========== PATTERN ④ EXCHANGE ==========

@router.post("/exchange", status_code=201)
def create_exchange(request: ExchangeCreate, db: Session = Depends(get_db)):
    """Create exchange transactions (Pattern ④). Supports same-account and cross-account exchanges."""
    try:
        # Handle optional to_account_id
        to_account_id = request.to_account_id

        if to_account_id is None or to_account_id == request.account_id:
            # Same-account exchange (2 transactions)
            tx1, tx2 = transaction_service._create_exchange_pair(
                account_id=request.account_id,
                from_ticker=request.from_ticker,
                to_ticker=request.to_ticker,
                from_amount=request.from_amount,
                to_amount=request.to_amount,
                transaction_date=request.date,
                description=request.description,
                db=db
            )

            # Handle snapshots and recalculation
            transaction_service._create_transaction_snapshot(request.date, db)
            if is_past_transaction(request.date):
                transaction_service._trigger_recalculation(request.date, db)

            db.commit()

            return {
                "status": "success",
                "data": {
                    "type": "same_account",
                    "exchange_sell_id": tx1.id,
                    "exchange_buy_id": tx2.id
                }
            }
        else:
            # Cross-account exchange (4 transactions)
            tx1, tx2, tx3, tx4 = transaction_service.create_exchange(
                account_id=request.account_id,
                from_ticker=request.from_ticker,
                to_ticker=request.to_ticker,
                from_amount=request.from_amount,
                to_amount=request.to_amount,
                transaction_date=request.date,
                description=request.description,
                to_account_id=to_account_id,
                db=db
            )

            return {
                "status": "success",
                "data": {
                    "type": "cross_account",
                    "exchange_sell_id": tx1.id,
                    "exchange_buy_id": tx2.id,
                    "transfer_out_id": tx3.id,
                    "transfer_in_id": tx4.id
                }
            }
    except ValueError as e:
        # Business logic validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        # Database constraint violations
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


# ========== QUERY ENDPOINTS ==========

@router.get("/")
def list_transactions(
    account_id: Optional[int] = None,
    type: Optional[str] = None,
    ticker: Optional[str] = None,
    start_date: Optional[str] = None,  # Accept as string first
    end_date: Optional[str] = None,    # Accept as string first
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List transactions with filtering and pagination."""
    # Convert empty strings to None and parse dates
    type_filter = type if type and type.strip() else None
    ticker_filter = ticker if ticker and ticker.strip() else None

    # Parse date strings
    start_date_parsed = None
    end_date_parsed = None

    if start_date and start_date.strip():
        try:
            start_date_parsed = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid start_date format: {start_date}")

    if end_date and end_date.strip():
        try:
            end_date_parsed = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid end_date format: {end_date}")

    transactions = transaction_service.list_transactions(
        db=db,
        account_id=account_id,
        type=type_filter,
        ticker=ticker_filter,
        start_date=start_date_parsed,
        end_date=end_date_parsed,
        limit=limit,
        offset=offset
    )

    # Calculate total for pagination
    from app.models.transaction import Transaction
    total_query = db.query(Transaction).filter(Transaction.deleted_at.is_(None))
    if account_id:
        total_query = total_query.filter(Transaction.account_id == account_id)
    if type_filter:
        total_query = total_query.filter(Transaction.type == type_filter)
    if ticker_filter:
        total_query = total_query.filter(Transaction.ticker == ticker_filter)
    if start_date_parsed:
        total_query = total_query.filter(Transaction.date >= start_date_parsed)
    if end_date_parsed:
        total_query = total_query.filter(Transaction.date <= end_date_parsed)

    total = total_query.count()

    # Convert ORM models to dicts for JSON serialization
    transactions_data = [
        {
            "id": tx.id,
            "account_id": tx.account_id,
            "type": tx.type,
            "ticker": tx.ticker,
            "quantity": str(tx.quantity) if tx.quantity else None,
            "price": str(tx.price) if tx.price else None,
            "price_currency": tx.price_currency,
            "amount": str(tx.amount),
            "date": tx.date.isoformat(),
            "linked_tx_id": tx.linked_tx_id,
            "description": tx.description,
            "created_at": tx.created_at.isoformat(),
            "deleted_at": tx.deleted_at.isoformat() if tx.deleted_at else None
        }
        for tx in transactions
    ]

    return {
        "transactions": transactions_data,
        "total": total,
        "limit": limit,
        "offset": offset
    }


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
