from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, UniqueConstraint
from datetime import datetime
from app.database import Base


class MarketData(Base):
    __tablename__ = 'market_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    hour = Column(Integer, nullable=True)  # 0-23 for hourly data, NULL for daily data
    closing_price = Column(Numeric(18, 4), nullable=True)
    exchange_rate = Column(Numeric(18, 6), nullable=True)
    source = Column(String(50), nullable=False)  # 'yahoo_finance', 'alpha_vantage', 'manual'
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Constraints - allows both daily (hour=NULL) and hourly (hour=0-23) data
    __table_args__ = (
        UniqueConstraint('ticker', 'date', 'hour', name='uq_ticker_date_hour'),
    )

    def __repr__(self):
        return f"<MarketData(ticker='{self.ticker}', date={self.date}, hour={self.hour}, source='{self.source}')>"
