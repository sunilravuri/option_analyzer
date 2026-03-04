# Contributing to Option Analyzer

Thank you for considering a contribution! This document explains how to get
involved and the standards we follow.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Commit Messages](#commit-messages)
5. [Pull Requests](#pull-requests)
6. [Reporting Issues](#reporting-issues)

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
By participating, you agree to uphold a welcoming, inclusive environment.

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/option_analyzer.git
   cd option_analyzer
   ```
3. **Create a virtual environment** and install dev dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   .venv\Scripts\activate      # Windows
   pip install -e ".[dev]"
   ```
4. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

| Tool   | Command              | Purpose            |
| ------ | -------------------- | ------------------ |
| pytest | `pytest`             | Run test suite     |
| ruff   | `ruff check .`       | Lint source code   |
| ruff   | `ruff format .`      | Format source code |
| mypy   | `mypy src/`          | Type checking      |

- Write tests for every new feature or bug fix.
- Ensure all checks pass before pushing.

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <short summary>

<optional body>

<optional footer>
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `ci`, `chore`

Examples:
- `feat(greeks): add charm (delta decay) calculation`
- `fix(pricing): correct dividend handling in Black-Scholes`
- `docs(readme): update installation instructions`

## Pull Requests

1. Keep PRs focused — one feature or fix per PR.
2. Fill out the [PR template](.github/PULL_REQUEST_TEMPLATE.md).
3. Link the related issue (e.g., `Closes #42`).
4. Ensure CI passes before requesting review.
5. Be responsive to feedback and iterate quickly.

## Reporting Issues

- Use the appropriate [issue template](.github/ISSUE_TEMPLATE/).
- Include steps to reproduce, expected vs. actual behavior, and environment details.
- Attach logs or screenshots when relevant.

---

Thank you for helping improve Option Analyzer!
