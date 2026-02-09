# Generated using Claude cli
"""Tests for PR analyzer."""

import pytest

from gh_pr_analyzer.analyzer import MergeBlocker, PRAnalysis, ReviewLabel, analyze_pr


class TestMergeBlocker:
    """Test MergeBlocker dataclass."""

    def test_merge_blocker_without_details(self):
        """Test MergeBlocker string representation without details."""
        blocker = MergeBlocker(
            type="FAILING_CHECK",
            description="Test failed",
        )
        assert str(blocker) == "FAILING_CHECK: Test failed"

    def test_merge_blocker_with_details(self):
        """Test MergeBlocker string representation with details."""
        blocker = MergeBlocker(
            type="FAILING_CHECK",
            description="Test failed",
            details="Error at line 42",
        )
        assert str(blocker) == "FAILING_CHECK: Test failed\n  Error at line 42"

    def test_merge_blocker_attributes(self):
        """Test MergeBlocker attributes are properly set."""
        blocker = MergeBlocker(
            type="CHANGES_REQUESTED",
            description="Changes needed",
            details="Reviewer: alice",
        )
        assert blocker.type == "CHANGES_REQUESTED"
        assert blocker.description == "Changes needed"
        assert blocker.details == "Reviewer: alice"


class TestPRAnalysis:
    """Test PRAnalysis dataclass."""

    def test_pr_analysis_mergeable(self):
        """Test PR is mergeable when no blockers."""
        analysis = PRAnalysis(
            repo="owner/repo",
            pr_number=123,
            title="Test PR",
            url="https://github.com/owner/repo/pull/123",
            blockers=[],
        )
        assert analysis.is_mergeable is True

    def test_pr_analysis_not_mergeable(self):
        """Test PR is not mergeable when blockers exist."""
        blocker = MergeBlocker(type="FAILING_CHECK", description="Test failed")
        analysis = PRAnalysis(
            repo="owner/repo",
            pr_number=123,
            title="Test PR",
            url="https://github.com/owner/repo/pull/123",
            blockers=[blocker],
        )
        assert analysis.is_mergeable is False

    def test_pr_analysis_attributes(self):
        """Test PRAnalysis attributes are properly set."""
        analysis = PRAnalysis(
            repo="owner/repo",
            pr_number=456,
            title="My Test PR",
            url="https://github.com/owner/repo/pull/456",
        )
        assert analysis.repo == "owner/repo"
        assert analysis.pr_number == 456
        assert analysis.title == "My Test PR"
        assert analysis.url == "https://github.com/owner/repo/pull/456"
        assert analysis.blockers == []


class TestAnalyzePRClean:
    """Test analyze_pr with clean PRs (no blockers)."""

    def test_analyze_clean_pr(self, mock_pr_data, mock_reviews_approved, mock_check_runs_passing):
        """Test analyzing a clean PR with no blockers."""
        analysis = analyze_pr(mock_pr_data, mock_reviews_approved, mock_check_runs_passing)

        assert analysis.is_mergeable is True
        assert len(analysis.blockers) == 0
        assert analysis.repo == "owner/repo"
        assert analysis.pr_number == 123
        assert analysis.title == "Test PR"

    def test_analyze_pr_no_reviews_no_checks(self, mock_pr_data):
        """Test analyzing PR with no reviews and no checks."""
        analysis = analyze_pr(mock_pr_data, [], [])

        assert analysis.is_mergeable is True
        assert len(analysis.blockers) == 0

    def test_analyze_pr_with_comments_only(self, mock_pr_data, mock_check_runs_passing):
        """Test PR with comment reviews (not blocking)."""
        reviews = [
            {"id": 1, "user": {"login": "reviewer1"}, "state": "COMMENTED"},
        ]
        analysis = analyze_pr(mock_pr_data, reviews, mock_check_runs_passing)

        assert analysis.is_mergeable is True
        assert len(analysis.blockers) == 0


