"""CLI interface for GitHub PR analyzer."""

import asyncio
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from gh_pr_analyzer.analyzer import PRAnalysis, analyze_pr
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


def export_to_html(analyses: list[PRAnalysis], filename: str, username: str, is_authenticated: bool = True) -> None:
    """Export analysis results to an HTML file.

    Args:
        analyses: List of PRAnalysis objects
        filename: Output HTML filename
        username: GitHub username being analyzed
        is_authenticated: Whether the client was authenticated when fetching data
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Count summary statistics
    mergeable_count = sum(1 for a in analyses if a.is_mergeable)
    blocked_count = len(analyses) - mergeable_count

    # Build HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PR Analysis - {username}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            max-width: 100%;
            padding: 20px;
            box-sizing: border-box;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
        }}

        h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}

        .metadata {{
            opacity: 0.9;
            font-size: 0.95rem;
        }}

        .metadata span {{
            margin-right: 1.5rem;
        }}

        .warning-banner {{
            background: #fef5e7;
            border: 2px solid #f39c12;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem;
            color: #975a16;
            font-weight: 600;
            text-align: center;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
            table-layout: auto;
        }}

        thead {{
            background: #f7fafc;
            border-bottom: 2px solid #e2e8f0;
        }}

        th {{
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            color: #2d3748;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }}

        td {{
            padding: 1rem;
            border-bottom: 1px solid #e2e8f0;
            vertical-align: top;
            word-wrap: break-word;
            max-width: 300px;
        }}

        tbody tr:hover {{
            background: #f7fafc;
        }}

        .status-badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            white-space: nowrap;
        }}

        .status-passing {{
            background: #c6f6d5;
            color: #22543d;
        }}

        .status-failing {{
            background: #fed7d7;
            color: #742a2a;
        }}

        .status-pending {{
            background: #fef5e7;
            color: #975a16;
        }}

        .status-none {{
            background: #e2e8f0;
            color: #4a5568;
        }}

        .status-unknown {{
            background: #e2e8f0;
            color: #718096;
        }}

        .check-list {{
            margin: 0.5rem 0;
            padding-left: 1rem;
            font-size: 0.85rem;
        }}

        .check-list li {{
            margin: 0.25rem 0;
        }}

        .failing-check {{
            color: #c53030;
        }}

        .pending-check {{
            color: #d69e2e;
        }}

        .comment-link {{
            color: #3182ce;
            text-decoration: none;
            word-break: break-all;
            font-size: 0.85rem;
        }}

        .comment-link:hover {{
            text-decoration: underline;
        }}

        .pr-title {{
            color: #2d3748;
            text-decoration: none;
            font-weight: 500;
        }}

        .pr-title:hover {{
            color: #667eea;
        }}

        .pr-number {{
            color: #3182ce;
            font-weight: 600;
        }}

        .summary {{
            padding: 2rem;
            background: #f7fafc;
            border-top: 2px solid #e2e8f0;
        }}

        .summary h2 {{
            color: #2d3748;
            margin-bottom: 1rem;
            font-size: 1.25rem;
        }}

        .summary-stats {{
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
        }}

        .stat {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .stat-label {{
            color: #4a5568;
            font-weight: 500;
        }}

        .stat-value {{
            font-weight: 700;
            font-size: 1.25rem;
        }}

        .stat-value.green {{
            color: #22543d;
        }}

        .stat-value.red {{
            color: #742a2a;
        }}

        .stat-value.blue {{
            color: #2c5282;
        }}

        .comment-list {{
            margin-top: 0.5rem;
        }}

        .comment-item {{
            margin: 0.25rem 0;
            padding-left: 1rem;
        }}

        /* Responsive for mobile */
        @media (max-width: 768px) {{
            table {{
                font-size: 12px;
            }}
            td, th {{
                padding: 8px 4px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 PR Merge Blocker Analysis</h1>
            <div class="metadata">
                <span>👤 User: <strong>{username}</strong></span>
                <span>📅 Generated: <strong>{timestamp}</strong></span>
            </div>
        </header>
"""

    # Add warning banner if unauthenticated
    if not is_authenticated:
        html_content += """
        <div class="warning-banner">
            ⚠️ Warning: No GitHub token provided. Only public repository data is included. Private repositories are not shown.
        </div>
"""

    html_content += f"""
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-stats">
                <div class="stat">
                    <span class="stat-label">Total PRs analyzed:</span>
                    <span class="stat-value blue">{len(analyses)}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Ready to merge:</span>
                    <span class="stat-value green">{mergeable_count}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Blocked:</span>
                    <span class="stat-value red">{blocked_count}</span>
                </div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Repository</th>
                    <th>PR #</th>
                    <th>Title</th>
                    <th>CI Status</th>
                    <th>Reviews</th>
                    <th>Comments</th>
                    <th>Conflicts</th>
                </tr>
            </thead>
            <tbody>
"""

    # Add table rows for each PR
    for analysis in analyses:
        # Repository name
        repo_cell = f'<td>{escape(analysis.repo)}</td>'

        # PR number (linked)
        pr_number_cell = f'<td><a href="{escape(analysis.url)}" class="pr-number" target="_blank">#{analysis.pr_number}</a></td>'

        # PR title (linked)
        title_cell = f'<td><a href="{escape(analysis.url)}" class="pr-title" target="_blank">{escape(analysis.title[:80])}</a></td>'

        # CI Status
        if analysis.ci_status == "passing":
            ci_cell = '<td><span class="status-badge status-passing">✅ Passing</span></td>'
        elif analysis.failed_check_names or analysis.pending_check_names:
            ci_content = []
            if analysis.failed_check_names:
                ci_content.append('<div><span class="status-badge status-failing">❌ Failing</span></div>')
                ci_content.append('<ul class="check-list">')
                for check_name in analysis.failed_check_names:
                    ci_content.append(f'<li class="failing-check">{escape(check_name)}</li>')
                ci_content.append('</ul>')

            if analysis.pending_check_names:
                ci_content.append('<div><span class="status-badge status-pending">⏳ Pending</span></div>')
                ci_content.append('<ul class="check-list">')
                for check_name in analysis.pending_check_names:
                    ci_content.append(f'<li class="pending-check">{escape(check_name)}</li>')
                ci_content.append('</ul>')

            ci_cell = f'<td>{"".join(ci_content)}</td>'
        else:
            ci_cell = '<td><span class="status-badge status-unknown">⏳ Unknown</span></td>'

        # Reviews
        if analysis.review_status == "approved":
            review_cell = '<td><span class="status-badge status-passing">✅ Approved</span></td>'
        elif analysis.review_status == "changes_requested":
            review_cell = '<td><span class="status-badge status-failing">❌ Changes requested</span></td>'
        elif analysis.review_status == "pending":
            review_cell = '<td><span class="status-badge status-pending">⏳ Pending</span></td>'
        elif analysis.review_status == "none":
            review_cell = '<td><span class="status-badge status-none">➖ None</span></td>'
        else:
            review_cell = '<td><span class="status-badge status-unknown">⏳ Unknown</span></td>'

        # Comments
        if analysis.comments_status == "resolved":
            comments_cell = '<td><span class="status-badge status-passing">✅ Resolved</span></td>'
        elif analysis.comments_status == "unresolved":
            comments_content = [f'<div><span class="status-badge status-failing">❌ {analysis.unresolved_comment_count} unresolved</span></div>']
            comments_content.append('<div class="comment-list">')
            for url in analysis.unresolved_comment_urls:  # Show all URLs
                comments_content.append(f'<div class="comment-item">• <a href="{escape(url)}" class="comment-link" target="_blank">{escape(url)}</a></div>')
            comments_content.append('</div>')
            comments_cell = f'<td>{"".join(comments_content)}</td>'
        elif analysis.comments_status == "none":
            comments_cell = '<td><span class="status-badge status-none">➖ None</span></td>'
        else:
            comments_cell = '<td><span class="status-badge status-unknown">⏳ Unknown</span></td>'

        # Conflicts
        if analysis.conflicts_status == "clean":
            conflicts_cell = '<td><span class="status-badge status-passing">✅ Clean</span></td>'
        elif analysis.conflicts_status == "conflicts":
            conflicts_cell = '<td><span class="status-badge status-failing">❌ Has conflicts</span></td>'
        else:
            conflicts_cell = '<td><span class="status-badge status-unknown">⏳ Unknown</span></td>'

        # Add row
        html_content += f"""
                <tr>
                    {repo_cell}
                    {pr_number_cell}
                    {title_cell}
                    {ci_cell}
                    {review_cell}
                    {comments_cell}
                    {conflicts_cell}
                </tr>
"""

    # Close table
    html_content += f"""
            </tbody>
        </table>
    </div>
</body>
</html>
"""

    # Write to file
    output_path = Path(filename)
    output_path.write_text(html_content, encoding="utf-8")
    console.print(f"[green]✅ HTML report exported to: {output_path.absolute()}[/green]")


