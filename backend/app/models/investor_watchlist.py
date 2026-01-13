from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Float, Index, JSON
from app.database import Base
from datetime import datetime


class InvestorWatchlist(Base):
    __tablename__ = "investor_watchlists"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repos.id"), nullable=False, index=True)
    watchlist_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Three-track scores
    momentum_score = Column(Float, nullable=False)
    durability_score = Column(Float, nullable=False)
    adoption_score = Column(Float, nullable=False)

    # Rationale
    rationale = Column(String, nullable=False)

    # Supporting data
    metrics_snapshot = Column(JSON, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_watchlist_date_momentum", "watchlist_date", "momentum_score"),
        Index("idx_watchlist_date_durability", "watchlist_date", "durability_score"),
        Index("idx_watchlist_date_adoption", "watchlist_date", "adoption_score"),
    )
