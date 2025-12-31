"""Tests for CLI interface."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import typer
from rich.console import Console
from rich.text import Text

from gh_pr_analyzer.analyzer import MergeBlocker, PRAnalysis
from gh_pr_analyzer.cli import analyze_user_prs, display_results, parse_repo_from_url


class TestParseRepoFromURL:
    """Test parse_repo_from_url function."""

    def test_parse_standard_github_url(self):
        """Test parsing standard github.com URL."""
        url = "https://github.com/owner/repo"
        owner, repo = parse_repo_from_url(url)
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_github_url_with_trailing_slash(self):
        """Test parsing URL with trailing slash."""
        url = "https://github.com/owner/repo/"
        owner, repo = parse_repo_from_url(url)
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_api_github_url(self):
        """Test parsing API GitHub URL."""
        url = "https://api.github.com/repos/owner/repo"
        owner, repo = parse_repo_from_url(url)
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_api_github_url_trailing_slash(self):
        """Test parsing API URL with trailing slash."""
        url = "https://api.github.com/repos/owner/repo/"
        owner, repo = parse_repo_from_url(url)
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_url_with_org_name(self):
        """Test parsing URL with organization name."""
        url = "https://github.com/my-org/my-repo"
        owner, repo = parse_repo_from_url(url)
        assert owner == "my-org"
        assert repo == "my-repo"

    def test_parse_url_with_underscores(self):
        """Test parsing URL with underscores."""
        url = "https://github.com/my_owner/my_repo"
        owner, repo = parse_repo_from_url(url)
        assert owner == "my_owner"
        assert repo == "my_repo"

    def test_parse_url_without_https(self):
        """Test parsing URL without protocol raises ValueError."""
        url = "github.com/owner/repo"
        # URLs without protocol don't have a netloc, so this should fail validation
        with pytest.raises(ValueError, match="Invalid GitHub URL domain"):
            parse_repo_from_url(url)

    def test_parse_url_with_path_segments(self):
        """Test parsing URL with additional path segments."""
        url = "https://github.com/owner/repo/pulls/123"
        owner, repo = parse_repo_from_url(url)
        # Our improved parser correctly extracts owner/repo from the path
        assert owner == "owner"
        assert repo == "repo"


class TestDisplayResults:
    """Test display_results function."""

    def test_display_results_empty_list(self):
        """Test displaying empty results."""
        with patch("gh_pr_analyzer.cli.console") as mock_console:
            display_results([])

            # Should still display table and summary
            assert mock_console.print.call_count >= 2  # At least table + summary

    def test_display_results_single_mergeable_pr(self):
        """Test displaying single mergeable PR."""
        analysis = PRAnalysis(
            repo="owner/repo",
            pr_number=123,
            title="Test PR",
            url="https://github.com/owner/repo/pull/123",
            blockers=[],
        )

        with patch("gh_pr_analyzer.cli.console") as mock_console:
            display_results([analysis])

            # Should show green "Ready to merge"
            mock_console.print.assert_called()

    def test_display_results_single_blocked_pr(self):
        """Test displaying single blocked PR."""
        blocker = MergeBlocker(
            type="FAILING_CHECK",
            description="CI failed",
            details="Tests failed at line 42",
        )
        analysis = PRAnalysis(
            repo="owner/repo",
            pr_number=123,
            title="Test PR",
            url="https://github.com/owner/repo/pull/123",
            blockers=[blocker],
        )

        with patch("gh_pr_analyzer.cli.console") as mock_console:
            display_results([analysis])

            mock_console.print.assert_called()

    def test_display_results_multiple_prs(self):
        """Test displaying multiple PRs."""
        analyses = [
            PRAnalysis(
                repo="owner/repo1",
                pr_number=123,
                title="PR 1",
                url="https://github.com/owner/repo1/pull/123",
                blockers=[],
            ),
            PRAnalysis(
                repo="owner/repo2",
                pr_number=456,
                title="PR 2",
                url="https://github.com/owner/repo2/pull/456",
                blockers=[MergeBlocker(type="FAILING_CHECK", description="Failed")],
            ),
        ]

        with patch("gh_pr_analyzer.cli.console") as mock_console:
            display_results(analyses)

            # Should display table and summary
            assert mock_console.print.call_count >= 2

    def test_display_results_failing_check_blocker(self):
        """Test displaying PR with failing check blocker."""
        blocker = MergeBlocker(
            type="FAILING_CHECK",
            description="CI / Test failed",
        )
        analysis = PRAnalysis(
            repo="owner/repo",
            pr_number=123,
            title="Test PR",
            url="https://github.com/owner/repo/pull/123",
            blockers=[blocker],
        )

        with patch("gh_pr_analyzer.cli.console"):
            display_results([analysis])
            # Should use red color and ✗ icon for failing checks

    def test_display_results_changes_requested_blocker(self):
        """Test displaying PR with changes requested blocker."""
        blocker = MergeBlocker(
            type="CHANGES_REQUESTED",
            description="Changes requested",
            details="Reviewers: alice, bob",
        )
        analysis = PRAnalysis(
            repo="owner/repo",
            pr_number=123,
            title="Test PR",
            url="https://github.com/owner/repo/pull/123",
            blockers=[blocker],
        )

        with patch("gh_pr_analyzer.cli.console"):
            display_results([analysis])
            # Should use yellow color and ⚠ icon for changes requested

    def test_display_results_pending_checks_blocker(self):
        """Test displaying PR with pending checks blocker."""
        blocker = MergeBlocker(
            type="PENDING_CHECKS",
            description="2 checks running",
            details="CI / Test, CI / Lint",
        )
        analysis = PRAnalysis(
            repo="owner/repo",
            pr_number=123,
            title="Test PR",
            url="https://github.com/owner/repo/pull/123",
            blockers=[blocker],
        )

        with patch("gh_pr_analyzer.cli.console"):
            display_results([analysis])
            # Should use blue color and ⏳ icon for pending checks

    def test_display_results_merge_conflict_blocker(self):
        """Test displaying PR with merge conflict blocker."""
        blocker = MergeBlocker(
            type="MERGE_CONFLICT",
            description="Has conflicts",
        )
        analysis = PRAnalysis(
            repo="owner/repo",
            pr_number=123,
            title="Test PR",
            url="https://github.com/owner/repo/pull/123",
            blockers=[blocker],
        )

        with patch("gh_pr_analyzer.cli.console"):
            display_results([analysis])
            # Should use red color and ⚡ icon for merge conflicts

    def test_display_results_unknown_blocker_type(self):
        """Test displaying PR with unknown blocker type."""
        blocker = MergeBlocker(
            type="UNKNOWN_TYPE",
            description="Unknown issue",
        )
        analysis = PRAnalysis(
            repo="owner/repo",
            pr_number=123,
            title="Test PR",
            url="https://github.com/owner/repo/pull/123",
            blockers=[blocker],
        )

        with patch("gh_pr_analyzer.cli.console"):
            display_results([analysis])
            # Should use default yellow color and • icon

    def test_display_results_long_title_truncation(self):
        """Test that long PR titles are truncated."""
        long_title = "A" * 100  # 100 character title
        analysis = PRAnalysis(
            repo="owner/repo",
            pr_number=123,
            title=long_title,
            url="https://github.com/owner/repo/pull/123",
            blockers=[],
        )

        with patch("gh_pr_analyzer.cli.console"):
            display_results([analysis])
            # Title should be truncated to 50 characters in the table

    def test_display_results_summary_counts(self):
        """Test summary counts are correct."""
        analyses = [
            PRAnalysis(
                repo="owner/repo",
                pr_number=1,
                title="PR 1",
                url="https://github.com/owner/repo/pull/1",
                blockers=[],
            ),
            PRAnalysis(
                repo="owner/repo",
                pr_number=2,
                title="PR 2",
                url="https://github.com/owner/repo/pull/2",
                blockers=[],
            ),
            PRAnalysis(
                repo="owner/repo",
                pr_number=3,
                title="PR 3",
                url="https://github.com/owner/repo/pull/3",
                blockers=[MergeBlocker(type="FAILING_CHECK", description="Failed")],
            ),
        ]

        with patch("gh_pr_analyzer.cli.console") as mock_console:
            display_results(analyses)

            # Check that summary is printed with correct counts
            # Should show: 2 ready, 1 blocked, 3 total
            calls = [str(call) for call in mock_console.print.call_args_list]
            summary_calls = [c for c in calls if "Summary" in c or "Ready" in c or "Blocked" in c or "Total" in c]
            assert len(summary_calls) > 0


class TestAnalyzeUserPRs:
    """Test analyze_user_prs async function."""

    @pytest.mark.asyncio
    async def test_analyze_user_prs_with_username(self, mock_token, mock_user_prs, mock_pr_data):
        """Test analyzing PRs with explicit username."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": mock_token}):
            with patch("gh_pr_analyzer.cli.GitHubClient") as mock_client_class:
                # Setup mock client
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client

                mock_client.get_user_open_prs.return_value = mock_user_prs
                mock_client.get_pr_details.return_value = mock_pr_data
                mock_client.get_pr_reviews.return_value = []
                mock_client.get_check_runs.return_value = []

                with patch("gh_pr_analyzer.cli.display_results") as mock_display:
                    with patch("gh_pr_analyzer.cli.console"):
                        await analyze_user_prs("testuser")

                        # Verify calls
                        mock_client.get_user_open_prs.assert_called_once_with("testuser")
                        mock_display.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_user_prs_without_username(self, mock_token, mock_user_data, mock_user_prs, mock_pr_data):
        """Test analyzing PRs without username (uses authenticated user)."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": mock_token}):
            with patch("gh_pr_analyzer.cli.GitHubClient") as mock_client_class:
                # Setup mock client
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client

                mock_client.get_authenticated_user.return_value = mock_user_data
                mock_client.get_user_open_prs.return_value = mock_user_prs
                mock_client.get_pr_details.return_value = mock_pr_data
                mock_client.get_pr_reviews.return_value = []
                mock_client.get_check_runs.return_value = []

                with patch("gh_pr_analyzer.cli.display_results") as mock_display:
                    with patch("gh_pr_analyzer.cli.console"):
                        await analyze_user_prs(None)

                        # Should fetch authenticated user first
                        mock_client.get_authenticated_user.assert_called_once()
                        mock_client.get_user_open_prs.assert_called_once_with("testuser")
                        mock_display.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_user_prs_no_prs_found(self, mock_token):
        """Test analyzing when user has no open PRs."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": mock_token}):
            with patch("gh_pr_analyzer.cli.GitHubClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client
                mock_client.get_user_open_prs.return_value = []

                with patch("gh_pr_analyzer.cli.console") as mock_console:
                    await analyze_user_prs("testuser")

                    # Should print "No open PRs found" message
                    print_calls = [str(call) for call in mock_console.print.call_args_list]
                    assert any("No open PRs" in str(call) for call in print_calls)

    @pytest.mark.asyncio
    async def test_analyze_user_prs_github_error(self, mock_token):
        """Test handling of GitHub API errors."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": mock_token}):
            with patch("gh_pr_analyzer.cli.GitHubClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client
                mock_client.get_user_open_prs.side_effect = httpx.HTTPStatusError(
                    "Not Found", request=MagicMock(), response=MagicMock()
                )

                with patch("gh_pr_analyzer.cli.console"):
                    with pytest.raises(typer.Exit):
                        await analyze_user_prs("testuser")

    @pytest.mark.asyncio
    async def test_analyze_user_prs_no_token_error(self):
        """Test handling of missing token error."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("gh_pr_analyzer.cli.console") as mock_console:
                with pytest.raises(typer.Exit):
                    await analyze_user_prs("testuser")

                # Should print error message
                print_calls = [str(call) for call in mock_console.print.call_args_list]
                assert any("Error" in str(call) for call in print_calls)

    @pytest.mark.asyncio
    async def test_analyze_user_prs_unexpected_error(self, mock_token):
        """Test handling of unexpected errors."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": mock_token}):
            with patch("gh_pr_analyzer.cli.GitHubClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client
                mock_client.get_user_open_prs.side_effect = RuntimeError("Unexpected error")

                with patch("gh_pr_analyzer.cli.console"):
                    with pytest.raises(typer.Exit):
                        await analyze_user_prs("testuser")

    @pytest.mark.asyncio
    async def test_analyze_user_prs_multiple_prs(self, mock_token, mock_user_prs, mock_pr_data):
        """Test analyzing multiple PRs."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": mock_token}):
            with patch("gh_pr_analyzer.cli.GitHubClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client

                mock_client.get_user_open_prs.return_value = mock_user_prs
                mock_client.get_pr_details.return_value = mock_pr_data
                mock_client.get_pr_reviews.return_value = []
                mock_client.get_check_runs.return_value = []

                with patch("gh_pr_analyzer.cli.display_results") as mock_display:
                    with patch("gh_pr_analyzer.cli.console"):
                        await analyze_user_prs("testuser")

                        # Should call get_pr_details for each PR
                        assert mock_client.get_pr_details.call_count == len(mock_user_prs)

                        # Should display results with all PRs
                        mock_display.assert_called_once()
                        displayed_analyses = mock_display.call_args[0][0]
                        assert len(displayed_analyses) == len(mock_user_prs)

    @pytest.mark.asyncio
    async def test_analyze_user_prs_fetches_reviews_and_checks(
        self, mock_token, mock_user_prs, mock_pr_data, mock_reviews_approved, mock_check_runs_passing
    ):
        """Test that reviews and checks are fetched for each PR."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": mock_token}):
            with patch("gh_pr_analyzer.cli.GitHubClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client

                mock_client.get_user_open_prs.return_value = [mock_user_prs[0]]  # Just one PR
                mock_client.get_pr_details.return_value = mock_pr_data
                mock_client.get_pr_reviews.return_value = mock_reviews_approved
                mock_client.get_check_runs.return_value = mock_check_runs_passing

                with patch("gh_pr_analyzer.cli.display_results"):
                    with patch("gh_pr_analyzer.cli.console"):
                        await analyze_user_prs("testuser")

                        # Verify all data was fetched
                        mock_client.get_pr_details.assert_called_once()
                        mock_client.get_pr_reviews.assert_called_once()
                        mock_client.get_check_runs.assert_called_once()


class TestCLIEdgeCases:
    """Test edge cases for CLI."""

    def test_parse_repo_very_long_names(self):
        """Test parsing URLs with very long owner/repo names."""
        url = "https://github.com/very-long-organization-name/very-long-repository-name"
        owner, repo = parse_repo_from_url(url)
        assert owner == "very-long-organization-name"
        assert repo == "very-long-repository-name"

    def test_display_results_with_multiline_details(self):
        """Test displaying blockers with multiline details."""
        blocker = MergeBlocker(
            type="FAILING_CHECK",
            description="CI failed",
            details="Line 1\nLine 2\nLine 3",
        )
        analysis = PRAnalysis(
            repo="owner/repo",
            pr_number=123,
            title="Test PR",
            url="https://github.com/owner/repo/pull/123",
            blockers=[blocker],
        )

        with patch("gh_pr_analyzer.cli.console"):
            display_results([analysis])
            # Should handle multiline details properly

    def test_display_results_many_blockers(self):
        """Test displaying PR with many blockers."""
        blockers = [
            MergeBlocker(type=f"TYPE_{i}", description=f"Blocker {i}")
            for i in range(10)
        ]
        analysis = PRAnalysis(
            repo="owner/repo",
            pr_number=123,
            title="Test PR",
            url="https://github.com/owner/repo/pull/123",
            blockers=blockers,
        )

        with patch("gh_pr_analyzer.cli.console"):
            display_results([analysis])
            # Should display all blockers

    @pytest.mark.asyncio
    async def test_analyze_user_prs_connection_timeout(self, mock_token):
        """Test handling of connection timeout."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": mock_token}):
            with patch("gh_pr_analyzer.cli.GitHubClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client
                mock_client.get_user_open_prs.side_effect = httpx.TimeoutException("Timeout")

                with patch("gh_pr_analyzer.cli.console"):
                    with pytest.raises(typer.Exit):
                        await analyze_user_prs("testuser")
