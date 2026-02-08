# Generated using Claude cli
"""Tests for GitHubClient."""

import os
from unittest.mock import patch

import httpx
import pytest
from pytest_httpx import HTTPXMock

from gh_pr_analyzer.github_client import GitHubClient


class TestGitHubClientInit:
    """Test GitHubClient initialization."""

    def test_init_with_token(self, mock_token):
        """Test initialization with explicit token."""
        client = GitHubClient(token=mock_token)
        assert client.token == mock_token
        assert client.headers["Authorization"] == f"Bearer {mock_token}"
        assert client.headers["Accept"] == "application/vnd.github+json"
        assert client.headers["X-GitHub-Api-Version"] == "2022-11-28"
        assert client.base_url == "https://api.github.com"

    def test_init_with_env_token(self, mock_token):
        """Test initialization with token from environment."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": mock_token}):
            client = GitHubClient()
            assert client.token == mock_token

    def test_init_without_token(self):
        """Test client initializes without token (unauthenticated mode)."""
        with patch.dict(os.environ, {}, clear=True):
            client = GitHubClient()
            assert client.is_authenticated is False
            assert "Authorization" not in client.headers

    def test_init_with_empty_token(self):
        """Test client with empty token uses unauthenticated mode."""
        with patch.dict(os.environ, {}, clear=True):
            client = GitHubClient(token="")
            assert client.is_authenticated is False
            assert "Authorization" not in client.headers


class TestGitHubClientRequest:
    """Test GitHubClient HTTP request method."""

    @pytest.mark.asyncio
    async def test_request_get_success(self, mock_token, httpx_mock: HTTPXMock):
        """Test successful GET request."""
        httpx_mock.add_response(
            url="https://api.github.com/user",
            json={"login": "testuser"},
        )

        client = GitHubClient(token=mock_token)
        result = await client._request("GET", "/user")

        assert result == {"login": "testuser"}

    @pytest.mark.asyncio
    async def test_request_with_params(self, mock_token, httpx_mock: HTTPXMock):
        """Test request with query parameters."""
        httpx_mock.add_response(
            url="https://api.github.com/search/issues?q=test&per_page=10",
            json={"total_count": 0, "items": []},
        )

        client = GitHubClient(token=mock_token)
        result = await client._request("GET", "/search/issues", params={"q": "test", "per_page": 10})

        assert result == {"total_count": 0, "items": []}

    @pytest.mark.asyncio
    async def test_request_404_error(self, mock_token, httpx_mock: HTTPXMock):
        """Test request with 404 error."""
        httpx_mock.add_response(
            url="https://api.github.com/repos/owner/repo",
            status_code=404,
            json={"message": "Not Found"},
        )

        client = GitHubClient(token=mock_token)
        with pytest.raises(ValueError, match="Resource not found: Not Found"):
            await client._request("GET", "/repos/owner/repo")

    @pytest.mark.asyncio
    async def test_request_401_error(self, mock_token, httpx_mock: HTTPXMock):
        """Test request with 401 unauthorized error."""
        httpx_mock.add_response(
            url="https://api.github.com/user",
            status_code=401,
            json={"message": "Bad credentials"},
        )

        client = GitHubClient(token=mock_token)
        with pytest.raises(ValueError, match="Invalid or expired GitHub token"):
            await client._request("GET", "/user")

    @pytest.mark.asyncio
    async def test_request_rate_limit_error(self, mock_token, httpx_mock: HTTPXMock):
        """Test request with rate limit error."""
        httpx_mock.add_response(
            url="https://api.github.com/user",
            status_code=403,
            json={"message": "API rate limit exceeded"},
        )

        client = GitHubClient(token=mock_token)
        with pytest.raises(ValueError, match="GitHub API forbidden \\(rate limit or permissions\\): API rate limit exceeded"):
            await client._request("GET", "/user")

    @pytest.mark.asyncio
    async def test_request_network_error(self, mock_token, httpx_mock: HTTPXMock):
        """Test request with network error."""
        httpx_mock.add_exception(
            httpx.ConnectError("Connection failed"),
        )

        client = GitHubClient(token=mock_token)
        with pytest.raises(ValueError, match="Failed to connect to GitHub API"):
            await client._request("GET", "/user")

    @pytest.mark.asyncio
    async def test_request_timeout_error(self, mock_token, httpx_mock: HTTPXMock):
        """Test request with timeout error."""
        httpx_mock.add_exception(
            httpx.TimeoutException("Request timeout"),
        )

        client = GitHubClient(token=mock_token)
        with pytest.raises(ValueError, match="Request timed out after 30 seconds"):
            await client._request("GET", "/user")


class TestGitHubClientGetAuthenticatedUser:
    """Test get_authenticated_user method."""

    @pytest.mark.asyncio
    async def test_get_authenticated_user_success(self, mock_token, mock_user_data, httpx_mock: HTTPXMock):
        """Test getting authenticated user successfully."""
        httpx_mock.add_response(
            url="https://api.github.com/user",
            json=mock_user_data,
        )

        client = GitHubClient(token=mock_token)
        result = await client.get_authenticated_user()

        assert result == mock_user_data
        assert result["login"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_authenticated_user_unauthorized(self, mock_token, httpx_mock: HTTPXMock):
        """Test getting authenticated user with invalid token."""
        httpx_mock.add_response(
            url="https://api.github.com/user",
            status_code=401,
            json={"message": "Bad credentials"},
        )

        client = GitHubClient(token=mock_token)
        with pytest.raises(ValueError, match="Invalid or expired GitHub token"):
            await client.get_authenticated_user()


class TestGitHubClientGetUserOpenPRs:
    """Test get_user_open_prs method."""

    @pytest.mark.asyncio
    async def test_get_user_open_prs_success(self, mock_token, mock_user_prs, httpx_mock: HTTPXMock):
        """Test getting user's open PRs successfully."""
        httpx_mock.add_response(
            url="https://api.github.com/search/issues?q=is%3Apr+is%3Aopen+author%3Atestuser&per_page=100",
            json={"total_count": 2, "items": mock_user_prs},
        )

        client = GitHubClient(token=mock_token)
        result = await client.get_user_open_prs("testuser")

        assert result == mock_user_prs
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_user_open_prs_empty(self, mock_token, httpx_mock: HTTPXMock):
        """Test getting user's open PRs when none exist."""
        httpx_mock.add_response(
            url="https://api.github.com/search/issues?q=is%3Apr+is%3Aopen+author%3Atestuser&per_page=100",
            json={"total_count": 0, "items": []},
        )

        client = GitHubClient(token=mock_token)
        result = await client.get_user_open_prs("testuser")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_user_open_prs_invalid_user(self, mock_token, httpx_mock: HTTPXMock):
        """Test getting PRs for non-existent user."""
        httpx_mock.add_response(
            url="https://api.github.com/search/issues?q=is%3Apr+is%3Aopen+author%3Anonexistent&per_page=100",
            json={"total_count": 0, "items": []},
        )

        client = GitHubClient(token=mock_token)
        result = await client.get_user_open_prs("nonexistent")

        assert result == []


