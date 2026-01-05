from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.database import Base


class Holding(Base):
    __tablename__ = 'holding'

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    ticker = Column(String(20), nullable=False)
    quantity = Column(Numeric(18, 8), nullable=False, default=0)  # NEVER use Float for money
    avg_price = Column(Numeric(18, 4), nullable=False, default=0)  # NEVER use Float for money

    # Relationship
    account = relationship("Account", back_populates="holdings")

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint('account_id', 'ticker', name='uq_account_ticker'),
        Index('idx_holding_account', 'account_id'),
        Index('idx_holding_ticker', 'ticker'),
    )

    def __repr__(self):
        return f"<Holding(id={self.id}, account_id={self.account_id}, ticker='{self.ticker}', quantity={self.quantity})>"