class TestAnalyzePRMergeConflicts:
    """Test analyze_pr with merge conflicts."""

    def test_analyze_pr_merge_conflict_dirty(self, mock_pr_data_with_conflicts):
        """Test PR with merge conflicts (dirty state)."""
        analysis = analyze_pr(mock_pr_data_with_conflicts, [], [])

        assert analysis.is_mergeable is False
        assert len(analysis.blockers) == 1
        assert analysis.blockers[0].type == "MERGE_CONFLICT"
        assert analysis.blockers[0].description == "PR has merge conflicts"

    def test_analyze_pr_mergeable_false(self):
        """Test PR with mergeable=False."""
        pr_data = {
            "number": 124,
            "title": "Conflicted PR",
            "html_url": "https://github.com/owner/repo/pull/124",
            "mergeable": False,
            "mergeable_state": "clean",  # Different from dirty
            "base": {"repo": {"full_name": "owner/repo", "private": False}},
            "head": {"sha": "abc123"},
        }
        analysis = analyze_pr(pr_data, [], [])

        assert analysis.is_mergeable is False
        assert any(b.type == "MERGE_CONFLICT" for b in analysis.blockers)


class TestAnalyzePRFailingChecks:
    """Test analyze_pr with failing checks."""

    def test_analyze_pr_failing_checks(self, mock_pr_data, mock_check_runs_failing):
        """Test PR with failing checks."""
        analysis = analyze_pr(mock_pr_data, [], mock_check_runs_failing)

        assert analysis.is_mergeable is False
        assert len(analysis.blockers) == 1
        assert analysis.blockers[0].type == "FAILING_CHECK"
        assert "CI / Test" in analysis.blockers[0].description
        assert analysis.blockers[0].details is not None

    def test_analyze_pr_multiple_failing_checks(self, mock_pr_data):
        """Test PR with multiple failing checks."""
        check_runs = [
            {
                "id": 1,
                "name": "CI / Test",
                "status": "completed",
                "conclusion": "failure",
                "output": {"summary": "Tests failed"},
            },
            {
                "id": 2,
                "name": "CI / Lint",
                "status": "completed",
                "conclusion": "failure",
                "output": {"summary": "Linting errors"},
            },
        ]
        analysis = analyze_pr(mock_pr_data, [], check_runs)

        assert analysis.is_mergeable is False
        assert len(analysis.blockers) == 2
        failing_blockers = [b for b in analysis.blockers if b.type == "FAILING_CHECK"]
        assert len(failing_blockers) == 2

    def test_analyze_pr_failing_check_without_output(self, mock_pr_data):
        """Test failing check without output summary."""
        check_runs = [
            {
                "id": 1,
                "name": "CI / Test",
                "status": "completed",
                "conclusion": "failure",
                "output": {},
            },
        ]
        analysis = analyze_pr(mock_pr_data, [], check_runs)

        assert analysis.is_mergeable is False
        assert len(analysis.blockers) == 1
        assert analysis.blockers[0].details is None

    def test_analyze_pr_failing_check_with_multiline_output(self, mock_pr_data):
        """Test failing check with multiline error output."""
        check_runs = [
            {
                "id": 1,
                "name": "CI / Test",
                "status": "completed",
                "conclusion": "failure",
                "output": {
                    "summary": "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7",
                },
            },
        ]
        analysis = analyze_pr(mock_pr_data, [], check_runs)

        # Should extract last 5 lines
        assert analysis.is_mergeable is False
        assert "Line 3" in analysis.blockers[0].details
        assert "Line 7" in analysis.blockers[0].details


class TestAnalyzePRPendingChecks:
    """Test analyze_pr with pending checks."""

    def test_analyze_pr_pending_checks(self, mock_pr_data, mock_check_runs_pending):
        """Test PR with pending checks."""
        analysis = analyze_pr(mock_pr_data, [], mock_check_runs_pending)

        assert analysis.is_mergeable is False
        assert len(analysis.blockers) == 1
        assert analysis.blockers[0].type == "PENDING_CHECKS"
        assert "2 check(s) still running" in analysis.blockers[0].description
        assert "CI / Test" in analysis.blockers[0].details
        assert "CI / Lint" in analysis.blockers[0].details

    def test_analyze_pr_many_pending_checks(self, mock_pr_data):
        """Test PR with many pending checks (more than 3)."""
        check_runs = [
            {"id": i, "name": f"Check {i}", "status": "in_progress", "conclusion": None}
            for i in range(5)
        ]
        analysis = analyze_pr(mock_pr_data, [], check_runs)

        assert analysis.is_mergeable is False
        assert "5 check(s) still running" in analysis.blockers[0].description
        assert "and 2 more" in analysis.blockers[0].details

    def test_analyze_pr_single_pending_check(self, mock_pr_data):
        """Test PR with single pending check."""
        check_runs = [
            {"id": 1, "name": "CI / Test", "status": "queued", "conclusion": None},
        ]
        analysis = analyze_pr(mock_pr_data, [], check_runs)

        assert analysis.is_mergeable is False
        assert "1 check(s) still running" in analysis.blockers[0].description


