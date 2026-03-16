# GLD LEAP Agent — Claude Code Instructions

## Context

This is a GLD LEAP options analysis agent that:
- Runs on GitHub Actions (Mon–Fri, every 15 min, 8:30 AM – 3:00 PM CST)
- Uses the Anthropic API (`claude-sonnet-4-6`) with web_search tool
- Delivers structured recommendations to a Telegram channel
- Files: `agent.py`, `telegram_sender.py`, `scheduler.py`, `.github/workflows/gld_agent.yml`

---

## Task Overview

Implement 4 upgrades to reduce API costs and improve analysis quality:

1. **Model routing** — use Haiku for lightweight prompts, Sonnet for synthesis
2. **Prompt caching** — cache static GLD context to save ~90% on repeated tokens
3. **Run-type scheduling** — full 7-prompt suite at open, prompts 3+7 only intraday
4. **Richer prompts** — integrate the 7-prompt analysis framework below

---

## Task 1 — Model Routing in `agent.py`

### What to do
Add two model constants at the top of `agent.py`, after the imports:

```python
# Model routing — cost optimization
MODEL_HEAVY = "claude-sonnet-4-6"        # News sentiment, fundamentals, master synthesis
MODEL_LIGHT = "claude-haiku-4-5-20251001" # IV analysis, event calendar, strike optimizer
```

Identify every `client.messages.create()` call in `agent.py`. For each one, determine
which prompt it serves and assign the model accordingly:

| Prompt purpose                          | Model to use  |
|-----------------------------------------|---------------|
| IV / Greeks analysis (structured math)  | MODEL_LIGHT   |
| IV entry timing (yes/no gate)           | MODEL_LIGHT   |
| News sentiment scoring                  | MODEL_HEAVY   |
| Event risk calendar                     | MODEL_LIGHT   |
| ETF fundamental scorecard               | MODEL_HEAVY   |
| Strike & expiry optimization            | MODEL_LIGHT   |
| Master synthesis / final recommendation | MODEL_HEAVY   |

Replace any hardcoded model string (e.g. `"claude-sonnet-4-6"`) with the
appropriate constant.

---

## Task 2 — Prompt Caching in `agent.py`