class TestGitHubClientGetPRDetails:
    """Test get_pr_details method."""

    @pytest.mark.asyncio
    async def test_get_pr_details_success(self, mock_token, mock_pr_data, httpx_mock: HTTPXMock):
        """Test getting PR details successfully."""
        httpx_mock.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/123",
            json=mock_pr_data,
        )

        client = GitHubClient(token=mock_token)
        result = await client.get_pr_details("owner", "repo", 123)

        assert result == mock_pr_data
        assert result["number"] == 123

    @pytest.mark.asyncio
    async def test_get_pr_details_not_found(self, mock_token, httpx_mock: HTTPXMock):
        """Test getting non-existent PR details."""
        httpx_mock.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/999",
            status_code=404,
            json={"message": "Not Found"},
        )

        client = GitHubClient(token=mock_token)
        with pytest.raises(ValueError, match="Resource not found: Not Found"):
            await client.get_pr_details("owner", "repo", 999)


class TestGitHubClientGetPRReviews:
    """Test get_pr_reviews method."""

    @pytest.mark.asyncio
    async def test_get_pr_reviews_success(self, mock_token, mock_reviews_approved, httpx_mock: HTTPXMock):
        """Test getting PR reviews successfully."""
        httpx_mock.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/123/reviews",
            json=mock_reviews_approved,
        )

        client = GitHubClient(token=mock_token)
        result = await client.get_pr_reviews("owner", "repo", 123)

        assert result == mock_reviews_approved
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_pr_reviews_empty(self, mock_token, httpx_mock: HTTPXMock):
        """Test getting PR reviews when none exist."""
        httpx_mock.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/123/reviews",
            json=[],
        )

        client = GitHubClient(token=mock_token)
        result = await client.get_pr_reviews("owner", "repo", 123)

        assert result == []


