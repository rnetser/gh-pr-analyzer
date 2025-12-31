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
