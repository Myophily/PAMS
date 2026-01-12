from sqlalchemy import Column, Integer, Numeric, Boolean, ForeignKey, CheckConstraint, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base, KSTDateTime
from app.utils.timezone import now_kst


class RecurringTransfer(Base):
    """
    Recurring transfer configuration model.

    Stores rules for automatic monthly transfers between accounts.
    Each active recurring transfer is executed by the scheduler on the
    specified day_of_month, creating actual Transfer_Out/Transfer_In transactions.

    Attributes:
        id: Primary key
        from_account_id: Source account foreign key
        to_account_id: Target account foreign key
        amount: Transfer amount (always positive)
        day_of_month: Day of month to execute (1-31)
        description: Optional user notes
        is_active: Whether this recurring transfer is active
        last_executed_date: Last successful execution timestamp
        created_at: Creation timestamp
        deleted_at: Soft delete timestamp
    """
    __tablename__ = 'recurring_transfer'

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_account_id = Column(Integer, ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    to_account_id = Column(Integer, ForeignKey('account.id', ondelete='CASCADE'), nullable=True)  # NULL = external transfer
    amount = Column(Numeric(18, 2), nullable=False)
    day_of_month = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_executed_date = Column(KSTDateTime, nullable=True)
    created_at = Column(KSTDateTime, nullable=False, default=now_kst)
    deleted_at = Column(KSTDateTime, nullable=True)

    # Relationships
    from_account = relationship("Account", foreign_keys=[from_account_id])
    to_account = relationship("Account", foreign_keys=[to_account_id])

    # Constraints
    __table_args__ = (
        CheckConstraint('day_of_month >= 1 AND day_of_month <= 31', name='check_day_of_month'),
        # Note: Different accounts constraint moved to application layer to handle NULL properly
        CheckConstraint('amount > 0', name='check_positive_amount'),
        Index('idx_recurring_transfer_from_account', 'from_account_id'),
        Index('idx_recurring_transfer_to_account', 'to_account_id'),
        Index('idx_recurring_transfer_active', 'is_active'),
    )

    def __repr__(self):
        return f"<RecurringTransfer(id={self.id}, from={self.from_account_id}, to={self.to_account_id}, amount={self.amount}, day={self.day_of_month}, active={self.is_active})>"
