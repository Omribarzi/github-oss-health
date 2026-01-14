import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import statistics

from app.models.repo import Repo
from app.models.deep_snapshot import DeepSnapshot
from app.models.repo_queue import RepoQueue
from app.models.job_run import JobRun
from app.utils.github_client import GitHubClient, GitHubRateLimitExceeded
from app.config import settings

logger = logging.getLogger(__name__)


class DeepAnalysisService:
    """
    Deep analysis pipeline: expensive, bi-weekly per-repo analysis.

    Computes:
    - Contributor health (monthly active contributors, distribution)
    - Velocity & trend (commits, PRs, issues over 12 weeks)
    - Responsiveness (median time to first maintainer response)
    - Adoption signals (dependents, npm downloads, fork-to-star ratio)
    - Community risk (top contributor share, Gini coefficient, bus factor)
    - Health index (optional, weighted composite)
    """

    def __init__(self, db: Session):
        self.db = db
        self.client = GitHubClient()

    def _get_contributors_last_6_months(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get monthly active contributors for last 6 months.

        Returns dict with contributor counts per month and distribution data.
        """
        try:
            # Get commit activity for last year to ensure 6 months of data
            endpoint = f"repos/{owner}/{repo}/stats/commit_activity"
            data = self.client.get(endpoint)

            if not data:
                return {
                    "monthly_contributors": None,
                    "distribution": None,
                    "availability": "not_available",
                    "reason": "GitHub statistics not available for this repo"
                }

            # GitHub returns 52 weeks, take last 26 weeks (6 months)
            recent_weeks = data[-26:] if len(data) >= 26 else data

            # Get contributor stats
            contributors_endpoint = f"repos/{owner}/{repo}/stats/contributors"
            contributors_data = self.client.get(contributors_endpoint)

            if not contributors_data:
                return {
                    "monthly_contributors": None,
                    "distribution": None,
                    "availability": "partial",
                    "reason": "Contributor stats not available"
                }

            # Calculate monthly active contributors (approximate from weekly data)
            # Group by ~4-week periods
            monthly_active = []
            for i in range(0, len(recent_weeks), 4):
                month_weeks = recent_weeks[i:i+4]
                total_contributors = sum(week.get("total", 0) for week in month_weeks)
                monthly_active.append(total_contributors if total_contributors > 0 else 0)

            # Calculate contribution distribution from all-time stats
            total_commits = sum(c.get("total", 0) for c in contributors_data)
            if total_commits > 0:
                contributions = [c.get("total", 0) for c in contributors_data]
                contributions.sort(reverse=True)

                top_1_share = contributions[0] / total_commits if len(contributions) > 0 else 0
                top_5_share = sum(contributions[:5]) / total_commits if len(contributions) >= 5 else sum(contributions) / total_commits

                distribution = {
                    "total_contributors": len(contributors_data),
                    "top_contributor_commits": contributions[0] if contributions else 0,
                    "top_1_share": round(top_1_share, 3),
                    "top_5_share": round(top_5_share, 3),
                }
            else:
                distribution = None

            return {
                "monthly_contributors": monthly_active,
                "distribution": distribution,
                "availability": "available",
                "reason": None
            }

        except Exception as e:
            logger.error(f"Error fetching contributors for {owner}/{repo}: {e}")
            return {
                "monthly_contributors": None,
                "distribution": None,
                "availability": "error",
                "reason": str(e)
            }

    def _get_weekly_activity_12_weeks(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get weekly commits, PRs, and issues for last 12 weeks.

        Returns activity data and trend slopes.
        """
        try:
            now = datetime.utcnow()
            twelve_weeks_ago = now - timedelta(weeks=12)

            # Weekly commits from commit activity
            commit_activity = self.client.get(f"repos/{owner}/{repo}/stats/commit_activity")
            if commit_activity:
                weekly_commits = [week.get("total", 0) for week in commit_activity[-12:]]
            else:
                weekly_commits = None

            # PRs and issues via search (more API calls)
            weekly_prs = []
            weekly_issues = []

            for week_offset in range(12):
                week_start = twelve_weeks_ago + timedelta(weeks=week_offset)
                week_end = week_start + timedelta(weeks=1)

                # PRs created in this week
                pr_query = f"repo:{owner}/{repo} is:pr created:{week_start.strftime('%Y-%m-%d')}..{week_end.strftime('%Y-%m-%d')}"
                pr_result = self.client.get("search/issues", params={"q": pr_query, "per_page": 1})
                weekly_prs.append(pr_result.get("total_count", 0) if pr_result else 0)

                # Issues created in this week
                issue_query = f"repo:{owner}/{repo} is:issue created:{week_start.strftime('%Y-%m-%d')}..{week_end.strftime('%Y-%m-%d')}"
                issue_result = self.client.get("search/issues", params={"q": issue_query, "per_page": 1})
                weekly_issues.append(issue_result.get("total_count", 0) if issue_result else 0)

            # Calculate trend slopes (simple linear regression)
            def calculate_slope(data: List[int]) -> Optional[float]:
                if not data or len(data) < 2:
                    return None
                n = len(data)
                x = list(range(n))
                x_mean = sum(x) / n
                y_mean = sum(data) / n
                numerator = sum((x[i] - x_mean) * (data[i] - y_mean) for i in range(n))
                denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
                return numerator / denominator if denominator != 0 else 0

            return {
                "weekly_commits": weekly_commits,
                "weekly_prs": weekly_prs,
                "weekly_issues": weekly_issues,
                "commit_trend_slope": calculate_slope(weekly_commits) if weekly_commits else None,
                "pr_trend_slope": calculate_slope(weekly_prs),
                "issue_trend_slope": calculate_slope(weekly_issues),
                "availability": "available"
            }

        except GitHubRateLimitExceeded:
            raise
        except Exception as e:
            logger.error(f"Error fetching activity for {owner}/{repo}: {e}")
            return {
                "weekly_commits": None,
                "weekly_prs": None,
                "weekly_issues": None,
                "commit_trend_slope": None,
                "pr_trend_slope": None,
                "issue_trend_slope": None,
                "availability": "error",
                "reason": str(e)
            }

    def _get_responsiveness(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Calculate median time to first maintainer response for issues and PRs.

        Maintainer identified via author_association: OWNER, MEMBER, COLLABORATOR.
        """
        try:
            # Sample recent closed issues and PRs
            issues = self.client.get(f"repos/{owner}/{repo}/issues", params={
                "state": "closed",
                "per_page": 30,
                "sort": "updated",
                "direction": "desc"
            })

            if not issues:
                return {
                    "median_issue_response_hours": None,
                    "median_pr_response_hours": None,
                    "availability": "not_available",
                    "reason": "No closed issues/PRs found"
                }

            issue_response_times = []
            pr_response_times = []

            for item in issues[:30]:  # Limit to reduce API calls
                item_number = item["number"]
                is_pr = "pull_request" in item

                # Get comments/timeline
                comments = self.client.get(f"repos/{owner}/{repo}/issues/{item_number}/comments")

                if not comments:
                    continue

                created_at = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")).replace(tzinfo=None)

                # Find first maintainer response
                for comment in comments:
                    association = comment.get("author_association", "")
                    if association in ["OWNER", "MEMBER", "COLLABORATOR"]:
                        commented_at = datetime.fromisoformat(comment["created_at"].replace("Z", "+00:00"))
                        response_time_hours = (commented_at - created_at).total_seconds() / 3600

                        if is_pr:
                            pr_response_times.append(response_time_hours)
                        else:
                            issue_response_times.append(response_time_hours)
                        break

            median_issue = statistics.median(issue_response_times) if issue_response_times else None
            median_pr = statistics.median(pr_response_times) if pr_response_times else None

            return {
                "median_issue_response_hours": round(median_issue, 2) if median_issue else None,
                "median_pr_response_hours": round(median_pr, 2) if median_pr else None,
                "availability": "available" if (median_issue or median_pr) else "insufficient_data",
                "reason": None if (median_issue or median_pr) else "Not enough maintainer responses found"
            }

        except GitHubRateLimitExceeded:
            raise
        except Exception as e:
            logger.error(f"Error calculating responsiveness for {owner}/{repo}: {e}")
            return {
                "median_issue_response_hours": None,
                "median_pr_response_hours": None,
                "availability": "error",
                "reason": str(e)
            }

    def _get_adoption_signals(self, owner: str, repo: str, language: Optional[str]) -> Dict[str, Any]:
        """
        Get adoption signals: dependents, npm downloads, fork-to-star ratio.
        """
        try:
            # Get dependents from GitHub (if available via dependency graph)
            # Note: This data is not always available via REST API
            dependents = None
            npm_downloads = None

            # For JavaScript/TypeScript projects, try to get npm download stats
            if language in ["JavaScript", "TypeScript"]:
                # This would require the npm package name, which we'd need to detect
                # For now, mark as not_implemented
                npm_downloads = None

            # Fork-to-star ratio is straightforward
            repo_data = self.client.get(f"repos/{owner}/{repo}")
            if repo_data:
                stars = repo_data.get("stargazers_count", 0)
                forks = repo_data.get("forks_count", 0)
                fork_to_star = round(forks / stars, 3) if stars > 0 else 0
            else:
                fork_to_star = None

            return {
                "dependents_count": dependents,
                "npm_downloads_30d": npm_downloads,
                "fork_to_star_ratio": fork_to_star,
                "availability": "partial" if fork_to_star else "limited",
                "reason": "Dependents and npm downloads require additional API integrations"
            }

        except Exception as e:
            logger.error(f"Error fetching adoption signals for {owner}/{repo}: {e}")
            return {
                "dependents_count": None,
                "npm_downloads_30d": None,
                "fork_to_star_ratio": None,
                "availability": "error",
                "reason": str(e)
            }

    def _calculate_community_risk(self, contributor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate community risk metrics: top contributor share, Gini coefficient, active maintainers.
        """
        distribution = contributor_data.get("distribution")

        if not distribution:
            return {
                "top_contributor_share": None,
                "gini_coefficient": None,
                "active_maintainers_count": None,
                "availability": "not_available"
            }

        return {
            "top_contributor_share": distribution.get("top_1_share"),
            "gini_coefficient": None,  # Would need full contribution list to calculate
            "active_maintainers_count": distribution.get("total_contributors"),
            "availability": "partial"
        }

    def analyze_repo(self, repo: Repo) -> Dict[str, Any]:
        """
        Perform deep analysis on a single repo.

        Returns metrics dict with all computed values.
        """
        owner, name = repo.owner, repo.name
        logger.info(f"Analyzing {owner}/{name}...")

        metrics = {}

        # Contributor health
        contributor_data = self._get_contributors_last_6_months(owner, name)
        metrics["contributor_health"] = contributor_data

        # Velocity & trend
        activity_data = self._get_weekly_activity_12_weeks(owner, name)
        metrics["velocity"] = activity_data

        # Responsiveness
        responsiveness_data = self._get_responsiveness(owner, name)
        metrics["responsiveness"] = responsiveness_data

        # Adoption signals
        adoption_data = self._get_adoption_signals(owner, name, repo.language)
        metrics["adoption"] = adoption_data

        # Community risk
        risk_data = self._calculate_community_risk(contributor_data)
        metrics["community_risk"] = risk_data

        return metrics

    def _save_deep_snapshot(self, repo: Repo, metrics: Dict[str, Any]):
        """Save deep analysis snapshot to database."""
        contributor_health = metrics.get("contributor_health", {})
        velocity = metrics.get("velocity", {})
        responsiveness = metrics.get("responsiveness", {})
        adoption = metrics.get("adoption", {})
        community_risk = metrics.get("community_risk", {})

        snapshot = DeepSnapshot(
            repo_id=repo.id,
            snapshot_date=datetime.utcnow(),
            monthly_active_contributors_6m=contributor_health.get("monthly_contributors"),
            contribution_distribution=contributor_health.get("distribution"),
            weekly_commits_12w=velocity.get("weekly_commits"),
            weekly_prs_12w=velocity.get("weekly_prs"),
            weekly_issues_12w=velocity.get("weekly_issues"),
            commit_trend_slope=velocity.get("commit_trend_slope"),
            pr_trend_slope=velocity.get("pr_trend_slope"),
            issue_trend_slope=velocity.get("issue_trend_slope"),
            median_issue_response_time_hours=responsiveness.get("median_issue_response_hours"),
            median_pr_response_time_hours=responsiveness.get("median_pr_response_hours"),
            response_time_availability=responsiveness.get("availability"),
            dependents_count=adoption.get("dependents_count"),
            npm_downloads_30d=adoption.get("npm_downloads_30d"),
            fork_to_star_ratio=adoption.get("fork_to_star_ratio"),
            adoption_availability=adoption.get("availability"),
            top_contributor_share=community_risk.get("top_contributor_share"),
            gini_coefficient=community_risk.get("gini_coefficient"),
            active_maintainers_count=community_risk.get("active_maintainers_count"),
            health_index=None,  # Computed later if needed
            metrics_json=metrics
        )

        self.db.add(snapshot)

    def run(self, max_repos: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute deep analysis pipeline.

        Processes repos from queue in priority order.
        """
        job_run = JobRun(
            job_type="deep_analysis",
            started_at=datetime.utcnow(),
            status="running",
            stats_json={}
        )
        self.db.add(job_run)
        self.db.commit()

        stats = {
            "repos_processed": 0,
            "repos_skipped": 0,
            "requests_made": 0,
            "rate_limit_remaining": None,
            "errors": []
        }

        try:
            # Get repos from queue
            queue_items = self.db.query(RepoQueue).filter(
                RepoQueue.processed == False
            ).order_by(
                RepoQueue.priority.desc(),
                RepoQueue.queued_at
            ).limit(max_repos or 100).all()

            for queue_item in queue_items:
                # Check rate limit budget
                if self.client.total_requests >= settings.deep_analysis_max_requests_per_run:
                    logger.warning("Max requests per run reached, stopping")
                    stats["repos_skipped"] += 1
                    break

                repo = self.db.query(Repo).filter(Repo.id == queue_item.repo_id).first()
                if not repo:
                    continue

                try:
                    metrics = self.analyze_repo(repo)
                    self._save_deep_snapshot(repo, metrics)

                    queue_item.processed = True
                    queue_item.processed_at = datetime.utcnow()
                    queue_item.last_deep_analysis_at = datetime.utcnow()

                    self.db.commit()
                    stats["repos_processed"] += 1

                except GitHubRateLimitExceeded as e:
                    logger.error(f"Rate limit exceeded: {e}")
                    stats["errors"].append(str(e))
                    break

                except Exception as e:
                    logger.error(f"Error analyzing {repo.full_name}: {e}")
                    stats["errors"].append(f"{repo.full_name}: {str(e)}")
                    continue

            client_stats = self.client.get_stats()
            stats["requests_made"] = client_stats["total_requests"]
            stats["rate_limit_remaining"] = client_stats["remaining_calls"]

            job_run.completed_at = datetime.utcnow()
            job_run.status = "completed"
            job_run.stats_json = stats
            self.db.commit()

            logger.info(f"Deep analysis completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Deep analysis failed: {e}", exc_info=True)
            job_run.status = "failed"
            job_run.error_message = str(e)
            job_run.stats_json = stats
            self.db.commit()
            raise

        finally:
            self.client.close()
