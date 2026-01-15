"""
Admin API endpoints for triggering background jobs.

These endpoints allow triggering data collection jobs via HTTP requests.
Protected by API key authentication for security.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import Optional
import logging
import secrets
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.config import settings

# Rate limiter for admin endpoints (stricter limits)
limiter = Limiter(key_func=get_remote_address)
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

    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(x_admin_token, settings.admin_api_key):
        raise HTTPException(
            status_code=403,
            detail="Invalid admin token"
        )

    return True


@router.post("/trigger-discovery")
@limiter.limit("10/hour")
def trigger_discovery(
    request: Request,
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

        logger.info(f"Discovery completed: {stats}")

        # Auto-refresh queue after discovery
        try:
            queue_mgr = QueueManager(db)
            queue_stats = queue_mgr.refresh_queue()
            logger.info(f"Queue refreshed: {queue_stats}")
        except Exception as e:
            logger.warning(f"Queue refresh failed (non-fatal): {e}", exc_info=True)
            queue_stats = {"error": str(e)}

        return {
            "status": "completed",
            "job_type": "discovery",
            "stats": stats,
            "queue_stats": queue_stats,
            "message": "Discovery completed successfully"
        }
    except Exception as e:
        logger.error(f"Discovery job failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Discovery job failed: {str(e)}"
        )


@router.post("/trigger-deep-analysis")
@limiter.limit("10/hour")
def trigger_deep_analysis(
    request: Request,
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
@limiter.limit("10/hour")
def trigger_watchlist(
    request: Request,
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
@limiter.limit("10/hour")
def refresh_queue(
    request: Request,
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


@router.post("/reset-database")
@limiter.limit("5/hour")
def reset_database(
    request: Request,
    db: Session = Depends(get_db),
    _auth: bool = Depends(verify_admin_token)
):
    """
    **DANGER:** Reset database - drops all tables and recreates schema.

    This endpoint is for development/testing only. It will:
    - Drop all existing tables
    - Recreate schema from models
    - Clear all data

    Use with extreme caution!

    BLOCKED in production environment.
    """
    # Security: Block this dangerous endpoint in production
    if settings.environment == "production":
        logger.warning("Admin API: DATABASE RESET BLOCKED - production environment")
        raise HTTPException(
            status_code=403,
            detail="Database reset is disabled in production environment"
        )

    try:
        logger.warning("Admin API: DATABASE RESET REQUESTED")

        from app.database import Base, engine

        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        logger.info("Dropped all tables")

        # Recreate all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Recreated all tables")

        return {
            "status": "completed",
            "message": "Database reset successfully - all data cleared",
            "warning": "All previous data has been permanently deleted"
        }
    except Exception as e:
        logger.error(f"Database reset failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Database reset failed: {str(e)}"
        )


@router.get("/status")
@limiter.limit("30/minute")
def get_admin_status(request: Request, _auth: bool = Depends(verify_admin_token)):
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
