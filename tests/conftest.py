"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def mock_token():
    """Provide a mock GitHub token for testing."""
    return "ghp_test_token_1234567890abcdef"


@pytest.fixture
def mock_pr_data():
    """Provide mock PR data for testing."""
    return {
        "number": 123,
        "title": "Test PR",
        "html_url": "https://github.com/owner/repo/pull/123",
        "mergeable": True,
        "mergeable_state": "clean",
        "base": {
            "repo": {
                "full_name": "owner/repo",
                "private": False,
            }
        },
        "head": {
            "sha": "abc123def456",
        },
    }


@pytest.fixture
def mock_pr_data_with_conflicts():
    """Provide mock PR data with merge conflicts."""
    return {
        "number": 124,
        "title": "PR with conflicts",
        "html_url": "https://github.com/owner/repo/pull/124",
        "mergeable": False,
        "mergeable_state": "dirty",
        "base": {
            "repo": {
                "full_name": "owner/repo",
                "private": False,
            }
        },
        "head": {
            "sha": "def456ghi789",
        },
    }


@pytest.fixture
def mock_pr_data_blocked():
    """Provide mock PR data that is blocked."""
    return {
        "number": 125,
        "title": "Blocked PR",
        "html_url": "https://github.com/owner/repo/pull/125",
        "mergeable": True,
        "mergeable_state": "blocked",
        "base": {
            "repo": {
                "full_name": "owner/repo",
                "private": True,
            }
        },
        "head": {
            "sha": "ghi789jkl012",
        },
    }


@pytest.fixture
def mock_reviews_approved():
    """Provide mock approved reviews."""
    return [
        {
            "id": 1,
            "user": {"login": "reviewer1"},
            "state": "APPROVED",
        },
        {
            "id": 2,
            "user": {"login": "reviewer2"},
            "state": "APPROVED",
        },
    ]


@pytest.fixture
def mock_reviews_changes_requested():
    """Provide mock reviews with changes requested."""
    return [
        {
            "id": 1,
            "user": {"login": "reviewer1"},
            "state": "CHANGES_REQUESTED",
        },
        {
            "id": 2,
            "user": {"login": "reviewer2"},
            "state": "CHANGES_REQUESTED",
        },
    ]


@pytest.fixture
def mock_reviews_mixed():
    """Provide mixed mock reviews."""
    return [
        {
            "id": 1,
            "user": {"login": "reviewer1"},
            "state": "APPROVED",
        },
        {
            "id": 2,
            "user": {"login": "reviewer2"},
            "state": "CHANGES_REQUESTED",
        },
        {
            "id": 3,
            "user": {"login": "reviewer3"},
            "state": "COMMENTED",
        },
    ]


@pytest.fixture
def mock_check_runs_passing():
    """Provide mock passing check runs."""
    return [
        {
            "id": 1,
            "name": "CI / Test",
            "status": "completed",
            "conclusion": "success",
        },
        {
            "id": 2,
            "name": "CI / Lint",
            "status": "completed",
            "conclusion": "success",
        },
    ]


@pytest.fixture
def mock_check_runs_failing():
    """Provide mock failing check runs."""
    return [
        {
            "id": 1,
            "name": "CI / Test",
            "status": "completed",
            "conclusion": "failure",
            "output": {
                "summary": "Tests failed\nError in test_foo.py\nAssertion failed\nExpected: 1\nActual: 2\nFailed at line 42",
            },
        },
        {
            "id": 2,
            "name": "CI / Lint",
            "status": "completed",
            "conclusion": "success",
        },
    ]


@pytest.fixture
def mock_check_runs_pending():
    """Provide mock pending check runs."""
    return [
        {
            "id": 1,
            "name": "CI / Test",
            "status": "in_progress",
            "conclusion": None,
        },
        {
            "id": 2,
            "name": "CI / Lint",
            "status": "queued",
            "conclusion": None,
        },
        {
            "id": 3,
            "name": "CI / Build",
            "status": "completed",
            "conclusion": "success",
        },
    ]


@pytest.fixture
def mock_check_runs_mixed():
    """Provide mixed check runs (passing, failing, pending)."""
    return [
        {
            "id": 1,
            "name": "CI / Test",
            "status": "completed",
            "conclusion": "failure",
            "output": {
                "summary": "Test failure",
            },
        },
        {
            "id": 2,
            "name": "CI / Lint",
            "status": "in_progress",
            "conclusion": None,
        },
        {
            "id": 3,
            "name": "CI / Build",
            "status": "completed",
            "conclusion": "success",
        },
    ]


@pytest.fixture
def mock_user_data():
    """Provide mock user data."""
    return {
        "login": "testuser",
        "id": 12345,
        "name": "Test User",
        "email": "test@example.com",
    }


@pytest.fixture
def mock_user_prs():
    """Provide mock list of user's PRs."""
    return [
        {
            "number": 123,
            "title": "First PR",
            "repository_url": "https://api.github.com/repos/owner/repo1",
        },
        {
            "number": 456,
            "title": "Second PR",
            "repository_url": "https://api.github.com/repos/owner/repo2",
        },
    ]
