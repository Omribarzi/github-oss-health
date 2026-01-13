import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.repo import Repo
from app.models.discovery_snapshot import DiscoverySnapshot
from app.models.deep_snapshot import DeepSnapshot
from app.models.investor_watchlist import InvestorWatchlist

logger = logging.getLogger(__name__)


class WatchlistGenerator:
    """
    Generate weekly investor watchlist with three-track ranking.

    Tracks:
    1. Momentum - Star velocity, time-to-2000, activity spikes
    2. Durability - Contributors, responsiveness, bus factor
    3. Adoption - Dependents/downloads where available, fork-to-star ratio

    Eligibility:
    - Created within 24 months
    - Meets base criteria
    - Recently crossed 2000 stars OR exceptional signals
    """

    def __init__(self, db: Session):
        self.db = db

    def _calculate_star_velocity(self, repo: Repo) -> float:
        """Calculate stars per day from recent snapshots."""
        snapshots = (
            self.db.query(DiscoverySnapshot)
            .filter(DiscoverySnapshot.repo_id == repo.id)
            .order_by(DiscoverySnapshot.snapshot_date.desc())
            .limit(2)
            .all()
        )

        if len(snapshots) < 2:
            return 0.0

        recent, older = snapshots[0], snapshots[1]
        star_diff = recent.stars - older.stars
        time_diff_days = (recent.snapshot_date - older.snapshot_date).total_seconds() / 86400

        return star_diff / time_diff_days if time_diff_days > 0 else 0.0

    def _calculate_time_to_2000(self, repo: Repo) -> Optional[int]:
        """Calculate days from creation to 2000 stars."""
        if repo.stars < 2000:
            return None

        # Find first snapshot >= 2000 stars
        snapshot = (
            self.db.query(DiscoverySnapshot)
            .filter(
                DiscoverySnapshot.repo_id == repo.id,
                DiscoverySnapshot.stars >= 2000
            )
            .order_by(DiscoverySnapshot.snapshot_date.asc())
            .first()
        )

        if snapshot:
            days = (snapshot.snapshot_date - repo.created_at).days
            return days
        else:
            # Use current date as approximation
            days = (datetime.utcnow() - repo.created_at).days
            return days

    def _calculate_momentum_score(self, repo: Repo, deep: Optional[DeepSnapshot]) -> Tuple[float, str]:
        """
        Calculate momentum score (0-100).

        Factors:
        - Star velocity (40%)
        - Time to 2000 stars (30%)
        - Activity trend (30%)
        """
        score = 0.0
        factors = []

        # Star velocity (0-40 points)
        velocity = self._calculate_star_velocity(repo)
        if velocity > 0:
            velocity_score = min(velocity * 2, 40)  # Cap at 40
            score += velocity_score
            factors.append(f"{velocity:.1f} stars/day")

        # Time to 2000 (0-30 points, faster is better)
        time_to_2k = self._calculate_time_to_2000(repo)
        if time_to_2k:
            # Inverse: faster = higher score. 30 days = 30 points, 360 days = 5 points
            time_score = max(30 - (time_to_2k / 12), 5)
            score += min(time_score, 30)
            factors.append(f"{time_to_2k}d to 2k stars")

        # Activity trend (0-30 points)
        if deep and deep.commit_trend_slope is not None:
            if deep.commit_trend_slope > 0:
                trend_score = min(deep.commit_trend_slope * 10, 30)
                score += trend_score
                factors.append(f"positive commit trend")
            else:
                factors.append(f"declining activity")

        return (min(score, 100), ", ".join(factors) if factors else "insufficient data")

    def _calculate_durability_score(self, repo: Repo, deep: Optional[DeepSnapshot]) -> Tuple[float, str]:
        """
        Calculate durability score (0-100).

        Factors:
        - Active contributors count (40%)
        - Low bus factor / distributed contributions (30%)
        - Responsiveness (30%)
        """
        if not deep:
            return (0.0, "no deep analysis available")

        score = 0.0
        factors = []

        # Active contributors (0-40 points)
        if deep.active_maintainers_count:
            # More contributors = better. 1 = 5 pts, 10 = 20 pts, 50+ = 40 pts
            contrib_score = min(deep.active_maintainers_count * 0.8, 40)
            score += contrib_score
            factors.append(f"{deep.active_maintainers_count} contributors")

        # Bus factor (0-30 points, lower top contributor share = better)
        if deep.top_contributor_share:
            # Inverse: lower share = higher score
            # 10% = 30 pts, 50% = 10 pts, 90% = 0 pts
            bus_factor_score = max(30 - (deep.top_contributor_share * 30), 0)
            score += bus_factor_score
            factors.append(f"{int(deep.top_contributor_share * 100)}% top contributor")

        # Responsiveness (0-30 points)
        if deep.median_issue_response_time_hours:
            # Faster = better. <2h = 30pts, 48h = 15pts, >168h = 0pts
            response_hours = deep.median_issue_response_time_hours
            response_score = max(30 - (response_hours / 5.6), 0)
            score += min(response_score, 30)
            factors.append(f"{response_hours:.1f}h median response")

        return (min(score, 100), ", ".join(factors) if factors else "insufficient metrics")

    def _calculate_adoption_score(self, repo: Repo, deep: Optional[DeepSnapshot]) -> Tuple[float, str]:
        """
        Calculate adoption score (0-100).

        Factors:
        - Dependents count (50%)
        - npm/package downloads (30%)
        - Fork-to-star ratio (20%)
        """
        if not deep:
            return (0.0, "no deep analysis available")

        score = 0.0
        factors = []

        # Dependents (0-50 points)
        if deep.dependents_count:
            # Log scale: 10 deps = 15pts, 100 = 30pts, 1000+ = 50pts
            import math
            dep_score = min(math.log10(deep.dependents_count + 1) * 15, 50)
            score += dep_score
            factors.append(f"{deep.dependents_count} dependents")
        else:
            factors.append("dependents N/A")

        # Downloads (0-30 points)
        if deep.npm_downloads_30d:
            # Log scale: 1k = 10pts, 10k = 20pts, 100k+ = 30pts
            import math
            dl_score = min(math.log10(deep.npm_downloads_30d + 1) * 8, 30)
            score += dl_score
            factors.append(f"{deep.npm_downloads_30d:,} npm downloads")
        else:
            factors.append("downloads N/A")

        # Fork-to-star ratio (0-20 points)
        if deep.fork_to_star_ratio:
            # Higher ratio = more adoption. 0.1 = 5pts, 0.3 = 15pts, 0.5+ = 20pts
            ratio_score = min(deep.fork_to_star_ratio * 40, 20)
            score += ratio_score
            factors.append(f"{deep.fork_to_star_ratio:.2f} fork/star")

        return (min(score, 100), ", ".join(factors))

    def _generate_rationale(self, repo: Repo, momentum_factors: str, durability_factors: str, adoption_factors: str) -> str:
        """Generate 1-2 sentence rationale for why repo surfaced."""
        age_days = (datetime.utcnow() - repo.created_at).days

        rationale_parts = []

        if age_days < 60:
            rationale_parts.append(f"Recently created ({age_days}d ago)")

        if momentum_factors and "stars/day" in momentum_factors:
            rationale_parts.append("strong growth momentum")

        if durability_factors and "contributors" in durability_factors:
            rationale_parts.append("healthy contributor base")

        if len(rationale_parts) == 0:
            rationale_parts.append(f"Eligible repo with {repo.stars} stars")

        return ". ".join(rationale_parts) + "."

    def _is_watchlist_eligible(self, repo: Repo) -> bool:
        """
        Check if repo is eligible for watchlist.

        Criteria:
        - Created within 24 months
        - Meets base criteria
        - Recently crossed 2000 stars (within 30 days) OR has deep analysis with strong signals
        """
        age_months = (datetime.utcnow() - repo.created_at).days / 30

        if age_months > 24:
            return False

        if not repo.eligible:
            return False

        # Recently crossed 2000?
        first_2k_snapshot = (
            self.db.query(DiscoverySnapshot)
            .filter(
                DiscoverySnapshot.repo_id == repo.id,
                DiscoverySnapshot.stars >= 2000
            )
            .order_by(DiscoverySnapshot.snapshot_date.asc())
            .first()
        )

        if first_2k_snapshot:
            days_since_2k = (datetime.utcnow() - first_2k_snapshot.snapshot_date).days
            if days_since_2k <= 30:
                return True

        # Has deep analysis with strong signals?
        deep = (
            self.db.query(DeepSnapshot)
            .filter(DeepSnapshot.repo_id == repo.id)
            .order_by(DeepSnapshot.snapshot_date.desc())
            .first()
        )

        if deep:
            # Check for exceptional signals
            if (deep.commit_trend_slope and deep.commit_trend_slope > 5) or \
               (deep.active_maintainers_count and deep.active_maintainers_count > 20) or \
               (deep.median_issue_response_time_hours and deep.median_issue_response_time_hours < 6):
                return True

        return False

    def generate_watchlist(self) -> Dict[str, Any]:
        """
        Generate weekly investor watchlist.

        Returns stats and list of repos with three-track scores.
        """
        logger.info("Generating investor watchlist...")

        # Get all repos created within 24 months
        cutoff_date = datetime.utcnow() - timedelta(days=24 * 30)
        repos = (
            self.db.query(Repo)
            .filter(
                Repo.created_at >= cutoff_date,
                Repo.eligible == True
            )
            .all()
        )

        watchlist_entries = []
        stats = {
            "total_candidates": len(repos),
            "watchlist_size": 0,
            "generated_at": datetime.utcnow(),
        }

        for repo in repos:
            if not self._is_watchlist_eligible(repo):
                continue

            # Get latest deep snapshot
            deep = (
                self.db.query(DeepSnapshot)
                .filter(DeepSnapshot.repo_id == repo.id)
                .order_by(DeepSnapshot.snapshot_date.desc())
                .first()
            )

            # Calculate three-track scores
            momentum_score, momentum_factors = self._calculate_momentum_score(repo, deep)
            durability_score, durability_factors = self._calculate_durability_score(repo, deep)
            adoption_score, adoption_factors = self._calculate_adoption_score(repo, deep)

            rationale = self._generate_rationale(repo, momentum_factors, durability_factors, adoption_factors)

            # Save to database
            entry = InvestorWatchlist(
                repo_id=repo.id,
                watchlist_date=datetime.utcnow(),
                momentum_score=momentum_score,
                durability_score=durability_score,
                adoption_score=adoption_score,
                rationale=rationale,
                metrics_snapshot={
                    "momentum_factors": momentum_factors,
                    "durability_factors": durability_factors,
                    "adoption_factors": adoption_factors,
                    "stars": repo.stars,
                    "age_days": (datetime.utcnow() - repo.created_at).days,
                },
            )
            self.db.add(entry)

            watchlist_entries.append({
                "repo": repo.full_name,
                "momentum_score": momentum_score,
                "durability_score": durability_score,
                "adoption_score": adoption_score,
                "rationale": rationale,
            })

        self.db.commit()
        stats["watchlist_size"] = len(watchlist_entries)

        logger.info(f"Watchlist generated: {stats['watchlist_size']} repos")
        return {
            "stats": stats,
            "watchlist": watchlist_entries,
        }
