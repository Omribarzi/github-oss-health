import pytest
from unittest.mock import Mock, patch
from app.utils.github_client import GitHubClient, GitHubRateLimitExceeded
from app.config import settings


class TestGitHubClient:
    """Test GitHub API client rate limit management."""

    def test_rate_limit_tracking(self):
        """Test that rate limit is tracked from response headers."""
        client = GitHubClient()

        headers = {
            "X-RateLimit-Remaining": "4500",
            "X-RateLimit-Reset": "1705176000",
        }

        client._update_rate_limit(headers)

        assert client.remaining_calls == 4500
        assert client.rate_limit_reset == 1705176000

    def test_safety_threshold_enforcement(self):
        """Test that client aborts when below safety threshold."""
        client = GitHubClient()
        client.remaining_calls = 400
        client.rate_limit_reset = 1705176000

        with pytest.raises(GitHubRateLimitExceeded):
            client._check_rate_limit()

    def test_stats_collection(self):
        """Test that client collects request statistics."""
        client = GitHubClient()
        client.total_requests = 50
        client.remaining_calls = 4950
        client.rate_limit_reset = 1705176000

        stats = client.get_stats()

        assert stats["total_requests"] == 50
        assert stats["remaining_calls"] == 4950
        assert stats["rate_limit_reset"] is not None