class TestAnalyzePRReviews:
    """Test analyze_pr with various review states."""

    def test_analyze_pr_changes_requested(self, mock_pr_data, mock_reviews_changes_requested, mock_check_runs_passing):
        """Test PR with changes requested."""
        analysis = analyze_pr(mock_pr_data, mock_reviews_changes_requested, mock_check_runs_passing)

        assert analysis.is_mergeable is False
        assert len(analysis.blockers) == 1
        assert analysis.blockers[0].type == "CHANGES_REQUESTED"
        assert "reviewer1" in analysis.blockers[0].details
        assert "reviewer2" in analysis.blockers[0].details

    def test_analyze_pr_mixed_reviews(self, mock_pr_data, mock_reviews_mixed, mock_check_runs_passing):
        """Test PR with mixed review states."""
        analysis = analyze_pr(mock_pr_data, mock_reviews_mixed, mock_check_runs_passing)

        assert analysis.is_mergeable is False
        # Should have changes requested blocker
        changes_blockers = [b for b in analysis.blockers if b.type == "CHANGES_REQUESTED"]
        assert len(changes_blockers) == 1

    def test_analyze_pr_duplicate_reviewer_changes_requested(self, mock_pr_data, mock_check_runs_passing):
        """Test PR with duplicate reviewers requesting changes."""
        reviews = [
            {"id": 1, "user": {"login": "reviewer1"}, "state": "CHANGES_REQUESTED"},
            {"id": 2, "user": {"login": "reviewer1"}, "state": "CHANGES_REQUESTED"},  # Same reviewer
        ]
        analysis = analyze_pr(mock_pr_data, reviews, mock_check_runs_passing)

        assert analysis.is_mergeable is False
        # Should deduplicate reviewer names
        assert analysis.blockers[0].details.count("reviewer1") == 1


class TestAnalyzePRApprovals:
    """Test analyze_pr with approval requirements."""

    def test_analyze_pr_private_repo_blocked_no_approvals(self, mock_pr_data_blocked):
        """Test private repo blocked state with no approvals."""
        analysis = analyze_pr(mock_pr_data_blocked, [], [])

        assert analysis.is_mergeable is False
        # Should have missing approvals blocker
        approval_blockers = [b for b in analysis.blockers if b.type == "MISSING_APPROVALS"]
        assert len(approval_blockers) == 1

    def test_analyze_pr_private_repo_with_approvals(self):
        """Test private repo blocked state with approvals."""
        pr_data = {
            "number": 125,
            "title": "Blocked PR",
            "html_url": "https://github.com/owner/repo/pull/125",
            "mergeable": True,
            "mergeable_state": "blocked",
            "base": {"repo": {"full_name": "owner/repo", "private": True}},
            "head": {"sha": "abc123"},
        }
        reviews = [
            {"id": 1, "user": {"login": "reviewer1"}, "state": "APPROVED"},
        ]
        analysis = analyze_pr(pr_data, reviews, [])

        # Should have branch protection blocker, not missing approvals
        approval_blockers = [b for b in analysis.blockers if b.type == "MISSING_APPROVALS"]
        assert len(approval_blockers) == 0

    def test_analyze_pr_public_repo_blocked_no_approval_blocker(self, mock_pr_data):
        """Test public repo blocked doesn't trigger approval blocker."""
        pr_data = dict(mock_pr_data)
        pr_data["mergeable_state"] = "blocked"

        analysis = analyze_pr(pr_data, [], [])

        # Should have branch protection blocker, not missing approvals
        approval_blockers = [b for b in analysis.blockers if b.type == "MISSING_APPROVALS"]
        assert len(approval_blockers) == 0


