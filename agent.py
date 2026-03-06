"""
GLD LEAP Option Analysis Agent
================================
Core Claude AI agent that uses web_search tool to gather live market data
and synthesize a structured GLD LEAP option recommendation.

Uses: Anthropic Python SDK with claude-sonnet-4-6 and web_search_20250305 tool.
"""

import os
import time
from datetime import datetime

import yfinance as yf
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-6"
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds — rate limit recovery

SYSTEM_PROMPT = """You are an elite options trader and quantitative analyst specializing in GLD LEAP calls.

When given a task, use web search to gather:

MARKET DATA (1-2 searches):
- Current live GLD ETF price and key technicals: RSI, MACD, 50/200-day SMA, Bollinger Bands, ATR
- Macro factors: DXY level, 10Y TIPS real yield, Fed stance, latest CPI/PCE print
- Major gold market news or central bank demand signals

OPTION CHAIN (1-2 searches):
- Live GLD LEAP call option chain across ALL expirations 12+ months out:
  Jan 15 2027, Mar 19 2027, Jun 17 2027, Jan 21 2028
- Find real bid/ask prices for ITM call strikes between $380–$470 on each expiry
- ONLY use real live bid/ask prices. If data is unavailable, say so explicitly — do NOT estimate.

ANALYSIS (for each expiry candidate within $6,500 budget):
- Intrinsic value = GLD price − strike
- Time premium = total premium − intrinsic value
- % intrinsic = intrinsic ÷ total premium (target ≥ 70%)
- Delta (target 0.70–0.85)
- Break-even at expiry = strike + premium paid

ADDITIONAL FACTORS:
- Assess current IV environment — is elevated IV making premiums expensive?
- Consider whether a GLD pullback to $440–$450 would unlock better ITM strikes within budget
- Cross-expiry comparison: Jun 2027 or Jan 2028 may give deeper ITM access vs Mar 2027 for same budget

IMPORTANT RULES:
- Recommend a SINGLE GLD LEAP call — NOT a spread, NOT multi-leg
- Budget is strictly $6,500 maximum for one contract
- Expiry must be 12+ months out
- Be efficient: aim for 3–4 searches total, combine related queries

Your FINAL response must contain ONLY the block below — no preamble, no data summaries, no reasoning, no notes, no extra lines. Output the block and nothing else. Total word count must be under 60 words:

📊 GLD LEAP — [DATE] [TIME] CST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 GLD: $[price]
🎯 Strike: $[strike] | Expiry: [date] | Ask: $[ask/contract] | Cost: $[total] ([N] contract[s])
📐 Delta: [delta] | Intrinsic: [%]% | Break-even: $[price]

📌 Rationale: [10–15 words max on why this strike/expiry beats alternatives]

⚡ Conviction: [HIGH/MEDIUM/LOW] — [10–15 words max on key factor]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Educational only. Not financial advice."""

def fetch_option_chain() -> str:
    """
    Fetch GLD call option chain for LEAP expirations via yfinance (15-min delayed).
    Returns a formatted string of ITM strikes ($380-$470) across 12+-month expirations.
    """
    try:
        gld = yf.Ticker("GLD")
        spot = gld.fast_info.last_price
        expirations = gld.options  # tuple of expiry strings "YYYY-MM-DD"

        # Filter to expirations 12+ months out
        today = datetime.utcnow().date()
        from datetime import date, timedelta
        cutoff = today + timedelta(days=365)
        leap_expiries = [e for e in expirations if datetime.strptime(e, "%Y-%m-%d").date() >= cutoff]

        if not leap_expiries:
            return f"GLD spot: ${spot:.2f}\nNo LEAP expirations (12+ months) found in option chain."

        rows = [f"GLD spot (delayed): ${spot:.2f}\n"]
        for expiry in leap_expiries[:4]:  # cap at 4 expirations
            chain = gld.option_chain(expiry)
            calls = chain.calls
            # Filter to ITM strikes $380-$470
            itm = calls[(calls["strike"] >= 380) & (calls["strike"] <= 470)].copy()
            if itm.empty:
                rows.append(f"{expiry}: no calls in $380-$470 range\n")
                continue
            rows.append(f"{expiry}:")
            for _, r in itm.iterrows():
                bid = f"${r['bid']:.2f}" if r['bid'] > 0 else "N/A"
                ask = f"${r['ask']:.2f}" if r['ask'] > 0 else "N/A"
                iv = f"{r['impliedVolatility']*100:.1f}%" if r['impliedVolatility'] > 0 else "N/A"
                delta = f"{r.get('delta', float('nan')):.2f}" if 'delta' in r and r['delta'] == r['delta'] else "N/A"
                rows.append(f"  Strike ${r['strike']:.0f} | Bid {bid} | Ask {ask} | IV {iv} | Vol {int(r['volume']) if r['volume'] == r['volume'] else 0}")
            rows.append("")

        return "\n".join(rows)
    except Exception as exc:
        return f"yfinance fetch failed: {exc}"