### What to do
The GLD context block (ETF fundamentals, static system prompt describing GLD,
the agent's role, budget constraints) does not change between runs. Cache it.

Find the `system` parameter in any `client.messages.create()` call that contains
the static GLD description or agent role. Convert it from a plain string to a list
with `cache_control`:

**Before:**
```python
response = client.messages.create(
    model=MODEL_HEAVY,
    max_tokens=1000,
    system="You are a GLD LEAP options analyst...",
    messages=[...]
)
```

**After:**
```python
response = client.messages.create(
    model=MODEL_HEAVY,
    max_tokens=1000,
    system=[
        {
            "type": "text",
            "text": "You are a GLD LEAP options analyst...",
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[...]
)
```

Apply this pattern to every API call that has a static system prompt.
Only the static/unchanging parts should be in the cached block.
Dynamic data (live prices, news, etc.) must remain in the `messages` array.

Also add the beta header required for prompt caching:
```python
import anthropic

client = anthropic.Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    default_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
)
```

---

## Task 3 — Run-Type Scheduling

### 3a — Update `agent.py` to accept a run type argument

Add this near the top of `agent.py`, after imports:

```python
import sys

# RUN_TYPE controls which prompts execute
# "full"     → all prompts (market open run at 8:30 AM CST)
# "intraday" → news + synthesis only (hourly runs)
RUN_TYPE = sys.argv[1] if len(sys.argv) > 1 else "full"
```

In the main analysis function, wrap the prompts in conditionals:

```python
def run_gld_analysis():
    results = {}

    # --- Always run (both full and intraday) ---
    results["news"] = run_news_sentiment_prompt()      # Prompt 3
    results["synthesis"] = run_master_synthesis_prompt(results)  # Prompt 7

    if RUN_TYPE == "full":
        # --- Market open only ---
        results["iv_chain"] = run_iv_chain_prompt()        # Prompt 1
        results["iv_timing"] = run_iv_timing_prompt()      # Prompt 2
        results["events"] = run_event_calendar_prompt()    # Prompt 4
        results["fundamentals"] = run_fundamentals_prompt() # Prompt 5
        results["strikes"] = run_strike_optimizer_prompt() # Prompt 6

    return results
```

Adjust the function names to match whatever functions actually exist in `agent.py`.
If the agent uses a single monolithic prompt rather than separate functions,
refactor it so prompts 3 and 7 can be called independently.

### 3b — Update `.github/workflows/gld_agent.yml`

Replace the existing single cron trigger with two separate jobs:

```yaml
name: GLD LEAP Agent

on:
  schedule:
    # Full run — market open (8:30 AM CST = 14:30 UTC), Mon–Fri
    - cron: '30 14 * * 1-5'
    # Intraday run — every hour 9:30–14:00 CST (15:30–20:00 UTC), Mon–Fri
    - cron: '30 15 * * 1-5'
    - cron: '30 16 * * 1-5'
    - cron: '30 17 * * 1-5'
    - cron: '30 18 * * 1-5'
    - cron: '30 19 * * 1-5'
  workflow_dispatch:
    inputs:
      run_type:
        description: 'Run type: full or intraday'
        required: false
        default: 'full'

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Determine run type
        id: run_type
        run: |
          # 8:30 AM CST = 14:30 UTC → full run
          HOUR=$(date -u +%H)
          MIN=$(date -u +%M)
          if [ "$HOUR" = "14" ] && [ "$MIN" = "30" ]; then
            echo "type=full" >> $GITHUB_OUTPUT
          else
            echo "type=intraday" >> $GITHUB_OUTPUT
          fi

      - name: Run GLD analysis
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python agent.py ${{ steps.run_type.outputs.type }}
```

---

## Task 4 — Upgrade the Analysis Prompts in `agent.py`

Replace or augment the existing prompts with the following 7-prompt framework.
Each prompt should be its own function for clean separation.

### Prompt 1 — IV & Options Chain Analysis (MODEL_LIGHT)
```
You are an expert options analyst. Search for the current GLD options chain
for LEAP expirations (12–24 months out).

Analyze:
1. IV Rank (IVR) and IV Percentile — is IV cheap (<30 IVR) or expensive (>70 IVR)?
2. IV vs Historical Volatility (30-day HV) ratio — are options over/underpriced?
3. Skew: compare IV across strikes (ATM vs OTM calls/puts)
4. Delta, Gamma, Theta, Vega for 3 candidate strikes
5. Open Interest and Volume — where is institutional positioning?
6. Identify top 3 strike/expiry combos for a long LEAP call (delta ~0.70–0.80 ITM,
   ~0.50 ATM), ranked by cost-efficiency

Output: table of top 3 candidates with strike, expiry, IV, delta, estimated cost,
and one-line reasoning. Plain text only, no markdown tables.
```

### Prompt 2 — IV Entry Timing Gate (MODEL_LIGHT)
```
Search for GLD's current implied volatility metrics:
- Current IV, 52-week IV High and Low, IV Rank, IV Percentile, HV 30-day

Then answer:
1. Is now favorable to BUY LEAPs? (IVR < 30 = YES, 30–50 = CAUTION, >50 = WAIT)
2. IV/HV ratio — are options fairly priced?
3. Implied ±1 standard deviation move by LEAP expiration
4. What IV level would be ideal entry?

Final output must be one of: ✅ BUY NOW / ⚠️ WAIT / ❌ AVOID
with a single sentence reason. Plain text only.
```

### Prompt 3 — News Sentiment (MODEL_HEAVY)
```
Search for the top GLD and gold market news from the past 5 trading days.
Include: Fed policy signals, DXY moves, real yields (TIPS), central bank gold
demand, geopolitical risk events, and any ETF flow data.

For each story:
1. Sentiment: Bullish / Bearish / Neutral for GLD
2. Impact window: <1 week / 1–4 weeks / 1–6 months
3. Relevance to a 12–24 month LEAP: High / Medium / Low

Then provide:
- Net sentiment score: −5 (very bearish) to +5 (very bullish)
- #1 macro risk that could invalidate a bullish LEAP thesis
- #1 catalyst that could accelerate a bullish move

Plain text only.
```

### Prompt 4 — Event Risk Calendar (MODEL_LIGHT)
```
Search for upcoming events over the next 3–18 months that could affect GLD:
1. FOMC meeting dates and rate decision expectations
2. CPI/PCE release dates
3. US dollar (DXY) key levels and catalysts
4. Central bank gold buying/selling reports
5. Geopolitical risk events (Middle East, Russia/Ukraine, Taiwan)

For each event:
- Estimated IV impact: High / Medium / Low spike expected
- Directional bias for GLD
- LEAP implication: enter before / after / avoid

Today's date: {today}. Plain text only.
```

### Prompt 5 — ETF Fundamental Scorecard (MODEL_HEAVY)
```
Analyze GLD as a LEAP candidate:

STRUCTURE:
- Current AUM, average daily options volume, typical bid/ask spread quality
- Expense ratio

MACRO FUNDAMENTALS:
- What macro regime benefits GLD most? Current regime assessment.
- DXY trend and correlation to GLD
- Real yield (10Y TIPS) direction and impact
- Fed policy stance

TECHNICAL SETUP (search for current data):
- GLD price vs 50-day and 200-day SMA
- RSI(14), MACD signal
- Current trend: consolidation / breakout / downtrend
- Key support and resistance levels relevant to LEAP strike selection

LEAP SUITABILITY SCORE:
Rate GLD 1–10 for LEAP buying today.
Scoring factors: IV environment (25%), trend (25%), macro (25%), liquidity (25%)

Plain text only.
```

### Prompt 6 — Strike & Expiry Optimizer (MODEL_LIGHT)
```
I want to buy a GLD LEAP call with these constraints:
- Max budget: $6,500 total (can buy multiple contracts)
- Holding period: 12–18 months
- Bullish price target: search for analyst consensus GLD target
- Risk tolerance: willing to lose up to 50% of premium

Search for current GLD price and use it to model 3 scenarios:
1. ITM strike (delta ~0.80)
2. ATM strike (delta ~0.50)
3. OTM strike (delta ~0.30)

For each scenario estimate:
- Approximate cost per contract
- Breakeven price at expiry
- Estimated probability of profit
- Theta decay per week
- Max contracts within $6,500 budget

Recommend the best strike for risk-adjusted return.
Also suggest a roll strategy: when/how to roll if the position moves
against me by 20%.

Plain text only.
```

### Prompt 7 — Master Synthesis (MODEL_HEAVY)
```
You are a quantitative options strategist for GLD (SPDR Gold Shares ETF).

Synthesize the following analysis results and deliver a final LEAP recommendation:

<iv_analysis>{iv_chain_result}</iv_analysis>
<iv_timing>{iv_timing_result}</iv_timing>
<news_sentiment>{news_result}</news_sentiment>
<event_calendar>{events_result}</event_calendar>
<fundamentals>{fundamentals_result}</fundamentals>
<strike_analysis>{strikes_result}</strike_analysis>

MY CONSTRAINTS:
- Budget: $6,500 max
- Target return: 2–3x
- Time horizon: 12–18 months
- Max loss tolerance: 50% of premium

Deliver your final output in this EXACT format for Telegram:

📊 GLD LEAP ANALYSIS — {datetime}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 GLD PRICE: $XXX.XX

📈 TECHNICAL BIAS: [BULLISH/NEUTRAL/BEARISH]
• RSI(14): XX — [comment]
• MACD: [signal]
• 50 SMA: $XXX | 200 SMA: $XXX
• Trend: [one line]

🌍 MACRO BIAS: [FAVORABLE/NEUTRAL/UNFAVORABLE]
• DXY: XXX — [trend]
• Real Yield (10Y TIPS): X.XX%
• Fed Stance: [one line]
• Net News Score: X/5

📉 IV ENVIRONMENT: [CHEAP/FAIR/EXPENSIVE]
• IV Rank: XX% — [buy signal or caution]
• IV/HV Ratio: X.X

[✅ GO / ⚠️ WAIT / ❌ NO-GO] LEAP RECOMMENDATION
• Type: GLD Call Option
• Strike: $XXX
• Expiry: [Month Year]
• Est. Premium: $XX.XX per contract
• Contracts: X (within $6,500 budget)
• Delta: ~X.XX
• Break-even: $XXX.XX
• Entry Zone: $XXX–$XXX

🎯 PRICE TARGET (12–18 months): $XXX
⚠️ STOP LOSS TRIGGER: GLD closes below $XXX
📉 RISK: [one line]
📈 REWARD: [one line]
⚡ CONVICTION: [HIGH/MEDIUM/LOW] (X/10)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Educational purposes only. Not financial advice.

For INTRADAY runs (when full analysis data is unavailable), use only the
news and macro context and clearly note it is an intraday update.
```

---

## Task 5 — Update `telegram_sender.py`

The output from Prompt 7 is already formatted for Telegram. Ensure
`telegram_sender.py` sends it using `parse_mode=None` (plain text, not
MarkdownV2), since the format uses Unicode symbols rather than Markdown syntax.

If the current sender uses `parse_mode="MarkdownV2"` or `parse_mode="Markdown"`,
change it to send plain text to avoid Telegram parse errors with characters like
`.`, `-`, `(`, `)`.

Recommended send call:
```python
requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message,
        # No parse_mode — send as plain text
    }
)
```

---

## Task 6 — Update `requirements.txt`

Ensure the following are present with minimum versions:
```
anthropic>=0.40.0
requests>=2.31.0
python-dotenv>=1.0.0
```

---

## Validation Checklist

After making all changes, verify:

- [ ] `python agent.py full` runs without errors and sends a Telegram message
- [ ] `python agent.py intraday` runs without errors, only executes prompts 3 and 7,
      and sends a shorter Telegram update
- [ ] Prompt caching beta header is present on the Anthropic client
- [ ] `cache_control` is set on all static system prompts
- [ ] MODEL_LIGHT is used for prompts 1, 2, 4, 6
- [ ] MODEL_HEAVY is used for prompts 3, 5, 7
- [ ] GitHub Actions workflow has both the 8:30 AM full run and the hourly
      intraday cron triggers
- [ ] Telegram message sends successfully as plain text

---

## Cost Target

After these changes, estimated monthly API cost should be:
- ~$0.09/day for the full run (market open)
- ~$0.01/run × 5 intraday runs/day = ~$0.05/day
- **Total: ~$0.14/day × 22 trading days = ~$3.10/month**

If costs exceed $6/month, check whether prompt caching is working by inspecting
the `usage` field in API responses — look for `cache_read_input_tokens > 0`.
