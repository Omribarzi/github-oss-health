from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index
from app.database import Base
from datetime import datetime


class Repo(Base):
    __tablename__ = "repos"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(Integer, unique=True, nullable=False, index=True)
    owner = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    full_name = Column(String, nullable=False, unique=True, index=True)
    language = Column(String, nullable=True, index=True)
    stars = Column(Integer, nullable=False, index=True)
    forks = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, index=True)
    pushed_at = Column(DateTime, nullable=False, index=True)
    archived = Column(Boolean, default=False, nullable=False)
    is_fork = Column(Boolean, default=False, nullable=False)
    first_discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    eligible = Column(Boolean, default=True, nullable=False, index=True)

    __table_args__ = (
        Index("idx_repo_stars_created", "stars", "created_at"),
        Index("idx_repo_eligible_stars", "eligible", "stars"),
    )
