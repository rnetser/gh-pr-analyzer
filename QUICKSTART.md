<!-- Generated using Claude cli -->
# Quick Start Guide

## 1. Set Your GitHub Token (Optional but Recommended)

```bash
export GITHUB_TOKEN="ghp_your_personal_access_token"
```

Get a token from: https://github.com/settings/tokens

Required permissions:
- `repo` (for private repos) OR `public_repo` (for public repos only)

**Why use a token?**
- ✅ Higher rate limits (5,000/hour vs 60/hour)
- ✅ Access to private repositories
- ✅ Can analyze your own PRs without specifying username
- ✅ No warning banner in output

**Without a token:**
- Username argument is **mandatory**
- Cannot analyze your own PRs
- Limited to 60 requests/hour
- Public repositories only

## 2. Install Dependencies

```bash
cd /home/rnetser/git/gh-pr-analyzer
uv sync
```

## 3. Run the Tool

### Analyze Your Own PRs

**Note:** Requires `GITHUB_TOKEN` to be set (see step 1).

```bash
uv run gh-pr-analyzer
```

### Analyze Another User's PRs

**Note:** Username is mandatory when running without `GITHUB_TOKEN`.

```bash
# Without token (public repos only)
uv run gh-pr-analyzer octocat

# With token (recommended - higher rate limits, private repos)
export GITHUB_TOKEN="ghp_your_token_here"
uv run gh-pr-analyzer octocat
```

## What You'll See

The tool shows a table with:
- Repository name
- PR number (clickable link)
- PR title
- Merge blockers (if any)

### Example Output

```
                                PR Analysis Results
┏━━━━━━━━━━━━━━━━━━┳━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Repository       ┃ PR #┃ Title              ┃ Merge Blockers      ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ owner/repo1      │ 123 │ Add feature        │ ✓ Ready to merge    │
│ owner/repo2      │ 456 │ Fix bug            │ ✗ Check 'tests'     │
│                  │     │                    │   failed            │
└──────────────────┴─────┴────────────────────┴─────────────────────┘

Summary:
  Ready to merge: 1
  Blocked: 1
  Total: 2
```

## Icons Explained

| Icon | Meaning |
|------|---------|
| ✓ | Ready to merge |
| ✗ | Failing CI/CD check |
| ⏳ | Checks still running |
| ⚡ | Merge conflict |
| ⚠ | Changes requested |
| • | Other blocker |

## Troubleshooting

### "GitHub token not found"
Set the GITHUB_TOKEN environment variable:
```bash
export GITHUB_TOKEN="your_token"
```

### "No open PRs found"
The user has no open pull requests. Try a different username.

### Rate Limiting
GitHub API has rate limits. Wait a bit and try again, or check:
```bash
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit
```

## Next Steps

- Read [README.md](README.md) for detailed documentation
- See [USAGE.md](USAGE.md) for advanced usage examples
- Check [IMPLEMENTATION.md](IMPLEMENTATION.md) for technical details

## Quick Commands

```bash
# Test installation
uv run python -c "from gh_pr_analyzer import cli; print('✅ Ready!')"

# Show help
uv run gh-pr-analyzer --help

# Analyze your PRs
uv run gh-pr-analyzer

# Analyze specific user
uv run gh-pr-analyzer username
```

That's it! You're ready to analyze GitHub PRs. 🚀