USER_PROMPT = (
    "Perform a complete GLD LEAP option analysis right now using "
    "live market data. Search for all required information."
)


def _log(msg: str) -> None:
    """Print a timestamped log message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def run_gld_analysis() -> str:
    """
    Run the full GLD LEAP analysis agentic loop.

    Uses Claude claude-sonnet-4-6 with web_search tool. Keeps calling the API
    until stop_reason is "end_turn". Retries up to MAX_RETRIES on failure.

    Returns:
        The final formatted analysis text string.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. "
            "Copy .env.example to .env and fill in your key."
        )

    client = Anthropic(api_key=api_key)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            _log(f"Attempt {attempt}/{MAX_RETRIES} — starting analysis...")
            return _agentic_loop(client)
        except Exception as exc:
            _log(f"Error on attempt {attempt}: {exc}")
            if attempt < MAX_RETRIES:
                _log(f"Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(
                    f"All {MAX_RETRIES} attempts failed. Last error: {exc}"
                ) from exc

    # Unreachable, but keeps type-checkers happy
    raise RuntimeError("Analysis failed unexpectedly.")


def _agentic_loop(client: Anthropic) -> str:
    """
    Core agentic loop: send messages, process tool calls, repeat until
    the model returns stop_reason == "end_turn".
    """
    _log("Fetching GLD option chain via yfinance...")
    chain_data = fetch_option_chain()
    _log(f"Option chain fetched ({len(chain_data)} chars)")

    user_content = (
        f"{USER_PROMPT}\n\n"
        f"--- GLD OPTION CHAIN DATA (yfinance, 15-min delayed) ---\n"
        f"{chain_data}\n"
        f"--- Use the above real prices for your analysis. "
        f"Only web search for macro/technical data you still need. ---"
    )
    messages = [{"role": "user", "content": user_content}]

    while True:
        _log("Calling Claude API...")
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
            messages=messages,
        )

        _log(f"stop_reason={response.stop_reason}")

        # If the model is done, extract the final text
        if response.stop_reason == "end_turn":
            return _extract_text(response)

        # Otherwise, process tool uses and feed results back
        # Append the assistant's full response (may contain text + tool_use blocks)
        messages.append({"role": "assistant", "content": response.content})

        # Build tool_result blocks for every tool_use in the response
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                _log(f"  ↳ tool_use: {block.name} (id={block.id})")
                # For server-side tools like web_search, the API handles
                # execution automatically — we just need to continue the loop.
                # If the stop_reason is "tool_use" we re-send and the API
                # will include the search results in the next turn.

        # If there were no explicit tool results to send, just continue
        # (the API will include web_search results automatically)
        if not tool_results:
            # For server-side tools we don't need to send tool_result;
            # just continue the conversation as-is.
            pass


def _extract_text(response) -> str:
    """Pull out the final text from the response content blocks."""
    text_parts = []
    for block in response.content:
        if hasattr(block, "text"):
            text_parts.append(block.text)
    result = "\n".join(text_parts).strip()
    if not result:
        raise ValueError("Agent returned empty analysis.")
    # Strip any preamble before the formatted block
    marker = "📊 GLD LEAP"
    idx = result.find(marker)
    if idx > 0:
        result = result[idx:]
    # Strip any trailing notes after the last separator line
    end_marker = "⚠️ Educational only. Not financial advice."
    end_idx = result.find(end_marker)
    if end_idx != -1:
        result = result[: end_idx + len(end_marker)]
    _log(f"Analysis complete ({len(result)} chars)")
    return result


# ---------------------------------------------------------------------------
# CLI entry-point for quick testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    _log("Starting GLD LEAP analysis (standalone)...")
    analysis = run_gld_analysis()
    print("\n" + "=" * 60)
    print(analysis)
    print("=" * 60)