class TestAnalyzePRBranchProtection:
    """Test analyze_pr with branch protection."""

    def test_analyze_pr_branch_protection_blocked(self):
        """Test PR blocked by branch protection with no other blockers."""
        pr_data = {
            "number": 126,
            "title": "Protected PR",
            "html_url": "https://github.com/owner/repo/pull/126",
            "mergeable": True,
            "mergeable_state": "blocked",
            "base": {"repo": {"full_name": "owner/repo", "private": False}},
            "head": {"sha": "abc123"},
        }
        analysis = analyze_pr(pr_data, [], [])

        assert analysis.is_mergeable is False
        assert len(analysis.blockers) == 1
        assert analysis.blockers[0].type == "BRANCH_PROTECTION"

    def test_analyze_pr_branch_protection_with_other_blockers(self, mock_pr_data, mock_check_runs_failing):
        """Test branch protection doesn't override other blockers."""
        pr_data = dict(mock_pr_data)
        pr_data["mergeable_state"] = "blocked"

        analysis = analyze_pr(pr_data, [], mock_check_runs_failing)

        # Should have failing check blocker, not branch protection
        # (because we already have another blocker)
        protection_blockers = [b for b in analysis.blockers if b.type == "BRANCH_PROTECTION"]
        assert len(protection_blockers) == 0


class TestAnalyzePRMultipleBlockers:
    """Test analyze_pr with multiple simultaneous blockers."""

    def test_analyze_pr_all_blockers(self):
        """Test PR with all types of blockers."""
        pr_data = {
            "number": 127,
            "title": "Severely blocked PR",
            "html_url": "https://github.com/owner/repo/pull/127",
            "mergeable": False,
            "mergeable_state": "dirty",
            "base": {"repo": {"full_name": "owner/repo", "private": False}},
            "head": {"sha": "abc123"},
        }
        reviews = [
            {"id": 1, "user": {"login": "reviewer1"}, "state": "CHANGES_REQUESTED"},
        ]
        check_runs = [
            {
                "id": 1,
                "name": "CI / Test",
                "status": "completed",
                "conclusion": "failure",
                "output": {"summary": "Failed"},
            },
            {
                "id": 2,
                "name": "CI / Lint",
                "status": "in_progress",
                "conclusion": None,
            },
        ]

        analysis = analyze_pr(pr_data, reviews, check_runs)

        assert analysis.is_mergeable is False
        assert len(analysis.blockers) == 4  # Conflict, failing check, pending check, changes requested

        blocker_types = {b.type for b in analysis.blockers}
        assert "MERGE_CONFLICT" in blocker_types
        assert "FAILING_CHECK" in blocker_types
        assert "PENDING_CHECKS" in blocker_types
        assert "CHANGES_REQUESTED" in blocker_types

    def test_analyze_pr_mixed_check_states(self, mock_pr_data, mock_check_runs_mixed):
        """Test PR with mixed check states."""
        analysis = analyze_pr(mock_pr_data, [], mock_check_runs_mixed)

        assert analysis.is_mergeable is False
        # Should have both failing and pending check blockers
        blocker_types = {b.type for b in analysis.blockers}
        assert "FAILING_CHECK" in blocker_types
        assert "PENDING_CHECKS" in blocker_types