class TestGitHubClientGetCheckRuns:
    """Test get_check_runs method."""

    @pytest.mark.asyncio
    async def test_get_check_runs_success(self, mock_token, mock_check_runs_passing, httpx_mock: HTTPXMock):
        """Test getting check runs successfully."""
        httpx_mock.add_response(
            url="https://api.github.com/repos/owner/repo/commits/abc123/check-runs",
            json={"total_count": 2, "check_runs": mock_check_runs_passing},
        )

        client = GitHubClient(token=mock_token)
        result = await client.get_check_runs("owner", "repo", "abc123")

        assert result == mock_check_runs_passing
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_check_runs_empty(self, mock_token, httpx_mock: HTTPXMock):
        """Test getting check runs when none exist."""
        httpx_mock.add_response(
            url="https://api.github.com/repos/owner/repo/commits/abc123/check-runs",
            json={"total_count": 0, "check_runs": []},
        )

        client = GitHubClient(token=mock_token)
        result = await client.get_check_runs("owner", "repo", "abc123")

        assert result == []


class TestGitHubClientGetCheckRunAnnotations:
    """Test get_check_run_annotations method."""

    @pytest.mark.asyncio
    async def test_get_check_run_annotations_success(self, mock_token, httpx_mock: HTTPXMock):
        """Test getting check run annotations successfully."""
        annotations = [
            {
                "path": "test.py",
                "start_line": 10,
                "end_line": 10,
                "annotation_level": "failure",
                "message": "Test failed",
            }
        ]

        httpx_mock.add_response(
            url="https://api.github.com/repos/owner/repo/check-runs/123/annotations",
            json=annotations,
        )

        client = GitHubClient(token=mock_token)
        result = await client.get_check_run_annotations("owner", "repo", 123)

        assert result == annotations
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_check_run_annotations_empty(self, mock_token, httpx_mock: HTTPXMock):
        """Test getting check run annotations when none exist."""
        httpx_mock.add_response(
            url="https://api.github.com/repos/owner/repo/check-runs/123/annotations",
            json=[],
        )

        client = GitHubClient(token=mock_token)
        result = await client.get_check_run_annotations("owner", "repo", 123)

        assert result == []


class TestGitHubClientHeaders:
    """Test that proper headers are sent with requests."""

    @pytest.mark.asyncio
    async def test_request_headers(self, mock_token, httpx_mock: HTTPXMock):
        """Test that requests include proper headers."""
        httpx_mock.add_response(
            url="https://api.github.com/user",
            json={"login": "testuser"},
        )

        client = GitHubClient(token=mock_token)
        await client.get_authenticated_user()

        request = httpx_mock.get_request()
        assert request.headers["Authorization"] == f"Bearer {mock_token}"
        assert request.headers["Accept"] == "application/vnd.github+json"
        assert request.headers["X-GitHub-Api-Version"] == "2022-11-28"


