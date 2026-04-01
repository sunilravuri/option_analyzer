# ⚡ GLD LEAP Option Agent

[![GLD Agent](https://github.com/sunilravuri/option_analyzer/actions/workflows/gld_agent.yml/badge.svg)](https://github.com/sunilravuri/option_analyzer/actions/workflows/gld_agent.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An agentic trading system that runs a **7-prompt analysis framework** using Claude AI with live web search, real-time option chain data (yfinance), and TradingView technical analysis to evaluate GLD (Gold ETF) LEAP options and deliver concise recommendations via **Telegram** — scheduled automatically through **cron-job.org → GitHub Actions**.

---

## System Architecture

```
cron-job.org (external scheduler)
  ↓ POST to GitHub API (workflow_dispatch)
  ↓ run_type=full (8:30 AM CST) or run_type=intraday (hourly)

GitHub Actions
  ↓ python agent.py full | intraday

Data Sources (run in parallel before AI analysis)
  ├── yfinance        → Live GLD option chain (real bid/ask prices, 15-min delayed)
  └── TradingView     → RSI, MACD, SMA50/200, technical bias (authenticated)

7-Prompt Analysis Framework (Claude AI)
  Prompt 1 (Haiku)  → IV & Options Chain Analysis    [full only]
  Prompt 2 (Haiku)  → IV Entry Timing Gate            [full only]
  Prompt 3 (Sonnet) → News Sentiment                  [always]
  Prompt 4 (Haiku)  → Event Risk Calendar             [full only]
  Prompt 5 (Sonnet) → ETF Fundamental Scorecard       [full only]
  Prompt 6 (Haiku)  → Strike & Expiry Optimizer       [full only]
  Prompt 7 (Sonnet) → Master Synthesis                [always]
  ↓
Telegram Bot → concise recommendation to your group/channel
```

| Detail | Value |
|--------|-------|
| 📅 Schedule | Mon–Fri, full at 8:30 AM CST + hourly intraday 9:30 AM–2:30 PM CST |
| 💬 Delivery | Telegram (plain text, group or channel) |
| ☁️ Host | GitHub Actions (triggered via cron-job.org) |
| 💰 API Cost | ~$3–5/month |

---

## How the Analysis Works — Step by Step

Each full run executes 7 sequential AI prompts, each building on the previous. Here's exactly what happens:

### Step 1 — Fetch Live Market Data (no AI)

Before any AI call, the agent collects real data:

- **yfinance**: Fetches the GLD option chain for all expirations 12+ months out. For each expiry, it pulls strikes in the $380–$470 range with bid, ask, IV, and volume. Marks which strikes are within the $6,500/contract budget.
- **TradingView** (authenticated): Fetches 100 daily candles for GLD. Computes RSI(14), MACD, SMA50, SMA200, and a technical bias (BULLISH/NEUTRAL/BEARISH) locally in Python — no AI needed.

---

### Prompt 1 — IV & Options Chain Analysis (Haiku, no web search)

**Input:** The raw yfinance option chain data  
**Task:** Analyze the chain without any web search since real data is already provided.

- Calculates IV Rank (IVR) and IV Percentile — cheap (<30) vs expensive (>70)
- Compares IV vs 30-day Historical Volatility to assess if options are over/underpriced
- Analyzes IV skew across strikes (ATM vs OTM)
- Estimates Delta, Gamma, Theta, Vega for 3 candidate strikes
- Identifies institutional positioning from Open Interest and Volume
- Outputs top 3 strike/expiry combos ranked by cost-efficiency (ITM delta ~0.70–0.80, ATM ~0.50)

---

### Prompt 2 — IV Entry Timing Gate (Haiku, web search)

**Input:** Web search for current GLD IV metrics  
**Task:** Determine if now is a good time to enter a LEAP position.

- Retrieves current IV, 52-week high/low, IV Rank, IV Percentile, 30-day HV
- Applies a simple gate: IVR < 30 = BUY NOW, 30–50 = CAUTION, >50 = WAIT
- Calculates IV/HV ratio (>1.2 means options are expensive)
- Estimates the implied ±1 standard deviation move by LEAP expiration
- Outputs a single verdict: ✅ BUY NOW / ⚠️ WAIT / ❌ AVOID

---

### Prompt 3 — News Sentiment (Sonnet, web search) — runs every run

**Input:** Web search for GLD/gold news from the past 5 trading days  
**Task:** Score the macro news environment for a 12–24 month LEAP thesis.

- Searches for: Fed policy signals, DXY moves, real yields (TIPS), central bank gold demand, geopolitical events, ETF flow data
- For each story: sentiment (Bullish/Bearish/Neutral), impact window, and LEAP relevance
- Outputs a net sentiment score from −5 (very bearish) to +5 (very bullish)
- Identifies the #1 macro risk that could invalidate the thesis and the #1 upside catalyst

---

### Prompt 4 — Event Risk Calendar (Haiku, web search)

**Input:** Web search for upcoming macro events  
**Task:** Map out the event landscape over the next 3–18 months.

- Searches for: FOMC meeting dates, CPI/PCE releases, DXY key levels, central bank reports, geopolitical risk events
- For each event: estimated IV impact (High/Medium/Low), directional bias for GLD, and LEAP implication (enter before / after / avoid)

---

### Prompt 5 — ETF Fundamental Scorecard (Sonnet, no web search)

**Input:** TradingView technical data (RSI, MACD, SMAs, price) fetched in Step 1  
**Task:** Score GLD as a LEAP candidate across 4 dimensions.

- **Structure:** AUM, daily options volume, bid/ask spread quality, expense ratio
- **Macro:** Assesses current macro regime (risk-off/on), DXY trend and correlation, real yield direction, Fed policy stance
- **Technical:** Uses live TradingView data — price vs SMA50/200, RSI(14), MACD signal, trend, key support/resistance
- **LEAP Suitability Score:** Rates GLD 1–10 weighted equally across IV environment (25%), trend (25%), macro (25%), and liquidity (25%)

---

### Prompt 6 — Strike & Expiry Optimizer (Haiku, no web search)

**Input:** The raw yfinance option chain data  
**Task:** Find the best specific trade within the $6,500 budget using real ask prices.

- Uses only real ask prices from the chain (never estimates premiums)
- Models 3 scenarios: ITM (delta ~0.80), ATM (delta ~0.50), OTM (delta ~0.30)
- For each: cost per contract (ask × 100), breakeven at expiry (strike + ask), probability of profit, max contracts within $6,500
- Recommends the best strike for risk-adjusted return
- Provides a roll strategy: when/how to roll if the position moves 20% against

---

### Prompt 7 — Master Synthesis (Sonnet, no web search) — runs every run

**Input:** All outputs from Prompts 1–6  
**Task:** Synthesize everything into a single Telegram-ready recommendation.

- Weighs all 6 analysis components against the constraints: $6,500 budget, 2–3x target return, 12–18 month horizon, 50% max loss tolerance
- Enforces pricing rules: only recommends strikes where ask × 100 ≤ $6,500
- If no strike fits the budget, outputs a WAIT message with the cheapest available option and the price level to watch
- Delivers a fixed-format output directly usable as a Telegram message

---

### Intraday Runs (news + synthesis only)

For hourly intraday runs, only **Prompt 3** (news) and **Prompt 7** (synthesis) execute. The synthesis prompt is aware it's an intraday run and bases the recommendation primarily on news and macro context, clearly noting it's an intraday update rather than a full analysis.

---

## Cost Optimization

| Technique | Saving |
|-----------|--------|
| Model routing: Haiku for P1,P2,P4,P6 | ~70% cheaper than Sonnet for those calls |
| No web search on P1, P5, P6 | Eliminates ~3 unnecessary search calls |
| `max_uses=2` per search (was 5) | Halves search token consumption |
| Per-prompt `max_tokens` (350–900) | Cuts wasted output budget vs 2048–3000 default |
| Intraday = 2 prompts only | ~$0.01/run vs ~$0.16/full run |

**Estimated monthly cost:** ~$3–5 for 22 trading days (1 full + 5 intraday runs/day)

To verify caching is working, check logs for `cache_read_input_tokens > 0`.

---

## Project Structure

```
option_analyzer/
├── agent.py               # 7-prompt analysis agent with model routing & prompt caching
├── tv_analysis.py         # TradingView data fetcher (RSI, MACD, SMA — no AI)
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
- TradingView account (free tier works)

### Installation

```bash
git clone https://github.com/sunilravuri/option_analyzer.git
cd option_analyzer

python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### Configure Environment

```bash
cp .env.example .env
# Edit .env:
#   ANTHROPIC_API_KEY=sk-ant-...
#   TELEGRAM_BOT_TOKEN=...
#   TELEGRAM_CHAT_ID=...         # negative number for group/channel
#   TRADINGVIEW_USERNAME=...
#   TRADINGVIEW_PASSWORD=...
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
   | `TELEGRAM_CHAT_ID` | Use negative ID for groups/channels (e.g. `-1003358222047`) |
   | `TRADINGVIEW_USERNAME` | Your TradingView login email |
   | `TRADINGVIEW_PASSWORD` | Your TradingView password |

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
4. **For a group:** Add the bot to your group, then get the group's negative chat ID
5. **For a channel:** Add the bot as admin, use the channel's `-100XXXXXXXXXX` ID
6. To find the chat ID: send a message in the group/channel, then visit `https://api.telegram.org/bot<TOKEN>/getUpdates` and look for `"chat":{"id": -100XXXXXXXXXX}`

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

## License

MIT — see [LICENSE](LICENSE).

---

> ⚠️ **Disclaimer:** This agent is for educational and automation purposes only. The GLD LEAP option analysis generated does not constitute financial advice. Always consult a licensed financial advisor before making investment decisions. Options trading involves significant risk of loss.
