from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from app.database import Base
from datetime import datetime


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, index=True)
    repo_id = Column(Integer, ForeignKey("repos.id"), nullable=True, index=True)
    message = Column(String, nullable=False)
    resolved = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_alert_unresolved", "resolved", "severity", "created_at"),
    )
