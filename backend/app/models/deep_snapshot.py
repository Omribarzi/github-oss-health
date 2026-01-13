from sqlalchemy import Column, Integer, ForeignKey, DateTime, JSON, Index, Float, String
from app.database import Base
from datetime import datetime


class DeepSnapshot(Base):
    __tablename__ = "deep_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repos.id"), nullable=False, index=True)
    snapshot_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Contributor Health
    monthly_active_contributors_6m = Column(JSON, nullable=True)
    contribution_distribution = Column(JSON, nullable=True)

    # Velocity & Trend
    weekly_commits_12w = Column(JSON, nullable=True)
    weekly_prs_12w = Column(JSON, nullable=True)
    weekly_issues_12w = Column(JSON, nullable=True)
    commit_trend_slope = Column(Float, nullable=True)
    pr_trend_slope = Column(Float, nullable=True)
    issue_trend_slope = Column(Float, nullable=True)

    # Responsiveness
    median_issue_response_time_hours = Column(Float, nullable=True)
    median_pr_response_time_hours = Column(Float, nullable=True)
    response_time_availability = Column(String, nullable=True)

    # Adoption Signals
    dependents_count = Column(Integer, nullable=True)
    npm_downloads_30d = Column(Integer, nullable=True)
    fork_to_star_ratio = Column(Float, nullable=True)
    adoption_availability = Column(String, nullable=True)

    # Community Risk
    top_contributor_share = Column(Float, nullable=True)
    gini_coefficient = Column(Float, nullable=True)
    active_maintainers_count = Column(Integer, nullable=True)

    # Health Index (optional)
    health_index = Column(Float, nullable=True)

    # Raw snapshot data
    metrics_json = Column(JSON, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_deep_repo_date", "repo_id", "snapshot_date"),
    )