async def analyze_user_prs(username: str | None = None, html_output: str | None = None) -> None:
    """Analyze all open PRs for a user.

    Args:
        username: GitHub username. If None, uses authenticated user.
        html_output: Optional HTML filename for exporting results
    """
    try:
        client = GitHubClient()

        # Warn if unauthenticated
        if not client.is_authenticated:
            console.print("[yellow]⚠️  No GITHUB_TOKEN set. Only public repository data will be collected.[/yellow]\n")

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

        # Export to HTML if requested
        if html_output:
            export_to_html(analyses, html_output, username, client.is_authenticated)

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

        # Format CI Status - show both failing and pending when applicable
        if analysis.ci_status == "passing":
            ci_text = Text("✅ Passing", style="bold green")
        elif analysis.failed_check_names or analysis.pending_check_names:
            # Build combined status showing both failing and pending
            ci_text = Text()

            # Add failing checks if present
            if analysis.failed_check_names:
                ci_text.append("❌ Failing:\n", style="bold red")
                for check_name in analysis.failed_check_names:
                    ci_text.append(f"  • {check_name}\n", style="red")

            # Add pending checks if present
            if analysis.pending_check_names:
                ci_text.append("⏳ Pending:\n", style="bold yellow")
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
    html: Optional[str] = typer.Option(None, "--html", help="Export results to HTML file"),
) -> None:
    """Analyze all open PRs for a GitHub user and show merge blockers."""
    asyncio.run(analyze_user_prs(username, html_output=html))


if __name__ == "__main__":
    app()
