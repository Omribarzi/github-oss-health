from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import json
from datetime import datetime

from app.database import get_db
from app.models.investor_watchlist import InvestorWatchlist
from app.models.repo import Repo

router = APIRouter()


@router.get("/latest")
def get_latest_watchlist(
    sort_by: str = Query("momentum", regex="^(momentum|durability|adoption)$"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """
    Get latest investor watchlist.

    Query params:
    - sort_by: Which track to sort by (momentum, durability, adoption)
    - limit: Max results (default 50, max 200)

    Returns three-track ranked list of newly interesting repos.
    """
    # Get latest watchlist date
    latest_date = (
        db.query(InvestorWatchlist.watchlist_date)
        .order_by(InvestorWatchlist.watchlist_date.desc())
        .first()
    )

    if not latest_date:
        return {
            "watchlist_date": None,
            "total": 0,
            "repos": [],
        }

    # Get watchlist entries for that date
    query = (
        db.query(InvestorWatchlist, Repo)
        .join(Repo, InvestorWatchlist.repo_id == Repo.id)
        .filter(InvestorWatchlist.watchlist_date == latest_date[0])
    )

    # Sort by requested track
    if sort_by == "momentum":
        query = query.order_by(InvestorWatchlist.momentum_score.desc())
    elif sort_by == "durability":
        query = query.order_by(InvestorWatchlist.durability_score.desc())
    elif sort_by == "adoption":
        query = query.order_by(InvestorWatchlist.adoption_score.desc())

    results = query.limit(limit).all()

    repos = []
    for entry, repo in results:
        repos.append({
            "full_name": repo.full_name,
            "language": repo.language,
            "stars": repo.stars,
            "created_at": repo.created_at.isoformat(),
            "scores": {
                "momentum": round(entry.momentum_score, 1),
                "durability": round(entry.durability_score, 1),
                "adoption": round(entry.adoption_score, 1),
            },
            "rationale": entry.rationale,
            "factors": entry.metrics_snapshot,
        })

    return {
        "watchlist_date": latest_date[0].isoformat(),
        "sort_by": sort_by,
        "total": len(repos),
        "repos": repos,
    }


@router.get("/export")
def export_watchlist(
    sort_by: str = Query("momentum", regex="^(momentum|durability|adoption)$"),
    db: Session = Depends(get_db),
):
    """
    Export latest watchlist as JSON file.

    Returns downloadable JSON with full three-track data.
    """
    # Get latest watchlist
    latest_date = (
        db.query(InvestorWatchlist.watchlist_date)
        .order_by(InvestorWatchlist.watchlist_date.desc())
        .first()
    )

    if not latest_date:
        return JSONResponse(
            content={"error": "No watchlist available"},
            status_code=404
        )

    query = (
        db.query(InvestorWatchlist, Repo)
        .join(Repo, InvestorWatchlist.repo_id == Repo.id)
        .filter(InvestorWatchlist.watchlist_date == latest_date[0])
    )

    if sort_by == "momentum":
        query = query.order_by(InvestorWatchlist.momentum_score.desc())
    elif sort_by == "durability":
        query = query.order_by(InvestorWatchlist.durability_score.desc())
    elif sort_by == "adoption":
        query = query.order_by(InvestorWatchlist.adoption_score.desc())

    results = query.all()

    export_data = {
        "generated_at": latest_date[0].isoformat(),
        "sort_by": sort_by,
        "total_repos": len(results),
        "methodology": "Three-track ranking: Momentum (growth velocity), Durability (contributor health), Adoption (usage signals)",
        "repos": []
    }

    for entry, repo in results:
        export_data["repos"].append({
            "full_name": repo.full_name,
            "github_url": f"https://github.com/{repo.full_name}",
            "language": repo.language,
            "stars": repo.stars,
            "forks": repo.forks,
            "created_at": repo.created_at.isoformat(),
            "age_days": entry.metrics_snapshot.get("age_days"),
            "scores": {
                "momentum": round(entry.momentum_score, 1),
                "durability": round(entry.durability_score, 1),
                "adoption": round(entry.adoption_score, 1),
            },
            "rationale": entry.rationale,
            "factors": {
                "momentum": entry.metrics_snapshot.get("momentum_factors"),
                "durability": entry.metrics_snapshot.get("durability_factors"),
                "adoption": entry.metrics_snapshot.get("adoption_factors"),
            }
        })

    # Return as downloadable JSON
    json_str = json.dumps(export_data, indent=2)
    filename = f"watchlist_{latest_date[0].strftime('%Y%m%d')}.json"

    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/history")
def get_watchlist_history(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
):
    """
    Get history of watchlist generation dates.

    Returns list of dates when watchlists were generated.
    """
    dates = (
        db.query(InvestorWatchlist.watchlist_date)
        .distinct()
        .order_by(InvestorWatchlist.watchlist_date.desc())
        .limit(limit)
        .all()
    )

    return {
        "watchlist_dates": [d[0].isoformat() for d in dates],
        "total": len(dates),
    }