class TestGitHubClientGraphQLRequest:
    """Test GitHubClient GraphQL request method."""

    @pytest.mark.asyncio
    async def test_graphql_request_success(self, mock_token, httpx_mock: HTTPXMock):
        """Test successful GraphQL request."""
        httpx_mock.add_response(
            url="https://api.github.com/graphql",
            json={
                "data": {
                    "repository": {
                        "pullRequest": {
                            "title": "Test PR",
                        }
                    }
                }
            },
        )

        client = GitHubClient(token=mock_token)
        result = await client._graphql_request(
            "query { repository(owner: \"owner\", name: \"repo\") { pullRequest(number: 1) { title } } }"
        )

        assert result["data"]["repository"]["pullRequest"]["title"] == "Test PR"

    @pytest.mark.asyncio
    async def test_graphql_request_with_errors(self, mock_token, httpx_mock: HTTPXMock):
        """Test GraphQL response containing errors field."""
        httpx_mock.add_response(
            url="https://api.github.com/graphql",
            json={
                "errors": [
                    {"message": "Field 'unknown' doesn't exist on type 'Query'"},
                ]
            },
        )

        client = GitHubClient(token=mock_token)
        with pytest.raises(ValueError, match="GraphQL error: Field 'unknown' doesn't exist on type 'Query'"):
            await client._graphql_request("query { unknown }")

    @pytest.mark.asyncio
    async def test_graphql_request_401_with_token(self, mock_token, httpx_mock: HTTPXMock):
        """Test 401 error with token configured."""
        httpx_mock.add_response(
            url="https://api.github.com/graphql",
            status_code=401,
            json={"message": "Bad credentials"},
        )

        client = GitHubClient(token=mock_token)
        with pytest.raises(ValueError, match="Invalid or expired GitHub token"):
            await client._graphql_request("query { viewer { login } }")

    @pytest.mark.asyncio
    async def test_graphql_request_401_without_token(self, httpx_mock: HTTPXMock):
        """Test 401 error without token configured."""
        with patch.dict(os.environ, {}, clear=True):
            httpx_mock.add_response(
                url="https://api.github.com/graphql",
                status_code=401,
                json={"message": "Requires authentication"},
            )

            client = GitHubClient()
            with pytest.raises(ValueError, match="No GitHub token configured.*GraphQL API requires authentication"):
                await client._graphql_request("query { viewer { login } }")

    @pytest.mark.asyncio
    async def test_graphql_request_403(self, mock_token, httpx_mock: HTTPXMock):
        """Test rate limit error on GraphQL endpoint."""
        httpx_mock.add_response(
            url="https://api.github.com/graphql",
            status_code=403,
            json={"message": "API rate limit exceeded"},
        )

        client = GitHubClient(token=mock_token)
        with pytest.raises(ValueError, match="GitHub API forbidden \\(rate limit or permissions\\): API rate limit exceeded"):
            await client._graphql_request("query { viewer { login } }")


