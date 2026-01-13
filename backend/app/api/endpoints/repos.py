from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.repo import Repo
from app.models.discovery_snapshot import DiscoverySnapshot
from app.models.deep_snapshot import DeepSnapshot

router = APIRouter()


@router.get("/{owner}/{repo_name}")
def get_repo_detail(owner: str, repo_name: str, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific repo.

    Returns:
    - Basic repo info
    - Latest discovery snapshot
    - Latest deep analysis snapshot (if available)
    - Historical snapshots metadata
    """
    full_name = f"{owner}/{repo_name}"
    repo = db.query(Repo).filter(Repo.full_name == full_name).first()

    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Latest discovery snapshot
    latest_discovery = (
        db.query(DiscoverySnapshot)
        .filter(DiscoverySnapshot.repo_id == repo.id)
        .order_by(DiscoverySnapshot.snapshot_date.desc())
        .first()
    )

    # Latest deep analysis
    latest_deep = (
        db.query(DeepSnapshot)
        .filter(DeepSnapshot.repo_id == repo.id)
        .order_by(DeepSnapshot.snapshot_date.desc())
        .first()
    )

    # Historical snapshot counts
    discovery_count = db.query(DiscoverySnapshot).filter(DiscoverySnapshot.repo_id == repo.id).count()
    deep_count = db.query(DeepSnapshot).filter(DeepSnapshot.repo_id == repo.id).count()

    response = {
        "repo": {
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
            "last_seen_at": repo.last_seen_at.isoformat(),
        },
        "latest_discovery": None,
        "latest_deep_analysis": None,
        "history": {
            "discovery_snapshots": discovery_count,
            "deep_snapshots": deep_count,
        },
    }

    if latest_discovery:
        response["latest_discovery"] = {
            "snapshot_date": latest_discovery.snapshot_date.isoformat(),
            "stars": latest_discovery.stars,
            "forks": latest_discovery.forks,
            "pushed_at": latest_discovery.pushed_at.isoformat(),
            "eligible": latest_discovery.eligible,
            "raw_data": latest_discovery.snapshot_json,
        }

    if latest_deep:
        response["latest_deep_analysis"] = {
            "snapshot_date": latest_deep.snapshot_date.isoformat(),
            "contributor_health": {
                "monthly_active_contributors_6m": latest_deep.monthly_active_contributors_6m,
                "contribution_distribution": latest_deep.contribution_distribution,
            },
            "velocity": {
                "weekly_commits_12w": latest_deep.weekly_commits_12w,
                "weekly_prs_12w": latest_deep.weekly_prs_12w,
                "weekly_issues_12w": latest_deep.weekly_issues_12w,
                "commit_trend_slope": latest_deep.commit_trend_slope,
                "pr_trend_slope": latest_deep.pr_trend_slope,
                "issue_trend_slope": latest_deep.issue_trend_slope,
            },
            "responsiveness": {
                "median_issue_response_hours": latest_deep.median_issue_response_time_hours,
                "median_pr_response_hours": latest_deep.median_pr_response_time_hours,
                "availability": latest_deep.response_time_availability,
            },
            "adoption": {
                "dependents_count": latest_deep.dependents_count,
                "npm_downloads_30d": latest_deep.npm_downloads_30d,
                "fork_to_star_ratio": latest_deep.fork_to_star_ratio,
                "availability": latest_deep.adoption_availability,
            },
            "community_risk": {
                "top_contributor_share": latest_deep.top_contributor_share,
                "gini_coefficient": latest_deep.gini_coefficient,
                "active_maintainers_count": latest_deep.active_maintainers_count,
            },
            "health_index": latest_deep.health_index,
            "raw_metrics": latest_deep.metrics_json,
        }

    return response


@router.get("/{owner}/{repo_name}/history")
def get_repo_history(
    owner: str,
    repo_name: str,
    snapshot_type: str = "discovery",
    limit: int = 30,
    db: Session = Depends(get_db),
):
    """
    Get historical snapshots for a repo.

    Query params:
    - snapshot_type: "discovery" or "deep"
    - limit: Max number of snapshots to return
    """
    full_name = f"{owner}/{repo_name}"
    repo = db.query(Repo).filter(Repo.full_name == full_name).first()

    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if snapshot_type == "discovery":
        snapshots = (
            db.query(DiscoverySnapshot)
            .filter(DiscoverySnapshot.repo_id == repo.id)
            .order_by(DiscoverySnapshot.snapshot_date.desc())
            .limit(limit)
            .all()
        )

        return {
            "repo": full_name,
            "snapshot_type": "discovery",
            "snapshots": [
                {
                    "snapshot_date": s.snapshot_date.isoformat(),
                    "stars": s.stars,
                    "forks": s.forks,
                    "eligible": s.eligible,
                }
                for s in snapshots
            ],
        }

    elif snapshot_type == "deep":
        snapshots = (
            db.query(DeepSnapshot)
            .filter(DeepSnapshot.repo_id == repo.id)
            .order_by(DeepSnapshot.snapshot_date.desc())
            .limit(limit)
            .all()
        )

        return {
            "repo": full_name,
            "snapshot_type": "deep",
            "snapshots": [
                {
                    "snapshot_date": s.snapshot_date.isoformat(),
                    "commit_trend_slope": s.commit_trend_slope,
                    "pr_trend_slope": s.pr_trend_slope,
                    "top_contributor_share": s.top_contributor_share,
                    "health_index": s.health_index,
                }
                for s in snapshots
            ],
        }

    else:
        raise HTTPException(status_code=400, detail="Invalid snapshot_type. Use 'discovery' or 'deep'")
