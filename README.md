# gh-pr-analyzer

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A CLI tool that analyzes GitHub pull requests and shows why they cannot be merged.

## Features

- **Detects merge blockers**:
  - ✗ Failing CI checks (with last 5 lines of error output)
  - ⏳ Pending reviews
  - ⚠ Requested changes
  - ⚡ Merge conflicts
- **Beautiful terminal output** with Rich tables and color-coded status indicators
- **Summary statistics** showing ready-to-merge vs blocked PRs
- **Fast async** HTTP requests for quick analysis

## Installation

```bash
# Clone the repository
git clone https://github.com/rnetser/gh-pr-analyzer.git
cd gh-pr-analyzer

# Install with uv
uv sync
```

## Configuration

The tool requires a GitHub personal access token to authenticate with the GitHub API.

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
# Set your GitHub token
export GITHUB_TOKEN="your_token_here"

# Analyze your own PRs
uv run gh-pr-analyzer

# Analyze another user's PRs
uv run gh-pr-analyzer username
```

## Example Output

```
                                    PR Analysis Results
┏━━━━━━━━━━━━━━━━━━━┳━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Repository        ┃ PR #┃ Title                  ┃ Merge Blockers                ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ user/awesome-app  │ 123 │ Add dark mode toggle   │ ✓ Ready to merge              │
│ user/backend-api  │ 456 │ Fix authentication bug │ ✗ FAILING_CHECK:              │
│                   │     │                        │   CI Build (exit 1)           │
│                   │     │                        │   Last 5 lines:               │
│                   │     │                        │   Error: tests failed         │
│                   │     │                        │   FAILED test_auth.py::...    │
│ user/docs-site    │ 789 │ Update installation    │ ⚠ CHANGES_REQUESTED:          │
│                   │     │                        │   Reviewers: alice, bob       │
│ user/frontend     │ 234 │ Refactor components    │ ⏳ PENDING_CHECKS:            │
│                   │     │                        │   Tests (in_progress)         │
└───────────────────┴─────┴────────────────────────┴───────────────────────────────┘

Summary:
  ✓ Ready to merge: 1
  ✗ Blocked: 3
  Total PRs: 4
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
