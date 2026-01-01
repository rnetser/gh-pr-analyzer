"""GitHub API client for fetching PR data."""

import os
from typing import Any

import httpx


class GitHubClient:
    """Client for GitHub API interactions."""

    def __init__(self, token: str | None = None) -> None:
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token. If not provided, reads from GITHUB_TOKEN env var.
                  If no token is available, unauthenticated requests are allowed (rate limited to 60/hour, public repos only).
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

        self.is_authenticated = bool(self.token)

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any] | list[dict[str, Any]]:
        """Make an HTTP request to GitHub API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx request

        Returns:
            JSON response from API

        Raises:
            ValueError: For HTTP errors, network errors, or timeouts with sanitized messages
        """
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, headers=self.headers, timeout=30.0, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status == 401:
                    raise ValueError("Invalid or expired GitHub token") from None
                elif status == 403:
                    raise ValueError("GitHub API rate limit exceeded or permission denied") from None
                elif status == 404:
                    raise ValueError(f"Resource not found: {endpoint}") from None
                raise ValueError(f"GitHub API error: {status}") from None
            except httpx.TimeoutException:
                raise ValueError(f"Request timed out after 30 seconds") from None
            except httpx.ConnectError:
                raise ValueError("Failed to connect to GitHub API. Check your network connection.") from None

    async def get_authenticated_user(self) -> dict[str, Any]:
        """Get the authenticated user's information.

        Returns:
            User information dictionary
        """
        return await self._request("GET", "/user")  # type: ignore[return-value]

    async def get_user_open_prs(self, username: str) -> list[dict[str, Any]]:
        """Get all open PRs authored by a user.

        Args:
            username: GitHub username

        Returns:
            List of PR dictionaries from search results
        """
        query = f"is:pr is:open author:{username}"
        result = await self._request("GET", "/search/issues", params={"q": query, "per_page": 100})
        return result["items"]  # type: ignore[return-value]

    async def get_pr_details(self, owner: str, repo: str, pr_number: int) -> dict[str, Any]:
        """Get detailed information about a specific PR.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            PR details dictionary including mergeable state
        """
        return await self._request("GET", f"/repos/{owner}/{repo}/pulls/{pr_number}")  # type: ignore[return-value]

    async def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Get reviews for a specific PR.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            List of review dictionaries
        """
        return await self._request("GET", f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews")  # type: ignore[return-value]

    async def get_pr_review_comments(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Get all review threads/comments to check for unresolved ones.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            List of review comment dictionaries
        """
        return await self._request("GET", f"/repos/{owner}/{repo}/pulls/{pr_number}/comments")  # type: ignore[return-value]

    async def get_check_runs(self, owner: str, repo: str, ref: str) -> list[dict[str, Any]]:
        """Get check runs for a specific commit ref.

        Args:
            owner: Repository owner
            repo: Repository name
            ref: Git reference (commit SHA, branch name, etc.)

        Returns:
            List of check run dictionaries
        """
        result = await self._request("GET", f"/repos/{owner}/{repo}/commits/{ref}/check-runs")
        return result["check_runs"]  # type: ignore[return-value]

    async def get_check_run_annotations(self, owner: str, repo: str, check_run_id: int) -> list[dict[str, Any]]:
        """Get annotations (error details) for a check run.

        Args:
            owner: Repository owner
            repo: Repository name
            check_run_id: Check run ID

        Returns:
            List of annotation dictionaries
        """
        return await self._request("GET", f"/repos/{owner}/{repo}/check-runs/{check_run_id}/annotations")  # type: ignore[return-value]

    async def check_rate_limit(self) -> dict[str, Any]:
        """Check current rate limit status.

        Returns:
            Rate limit information including remaining requests and reset time
        """
        return await self._request("GET", "/rate_limit")  # type: ignore[return-value]
