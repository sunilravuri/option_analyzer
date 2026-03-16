"""
GLD LEAP Option Analysis Agent
================================
Core Claude AI agent that uses web_search tool to gather live market data
and synthesize a structured GLD LEAP option recommendation.

Uses: Anthropic Python SDK with model routing (Sonnet/Haiku) and prompt caching.
"""

import os
import sys
import time
from datetime import datetime, timedelta

import yfinance as yf
import anthropic
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Model routing — cost optimization
MODEL_HEAVY = "claude-sonnet-4-6"         # News sentiment, fundamentals, master synthesis
MODEL_LIGHT = "claude-haiku-4-5-20251001"  # IV analysis, event calendar, strike optimizer

MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds — rate limit recovery

# RUN_TYPE controls which prompts execute
# "full"     → all 7 prompts (market open run at 8:30 AM CST)
# "intraday" → news + synthesis only (hourly runs)
RUN_TYPE = sys.argv[1] if len(sys.argv) > 1 else "full"

WEB_SEARCH_TOOL = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log(msg: str) -> None:
    """Print a timestamped log message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def _get_client() -> anthropic.Anthropic:
    """Create Anthropic client with prompt caching beta header."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. Copy .env.example to .env and fill in your key."
        )
    return anthropic.Anthropic(
        api_key=api_key,
        default_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
    )


def _extract_text(response) -> str:
    """Pull text blocks out of an API response."""
    parts = []
    for block in response.content:
        if hasattr(block, "text"):
            parts.append(block.text)
    return "\n".join(parts).strip()


