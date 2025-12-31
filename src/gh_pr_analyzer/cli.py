"""CLI interface for GitHub PR analyzer."""

import asyncio
from typing import Optional
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from gh_pr_analyzer.analyzer import analyze_pr
from gh_pr_analyzer.github_client import GitHubClient

app = typer.Typer(help="Analyze GitHub PRs and show why they cannot be merged")
console = Console()


def parse_repo_from_url(url: str) -> tuple[str, str]:
    """Extract owner and repo from a GitHub URL with proper validation.

    Args:
        url: GitHub repository URL

    Returns:
        Tuple of (owner, repo)

    Raises:
        ValueError: If URL is invalid or not a GitHub URL
    """
    parsed = urlparse(url)

    # Validate domain
    valid_domains = ['github.com', 'api.github.com', 'www.github.com']
    if parsed.netloc not in valid_domains:
        raise ValueError(f"Invalid GitHub URL domain: {parsed.netloc}")

    # Remove leading/trailing slashes and split
    path_parts = [p for p in parsed.path.split('/') if p]

    # Handle API format: /repos/owner/repo/...
    if 'repos' in path_parts:
        idx = path_parts.index('repos')
        if len(path_parts) < idx + 3:
            raise ValueError(f"Invalid GitHub repo URL: {url}")
        return path_parts[idx + 1], path_parts[idx + 2]

    # Standard format: /owner/repo/...
    if len(path_parts) < 2:
        raise ValueError(f"Invalid GitHub repo URL: {url}")

    return path_parts[0], path_parts[1]


async def analyze_user_prs(username: str | None = None) -> None:
    """Analyze all open PRs for a user.

    Args:
        username: GitHub username. If None, uses authenticated user.
    """
    try:
        client = GitHubClient()

        # Get username if not provided
        if not username:
            with console.status("[bold blue]Fetching authenticated user..."):
                user_data = await client.get_authenticated_user()
                username = user_data["login"]

        # Fetch open PRs
        with console.status(f"[bold blue]Fetching open PRs for {username}..."):
            prs = await client.get_user_open_prs(username)

        if not prs:
            console.print(f"[yellow]No open PRs found for {username}[/yellow]")
            return

        console.print(f"\n[bold green]Found {len(prs)} open PR(s) for {username}[/bold green]\n")

        # Analyze each PR
        analyses = []
        for pr in prs:
            # Extract repo info from PR URL
            repo_url = pr["repository_url"]
            owner, repo = parse_repo_from_url(repo_url)
            pr_number = pr["number"]

            with console.status(f"[bold blue]Analyzing {owner}/{repo}#{pr_number}..."):
                # Fetch detailed data
                pr_details = await client.get_pr_details(owner, repo, pr_number)
                reviews = await client.get_pr_reviews(owner, repo, pr_number)
                review_comments = await client.get_pr_review_comments(owner, repo, pr_number)
                head_sha = pr_details["head"]["sha"]
                check_runs = await client.get_check_runs(owner, repo, head_sha)

                # Analyze
                analysis = analyze_pr(pr_details, reviews, check_runs, review_comments)
                analyses.append(analysis)

        # Display results
        display_results(analyses)

    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        raise typer.Exit(1)


def display_results(analyses: list) -> None:
    """Display analysis results in a rich table.

    Args:
        analyses: List of PRAnalysis objects
    """
    table = Table(
        title="PR Analysis Results",
        show_header=True,
        header_style="bold magenta",
        show_lines=True,  # Add horizontal separators between rows
    )

    table.add_column("Repository", style="cyan", no_wrap=True)
    table.add_column("PR #", style="blue")
    table.add_column("Title", style="white")
    table.add_column("CI Status", style="white", justify="center")
    table.add_column("Reviews", style="white", justify="center")
    table.add_column("Comments", style="white", justify="center")
    table.add_column("Conflicts", style="white", justify="center")

    mergeable_count = 0
    blocked_count = 0

    for analysis in analyses:
        # Track mergeable status
        if analysis.is_mergeable:
            mergeable_count += 1
        else:
            blocked_count += 1

        # Format CI Status
        if analysis.ci_status == "passing":
            ci_text = Text("✅ Passing", style="bold green")
        elif analysis.ci_status == "failing":
            ci_text = Text("❌ Failing:\n", style="bold red")
            for check_name in analysis.failed_check_names:
                ci_text.append(f"  • {check_name}\n", style="red")
        elif analysis.ci_status == "pending":
            ci_text = Text("⏳ Pending:\n", style="bold yellow")
            for check_name in analysis.pending_check_names:
                ci_text.append(f"  • {check_name}\n", style="yellow")
        else:
            ci_text = Text("⏳ Unknown", style="dim")

        # Format Reviews
        if analysis.review_status == "approved":
            review_text = Text("✅ Approved", style="bold green")
        elif analysis.review_status == "changes_requested":
            review_text = Text("❌ Changes requested", style="bold red")
        elif analysis.review_status == "pending":
            review_text = Text("⏳ Pending", style="bold yellow")
        elif analysis.review_status == "none":
            review_text = Text("➖ None", style="dim")
        else:
            review_text = Text("⏳ Unknown", style="dim")

        # Format Comments
        if analysis.comments_status == "resolved":
            comments_text = Text("✅ Resolved", style="bold green")
        elif analysis.comments_status == "unresolved":
            comments_text = Text(f"❌ {analysis.unresolved_comment_count} unresolved:\n", style="bold red")
            for url in analysis.unresolved_comment_urls:
                # Use Rich's link markup syntax for clickable links
                comments_text.append(f"  • ", style="red")
                comments_text.append(url, style="link " + url)
                comments_text.append("\n")
        elif analysis.comments_status == "none":
            comments_text = Text("➖ None", style="dim")
        else:
            comments_text = Text("⏳ Unknown", style="dim")

        # Format Conflicts
        if analysis.conflicts_status == "clean":
            conflicts_text = Text("✅ Clean", style="bold green")
        elif analysis.conflicts_status == "conflicts":
            conflicts_text = Text("❌ Has conflicts", style="bold red")
        else:
            conflicts_text = Text("⏳ Unknown", style="dim")

        table.add_row(
            analysis.repo,
            str(analysis.pr_number),
            analysis.title[:50],
            ci_text,
            review_text,
            comments_text,
            conflicts_text,
        )

    console.print(table)

    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  [green]Ready to merge:[/green] {mergeable_count}")
    console.print(f"  [red]Blocked:[/red] {blocked_count}")
    console.print(f"  [blue]Total:[/blue] {len(analyses)}\n")


@app.command()
def main(
    username: Optional[str] = typer.Argument(None, help="GitHub username (defaults to authenticated user)"),
) -> None:
    """Analyze all open PRs for a GitHub user and show merge blockers."""
    asyncio.run(analyze_user_prs(username))


if __name__ == "__main__":
    app()
