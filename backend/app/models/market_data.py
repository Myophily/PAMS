from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, UniqueConstraint
from datetime import datetime
from app.database import Base


class MarketData(Base):
    __tablename__ = 'market_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    closing_price = Column(Numeric(18, 4), nullable=True)
    exchange_rate = Column(Numeric(18, 6), nullable=True)
    source = Column(String(50), nullable=False)  # 'yahoo_finance', 'alpha_vantage', 'manual'
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        UniqueConstraint('ticker', 'date', name='uq_ticker_date'),
    )

    def __repr__(self):
        return f"<MarketData(ticker='{self.ticker}', date={self.date}, source='{self.source}')>"