def _call_api(
    client: anthropic.Anthropic,
    model: str,
    system_text: str,
    user_text: str,
    use_search: bool = True,
    max_tokens: int = 2048,
) -> str:
    """
    Make a single API call with optional web_search tool.
    Applies cache_control to the static system prompt.
    """
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "system": [
            {
                "type": "text",
                "text": system_text,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        "messages": [{"role": "user", "content": user_text}],
    }
    if use_search:
        kwargs["tools"] = WEB_SEARCH_TOOL

    response = client.messages.create(**kwargs)
    result = _extract_text(response)
    if not result:
        raise ValueError("API returned empty response.")
    return result


def _retry(fn):
    """Call fn() up to MAX_RETRIES times, sleeping RETRY_DELAY on error."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn()
        except Exception as exc:
            _log(f"Error on attempt {attempt}/{MAX_RETRIES}: {exc}")
            if attempt < MAX_RETRIES:
                _log(f"Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise


# ---------------------------------------------------------------------------
# Option chain fetcher (yfinance — 15-min delayed)
# ---------------------------------------------------------------------------

def fetch_option_chain() -> str:
    """
    Fetch GLD call option chain for LEAP expirations via yfinance.
    Returns a formatted string of ITM strikes ($380–$470) across 12+ month expirations.
    """
    try:
        gld = yf.Ticker("GLD")
        spot = gld.fast_info.last_price
        expirations = gld.options

        today = datetime.utcnow().date()
        cutoff = today + timedelta(days=365)
        leap_expiries = [
            e for e in expirations
            if datetime.strptime(e, "%Y-%m-%d").date() >= cutoff
        ]

        if not leap_expiries:
            return f"GLD spot: ${spot:.2f}\nNo LEAP expirations (12+ months) found in option chain."

        rows = [f"GLD spot (delayed): ${spot:.2f}\n"]
        for expiry in leap_expiries[:4]:
            chain = gld.option_chain(expiry)
            calls = chain.calls
            itm = calls[(calls["strike"] >= 380) & (calls["strike"] <= 470)].copy()
            if itm.empty:
                rows.append(f"{expiry}: no calls in $380–$470 range\n")
                continue
            rows.append(f"{expiry}:")
            for _, r in itm.iterrows():
                bid = f"${r['bid']:.2f}" if r["bid"] > 0 else "N/A"
                ask_per_share = r["ask"] if r["ask"] > 0 else None
                ask_str = f"${ask_per_share:.2f}/share (${ask_per_share*100:.0f}/contract)" if ask_per_share else "N/A"
                iv = f"{r['impliedVolatility']*100:.1f}%" if r["impliedVolatility"] > 0 else "N/A"
                vol = int(r["volume"]) if r["volume"] == r["volume"] else 0
                within_budget = " ✓ within $6500" if ask_per_share and ask_per_share * 100 <= 6500 else " ✗ over $6500"
                rows.append(
                    f"  Strike ${r['strike']:.0f} | Ask {ask_str}{within_budget} | IV {iv} | Vol {vol}"
                )
            rows.append("")
        return "\n".join(rows)
    except Exception as exc:
        return f"yfinance fetch failed: {exc}"


# ---------------------------------------------------------------------------
# Prompt functions — 7-prompt analysis framework
# ---------------------------------------------------------------------------

_SYS_OPTIONS = (
    "You are an expert options analyst specializing in GLD LEAP calls. "
    "Provide precise, data-driven analysis. Plain text only, no markdown tables."
)

_SYS_MACRO = (
    "You are a macro market analyst specializing in gold markets, Fed policy, "
    "and precious metals ETFs. Provide clear, concise analysis. Plain text only."
)

_SYS_QUANT = (
    "You are a quantitative options strategist specializing in GLD "
    "(SPDR Gold Shares ETF). Provide structured, actionable analysis. Plain text only."
)

_SYS_SYNTHESIS = (
    "You are a quantitative options strategist for GLD (SPDR Gold Shares ETF). "
    "Synthesize analysis from multiple sources and deliver a final LEAP recommendation "
    "formatted for Telegram. Plain text only."
)


def run_iv_chain_prompt(client: anthropic.Anthropic, chain_data: str) -> str:
    """Prompt 1 — IV & Options Chain Analysis (MODEL_LIGHT)."""
    _log("Prompt 1: IV & Options Chain Analysis...")
    user = f"""Search for the current GLD options chain for LEAP expirations (12–24 months out).

Live GLD option chain data (yfinance, 15-min delayed):
{chain_data}

Analyze:
1. IV Rank (IVR) and IV Percentile — is IV cheap (<30 IVR) or expensive (>70 IVR)?
2. IV vs Historical Volatility (30-day HV) ratio — are options over/underpriced?
3. Skew: compare IV across strikes (ATM vs OTM calls/puts)
4. Delta, Gamma, Theta, Vega for 3 candidate strikes
5. Open Interest and Volume — where is institutional positioning?
6. Identify top 3 strike/expiry combos for a long LEAP call (delta ~0.70–0.80 ITM, ~0.50 ATM), ranked by cost-efficiency

Output: table of top 3 candidates with strike, expiry, IV, delta, estimated cost, and one-line reasoning. Plain text only, no markdown tables."""
    return _retry(lambda: _call_api(client, MODEL_LIGHT, _SYS_OPTIONS, user))


def run_iv_timing_prompt(client: anthropic.Anthropic) -> str:
    """Prompt 2 — IV Entry Timing Gate (MODEL_LIGHT)."""
    _log("Prompt 2: IV Entry Timing Gate...")
    user = """Search for GLD's current implied volatility metrics:
- Current IV, 52-week IV High and Low, IV Rank, IV Percentile, HV 30-day

Then answer:
1. Is now favorable to BUY LEAPs? (IVR < 30 = YES, 30–50 = CAUTION, >50 = WAIT)
2. IV/HV ratio — are options fairly priced?
3. Implied ±1 standard deviation move by LEAP expiration
4. What IV level would be ideal entry?

Final output must be one of: ✅ BUY NOW / ⚠️ WAIT / ❌ AVOID
with a single sentence reason. Plain text only."""
    return _retry(lambda: _call_api(client, MODEL_LIGHT, _SYS_OPTIONS, user))


def run_news_sentiment_prompt(client: anthropic.Anthropic) -> str:
    """Prompt 3 — News Sentiment (MODEL_HEAVY)."""
    _log("Prompt 3: News Sentiment...")
    user = """Search for the top GLD and gold market news from the past 5 trading days.
Include: Fed policy signals, DXY moves, real yields (TIPS), central bank gold demand, geopolitical risk events, and any ETF flow data.

For each story:
1. Sentiment: Bullish / Bearish / Neutral for GLD
2. Impact window: <1 week / 1–4 weeks / 1–6 months
3. Relevance to a 12–24 month LEAP: High / Medium / Low

Then provide:
- Net sentiment score: −5 (very bearish) to +5 (very bullish)
- #1 macro risk that could invalidate a bullish LEAP thesis
- #1 catalyst that could accelerate a bullish move

Plain text only."""
    return _retry(lambda: _call_api(client, MODEL_HEAVY, _SYS_MACRO, user))


def run_event_calendar_prompt(client: anthropic.Anthropic) -> str:
    """Prompt 4 — Event Risk Calendar (MODEL_LIGHT)."""
    _log("Prompt 4: Event Risk Calendar...")
    today = datetime.now().strftime("%Y-%m-%d")
    user = f"""Search for upcoming events over the next 3–18 months that could affect GLD:
1. FOMC meeting dates and rate decision expectations
2. CPI/PCE release dates
3. US dollar (DXY) key levels and catalysts
4. Central bank gold buying/selling reports
5. Geopolitical risk events (Middle East, Russia/Ukraine, Taiwan)

For each event:
- Estimated IV impact: High / Medium / Low spike expected
- Directional bias for GLD
- LEAP implication: enter before / after / avoid

Today's date: {today}. Plain text only."""
    return _retry(lambda: _call_api(client, MODEL_LIGHT, _SYS_MACRO, user))


def run_fundamentals_prompt(client: anthropic.Anthropic) -> str:
    """Prompt 5 — ETF Fundamental Scorecard (MODEL_HEAVY)."""
    _log("Prompt 5: ETF Fundamental Scorecard...")
    user = """Analyze GLD as a LEAP candidate:

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

Plain text only."""
    return _retry(lambda: _call_api(client, MODEL_HEAVY, _SYS_QUANT, user))


def run_strike_optimizer_prompt(client: anthropic.Anthropic, chain_data: str) -> str:
    """Prompt 6 — Strike & Expiry Optimizer (MODEL_LIGHT)."""
    _log("Prompt 6: Strike & Expiry Optimizer...")
    user = f"""I want to buy a GLD LEAP call with these constraints:
- Max budget: $6,500 total (can buy multiple contracts)
- Holding period: 12–18 months
- Bullish price target: search for analyst consensus GLD target
- Risk tolerance: willing to lose up to 50% of premium

LIVE GLD OPTION CHAIN (yfinance, 15-min delayed) — USE THESE REAL ASK PRICES:
{chain_data}

PRICING RULE: Ask prices in the chain are per share. Each contract = 100 shares.
Cost per contract = ask × 100. Budget limit = $6,500, so only strikes where ask × 100 ≤ $6,500 (ask ≤ $65.00) are viable.
The chain data already marks which strikes are within budget. Do NOT estimate premiums — use only real ask prices provided.

Model 3 scenarios using real strikes from the chain (only within-budget strikes):
1. ITM strike (delta ~0.80, ask ≤ $65)
2. ATM strike (delta ~0.50, ask ≤ $65)
3. OTM strike (delta ~0.30, ask ≤ $65)

For each scenario using the real ask price from the chain:
- Ask per share and cost per contract (ask × 100)
- Breakeven price at expiry = strike + ask
- Estimated probability of profit
- Max contracts within $6,500 budget = floor(6500 / (ask × 100))

Recommend the best strike for risk-adjusted return.
Also suggest a roll strategy: when/how to roll if the position moves against me by 20%.

Plain text only."""
    return _retry(lambda: _call_api(client, MODEL_LIGHT, _SYS_OPTIONS, user))


def run_master_synthesis_prompt(client: anthropic.Anthropic, results: dict) -> str:
    """Prompt 7 — Master Synthesis (MODEL_HEAVY)."""
    _log("Prompt 7: Master Synthesis...")
    dt = datetime.now().strftime("%Y-%m-%d %H:%M")
    is_intraday = RUN_TYPE == "intraday"

    iv_chain = results.get("iv_chain", "N/A — intraday run")
    iv_timing = results.get("iv_timing", "N/A — intraday run")
    news = results.get("news", "N/A")
    events = results.get("events", "N/A — intraday run")
    fundamentals = results.get("fundamentals", "N/A — intraday run")
    strikes = results.get("strikes", "N/A — intraday run")
    chain_data = results.get("chain_data", "")

    intraday_note = (
        "\nNOTE: This is an INTRADAY UPDATE. Full chain analysis was not run. "
        "Base your recommendation primarily on news and macro context, "
        "and clearly note it is an intraday update.\n"
        if is_intraday else ""
    )

    chain_section = (
        f"\nLIVE OPTION CHAIN (ground truth — use these real ask prices for Est. Premium and Contracts fields):\n{chain_data}\n"
        if chain_data else ""
    )

    user = f"""Synthesize the following analysis results and deliver a final LEAP recommendation:{intraday_note}
{chain_section}
<iv_analysis>{iv_chain}</iv_analysis>
<iv_timing>{iv_timing}</iv_timing>
<news_sentiment>{news}</news_sentiment>
<event_calendar>{events}</event_calendar>
<fundamentals>{fundamentals}</fundamentals>
<strike_analysis>{strikes}</strike_analysis>

MY CONSTRAINTS:
- Budget: $6,500 max per contract (ask × 100 ≤ $6,500, meaning ask ≤ $65.00/share)
- Target return: 2–3x
- Time horizon: 12–18 months
- Max loss tolerance: 50% of premium

PRICING RULES (CRITICAL — violations make the output useless):
1. Ask prices in the chain are per share. Cost per contract = ask × 100.
2. Only recommend strikes where ask × 100 ≤ $6,500.
3. If NO strike across all expirations fits the budget, output the WAIT block.
4. Do NOT estimate premiums — use only the real ask prices from the chain above.

Deliver your final output in this EXACT format for Telegram (keep it concise — no extra lines, no bullet explanations):

📊 GLD LEAP — {dt} CST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 GLD: $XXX.XX | Tech: [BULLISH/NEUTRAL/BEARISH] | Macro: [FAVORABLE/NEUTRAL/UNFAVORABLE] | IV: [CHEAP/FAIR/EXPENSIVE]

[✅ GO / ⚠️ WAIT / ❌ NO-GO] RECOMMENDATION
Strike: $XXX | Expiry: [Mon YYYY] | Ask: $XX.XX/share → $X,XXX/contract
Contracts: X | Break-even: $XXX.XX | Delta: ~X.XX

📌 Why: [15 words max]
⚡ Conviction: [HIGH/MEDIUM/LOW] (X/10) — [10 words max]
🎯 Target: $XXX | 🛑 Stop: GLD < $XXX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Educational only. Not financial advice.

IF no strike fits within $6,500 budget (ask × 100 > $6,500 for all expirations):

📊 GLD LEAP — {dt} CST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 GLD: $XXX.XX
⏳ No entry within $6,500 — premiums too high.
📌 Cheapest available: Strike $XXX [Mon YYYY] ask $XX.XX/share ($X,XXX/contract)
🕐 Watch for: [15 words — price level or condition to unlock a valid entry]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Educational only. Not financial advice."""

    return _retry(lambda: _call_api(client, MODEL_HEAVY, _SYS_SYNTHESIS, user, use_search=False, max_tokens=3000))


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def run_gld_analysis() -> str:
    """
    Run GLD LEAP analysis. Full run executes all 7 prompts; intraday runs
    only news (Prompt 3) and synthesis (Prompt 7).

    Returns:
        The final formatted Telegram message string.
    """
    _log(f"Starting GLD LEAP analysis (run_type={RUN_TYPE})...")
    client = _get_client()
    results = {}

    # Always run: news sentiment
    results["news"] = run_news_sentiment_prompt(client)

    if RUN_TYPE == "full":
        _log("Fetching GLD option chain via yfinance...")
        chain_data = fetch_option_chain()
        _log(f"Option chain fetched ({len(chain_data)} chars)")

        results["chain_data"] = chain_data  # passed to Prompt 7 as price ground truth
        results["iv_chain"] = run_iv_chain_prompt(client, chain_data)
        results["iv_timing"] = run_iv_timing_prompt(client)
        results["events"] = run_event_calendar_prompt(client)
        results["fundamentals"] = run_fundamentals_prompt(client)
        results["strikes"] = run_strike_optimizer_prompt(client, chain_data)

    # Always run: master synthesis
    results["synthesis"] = run_master_synthesis_prompt(client, results)
    _log(f"Analysis complete ({len(results['synthesis'])} chars)")
    return results["synthesis"]


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    _log(f"Starting GLD LEAP Agent (run_type={RUN_TYPE})...")
    analysis = run_gld_analysis()

    print("\n" + "=" * 60)
    print(analysis)
    print("=" * 60)

    from telegram_sender import send_to_telegram
    send_to_telegram(analysis)
    _log("Done.")
