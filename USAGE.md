<!-- Generated using Claude cli -->
# Usage Examples

## Setup

1. **Set GitHub Token**

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

You can create a token at: https://github.com/settings/tokens

Required scopes:
- `repo` (full repository access) for private repos
- `public_repo` for public repos only

2. **Install the tool**

```bash
cd /home/rnetser/git/gh-pr-analyzer
uv sync
```

## Running the Tool

### Analyze Your Own PRs

**Note:** Analyzing your own PRs requires a `GITHUB_TOKEN` to be set.

```bash
# Set your GitHub token first
export GITHUB_TOKEN="ghp_your_token_here"

# Using the installed command
uv run gh-pr-analyzer

# Or run as a module
uv run python -m gh_pr_analyzer
```

### Analyze Another User's PRs

```bash
# Without token (public repos only, lower rate limits)
uv run gh-pr-analyzer octocat

# With token (higher rate limits, private repos)
export GITHUB_TOKEN="ghp_your_token_here"
uv run gh-pr-analyzer octocat
```

### Example Output

When you run the tool, you'll see output like:

```
Found 3 open PR(s) for username

                                PR Analysis Results
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Repository         ┃ PR #┃ Title                    ┃ Merge Blockers        ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ user/awesome-repo  │ 42  │ Add authentication       │ ✓ Ready to merge      │
│ user/cool-project  │ 137 │ Fix memory leak          │ ✗ Check 'tests' fail  │
│                    │     │                          │   Test suite exited   │
│ user/web-app       │ 256 │ Update documentation     │ ⚠ CHANGES_REQUESTED   │
│                    │     │                          │   Reviewers: alice    │
└────────────────────┴─────┴──────────────────────────┴───────────────────────┘

Summary:
  Ready to merge: 1
  Blocked: 2
  Total: 3
```

## Understanding the Output

### Status Indicators

| Icon | Meaning | Action Required |
|------|---------|----------------|
| ✓ | Ready to merge | None - can be merged |
| ✗ | Failing check | Fix the failing CI/CD tests |
| ⏳ | Pending checks | Wait for checks to complete |
| ⚡ | Merge conflict | Resolve conflicts with base branch |
| ⚠ | Changes requested | Address reviewer feedback |
| • | Other blocker | Check details |

### Blocker Types

1. **FAILING_CHECK**: One or more CI/CD checks failed
   - The tool shows which check failed
   - May include error output details

2. **PENDING_CHECKS**: CI/CD checks still running
   - Wait for completion before merging
   - Shows how many checks are pending

3. **MERGE_CONFLICT**: Branch conflicts with base
   - Pull latest changes from base branch
   - Resolve conflicts locally

4. **CHANGES_REQUESTED**: Reviewer requested changes
   - Shows which reviewers requested changes
   - Address their feedback

5. **MISSING_APPROVALS**: Required approvals not met
   - Request reviews from code owners
   - Wait for approval

6. **BRANCH_PROTECTION**: Blocked by repository rules
   - Check branch protection settings
   - Ensure all requirements are met

## Troubleshooting

### "GitHub token not found" Error

Make sure you've set the GITHUB_TOKEN environment variable:

```bash
echo $GITHUB_TOKEN
```

If empty, set it:

```bash
export GITHUB_TOKEN="your_token_here"
```

### "No open PRs found"

This means the user has no open pull requests. Try:
- Check if the username is correct
- Verify the user has public repositories with open PRs
- For private repos, ensure your token has `repo` scope

### API Rate Limiting

GitHub API has rate limits. If you hit them:
- Wait for the rate limit to reset (check headers)
- Use a personal access token (higher limits than unauthenticated)
- For organizations, consider using a GitHub App

## Advanced Usage

### Programmatic Use

You can also use the tool as a library in your Python code:

```python
import asyncio
from gh_pr_analyzer.github_client import GitHubClient
from gh_pr_analyzer.analyzer import analyze_pr

async def main():
    client = GitHubClient()

    # Get user's PRs
    prs = await client.get_user_open_prs("username")

    for pr in prs:
        # Get PR details
        owner, repo = "owner", "repo"
        pr_number = pr["number"]

        pr_details = await client.get_pr_details(owner, repo, pr_number)
        reviews = await client.get_pr_reviews(owner, repo, pr_number)
        check_runs = await client.get_check_runs(owner, repo, pr_details["head"]["sha"])

        # Analyze
        analysis = analyze_pr(pr_details, reviews, check_runs)

        if analysis.is_mergeable:
            print(f"✅ {analysis.repo}#{analysis.pr_number} - {analysis.title}")
        else:
            print(f"❌ {analysis.repo}#{analysis.pr_number} - {analysis.title}")
            for blocker in analysis.blockers:
                print(f"   - {blocker}")

asyncio.run(main())
```

## Tips

1. **Check PRs regularly**: Run the tool before starting your day to see what needs attention
2. **Filter by status**: The tool shows all blockers, prioritize by urgency
3. **Use with CI/CD**: Integrate into your workflow to automatically check PR status
4. **Team usage**: Share the tool with your team for consistent PR monitoring
