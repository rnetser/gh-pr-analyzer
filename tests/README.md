# Test Suite for gh-pr-analyzer

This directory contains comprehensive unit tests for the gh-pr-analyzer project.

## Test Structure

```
tests/
├── __init__.py              # Package marker
├── conftest.py              # Shared fixtures and configuration
├── test_analyzer.py         # Tests for analyzer.py (merge blocker detection)
├── test_cli.py              # Tests for cli.py (CLI interface)
└── test_github_client.py    # Tests for github_client.py (GitHub API client)
```

## Test Coverage

- **Total Tests**: 94
- **Code Coverage**: 97%
- **Lines of Test Code**: ~1,693

### Coverage by Module

| Module | Statements | Missing | Coverage |
|--------|-----------|---------|----------|
| `__init__.py` | 1 | 0 | 100% |
| `analyzer.py` | 49 | 0 | 100% |
| `github_client.py` | 31 | 0 | 100% |
| `cli.py` | 97 | 3 | 97% |
| `__main__.py` | 3 | 3 | 0% |

**Note**: `__main__.py` is not tested as it's just an entry point wrapper. The 3 missing lines in `cli.py` are the main entry point and `if __name__ == "__main__"` block.

## Test Categories

### test_github_client.py (31 tests)

Tests for GitHub API client functionality:

- **Initialization Tests (4)**: Token handling, environment variables, error cases
- **HTTP Request Tests (7)**: Successful requests, error handling, timeouts, rate limits
- **API Method Tests (17)**: All GitHub API methods (authenticated user, PRs, reviews, checks)
- **Edge Cases (3)**: Large PR numbers, special characters, timeout configuration

### test_analyzer.py (35 tests)

Tests for PR analysis and merge blocker detection:

- **Data Classes (6)**: MergeBlocker and PRAnalysis attributes and behavior
- **Clean PRs (3)**: PRs with no blockers
- **Merge Conflicts (2)**: Dirty state and mergeable=False scenarios
- **Failing Checks (4)**: Single/multiple failures, output parsing
- **Pending Checks (3)**: Running checks, many checks, single check
- **Reviews (3)**: Changes requested, mixed reviews, duplicate reviewers
- **Approvals (3)**: Private repo requirements, approval handling
- **Branch Protection (2)**: Blocked state, interaction with other blockers
- **Multiple Blockers (2)**: Complex scenarios with multiple issues
- **Edge Cases (7)**: Unknown states, missing data, various check conclusions

### test_cli.py (28 tests)

Tests for CLI interface:

- **URL Parsing (8)**: Various GitHub URL formats
- **Display Results (11)**: Table formatting, blocker icons, summary counts
- **Async Analysis (9)**: User PR fetching, error handling, data integration

## Running Tests

### Run all tests
```bash
uv run pytest -v
```

### Run specific test file
```bash
uv run pytest tests/test_analyzer.py -v
```

### Run with coverage report
```bash
uv run pytest --cov=src/gh_pr_analyzer --cov-report=html
```

### Run specific test class
```bash
uv run pytest tests/test_analyzer.py::TestAnalyzePRFailingChecks -v
```

### Run specific test
```bash
uv run pytest tests/test_github_client.py::TestGitHubClientInit::test_init_with_token -v
```

## Test Dependencies

Tests use the following frameworks and libraries:

- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **pytest-httpx**: HTTP request mocking
- **pytest-cov**: Code coverage reporting

Install test dependencies with:
```bash
uv add --dev pytest pytest-asyncio pytest-httpx pytest-cov
```

## Fixtures

Shared fixtures are defined in `conftest.py`:

- `mock_token`: Mock GitHub token
- `mock_pr_data`: Clean PR data
- `mock_pr_data_with_conflicts`: PR with merge conflicts
- `mock_pr_data_blocked`: Blocked PR data
- `mock_reviews_approved`: Approved reviews
- `mock_reviews_changes_requested`: Reviews requesting changes
- `mock_reviews_mixed`: Mixed review states
- `mock_check_runs_passing`: Passing CI checks
- `mock_check_runs_failing`: Failing CI checks
- `mock_check_runs_pending`: Pending CI checks
- `mock_check_runs_mixed`: Mixed check states
- `mock_user_data`: User information
- `mock_user_prs`: List of user PRs

## Test Patterns

### Mocking HTTP Requests

```python
@pytest.mark.asyncio
async def test_example(mock_token, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.github.com/user",
        json={"login": "testuser"},
    )
    client = GitHubClient(token=mock_token)
    result = await client.get_authenticated_user()
    assert result["login"] == "testuser"
```

### Testing Error Cases

```python
@pytest.mark.asyncio
async def test_error(mock_token, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.github.com/user",
        status_code=404,
    )
    client = GitHubClient(token=mock_token)
    with pytest.raises(httpx.HTTPStatusError):
        await client.get_authenticated_user()
```

### Parametrized Tests

While not currently used, tests can be parametrized for better coverage:

```python
@pytest.mark.parametrize("state,expected", [
    ("clean", True),
    ("dirty", False),
    ("blocked", False),
])
def test_mergeable_state(state, expected):
    # Test implementation
    pass
```

## Edge Cases Covered

- Empty responses from API
- Network errors and timeouts
- Rate limiting
- Invalid tokens
- Missing data fields
- Very long error messages
- Multiple simultaneous blockers
- Duplicate reviewers
- Special characters in usernames/repos
- Large PR numbers
- Unknown mergeable states

## Continuous Integration

Tests are configured to run in CI/CD pipelines with:

- Automatic async test detection
- Code coverage reporting (HTML and terminal)
- Strict marker enforcement
- Short traceback format for cleaner output

See `pytest.ini` for full configuration.
