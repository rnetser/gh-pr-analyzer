"""PR analysis logic to detect merge blockers."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MergeBlocker:
    """Represents a reason why a PR cannot be merged."""

    type: str
    description: str
    details: str | None = None

    def __str__(self) -> str:
        """Format blocker for display."""
        if self.details:
            return f"{self.type}: {self.description}\n  {self.details}"
        return f"{self.type}: {self.description}"


@dataclass
class PRAnalysis:
    """Analysis results for a pull request."""

    repo: str
    pr_number: int
    title: str
    url: str
    blockers: list[MergeBlocker] = field(default_factory=list)
    ci_status: str = "unknown"  # passing, failing, pending, unknown
    review_status: str = "unknown"  # approved, changes_requested, pending, none
    comments_status: str = "unknown"  # resolved, unresolved, none
    conflicts_status: str = "unknown"  # clean, conflicts, unknown
    unresolved_comment_count: int = 0
    failed_check_count: int = 0
    pending_check_count: int = 0

    @property
    def is_mergeable(self) -> bool:
        """Check if PR can be merged."""
        return len(self.blockers) == 0


def analyze_pr(
    pr_data: dict[str, Any],
    reviews: list[dict[str, Any]],
    check_runs: list[dict[str, Any]],
    review_comments: list[dict[str, Any]] | None = None,
) -> PRAnalysis:
    """Analyze a PR to identify merge blockers.

    Args:
        pr_data: PR details from GitHub API
        reviews: List of reviews for the PR
        check_runs: List of check runs for the PR's head commit
        review_comments: List of review comments (optional)

    Returns:
        PRAnalysis object with identified blockers
    """
    repo_full_name = pr_data["base"]["repo"]["full_name"]
    pr_number = pr_data["number"]
    title = pr_data["title"]
    url = pr_data["html_url"]

    analysis = PRAnalysis(repo=repo_full_name, pr_number=pr_number, title=title, url=url)

    if review_comments is None:
        review_comments = []

    # Check mergeable state
    mergeable_state = pr_data.get("mergeable_state", "unknown")
    mergeable = pr_data.get("mergeable")

    if mergeable is False or mergeable_state == "dirty":
        analysis.conflicts_status = "conflicts"
        analysis.blockers.append(
            MergeBlocker(
                type="MERGE_CONFLICT",
                description="PR has merge conflicts",
                details="Resolve conflicts with the base branch",
            )
        )
    elif mergeable is True:
        analysis.conflicts_status = "clean"
    else:
        analysis.conflicts_status = "unknown"

    # Check for failing check runs
    failed_checks = [check for check in check_runs if check.get("conclusion") == "failure"]
    analysis.failed_check_count = len(failed_checks)

    for check in failed_checks:
        output = check.get("output", {})
        summary = output.get("summary", "")

        # Extract last 5 lines of error output if available
        error_lines = summary.strip().split("\n")[-5:] if summary else []
        error_detail = "\n    ".join(error_lines) if error_lines else None

        check_name = check.get("name", "Unknown check")
        analysis.blockers.append(
            MergeBlocker(
                type="FAILING_CHECK",
                description=f"Check '{check_name}' failed",
                details=error_detail,
            )
        )

    # Check for pending check runs
    pending_checks = [
        check for check in check_runs if check.get("status") != "completed" and check.get("conclusion") is None
    ]
    analysis.pending_check_count = len(pending_checks)

    if pending_checks:
        check_names = ", ".join(check.get("name", "Unknown") for check in pending_checks[:3])
        if len(pending_checks) > 3:
            check_names += f" and {len(pending_checks) - 3} more"

        analysis.blockers.append(
            MergeBlocker(
                type="PENDING_CHECKS",
                description=f"{len(pending_checks)} check(s) still running",
                details=check_names,
            )
        )

    # Set CI status
    if failed_checks:
        analysis.ci_status = "failing"
    elif pending_checks:
        analysis.ci_status = "pending"
    elif check_runs:
        analysis.ci_status = "passing"
    else:
        analysis.ci_status = "unknown"

    # Check for requested changes
    changes_requested = [review for review in reviews if review.get("state") == "CHANGES_REQUESTED"]
    if changes_requested:
        analysis.review_status = "changes_requested"
        # Safely extract reviewer logins with fallback for missing user
        reviewer_logins = []
        for review in changes_requested:
            user = review.get("user")
            if user and user.get("login"):
                reviewer_logins.append(user["login"])

        reviewers = ", ".join(set(reviewer_logins)) if reviewer_logins else "Unknown reviewers"
        analysis.blockers.append(
            MergeBlocker(
                type="CHANGES_REQUESTED",
                description=f"Changes requested by reviewer(s)",
                details=f"Reviewers: {reviewers}",
            )
        )

    # Check for approvals if required
    approvals = [review for review in reviews if review.get("state") == "APPROVED"]
    if approvals:
        analysis.review_status = "approved"

    if pr_data.get("base", {}).get("repo", {}).get("private", False):
        # For private repos, check if approvals are needed (basic check)
        # This is a simplified check - real implementation would need branch protection rules
        if not approvals and mergeable_state == "blocked":
            analysis.review_status = "pending"
            analysis.blockers.append(
                MergeBlocker(
                    type="MISSING_APPROVALS",
                    description="Required approvals missing",
                    details="This PR may require approval from code owners",
                )
            )

    # Set review status if not set yet
    if analysis.review_status == "unknown":
        if reviews:
            analysis.review_status = "pending"
        else:
            analysis.review_status = "none"

    # Check for unresolved review comments
    # A comment is considered unresolved if it has no replies or the thread is still open
    if review_comments:
        # Group comments by thread (conversation_id or in_reply_to_id)
        # Comments without replies are potentially unresolved
        comment_ids = {comment["id"] for comment in review_comments}
        # Comments that are replies to other comments
        reply_to_ids = {comment.get("in_reply_to_id") for comment in review_comments if comment.get("in_reply_to_id")}

        # Top-level comments (not replies)
        top_level_comments = [c for c in review_comments if not c.get("in_reply_to_id")]

        # Count unresolved: top-level comments that have no replies
        unresolved_comments = [c for c in top_level_comments if c["id"] not in reply_to_ids]

        analysis.unresolved_comment_count = len(unresolved_comments)

        if unresolved_comments:
            analysis.comments_status = "unresolved"
            analysis.blockers.append(
                MergeBlocker(
                    type="UNRESOLVED_COMMENTS",
                    description=f"{len(unresolved_comments)} unresolved review comment(s)",
                    details="Review and resolve all discussion threads",
                )
            )
        else:
            analysis.comments_status = "resolved"
    else:
        analysis.comments_status = "none"

    # Check if blocked by branch protection
    if mergeable_state == "blocked" and not analysis.blockers:
        analysis.blockers.append(
            MergeBlocker(
                type="BRANCH_PROTECTION",
                description="Blocked by branch protection rules",
                details="Check repository branch protection settings",
            )
        )

    return analysis
