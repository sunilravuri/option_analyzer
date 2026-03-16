# ⚡ GLD LEAP Option Agent

[![GLD Agent](https://github.com/sunilravuri/option_analyzer/actions/workflows/gld_agent.yml/badge.svg)](https://github.com/sunilravuri/option_analyzer/actions/workflows/gld_agent.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An agentic trading system that runs a **7-prompt analysis framework** using Claude AI with live web search to analyze GLD (Gold ETF) LEAP options and deliver concise recommendations via **Telegram** — scheduled automatically through **cron-job.org → GitHub Actions**.

---

## System Architecture

```
cron-job.org (external scheduler)
  ↓ POST to GitHub API (workflow_dispatch)
  ↓ run_type=full (8:30 AM CST) or run_type=intraday (hourly)

GitHub Actions
  ↓ python agent.py full | intraday

7-Prompt Analysis Framework
  Prompt 1 (Haiku)  → IV & Options Chain Analysis    [full only]
  Prompt 2 (Haiku)  → IV Entry Timing Gate            [full only]
  Prompt 3 (Sonnet) → News Sentiment                  [always]
  Prompt 4 (Haiku)  → Event Risk Calendar             [full only]
  Prompt 5 (Sonnet) → ETF Fundamental Scorecard       [full only]
  Prompt 6 (Haiku)  → Strike & Expiry Optimizer       [full only]
  Prompt 7 (Sonnet) → Master Synthesis                [always]
  ↓
yfinance → Live GLD option chain (real bid/ask prices)
  ↓
Telegram Bot → concise recommendation to your channel
```

| Detail | Value |
|--------|-------|
| 📅 Schedule | Mon–Fri, full at 8:30 AM CST + hourly intraday 9:30 AM–2:30 PM CST |
| 💬 Delivery | Telegram (plain text) |
| ☁️ Host | GitHub Actions (triggered via cron-job.org) |
| 💰 API Cost | ~$3.10/month |

---

## Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| GitHub Actions | **FREE** | 2,000 free min/month |
| Claude API | **~$3.10/mo** | Haiku for light prompts, Sonnet for synthesis + prompt caching |
| Telegram Bot | **FREE** | BotFather creates a free bot instantly |
| cron-job.org | **FREE** | External scheduler for reliable triggering |

---

## Project Structure

```
option_analyzer/
├── agent.py               # 7-prompt analysis agent with model routing & prompt caching
├── telegram_sender.py     # Telegram bot sender (plain text)
├── requirements.txt       # Dependencies
├── CLAUDE.md              # Implementation spec for Claude Code
├── .env.example           # Template for environment variables
├── .github/
│   └── workflows/
│       └── gld_agent.yml  # workflow_dispatch only (triggered by cron-job.org)
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com)
- Telegram Bot Token & Chat ID (see [Telegram Setup](#telegram-bot-setup))

### Installation

```bash
git clone https://github.com/sunilravuri/option_analyzer.git
cd option_analyzer

python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### Configure Environment

```bash
cp .env.example .env
# Edit .env:
#   ANTHROPIC_API_KEY=sk-ant-...
#   TELEGRAM_BOT_TOKEN=...
#   TELEGRAM_CHAT_ID=...
```

### Run Locally

```bash
# Full run (all 7 prompts — use at market open)
python agent.py full

# Intraday run (news + synthesis only)
python agent.py intraday
```

---

## Deploy to GitHub Actions

1. Push this repo to GitHub.
2. Go to **Settings → Secrets → Actions** and add:

   | Secret | Where to Get It |
   |--------|----------------|
   | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) → API Keys |
   | `TELEGRAM_BOT_TOKEN` | Telegram → @BotFather → `/newbot` |
   | `TELEGRAM_CHAT_ID` | `api.telegram.org/bot<TOKEN>/getUpdates` → find `chat.id` |

3. To test: **Actions → GLD LEAP Agent → Run workflow** → set `run_type=full`.

---

## cron-job.org Setup

Create two jobs at [console.cron-job.org](https://console.cron-job.org):

**Job 1 — Full run (market open)**

| Field | Value |
|-------|-------|
| Schedule | `30 14 * * 1-5` (8:30 AM CST = 14:30 UTC, Mon–Fri) |
| URL | `https://api.github.com/repos/sunilravuri/option_analyzer/actions/workflows/gld_agent.yml/dispatches` |
| Method | `POST` |
| Header | `Authorization: Bearer YOUR_GITHUB_PAT` |
| Header | `Accept: application/vnd.github+json` |
| Body | `{"ref":"main","inputs":{"run_type":"full"}}` |

**Job 2 — Intraday runs (hourly)**

| Field | Value |
|-------|-------|
| Schedule | `30 15-20 * * 1-5` (9:30 AM–2:30 PM CST, Mon–Fri) |
| URL | same as above |
| Method | `POST` |
| Headers | same as above |
| Body | `{"ref":"main","inputs":{"run_type":"intraday"}}` |

> The GitHub PAT needs `repo` or `actions:write` scope.

---

## Telegram Bot Setup

1. Open Telegram → search **@BotFather** → tap "Start"
2. Send `/newbot`, give it a name and username
3. Copy the **BOT_TOKEN** BotFather gives you
4. Send your bot any message (e.g. "hello")
5. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
6. Find `"chat":{"id": 123456789}` — that number is your **CHAT_ID**

---

## Sample Output

```
📊 GLD LEAP — 2026-03-16 11:50 CST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 GLD: $458.46 | Tech: NEUTRAL | Macro: FAVORABLE | IV: FAIR

✅ GO RECOMMENDATION
Strike: $460 | Expiry: Mar 2027 | Ask: $57.80/share → $5,780/contract
Contracts: 1 | Break-even: $517.80 | Delta: ~0.52

📌 Why: Highest volume, ATM delta, 13-month runway, dollar weakness tailwind
⚡ Conviction: MEDIUM (6/10) — FOMC overhang resolved post March 18-19
🎯 Target: $520 | 🛑 Stop: GLD < $435
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Educational only. Not financial advice.
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT — see [LICENSE](LICENSE).

---

> ⚠️ **Disclaimer:** This agent is for educational and automation purposes only. The GLD LEAP option analysis generated does not constitute financial advice. Always consult a licensed financial advisor before making investment decisions. Options trading involves significant risk of loss.
