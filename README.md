# gh-pr-analyzer

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A CLI tool that analyzes GitHub pull requests and shows why they cannot be merged.

## Features

- **Comprehensive PR status overview**:
  - **CI Status**: Lists individual failing/pending check names with color-coded indicators
  - **Review Status**: Shows approval state and requested changes
  - **Comments**: Displays unresolved comment counts with clickable links
  - **Merge Conflicts**: Detects branch conflicts
- **Beautiful terminal output** with Rich tables and color-coded status indicators
- **HTML export** for shareable reports with styled tables and clickable links
- **Organized multi-column layout** for quick scanning
- **Summary statistics** showing ready-to-merge vs blocked PRs
- **Fast async** HTTP requests for quick analysis

### Status Indicators

- ✅ **Green** - Good/Passing/Ready
- ❌ **Red** - Blocking issue
- ⏳ **Yellow** - Pending/In progress
- ➖ **Gray** - Not applicable/None

## Installation

```bash
# Clone the repository
git clone https://github.com/rnetser/gh-pr-analyzer.git
cd gh-pr-analyzer

# Install with uv
uv sync
```

## Configuration

A GitHub personal access token is **optional** but recommended for better API limits and access to private repositories.

### Token Options

**Without a token:**
- ✅ Access to public repositories only
- ⚠️ Rate limited to 60 requests/hour
- ⚠️ Warning banner shown in output

**With a token:**
- ✅ Access to public and private repositories
- ✅ 5,000 requests/hour rate limit
- ✅ Full functionality

### Creating a GitHub Token

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give your token a descriptive name
4. Select the following scopes:
   - `repo` - Full control of private repositories
   - `read:user` - Read user profile data
5. Click "Generate token"
6. Copy the token immediately (you won't be able to see it again)

### Setting the Token

```bash
export GITHUB_TOKEN="your_token_here"
```

To make this permanent, add it to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

## Usage

```bash
# Analyze your own PRs (no token required, but limited)
uv run gh-pr-analyzer

# With authentication for better limits and private repo access
export GITHUB_TOKEN="your_token_here"
uv run gh-pr-analyzer

# Analyze another user's PRs
uv run gh-pr-analyzer username
```

### HTML Export

```bash
# Export results to an HTML file
uv run gh-pr-analyzer username --html report.html

# Export your own PRs to HTML
uv run gh-pr-analyzer --html my-prs.html
```

The HTML export includes:
- Summary statistics at the top of the report
- All unresolved comments with clickable links (no truncation)
- Responsive design that fits browser width
- Styled table with color-coded status badges
- Warning banner when running without authentication token
- Generation timestamp

## Example Output

```
                                          PR Analysis Results
┏━━━━━━━━━━━━━━┳━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Repository   ┃ PR #┃ Title            ┃ CI Status           ┃ Reviews      ┃ Comments                    ┃ Conflicts  ┃
┡━━━━━━━━━━━━━━╇━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ org/repo     │ #42 │ Add auth feature │ ❌ Failing:         │ ❌ Changes   │ ❌ 2 unresolved:            │ ✅ Clean   │
│              │     │                  │   • lint            │   requested  │   • github.com/.../r123     │            │
│              │     │                  │   • test-unit       │              │   • github.com/.../r456     │            │
├──────────────┼─────┼──────────────────┼─────────────────────┼──────────────┼─────────────────────────────┼────────────┤
│ org/repo2    │ #15 │ Fix login bug    │ ✅ Passing          │ ✅ Approved  │ ✅ Resolved                 │ ✅ Clean   │
├──────────────┼─────┼──────────────────┼─────────────────────┼──────────────┼─────────────────────────────┼────────────┤
│ org/repo3    │ #78 │ Update API docs  │ ⏳ Pending:         │ ⏳ Pending   │ ➖ None                     │ ❌ Conflicts│
│              │     │                  │   • deploy-preview  │              │                             │            │
└──────────────┴─────┴──────────────────┴─────────────────────┴──────────────┴─────────────────────────────┴────────────┘

Summary:
  ✅ Ready to merge: 1
  ❌ Blocked: 2
  Total PRs: 3
```

## Development

### Run tests

```bash
uv run pytest -v
```

### Run tests with coverage

```bash
uv run pytest --cov
```

### Type checking

```bash
uv run mypy src/gh_pr_analyzer
```

## License

MIT License - see the LICENSE file for details.