class TestAnalyzePREdgeCases:
    """Test edge cases and boundary conditions."""

    def test_analyze_pr_unknown_mergeable_state(self):
        """Test PR with unknown mergeable state."""
        pr_data = {
            "number": 128,
            "title": "Unknown state PR",
            "html_url": "https://github.com/owner/repo/pull/128",
            "mergeable": None,
            "mergeable_state": "unknown",
            "base": {"repo": {"full_name": "owner/repo", "private": False}},
            "head": {"sha": "abc123"},
        }
        analysis = analyze_pr(pr_data, [], [])

        # Unknown state shouldn't create blockers
        assert analysis.is_mergeable is True

    def test_analyze_pr_missing_mergeable_state(self):
        """Test PR with missing mergeable_state field."""
        pr_data = {
            "number": 129,
            "title": "Missing state PR",
            "html_url": "https://github.com/owner/repo/pull/129",
            "base": {"repo": {"full_name": "owner/repo", "private": False}},
            "head": {"sha": "abc123"},
        }
        analysis = analyze_pr(pr_data, [], [])

        # Should use default value and not crash
        assert isinstance(analysis, PRAnalysis)

    def test_analyze_pr_empty_reviews_and_checks(self, mock_pr_data):
        """Test PR with empty reviews and checks."""
        analysis = analyze_pr(mock_pr_data, [], [])

        assert analysis.is_mergeable is True
        assert len(analysis.blockers) == 0

    def test_analyze_pr_neutral_check_conclusion(self, mock_pr_data):
        """Test PR with neutral check conclusion."""
        check_runs = [
            {
                "id": 1,
                "name": "CI / Test",
                "status": "completed",
                "conclusion": "neutral",
            },
        ]
        analysis = analyze_pr(mock_pr_data, [], check_runs)

        # Neutral is not a failure
        assert analysis.is_mergeable is True

    def test_analyze_pr_skipped_check_conclusion(self, mock_pr_data):
        """Test PR with skipped check conclusion."""
        check_runs = [
            {
                "id": 1,
                "name": "CI / Test",
                "status": "completed",
                "conclusion": "skipped",
            },
        ]
        analysis = analyze_pr(mock_pr_data, [], check_runs)

        # Skipped is not a failure
        assert analysis.is_mergeable is True

    def test_analyze_pr_cancelled_check_conclusion(self, mock_pr_data):
        """Test PR with cancelled check conclusion."""
        check_runs = [
            {
                "id": 1,
                "name": "CI / Test",
                "status": "completed",
                "conclusion": "cancelled",
            },
        ]
        analysis = analyze_pr(mock_pr_data, [], check_runs)

        # Cancelled is not a failure (though might want to handle differently)
        assert analysis.is_mergeable is True

    def test_analyze_pr_very_long_error_output(self, mock_pr_data):
        """Test failing check with very long error output."""
        # Create 100 lines of output
        long_output = "\n".join([f"Error line {i}" for i in range(100)])

        check_runs = [
            {
                "id": 1,
                "name": "CI / Test",
                "status": "completed",
                "conclusion": "failure",
                "output": {"summary": long_output},
            },
        ]
        analysis = analyze_pr(mock_pr_data, [], check_runs)

        # Should only extract last 5 lines
        assert analysis.is_mergeable is False
        assert "Error line 99" in analysis.blockers[0].details
        assert "Error line 95" in analysis.blockers[0].details
        assert "Error line 0" not in analysis.blockers[0].details


