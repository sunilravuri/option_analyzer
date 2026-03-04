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

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-6"
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds — rate limit recovery

SYSTEM_PROMPT = """You are an elite options trader and quantitative analyst.
When given a task, use web search to find:
- Current live GLD ETF price
- RSI, MACD, 50/200 SMA, Bollinger Bands, ATR for GLD
- US Dollar Index (DXY) current level and trend
- 10-Year TIPS real yield (current)
- Federal Reserve latest policy stance
- Latest CPI/PCE inflation data
- Any major gold market news or central bank demand signals

Then synthesize everything into a structured GLD LEAP call option
recommendation with total premium budget of $6,500 max.

IMPORTANT: Recommend a single GLD LEAP call option — NOT a spread.
Do NOT suggest bull call spreads, bear spreads, or any multi-leg strategy.
The recommendation must be a single long call option with expiry 12+ months out.

Your FINAL response must contain ONLY the block below — no preamble, no data summaries, no reasoning, no notes, no extra lines. Output the block and nothing else:

📊 GLD LEAP — [DATE] [TIME] CST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 GLD: $[price]
🎯 Strike: $[strike] | Expiry: [date] | Cost: $[total] ([N] contract[s])

📌 Rationale: [20–30 words on why this strike and expiry given current price, technicals, and macro]

⚡ Conviction: [HIGH/MEDIUM/LOW] — [20–30 words explaining conviction level based on key supporting factors]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Educational only. Not financial advice."""

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
    messages = [{"role": "user", "content": USER_PROMPT}]

    while True:
        _log("Calling Claude API...")
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 10}],
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
