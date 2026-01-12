from sqlalchemy import Column, Integer, String, CheckConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base, KSTDateTime
from app.utils.timezone import now_kst


class Account(Base):
    __tablename__ = 'account'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(20), nullable=False)
    created_at = Column(KSTDateTime, nullable=False, default=now_kst)

    # Relationships
    holdings = relationship("Holding", back_populates="account", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            type.in_(['Deposit', 'Securities', 'ForeignCurrency', 'MoneyMarket', 'Savings']),
            name='check_account_type'
        ),
        Index('idx_account_type', 'type'),
    )

    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', type='{self.type}')>"
