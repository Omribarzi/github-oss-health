import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.repo import Repo
from app.models.discovery_snapshot import DiscoverySnapshot
from app.models.job_run import JobRun
from app.utils.github_client import GitHubClient, GitHubRateLimitExceeded
from app.config import settings

logger = logging.getLogger(__name__)


class DiscoveryService:
    """
    Discovery pipeline: broad, cheap weekly scrape.

    Finds all eligible repos meeting universe criteria:
    - stars >= 2000
    - created_at >= now() - 24 months
    - archived = false
    - fork = false
    - pushed_at within last 90 days (for eligibility check)

    Stores snapshot and tracks deltas (entered/exited/changed).
    """

    def __init__(self, db: Session):
        self.db = db
        self.client = GitHubClient()

    def _is_eligible(self, repo_data: Dict[str, Any]) -> bool:
        """Check if repo meets all universe criteria."""
        stars = repo_data.get("stargazers_count", 0)
        # Parse timestamps and convert to naive UTC (for database compatibility)
        created_at = datetime.fromisoformat(repo_data["created_at"].replace("Z", "+00:00")).replace(tzinfo=None)
        pushed_at = datetime.fromisoformat(repo_data["pushed_at"].replace("Z", "+00:00")).replace(tzinfo=None)
        archived = repo_data.get("archived", False)
        is_fork = repo_data.get("fork", False)

        now = datetime.utcnow()
        age_cutoff = now - timedelta(days=settings.max_age_months * 30)
        push_cutoff = now - timedelta(days=settings.max_days_since_push)

        eligible = (
            stars >= settings.min_stars
            and created_at >= age_cutoff
            and not archived
            and not is_fork
            and pushed_at >= push_cutoff
        )

        return eligible

    def _search_repos(self, query: str, sort: str = "stars", per_page: int = 100) -> List[Dict[str, Any]]:
        """
        Search GitHub repos using Search API.

        Returns list of repo data dictionaries.
        """
        repos = []
        page = 1
        max_pages = 10

        while page <= max_pages:
            try:
                result = self.client.get(
                    "search/repositories",
                    params={
                        "q": query,
                        "sort": sort,
                        "order": "desc",
                        "per_page": per_page,
                        "page": page,
                    },
                )

                if not result or "items" not in result:
                    break

                items = result["items"]
                if not items:
                    break

                repos.extend(items)
                logger.info(f"Fetched page {page}, total repos so far: {len(repos)}")

                if len(items) < per_page:
                    break

                page += 1

            except GitHubRateLimitExceeded:
                logger.error("Rate limit exceeded during discovery")
                raise

        return repos

    def _build_search_query(self) -> str:
        """Build GitHub search query for universe criteria."""
        now = datetime.utcnow()
        created_after = (now - timedelta(days=settings.max_age_months * 30)).strftime("%Y-%m-%d")

        query_parts = [
            f"stars:>={settings.min_stars}",
            f"created:>={created_after}",
            "archived:false",
            "fork:false",
        ]

        return " ".join(query_parts)

    def _upsert_repo(self, repo_data: Dict[str, Any], eligible: bool) -> Repo:
        """Insert or update repo in database."""
        github_id = repo_data["id"]
        existing = self.db.query(Repo).filter(Repo.github_id == github_id).first()

        repo_dict = {
            "github_id": github_id,
            "owner": repo_data["owner"]["login"],
            "name": repo_data["name"],
            "full_name": repo_data["full_name"],
            "language": repo_data.get("language"),
            "stars": repo_data["stargazers_count"],
            "forks": repo_data["forks_count"],
            "created_at": datetime.fromisoformat(repo_data["created_at"].replace("Z", "+00:00")).replace(tzinfo=None),
            "pushed_at": datetime.fromisoformat(repo_data["pushed_at"].replace("Z", "+00:00")).replace(tzinfo=None),
            "archived": repo_data.get("archived", False),
            "is_fork": repo_data.get("fork", False),
            "eligible": eligible,
            "last_seen_at": datetime.utcnow(),
        }

        if existing:
            for key, value in repo_dict.items():
                setattr(existing, key, value)
            return existing
        else:
            new_repo = Repo(**repo_dict, first_discovered_at=datetime.utcnow())
            self.db.add(new_repo)
            return new_repo

    def _create_snapshot(self, repo: Repo, repo_data: Dict[str, Any], eligible: bool):
        """Create immutable discovery snapshot."""
        snapshot = DiscoverySnapshot(
            repo_id=repo.id,
            snapshot_date=datetime.utcnow(),
            stars=repo_data["stargazers_count"],
            forks=repo_data["forks_count"],
            pushed_at=datetime.fromisoformat(repo_data["pushed_at"].replace("Z", "+00:00")).replace(tzinfo=None),
            eligible=eligible,
            snapshot_json={
                "github_id": repo_data["id"],
                "full_name": repo_data["full_name"],
                "description": repo_data.get("description"),
                "language": repo_data.get("language"),
                "homepage": repo_data.get("homepage"),
                "topics": repo_data.get("topics", []),
                "open_issues_count": repo_data.get("open_issues_count"),
                "watchers_count": repo_data.get("watchers_count"),
                "license": repo_data.get("license", {}).get("spdx_id") if repo_data.get("license") else None,
            },
        )
        self.db.add(snapshot)

    def run(self) -> Dict[str, Any]:
        """
        Execute discovery pipeline.

        Returns:
            Job statistics including repos processed, API calls, rate limit info.
        """
        job_run = JobRun(
            job_type="discovery",
            started_at=datetime.utcnow(),
            status="running",
            stats_json={},
        )
        self.db.add(job_run)
        self.db.commit()

        stats = {
            "repos_found": 0,
            "repos_eligible": 0,
            "repos_ineligible": 0,
            "new_repos": 0,
            "updated_repos": 0,
            "requests_made": 0,
            "rate_limit_remaining": None,
        }

        try:
            query = self._build_search_query()
            logger.info(f"Discovery query: {query}")

            repos_data = self._search_repos(query)
            stats["repos_found"] = len(repos_data)

            for repo_data in repos_data:
                eligible = self._is_eligible(repo_data)

                if eligible:
                    stats["repos_eligible"] += 1
                else:
                    stats["repos_ineligible"] += 1

                github_id = repo_data["id"]
                existing = self.db.query(Repo).filter(Repo.github_id == github_id).first()

                if existing:
                    stats["updated_repos"] += 1
                else:
                    stats["new_repos"] += 1

                repo = self._upsert_repo(repo_data, eligible)
                self.db.commit()

                self._create_snapshot(repo, repo_data, eligible)
                self.db.commit()

            client_stats = self.client.get_stats()
            stats["requests_made"] = client_stats["total_requests"]
            stats["rate_limit_remaining"] = client_stats["remaining_calls"]

            job_run.completed_at = datetime.utcnow()
            job_run.status = "completed"
            job_run.stats_json = stats
            self.db.commit()

            logger.info(f"Discovery completed: {stats}")
            return stats

        except GitHubRateLimitExceeded as e:
            logger.error(f"Rate limit exceeded: {e}")
            job_run.status = "failed"
            job_run.error_message = str(e)
            job_run.stats_json = stats
            self.db.commit()
            raise

        except Exception as e:
            logger.error(f"Discovery failed: {e}", exc_info=True)
            job_run.status = "failed"
            job_run.error_message = str(e)
            job_run.stats_json = stats
            self.db.commit()
            raise

        finally:
            self.client.close()
