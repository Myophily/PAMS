from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, CheckConstraint, Text, Index
from sqlalchemy.orm import relationship
from datetime import date, datetime
from app.database import Base, KSTDateTime
from app.utils.timezone import now_kst


class Transaction(Base):
    __tablename__ = 'transaction'

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(20), nullable=False)
    ticker = Column(String(20), nullable=True)
    quantity = Column(Numeric(18, 8), nullable=True)
    price = Column(Numeric(18, 4), nullable=True)
    price_currency = Column(String(3), nullable=True)  # Currency for stock prices (USD, KRW, JPY, etc.)
    amount = Column(Numeric(18, 2), nullable=False)  # CRITICAL: Decimal for money, NEVER Float
    date = Column(KSTDateTime, nullable=False)  # DateTime with minute precision (HH:MM)
    linked_tx_id = Column(Integer, ForeignKey('transaction.id', ondelete='SET NULL'), nullable=True)  # Self-referencing
    description = Column(Text, nullable=True)
    created_at = Column(KSTDateTime, nullable=False, default=now_kst)
    deleted_at = Column(KSTDateTime, nullable=True)  # Soft delete - transactions are immutable

    # Relationships
    account = relationship("Account", back_populates="transactions")
    linked_transaction = relationship("Transaction", remote_side=[id], uselist=False)

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            type.in_(['Deposit', 'Withdrawal', 'Dividend', 'Buy', 'Sell',
                     'Transfer_In', 'Transfer_Out', 'Exchange', 'Interest']),
            name='check_transaction_type'
        ),
        Index('idx_transaction_account', 'account_id'),
        Index('idx_transaction_date', 'date'),
        Index('idx_transaction_type', 'type'),
        Index('idx_transaction_ticker', 'ticker'),
        Index('idx_transaction_linked', 'linked_tx_id'),
    )

    def __repr__(self):
        return f"<Transaction(id={self.id}, account_id={self.account_id}, type='{self.type}', amount={self.amount}, date={self.date})>"
