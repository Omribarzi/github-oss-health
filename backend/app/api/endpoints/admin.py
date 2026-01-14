"""
Admin API endpoints for triggering background jobs.

These endpoints allow triggering data collection jobs via HTTP requests.
Protected by API key authentication for security.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.config import settings
from app.services.discovery import DiscoveryService
from app.services.deep_analysis import DeepAnalysisService
from app.services.queue_manager import QueueManager
from app.services.watchlist_generator import WatchlistGenerator

router = APIRouter()
logger = logging.getLogger(__name__)


def verify_admin_token(x_admin_token: Optional[str] = Header(None)):
    """
    Verify admin API token from header.

    Expected header: X-Admin-Token: <token>

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not hasattr(settings, 'admin_api_key') or not settings.admin_api_key:
        raise HTTPException(
            status_code=503,
            detail="Admin API is not configured. Set ADMIN_API_KEY environment variable."
        )

    if not x_admin_token:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Admin-Token header"
        )

    if x_admin_token != settings.admin_api_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid admin token"
        )

    return True


@router.post("/trigger-discovery")
def trigger_discovery(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _auth: bool = Depends(verify_admin_token)
):
    """
    Trigger discovery job to find eligible repos.

    This job:
    1. Searches GitHub for repos matching universe criteria
    2. Updates repo metadata
    3. Automatically refreshes the analysis queue

    Protected: Requires X-Admin-Token header

    Returns:
        Job status and estimated completion time
    """
    try:
        logger.info("Admin API: Discovery job triggered")

        service = DiscoveryService(db)
        stats = service.run()

        # Auto-refresh queue after discovery
        queue_mgr = QueueManager(db)
        queue_stats = queue_mgr.refresh_queue()

        logger.info(f"Discovery completed: {stats}")
        logger.info(f"Queue refreshed: {queue_stats}")

        return {
            "status": "completed",
            "job_type": "discovery",
            "stats": stats,
            "queue_stats": queue_stats,
            "message": "Discovery completed and queue refreshed successfully"
        }
    except Exception as e:
        logger.error(f"Discovery job failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Discovery job failed: {str(e)}"
        )


@router.post("/trigger-deep-analysis")
def trigger_deep_analysis(
    max_repos: int = Query(10, ge=1, le=100, description="Maximum repos to analyze"),
    db: Session = Depends(get_db),
    _auth: bool = Depends(verify_admin_token)
):
    """
    Trigger deep analysis job for top priority repos.

    This job:
    1. Analyzes repos from the priority queue
    2. Computes detailed metrics (contributors, velocity, responsiveness, adoption)
    3. Respects API rate limits

    Args:
        max_repos: Maximum number of repos to analyze (1-100)

    Protected: Requires X-Admin-Token header

    Returns:
        Job status and analysis results
    """
    try:
        logger.info(f"Admin API: Deep analysis job triggered (max_repos={max_repos})")

        service = DeepAnalysisService(db)
        stats = service.run(max_repos=max_repos)

        logger.info(f"Deep analysis completed: {stats}")

        return {
            "status": "completed",
            "job_type": "deep_analysis",
            "max_repos": max_repos,
            "stats": stats,
            "message": f"Analyzed {stats.get('repos_analyzed', 0)} repos successfully"
        }
    except Exception as e:
        logger.error(f"Deep analysis job failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Deep analysis job failed: {str(e)}"
        )


@router.post("/trigger-watchlist")
def trigger_watchlist(
    db: Session = Depends(get_db),
    _auth: bool = Depends(verify_admin_token)
):
    """
    Trigger watchlist generation job.

    This job:
    1. Computes three-track scores (Momentum, Durability, Adoption)
    2. Generates plain-English rationales
    3. Creates weekly investor watchlist

    Protected: Requires X-Admin-Token header

    Returns:
        Job status and watchlist summary
    """
    try:
        logger.info("Admin API: Watchlist generation triggered")

        generator = WatchlistGenerator(db)
        result = generator.generate_watchlist()

        logger.info(f"Watchlist generated: {result['stats']}")

        return {
            "status": "completed",
            "job_type": "watchlist",
            "stats": result['stats'],
            "top_repos": result['watchlist'][:5],  # Return top 5 as preview
            "message": "Watchlist generated successfully"
        }
    except Exception as e:
        logger.error(f"Watchlist generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Watchlist generation failed: {str(e)}"
        )


@router.post("/refresh-queue")
def refresh_queue(
    db: Session = Depends(get_db),
    _auth: bool = Depends(verify_admin_token)
):
    """
    Refresh analysis queue priorities.

    This job:
    1. Recalculates priorities for all eligible repos
    2. Ensures newly eligible repos get priority 10
    3. Updates stale repos (>30 days since last analysis)

    Protected: Requires X-Admin-Token header

    Returns:
        Queue statistics
    """
    try:
        logger.info("Admin API: Queue refresh triggered")

        queue_mgr = QueueManager(db)
        stats = queue_mgr.refresh_queue()
        summary = queue_mgr.get_queue_summary()

        logger.info(f"Queue refreshed: {stats}")

        return {
            "status": "completed",
            "job_type": "refresh_queue",
            "stats": stats,
            "summary": summary,
            "message": "Queue priorities refreshed successfully"
        }
    except Exception as e:
        logger.error(f"Queue refresh failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Queue refresh failed: {str(e)}"
        )


@router.get("/status")
def get_admin_status(_auth: bool = Depends(verify_admin_token)):
    """
    Check admin API status and configuration.

    Protected: Requires X-Admin-Token header

    Returns:
        System configuration and status
    """
    return {
        "status": "operational",
        "environment": settings.environment,
        "configuration": {
            "min_stars": settings.min_stars,
            "max_age_months": settings.max_age_months,
            "max_days_since_push": settings.max_days_since_push,
            "api_rate_limit_safety_threshold": settings.api_rate_limit_safety_threshold,
            "deep_analysis_max_requests_per_run": settings.deep_analysis_max_requests_per_run,
        },
        "message": "Admin API is configured and operational"
    }
