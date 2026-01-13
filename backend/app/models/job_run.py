from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from app.database import Base
from datetime import datetime


class JobRun(Base):
    __tablename__ = "job_runs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String, nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)
    stats_json = Column(JSON, nullable=False)
    error_message = Column(String, nullable=True)

    __table_args__ = (
        Index("idx_job_type_started", "job_type", "started_at"),
    )
