import logging
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.repo import Repo
from app.models.repo_queue import RepoQueue
from app.models.discovery_snapshot import DiscoverySnapshot
from app.models.deep_snapshot import DeepSnapshot

logger = logging.getLogger(__name__)


class QueueManager:
    """
    Manages prioritized queue for deep analysis.

    Priority levels (higher = more urgent):
    1. Newly eligible repos (10)
    2. High momentum repos - star velocity > threshold (8)
    3. Activity spikes - sudden increase in commits/PRs (7)
    4. Stale repos - no analysis in 30+ days (5)
    5. Regular refresh (3)
    """

    PRIORITY_NEW = 10
    PRIORITY_HIGH_MOMENTUM = 8
    PRIORITY_ACTIVITY_SPIKE = 7
    PRIORITY_STALE = 5
    PRIORITY_REGULAR = 3

    def __init__(self, db: Session):
        self.db = db

    def _get_star_velocity(self, repo: Repo) -> float:
        """
        Calculate star velocity (stars per day) from recent snapshots.
        """
        snapshots = self.db.query(DiscoverySnapshot).filter(
            DiscoverySnapshot.repo_id == repo.id
        ).order_by(DiscoverySnapshot.snapshot_date.desc()).limit(2).all()

        if len(snapshots) < 2:
            return 0.0

        recent, older = snapshots[0], snapshots[1]
        star_diff = recent.stars - older.stars
        time_diff_days = (recent.snapshot_date - older.snapshot_date).total_seconds() / 86400

        return star_diff / time_diff_days if time_diff_days > 0 else 0.0

    def _is_newly_eligible(self, repo: Repo) -> bool:
        """
        Check if repo recently became eligible (first discovered < 14 days ago).
        """
        days_since_discovery = (datetime.utcnow() - repo.first_discovered_at).days
        return days_since_discovery <= 14

    def _has_activity_spike(self, repo: Repo) -> bool:
        """
        Check if repo has recent activity spike.
        Would compare recent vs. historical activity, but requires deep snapshots.
        Simplified: check if pushed very recently.
        """
        days_since_push = (datetime.utcnow() - repo.pushed_at).days
        return days_since_push <= 3

    def _is_stale(self, repo_id: int) -> bool:
        """
        Check if repo hasn't been analyzed in 30+ days.
        """
        last_deep = self.db.query(DeepSnapshot).filter(
            DeepSnapshot.repo_id == repo_id
        ).order_by(DeepSnapshot.snapshot_date.desc()).first()

        if not last_deep:
            return True  # Never analyzed

        days_since_analysis = (datetime.utcnow() - last_deep.snapshot_date).days
        return days_since_analysis >= 30

    def _calculate_priority(self, repo: Repo) -> tuple[int, str]:
        """
        Calculate priority for a repo.

        Returns (priority_score, reason).
        """
        if self._is_newly_eligible(repo):
            return (self.PRIORITY_NEW, "newly_eligible")

        star_velocity = self._get_star_velocity(repo)
        if star_velocity > 10:  # More than 10 stars/day
            return (self.PRIORITY_HIGH_MOMENTUM, f"high_momentum_{int(star_velocity)}_stars_per_day")

        if self._has_activity_spike(repo):
            return (self.PRIORITY_ACTIVITY_SPIKE, "recent_activity_spike")

        if self._is_stale(repo.id):
            return (self.PRIORITY_STALE, "stale_analysis")

        return (self.PRIORITY_REGULAR, "regular_refresh")

    def refresh_queue(self) -> dict:
        """
        Refresh the queue: clear processed items and add/update priorities for eligible repos.

        Returns stats about queue operations.
        """
        stats = {
            "cleared_processed": 0,
            "added_to_queue": 0,
            "updated_priorities": 0
        }

        # Clear processed items older than 7 days
        old_processed = self.db.query(RepoQueue).filter(
            and_(
                RepoQueue.processed == True,
                RepoQueue.processed_at < datetime.utcnow() - timedelta(days=7)
            )
        ).delete()
        stats["cleared_processed"] = old_processed

        # Get all eligible repos
        eligible_repos = self.db.query(Repo).filter(Repo.eligible == True).all()

        for repo in eligible_repos:
            priority, reason = self._calculate_priority(repo)

            # Check if already in queue
            existing = self.db.query(RepoQueue).filter(
                and_(
                    RepoQueue.repo_id == repo.id,
                    RepoQueue.processed == False
                )
            ).first()

            if existing:
                # Update priority if changed
                if existing.priority != priority:
                    existing.priority = priority
                    existing.priority_reason = reason
                    stats["updated_priorities"] += 1
            else:
                # Add to queue
                queue_item = RepoQueue(
                    repo_id=repo.id,
                    priority=priority,
                    priority_reason=reason,
                    queued_at=datetime.utcnow(),
                    processed=False
                )
                self.db.add(queue_item)
                stats["added_to_queue"] += 1

        self.db.commit()
        logger.info(f"Queue refreshed: {stats}")
        return stats

    def get_queue_summary(self) -> dict:
        """
        Get summary statistics about the current queue.
        """
        total = self.db.query(RepoQueue).filter(RepoQueue.processed == False).count()

        by_priority = {}
        for priority_name, priority_val in [
            ("newly_eligible", self.PRIORITY_NEW),
            ("high_momentum", self.PRIORITY_HIGH_MOMENTUM),
            ("activity_spike", self.PRIORITY_ACTIVITY_SPIKE),
            ("stale", self.PRIORITY_STALE),
            ("regular", self.PRIORITY_REGULAR),
        ]:
            count = self.db.query(RepoQueue).filter(
                and_(
                    RepoQueue.processed == False,
                    RepoQueue.priority == priority_val
                )
            ).count()
            by_priority[priority_name] = count

        return {
            "total_pending": total,
            "by_priority": by_priority
        }