class TestAnalyzePRUnresolvedComments:
    """Test analyze_pr with review thread resolution status."""

    def test_analyze_pr_no_review_threads(self, mock_pr_data):
        """Test that comments_status is 'none' when review_threads is None."""
        analysis = analyze_pr(mock_pr_data, [], [], review_threads=None)

        assert analysis.comments_status == "none"
        assert analysis.unresolved_comment_count == 0
        assert analysis.unresolved_comment_urls == []

    def test_analyze_pr_empty_review_threads(self, mock_pr_data):
        """Test that comments_status is 'none' when review_threads is empty list."""
        analysis = analyze_pr(mock_pr_data, [], [], review_threads=[])

        assert analysis.comments_status == "none"
        assert analysis.unresolved_comment_count == 0
        assert analysis.unresolved_comment_urls == []

    def test_analyze_pr_all_threads_resolved(self, mock_pr_data):
        """Test that all resolved threads produce 'resolved' status and no blockers."""
        review_threads = [
            {
                "isResolved": True,
                "isOutdated": False,
                "comments": {
                    "nodes": [
                        {
                            "url": "https://github.com/owner/repo/pull/123#discussion_r100",
                            "author": {"login": "reviewer1"},
                            "body": "Looks good now",
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
                            "body": "Fixed",
                        }
                    ]
                },
            },
        ]

        analysis = analyze_pr(mock_pr_data, [], [], review_threads=review_threads)

        assert analysis.comments_status == "resolved"
        assert analysis.unresolved_comment_count == 0
        assert analysis.unresolved_comment_urls == []
        # No UNRESOLVED_COMMENTS blocker should exist
        unresolved_blockers = [b for b in analysis.blockers if b.type == "UNRESOLVED_COMMENTS"]
        assert len(unresolved_blockers) == 0

    def test_analyze_pr_some_threads_unresolved(self, mock_pr_data):
        """Test that a mix of resolved and unresolved threads detects correct count."""
        review_threads = [
            {
                "isResolved": True,
                "isOutdated": False,
                "comments": {
                    "nodes": [
                        {
                            "url": "https://github.com/owner/repo/pull/123#discussion_r100",
                            "author": {"login": "reviewer1"},
                            "body": "Resolved comment",
                        }
                    ]
                },
            },
            {
                "isResolved": False,
                "isOutdated": False,
                "comments": {
                    "nodes": [
                        {
                            "url": "https://github.com/owner/repo/pull/123#discussion_r200",
                            "author": {"login": "reviewer2"},
                            "body": "Please fix this",
                        }
                    ]
                },
            },
            {
                "isResolved": False,
                "isOutdated": False,
                "comments": {
                    "nodes": [
                        {
                            "url": "https://github.com/owner/repo/pull/123#discussion_r201",
                            "author": {"login": "reviewer3"},
                            "body": "This needs work",
                        }
                    ]
                },
            },
        ]

        analysis = analyze_pr(mock_pr_data, [], [], review_threads=review_threads)

        assert analysis.comments_status == "unresolved"
        assert analysis.unresolved_comment_count == 2
        assert len(analysis.unresolved_comment_urls) == 2
        # Verify blocker exists
        unresolved_blockers = [b for b in analysis.blockers if b.type == "UNRESOLVED_COMMENTS"]
        assert len(unresolved_blockers) == 1
        assert "2 unresolved review comment(s)" in unresolved_blockers[0].description

    def test_analyze_pr_all_threads_unresolved(self, mock_pr_data):
        """Test that all unresolved threads create a blocker."""
        review_threads = [
            {
                "isResolved": False,
                "isOutdated": False,
                "comments": {
                    "nodes": [
                        {
                            "url": "https://github.com/owner/repo/pull/123#discussion_r300",
                            "author": {"login": "reviewer1"},
                            "body": "Fix this",
                        }
                    ]
                },
            },
            {
                "isResolved": False,
                "isOutdated": False,
                "comments": {
                    "nodes": [
                        {
                            "url": "https://github.com/owner/repo/pull/123#discussion_r301",
                            "author": {"login": "reviewer2"},
                            "body": "And this",
                        }
                    ]
                },
            },
        ]

        analysis = analyze_pr(mock_pr_data, [], [], review_threads=review_threads)

        assert analysis.comments_status == "unresolved"
        assert analysis.unresolved_comment_count == 2
        assert analysis.is_mergeable is False
        unresolved_blockers = [b for b in analysis.blockers if b.type == "UNRESOLVED_COMMENTS"]
        assert len(unresolved_blockers) == 1
        assert "2 unresolved review comment(s)" in unresolved_blockers[0].description

    def test_analyze_pr_unresolved_thread_urls(self, mock_pr_data):
        """Test that URLs are correctly extracted from thread comment nodes."""
        review_threads = [
            {
                "isResolved": False,
                "isOutdated": False,
                "comments": {
                    "nodes": [
                        {
                            "url": "https://github.com/owner/repo/pull/123#discussion_r400",
                            "author": {"login": "reviewer1"},
                            "body": "Comment one",
                        }
                    ]
                },
            },
            {
                "isResolved": False,
                "isOutdated": False,
                "comments": {
                    "nodes": [
                        {
                            "url": "https://github.com/owner/repo/pull/123#discussion_r401",
                            "author": {"login": "reviewer2"},
                            "body": "Comment two",
                        }
                    ]
                },
            },
        ]

        analysis = analyze_pr(mock_pr_data, [], [], review_threads=review_threads)

        assert len(analysis.unresolved_comment_urls) == 2
        assert "https://github.com/owner/repo/pull/123#discussion_r400" in analysis.unresolved_comment_urls
        assert "https://github.com/owner/repo/pull/123#discussion_r401" in analysis.unresolved_comment_urls

    def test_analyze_pr_thread_without_url(self, mock_pr_data):
        """Test that a thread with no URL in comments does not crash."""
        review_threads = [
            {
                "isResolved": False,
                "isOutdated": False,
                "comments": {
                    "nodes": [
                        {
                            "author": {"login": "reviewer1"},
                            "body": "No URL here",
                        }
                    ]
                },
            },
        ]

        analysis = analyze_pr(mock_pr_data, [], [], review_threads=review_threads)

        assert analysis.comments_status == "unresolved"
        assert analysis.unresolved_comment_count == 1
        assert analysis.unresolved_comment_urls == []
        # Should still create blocker even without URL
        unresolved_blockers = [b for b in analysis.blockers if b.type == "UNRESOLVED_COMMENTS"]
        assert len(unresolved_blockers) == 1

    def test_analyze_pr_outdated_unresolved_thread(self, mock_pr_data):
        """Test that an outdated but unresolved thread is still counted."""
        review_threads = [
            {
                "isResolved": False,
                "isOutdated": True,
                "comments": {
                    "nodes": [
                        {
                            "url": "https://github.com/owner/repo/pull/123#discussion_r500",
                            "author": {"login": "reviewer1"},
                            "body": "Old comment still unresolved",
                        }
                    ]
                },
            },
        ]

        analysis = analyze_pr(mock_pr_data, [], [], review_threads=review_threads)

        assert analysis.comments_status == "unresolved"
        assert analysis.unresolved_comment_count == 1
        assert len(analysis.unresolved_comment_urls) == 1
        unresolved_blockers = [b for b in analysis.blockers if b.type == "UNRESOLVED_COMMENTS"]
        assert len(unresolved_blockers) == 1
        assert "1 unresolved review comment(s)" in unresolved_blockers[0].description


