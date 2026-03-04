"""
Local Test Scheduler
=====================
Runs the GLD LEAP analysis agent every 15 minutes for local testing.
In production, GitHub Actions handles scheduling via cron.

Usage:
    python scheduler.py
"""

import time
from datetime import datetime

from agent import run_gld_analysis
from telegram_sender import send_to_telegram

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INTERVAL_MINUTES = 15


def _log(msg: str) -> None:
    """Print a timestamped log message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def run_once() -> None:
    """Run a single analysis cycle: fetch → analyze → send to Telegram."""
    try:
        _log("Starting GLD LEAP analysis cycle...")
        analysis = run_gld_analysis()

        _log("Sending analysis to Telegram...")
        success = send_to_telegram(analysis)

        if success:
            _log("Cycle complete ✅")
        else:
            _log("Cycle complete with Telegram delivery issues ⚠️")
    except Exception as exc:
        _log(f"Cycle failed ❌: {exc}")


def main() -> None:
    """Run the scheduler loop — executes every INTERVAL_MINUTES."""
    _log(f"Local scheduler started (every {INTERVAL_MINUTES} min)")
    _log("Press Ctrl+C to stop.\n")

    while True:
        run_once()
        _log(f"Next run in {INTERVAL_MINUTES} minutes...\n")
        time.sleep(INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()
