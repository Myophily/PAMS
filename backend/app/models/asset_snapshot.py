from sqlalchemy import Column, Integer, Numeric, Date, DateTime, UniqueConstraint
from datetime import datetime
from app.database import Base


class AssetSnapshot(Base):
    __tablename__ = 'asset_snapshot'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True)
    total_assets_krw = Column(Numeric(18, 2), nullable=False)
    total_assets_usd = Column(Numeric(18, 2), nullable=False)
    principal = Column(Numeric(18, 2), nullable=False)  # Total deposits - withdrawals
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        UniqueConstraint('date', name='uq_snapshot_date'),
    )

    def __repr__(self):
        return f"<AssetSnapshot(date={self.date}, total_assets_krw={self.total_assets_krw})>"
