import httpx
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)


class GitHubRateLimitExceeded(Exception):
    pass


class GitHubClient:
    """
    GitHub API client with rate limit management and exponential backoff.

    Tracks:
    - Remaining rate limit
    - Reset time
    - Requests made
    - Aborts when below safety threshold
    """

    def __init__(self):
        self.base_url = "https://api.github.com"
        self.token = settings.github_token
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.remaining_calls = None
        self.rate_limit_reset = None
        self.total_requests = 0
        self.session = httpx.Client(headers=self.headers, timeout=30.0)

    def _update_rate_limit(self, headers: dict):
        """Update rate limit tracking from response headers."""
        if "X-RateLimit-Remaining" in headers:
            self.remaining_calls = int(headers["X-RateLimit-Remaining"])
            logger.debug(f"Rate limit remaining: {self.remaining_calls}")

        if "X-RateLimit-Reset" in headers:
            self.rate_limit_reset = int(headers["X-RateLimit-Reset"])

    def _check_rate_limit(self):
        """Check if we're below safety threshold."""
        if self.remaining_calls is not None:
            if self.remaining_calls < settings.api_rate_limit_safety_threshold:
                reset_time = datetime.fromtimestamp(self.rate_limit_reset) if self.rate_limit_reset else "unknown"
                raise GitHubRateLimitExceeded(
                    f"Rate limit safety threshold reached. "
                    f"Remaining: {self.remaining_calls}. "
                    f"Resets at: {reset_time}"
                )

    def _handle_secondary_rate_limit(self, retry_after: int, attempt: int):
        """Handle secondary rate limit with exponential backoff."""
        wait_time = min(retry_after * (2 ** attempt), 300)
        logger.warning(f"Secondary rate limit hit. Waiting {wait_time}s (attempt {attempt})")
        time.sleep(wait_time)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 3) -> Dict[str, Any]:
        """
        Make GET request with rate limit handling and exponential backoff.

        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            max_retries: Maximum retry attempts for secondary rate limits

        Returns:
            JSON response as dict

        Raises:
            GitHubRateLimitExceeded: When rate limit safety threshold is reached
            httpx.HTTPError: For other HTTP errors
        """
        self._check_rate_limit()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params)
                self.total_requests += 1

                self._update_rate_limit(response.headers)

                if response.status_code == 403:
                    if "X-RateLimit-Remaining" in response.headers and int(response.headers["X-RateLimit-Remaining"]) == 0:
                        raise GitHubRateLimitExceeded("Primary rate limit exceeded")

                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < max_retries - 1:
                        self._handle_secondary_rate_limit(retry_after, attempt)
                        continue
                    else:
                        raise GitHubRateLimitExceeded("Secondary rate limit exceeded after max retries")

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                raise

        raise GitHubRateLimitExceeded("Max retries exceeded")

    def graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute GraphQL query with rate limit handling.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            GraphQL response data
        """
        self._check_rate_limit()

        url = f"{self.base_url}/graphql"
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = self.session.post(url, json=payload)
        self.total_requests += 1

        self._update_rate_limit(response.headers)
        response.raise_for_status()

        result = response.json()
        if "errors" in result:
            logger.error(f"GraphQL errors: {result['errors']}")

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get current rate limit statistics."""
        return {
            "total_requests": self.total_requests,
            "remaining_calls": self.remaining_calls,
            "rate_limit_reset": datetime.fromtimestamp(self.rate_limit_reset).isoformat() if self.rate_limit_reset else None,
        }

    def close(self):
        """Close HTTP session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