class TestAnalyzePRReviewLabels:
    """Test analyze_pr review label parsing from PR labels."""

    def test_no_labels(self, mock_pr_data):
        """Test PR data with no labels field produces empty review_labels."""
        # mock_pr_data has no "labels" key by default
        analysis = analyze_pr(mock_pr_data, [], [])

        assert analysis.review_labels == []

    def test_empty_labels(self, mock_pr_data):
        """Test PR data with empty labels list produces empty review_labels."""
        mock_pr_data["labels"] = []
        analysis = analyze_pr(mock_pr_data, [], [])

        assert analysis.review_labels == []

    def test_lgtm_label(self, mock_pr_data):
        """Test lgtm-username label creates ReviewLabel with status lgtm."""
        mock_pr_data["labels"] = [{"name": "lgtm-alice"}]
        analysis = analyze_pr(mock_pr_data, [], [])

        assert len(analysis.review_labels) == 1
        assert analysis.review_labels[0].username == "alice"
        assert analysis.review_labels[0].status == "lgtm"

    def test_approved_label(self, mock_pr_data):
        """Test approved-username label creates ReviewLabel with status approved."""
        mock_pr_data["labels"] = [{"name": "approved-bob"}]
        analysis = analyze_pr(mock_pr_data, [], [])

        assert len(analysis.review_labels) == 1
        assert analysis.review_labels[0].username == "bob"
        assert analysis.review_labels[0].status == "approved"

    def test_changes_requested_label(self, mock_pr_data):
        """Test changes-requested-username label creates ReviewLabel with status changes-requested."""
        mock_pr_data["labels"] = [{"name": "changes-requested-carol"}]
        analysis = analyze_pr(mock_pr_data, [], [])

        assert len(analysis.review_labels) == 1
        assert analysis.review_labels[0].username == "carol"
        assert analysis.review_labels[0].status == "changes-requested"

    def test_change_requested_label(self, mock_pr_data):
        """Test change-requested-username (no 's') also creates ReviewLabel with status changes-requested."""
        mock_pr_data["labels"] = [{"name": "change-requested-dave"}]
        analysis = analyze_pr(mock_pr_data, [], [])

        assert len(analysis.review_labels) == 1
        assert analysis.review_labels[0].username == "dave"
        assert analysis.review_labels[0].status == "changes-requested"

    def test_commented_label_ignored(self, mock_pr_data):
        """Test commented-username label is no longer parsed and is ignored."""
        mock_pr_data["labels"] = [{"name": "commented-eve"}]
        analysis = analyze_pr(mock_pr_data, [], [])

        assert analysis.review_labels == []

    def test_bot_filtered_coderabbitai(self, mock_pr_data):
        """Test that lgtm-coderabbitai label is filtered out as a bot."""
        mock_pr_data["labels"] = [{"name": "lgtm-coderabbitai"}]
        analysis = analyze_pr(mock_pr_data, [], [])

        assert analysis.review_labels == []

    def test_bot_filtered_qe_bot(self, mock_pr_data):
        """Test that lgtm-openshift-virtualization-qe-bot label is filtered out as a bot."""
        mock_pr_data["labels"] = [{"name": "lgtm-openshift-virtualization-qe-bot"}]
        analysis = analyze_pr(mock_pr_data, [], [])

        assert analysis.review_labels == []

    def test_bot_filtered_bracket_bot(self, mock_pr_data):
        """Test that approved-somebot[bot] label is filtered out as a bot."""
        mock_pr_data["labels"] = [{"name": "approved-somebot[bot]"}]
        analysis = analyze_pr(mock_pr_data, [], [])

        assert analysis.review_labels == []

    def test_multiple_review_labels(self, mock_pr_data):
        """Test multiple review labels create corresponding ReviewLabels."""
        mock_pr_data["labels"] = [
            {"name": "lgtm-alice"},
            {"name": "changes-requested-bob"},
            {"name": "approved-charlie"},
        ]
        analysis = analyze_pr(mock_pr_data, [], [])

        assert len(analysis.review_labels) == 3
        usernames = {rl.username for rl in analysis.review_labels}
        statuses = {rl.status for rl in analysis.review_labels}
        assert usernames == {"alice", "bob", "charlie"}
        assert statuses == {"lgtm", "changes-requested", "approved"}

    def test_non_review_labels_ignored(self, mock_pr_data):
        """Test that non-review labels do not create ReviewLabels."""
        mock_pr_data["labels"] = [
            {"name": "size/XS"},
            {"name": "needs-rebase"},
            {"name": "branch-main"},
            {"name": "sig-network"},
            {"name": "commented-username"},
        ]
        analysis = analyze_pr(mock_pr_data, [], [])

        assert analysis.review_labels == []

    def test_mixed_review_and_non_review_labels(self, mock_pr_data):
        """Test that only review labels are extracted from a mix of labels."""
        mock_pr_data["labels"] = [
            {"name": "size/XS"},
            {"name": "lgtm-alice"},
            {"name": "needs-rebase"},
            {"name": "approved-bob"},
            {"name": "sig-network"},
        ]
        analysis = analyze_pr(mock_pr_data, [], [])

        assert len(analysis.review_labels) == 2
        usernames = {rl.username for rl in analysis.review_labels}
        assert usernames == {"alice", "bob"}

    def test_duplicate_user_approved_and_lgtm(self, mock_pr_data):
        """Test that a user can appear under both approved and lgtm (no deduplication)."""
        mock_pr_data["labels"] = [
            {"name": "approved-alice"},
            {"name": "lgtm-alice"},
        ]
        analysis = analyze_pr(mock_pr_data, [], [])

        assert len(analysis.review_labels) == 2
        statuses = [rl.status for rl in analysis.review_labels]
        assert "approved" in statuses
        assert "lgtm" in statuses
        assert all(rl.username == "alice" for rl in analysis.review_labels)


