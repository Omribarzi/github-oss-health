from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Index
from app.database import Base
from datetime import datetime


class DiscoverySnapshot(Base):
    __tablename__ = "discovery_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repos.id"), nullable=False, index=True)
    snapshot_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    stars = Column(Integer, nullable=False)
    forks = Column(Integer, nullable=False)
    pushed_at = Column(DateTime, nullable=False)
    eligible = Column(Boolean, nullable=False)
    snapshot_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_discovery_repo_date", "repo_id", "snapshot_date"),
    )