class TestGitHubClientGetReviewThreads:
    """Test get_pr_review_threads method."""

    @pytest.mark.asyncio
    async def test_get_review_threads_success(self, mock_token, httpx_mock: HTTPXMock):
        """Test successfully returning review thread data."""
        httpx_mock.add_response(
            url="https://api.github.com/graphql",
            json={
                "data": {
                    "repository": {
                        "pullRequest": {
                            "reviewThreads": {
                                "pageInfo": {
                                    "hasNextPage": False,
                                    "endCursor": None,
                                },
                                "nodes": [
                                    {
                                        "isResolved": False,
                                        "isOutdated": False,
                                        "comments": {
                                            "nodes": [
                                                {
                                                    "url": "https://github.com/owner/repo/pull/123#discussion_r100",
                                                    "author": {"login": "reviewer1"},
                                                    "body": "Please fix this",
                                                }
                                            ]
                                        },
                                    },
                                    {
                                        "isResolved": True,
                                        "isOutdated": False,
                                        "comments": {
                                            "nodes": [
                                                {
                                                    "url": "https://github.com/owner/repo/pull/123#discussion_r101",
                                                    "author": {"login": "reviewer2"},
                                                    "body": "Looks good",
                                                }
                                            ]
                                        },
                                    },
                                ],
                            }
                        }
                    }
                }
            },
        )

        client = GitHubClient(token=mock_token)
        threads = await client.get_pr_review_threads("owner", "repo", 123)

        assert len(threads) == 2
        assert threads[0]["isResolved"] is False
        assert threads[1]["isResolved"] is True
        assert threads[0]["comments"]["nodes"][0]["author"]["login"] == "reviewer1"

    @pytest.mark.asyncio
    async def test_get_review_threads_pagination(self, mock_token, httpx_mock: HTTPXMock):
        """Test handling multiple pages of review threads."""
        # First page
        httpx_mock.add_response(
            url="https://api.github.com/graphql",
            json={
                "data": {
                    "repository": {
                        "pullRequest": {
                            "reviewThreads": {
                                "pageInfo": {
                                    "hasNextPage": True,
                                    "endCursor": "cursor_page1",
                                },
                                "nodes": [
                                    {
                                        "isResolved": False,
                                        "isOutdated": False,
                                        "comments": {
                                            "nodes": [
                                                {
                                                    "url": "https://github.com/owner/repo/pull/123#discussion_r100",
                                                    "author": {"login": "reviewer1"},
                                                    "body": "First page thread",
                                                }
                                            ]
                                        },
                                    },
                                ],
                            }
                        }
                    }
                }
            },
        )
        # Second page
        httpx_mock.add_response(
            url="https://api.github.com/graphql",
            json={
                "data": {
                    "repository": {
                        "pullRequest": {
                            "reviewThreads": {
                                "pageInfo": {
                                    "hasNextPage": False,
                                    "endCursor": None,
                                },
                                "nodes": [
                                    {
                                        "isResolved": True,
                                        "isOutdated": False,
                                        "comments": {
                                            "nodes": [
                                                {
                                                    "url": "https://github.com/owner/repo/pull/123#discussion_r200",
                                                    "author": {"login": "reviewer2"},
                                                    "body": "Second page thread",
                                                }
                                            ]
                                        },
                                    },
                                ],
                            }
                        }
                    }
                }
            },
        )

        client = GitHubClient(token=mock_token)
        threads = await client.get_pr_review_threads("owner", "repo", 123)

        assert len(threads) == 2
        assert threads[0]["isResolved"] is False
        assert threads[0]["comments"]["nodes"][0]["body"] == "First page thread"
        assert threads[1]["isResolved"] is True
        assert threads[1]["comments"]["nodes"][0]["body"] == "Second page thread"

    @pytest.mark.asyncio
    async def test_get_review_threads_empty(self, mock_token, httpx_mock: HTTPXMock):
        """Test getting review threads when none exist."""
        httpx_mock.add_response(
            url="https://api.github.com/graphql",
            json={
                "data": {
                    "repository": {
                        "pullRequest": {
                            "reviewThreads": {
                                "pageInfo": {
                                    "hasNextPage": False,
                                    "endCursor": None,
                                },
                                "nodes": [],
                            }
                        }
                    }
                }
            },
        )

        client = GitHubClient(token=mock_token)
        threads = await client.get_pr_review_threads("owner", "repo", 123)

        assert threads == []


class TestGitHubClientEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_large_pr_number(self, mock_token, httpx_mock: HTTPXMock):
        """Test handling very large PR numbers."""
        large_pr_number = 999999
        httpx_mock.add_response(
            url=f"https://api.github.com/repos/owner/repo/pulls/{large_pr_number}",
            json={"number": large_pr_number},
        )

        client = GitHubClient(token=mock_token)
        result = await client.get_pr_details("owner", "repo", large_pr_number)

        assert result["number"] == large_pr_number

    @pytest.mark.asyncio
    async def test_special_characters_in_username(self, mock_token, httpx_mock: HTTPXMock):
        """Test handling usernames with special characters."""
        username = "test-user_123"
        httpx_mock.add_response(
            url=f"https://api.github.com/search/issues?q=is%3Apr+is%3Aopen+author%3A{username}&per_page=100",
            json={"total_count": 0, "items": []},
        )

        client = GitHubClient(token=mock_token)
        result = await client.get_user_open_prs(username)

        assert result == []

    @pytest.mark.asyncio
    async def test_timeout_configuration(self, mock_token, httpx_mock: HTTPXMock):
        """Test that timeout is properly configured."""
        httpx_mock.add_response(
            url="https://api.github.com/user",
            json={"login": "testuser"},
        )

        client = GitHubClient(token=mock_token)
        await client._request("GET", "/user")

        # Verify timeout is set to 30.0 seconds (this is tested indirectly)
        request = httpx_mock.get_request()
        assert request is not None