class TestAnalyzePRState:
    """Test PR state detection."""

    def test_state_open(self, mock_pr_data):
        """Test default state is open."""
        analysis = analyze_pr(mock_pr_data, [], [])
        assert analysis.state == "open"

    def test_state_merged(self, mock_pr_data):
        """Test merged PR state."""
        mock_pr_data["merged"] = True
        analysis = analyze_pr(mock_pr_data, [], [])
        assert analysis.state == "merged"

    def test_state_closed(self, mock_pr_data):
        """Test closed PR state."""
        mock_pr_data["state"] = "closed"
        analysis = analyze_pr(mock_pr_data, [], [])
        assert analysis.state == "closed"

    def test_state_draft(self, mock_pr_data):
        """Test draft PR state."""
        mock_pr_data["draft"] = True
        analysis = analyze_pr(mock_pr_data, [], [])
        assert analysis.state == "draft"

    def test_state_wip_colon_prefix(self, mock_pr_data):
        """Test WIP detection from title with colon prefix."""
        mock_pr_data["title"] = "WIP: work in progress"
        analysis = analyze_pr(mock_pr_data, [], [])
        assert analysis.state == "wip"

    def test_state_wip_bracket_prefix(self, mock_pr_data):
        """Test WIP detection from title with bracket prefix."""
        mock_pr_data["title"] = "[WIP] some feature"
        analysis = analyze_pr(mock_pr_data, [], [])
        assert analysis.state == "wip"

    def test_state_wip_space_prefix(self, mock_pr_data):
        """Test WIP detection from title with space prefix."""
        mock_pr_data["title"] = "wip some changes"
        analysis = analyze_pr(mock_pr_data, [], [])
        assert analysis.state == "wip"

    def test_state_merged_takes_priority(self, mock_pr_data):
        """Test merged state takes priority over draft."""
        mock_pr_data["merged"] = True
        mock_pr_data["draft"] = True
        analysis = analyze_pr(mock_pr_data, [], [])
        assert analysis.state == "merged"
