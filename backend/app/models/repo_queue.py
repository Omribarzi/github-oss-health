from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Boolean
from app.database import Base
from datetime import datetime


class RepoQueue(Base):
    __tablename__ = "repo_queue"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repos.id"), nullable=False, index=True)
    priority = Column(Integer, nullable=False, index=True)
    priority_reason = Column(String, nullable=False)
    queued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed = Column(Boolean, default=False, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    last_deep_analysis_at = Column(DateTime, nullable=True, index=True)

    __table_args__ = (
        Index("idx_queue_priority", "processed", "priority", "queued_at"),
    )
