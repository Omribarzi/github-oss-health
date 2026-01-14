from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.repo import Repo
from app.models.discovery_snapshot import DiscoverySnapshot
from app.models.job_run import JobRun
from app.config import settings

router = APIRouter()


@router.get("/stats")
def get_universe_stats(db: Session = Depends(get_db)):
    """
    Get universe overview statistics.

    Returns:
    - Total repos in universe
    - Eligible vs ineligible count
    - Breakdown by language
    - Last update timestamp
    - Universe criteria
    """
    total_repos = db.query(Repo).count()
    eligible_repos = db.query(Repo).filter(Repo.eligible == True).count()
    ineligible_repos = total_repos - eligible_repos

    # Language breakdown (top 10)
    language_counts = (
        db.query(Repo.language, func.count(Repo.id))
        .filter(Repo.eligible == True, Repo.language.isnot(None))
        .group_by(Repo.language)
        .order_by(func.count(Repo.id).desc())
        .limit(10)
        .all()
    )

    # Last discovery run
    last_discovery = (
        db.query(JobRun)
        .filter(JobRun.job_type == "discovery", JobRun.status == "completed")
        .order_by(JobRun.completed_at.desc())
        .first()
    )

    # Last deep analysis run
    last_deep = (
        db.query(JobRun)
        .filter(JobRun.job_type == "deep_analysis", JobRun.status == "completed")
        .order_by(JobRun.completed_at.desc())
        .first()
    )

    return {
        "universe_criteria": {
            "min_stars": settings.min_stars,
            "max_age_months": settings.max_age_months,
            "max_days_since_push": settings.max_days_since_push,
            "archived": False,
            "fork": False,
        },
        "counts": {
            "total_repos": total_repos,
            "eligible_repos": eligible_repos,
            "ineligible_repos": ineligible_repos,
        },
        "language_breakdown": [
            {"language": lang or "Unknown", "count": count}
            for lang, count in language_counts
        ],
        "last_update": {
            "discovery": last_discovery.completed_at.isoformat() if last_discovery else None,
            "deep_analysis": last_deep.completed_at.isoformat() if last_deep else None,
        },
    }


@router.get("/repos")
def list_repos(
    language: Optional[str] = None,
    min_stars: Optional[int] = None,
    max_stars: Optional[int] = None,
    eligible_only: bool = True,
    sort_by: str = "stars",
    order: str = "desc",
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    List repos with filtering and pagination.

    Query params:
    - language: Filter by programming language
    - min_stars, max_stars: Star range filter
    - eligible_only: Only show eligible repos (default: true)
    - sort_by: Field to sort by (stars, created_at, pushed_at)
    - order: Sort order (asc, desc)
    - limit: Max results (default 100, max 1000)
    - offset: Pagination offset
    """
    query = db.query(Repo)

    if eligible_only:
        query = query.filter(Repo.eligible == True)

    if language:
        query = query.filter(Repo.language == language)

    if min_stars:
        query = query.filter(Repo.stars >= min_stars)

    if max_stars:
        query = query.filter(Repo.stars <= max_stars)

    # Sorting
    sort_field = getattr(Repo, sort_by, Repo.stars)
    if order == "desc":
        query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(sort_field.asc())

    total = query.count()
    repos = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "repos": [
            {
                "id": repo.id,
                "github_id": repo.github_id,
                "full_name": repo.full_name,
                "owner": repo.owner,
                "name": repo.name,
                "language": repo.language,
                "stars": repo.stars,
                "forks": repo.forks,
                "created_at": repo.created_at.isoformat(),
                "pushed_at": repo.pushed_at.isoformat(),
                "eligible": repo.eligible,
                "first_discovered_at": repo.first_discovered_at.isoformat(),
            }
            for repo in repos
        ],
    }
