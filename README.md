# ⚡ GLD LEAP Option Agent

[![GLD Agent](https://github.com/<owner>/option_analyzer/actions/workflows/gld_agent.yml/badge.svg)](https://github.com/<owner>/option_analyzer/actions/workflows/gld_agent.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An agentic trading system that uses **Claude claude-sonnet-4-6** with live web search to
analyze GLD (Gold ETF) LEAP options and deliver structured recommendations
via **Telegram** — scheduled automatically through **GitHub Actions**.

---

## System Architecture

```
GitHub Actions (Free Scheduler)
  ↓ triggers every 15 min, Mon–Fri only
Claude Code Agent (claude-sonnet-4-6 + web_search)
  ↓ runs agentic loop with tools
  Tool 1: web_search → Live GLD price
  Tool 2: web_search → RSI, MACD, SMA, Bollinger Bands, ATR
  Tool 3: web_search → DXY, TIPS yield, Fed policy, CPI/PCE
  Tool 4: web_search → Gold news & central bank demand
  ↓ synthesizes into LEAP recommendation
Telegram Bot
  ↓ delivers formatted analysis to your channel
  YOU receive the report ✅
```

| Detail | Value |
|--------|-------|
| 📅 Schedule | Mon–Fri 8:30 AM – 3:00 PM CST |
| ⏱ Frequency | Every 15 minutes |
| 💬 Delivery | Telegram |
| ☁️ Host | GitHub Actions |
| 💰 Cost | ~$8–15/month |

## Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| GitHub Actions | **FREE** | 2,000 free min/month — uses ~130 min/month |
| Claude API | **~$8–15/mo** | 26 runs/day × 21 trading days, ~1,000 tokens/run |
| Telegram Bot | **FREE** | BotFather creates a free bot instantly |

## Project Structure

```
option_analyzer/
├── agent.py               # Core Claude AI agent with web_search tool
├── telegram_sender.py     # Telegram bot message formatter & sender
├── scheduler.py           # Local test scheduler (every 15 min)
├── requirements.txt       # Pinned dependencies
├── .env.example           # Template for environment variables
├── .gitignore
├── .github/
│   ├── workflows/
│   │   └── gld_agent.yml  # GitHub Actions cron schedule
│   ├── ISSUE_TEMPLATE/    # Bug report & feature request forms
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
└── SECURITY.md
```

## Quick Start

### Prerequisites

- Python 3.10+
- [Anthropic API key](https://console.anthropic.com)
- Telegram Bot Token & Chat ID (see [Telegram Setup](#telegram-bot-setup))

### Installation

```bash
git clone https://github.com/<owner>/option_analyzer.git
cd option_analyzer

python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### Configure Secrets

```bash
cp .env.example .env
# Edit .env with your actual keys:
#   ANTHROPIC_API_KEY=sk-ant-...
#   TELEGRAM_BOT_TOKEN=...
#   TELEGRAM_CHAT_ID=...
```

### Test Telegram Connection

```bash
python telegram_sender.py
```

### Run a Local Analysis

```bash
python -c "
from agent import run_gld_analysis
from telegram_sender import send_to_telegram

analysis = run_gld_analysis()
send_to_telegram(analysis)
print('Done.')
"
```

### Local Scheduler (every 15 min)

```bash
python scheduler.py
```

## Deploy to GitHub Actions

1. Push this repo to GitHub.
2. Go to **Settings → Secrets → Actions** and add:

   | Secret | Where to Get It |
   |--------|----------------|
   | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) → API Keys |
   | `TELEGRAM_BOT_TOKEN` | Telegram → @BotFather → `/newbot` → copy token |
   | `TELEGRAM_CHAT_ID` | Message your bot, then visit `api.telegram.org/bot<TOKEN>/getUpdates` |

3. To test immediately: **Actions → GLD LEAP Agent → Run workflow**.
4. The cron schedule will handle the rest automatically.

## Telegram Bot Setup

1. Open Telegram → search **@BotFather** → tap "Start"
2. Send `/newbot`, give it a name (e.g. "GLD LEAP Analyst") and username (e.g. `gld_leap_bot`)
3. Copy the **BOT_TOKEN** BotFather gives you
4. Search for your bot in Telegram and send it any message (e.g. "hello")
5. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
6. Find `"chat":{"id": 123456789}` — that number is your **CHAT_ID**

## Sample Output

```
📊 GLD LEAP ANALYSIS — 2026-03-04 10:30 CST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 GLD PRICE: $245.67

📈 TECHNICAL BIAS: BULLISH
• RSI(14): 58.3 — Neutral-to-bullish
• MACD: +1.2 — Bullish crossover
• 50 SMA: $240.15 | 200 SMA: $228.90
• Bollinger Bands: Trading near upper band
• ATR(14): $3.45

🌍 MACRO BIAS: FAVORABLE
• DXY: 103.2 — Weakening trend
• Real Yield (10Y TIPS): 1.85%
• Fed Stance: Holding, dovish lean
• Inflation (CPI/PCE): CPI 3.1% YoY
• Gold News: Central banks continue accumulation

✅ LEAP RECOMMENDATION
• Type: GLD Call Option
• Strike: $250
• Expiry: June 2027
• Est. Premium: $18.50 per contract
• Max Cost: $1,850 (within $6,500 budget)
• Delta: ~0.45
• Break-even at Expiry: $268.50
• GLD Entry Zone: $243–$248

🎯 PRICE TARGET (12–18 months): $280
⚠️ STOP LOSS TRIGGER: GLD closes below $225
📉 RISK: Premium loss if gold stagnates below strike
📈 REWARD: 3:1 risk/reward with macro tailwinds
⚡ CONVICTION: HIGH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Educational purposes only. Not financial advice.
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT — see [LICENSE](LICENSE).

---

> ⚠️ **Disclaimer:** This agent is for educational and automation purposes only. The GLD LEAP option analysis generated does not constitute financial advice. Always consult a licensed financial advisor before making investment decisions. Options trading involves significant risk of loss.
