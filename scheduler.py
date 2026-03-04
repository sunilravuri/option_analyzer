"""
GLD LEAP Scheduler
===================
Runs the GLD LEAP analysis agent every 15 minutes,
Monday–Friday, 8:30 AM–3:00 PM CST.

Usage:
    python scheduler.py
"""

import sys
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from agent import run_gld_analysis
from telegram_sender import send_to_telegram

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INTERVAL_MINUTES = 15
CST = ZoneInfo("America/Chicago")
MARKET_OPEN  = (8, 30)   # 8:30 AM CST
MARKET_CLOSE = (15, 0)   # 3:00 PM CST


def _log(msg: str) -> None:
    ts = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST")
    print(f"[{ts}] {msg}")


def _now_cst() -> datetime:
    return datetime.now(CST)


def _is_market_hours(dt: datetime) -> bool:
    """Return True if dt falls within Mon–Fri 8:30 AM–3:00 PM CST."""
    if dt.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    market_open  = dt.replace(hour=MARKET_OPEN[0],  minute=MARKET_OPEN[1],  second=0, microsecond=0)
    market_close = dt.replace(hour=MARKET_CLOSE[0], minute=MARKET_CLOSE[1], second=0, microsecond=0)
    return market_open <= dt <= market_close


def _seconds_until_next_open(dt: datetime) -> float:
    """Return seconds until the next 8:30 AM CST on a weekday."""
    candidate = dt.replace(hour=MARKET_OPEN[0], minute=MARKET_OPEN[1], second=0, microsecond=0)
    if candidate <= dt:
        candidate += timedelta(days=1)
    # Skip weekends
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return (candidate - dt).total_seconds()


def run_once() -> None:
    """Run a single analysis cycle: fetch → analyze → send to Telegram."""
    try:
        _log("Starting GLD LEAP analysis cycle...")
        analysis = run_gld_analysis()
        _log("Sending analysis to Telegram...")
        success = send_to_telegram(analysis)
        _log("Cycle complete ✅" if success else "Cycle complete with Telegram delivery issues ⚠️")
    except Exception as exc:
        _log(f"Cycle failed ❌: {exc}")


def main() -> None:
    _log("GLD LEAP Scheduler started — Mon–Fri 8:30 AM–3:00 PM CST, every 15 min")
    _log("Press Ctrl+C to stop.\n")

    while True:
        now = _now_cst()

        if _is_market_hours(now):
            run_once()
            # Sleep until next 15-min mark, accounting for run time
            elapsed = (_now_cst() - now).total_seconds()
            sleep_secs = max(0, INTERVAL_MINUTES * 60 - elapsed)
            next_run = _now_cst() + timedelta(seconds=sleep_secs)
            _log(f"Next run at {next_run.strftime('%H:%M:%S CST')}\n")
            time.sleep(sleep_secs)
        else:
            wait = _seconds_until_next_open(now)
            next_open = now + timedelta(seconds=wait)
            _log(f"Outside market hours — waiting until {next_open.strftime('%a %Y-%m-%d %H:%M CST')}")
            time.sleep(min(wait, 60))  # re-check every 60s near open


if __name__ == "__main__":
    main()
