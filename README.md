# Option Analyzer

[![CI](https://github.com/<owner>/option_analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/<owner>/option_analyzer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

A Python toolkit for options pricing, strategy analysis, and risk assessment.

---

## Features

- **Options Pricing** — Black-Scholes, Binomial Tree, and Monte Carlo models
- **Greeks Calculation** — Delta, Gamma, Theta, Vega, Rho
- **Strategy Builder** — Construct and evaluate multi-leg option strategies
- **P&L Visualization** — Payoff diagrams and profit/loss projections
- **Risk Metrics** — VaR, max loss, breakeven analysis
- **Market Data Integration** — Plug into live or historical data feeds

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip or uv package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/<owner>/option_analyzer.git
cd option_analyzer

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -e ".[dev]"
```

### Usage

```python
from option_analyzer import Option, Strategy

# Price a European call option
call = Option(
    strike=100,
    expiry="2026-06-19",
    option_type="call",
    underlying_price=105,
    risk_free_rate=0.05,
    volatility=0.20,
)

print(call.price())   # Black-Scholes price
print(call.greeks())  # Delta, Gamma, Theta, Vega, Rho
```

## Project Structure

```
option_analyzer/
├── .github/              # GitHub templates & workflows
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/
│   └── PULL_REQUEST_TEMPLATE.md
├── src/
│   └── option_analyzer/  # Main package source
├── tests/                # Test suite
├── docs/                 # Documentation
├── pyproject.toml        # Project metadata & dependencies
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Development

```bash
# Run tests
pytest

# Run linter
ruff check .

# Run formatter
ruff format .

# Run type checker
mypy src/
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to get started.

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Security

To report a vulnerability, please see [SECURITY.md](SECURITY.md).
