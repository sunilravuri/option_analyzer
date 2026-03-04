"""
Telegram Sender
================
Formats and sends GLD LEAP analysis reports to a Telegram channel/chat
via the Telegram Bot API.

Supports:
- HTML parse mode (converts markdown bold to HTML bold)
- Automatic message splitting for reports > 4096 chars
- Connection test function
"""

import os
import re
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot API limits
MAX_MESSAGE_LENGTH = 4096


def _log(msg: str) -> None:
    """Print a timestamped log message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def _get_credentials() -> tuple[str, str]:
    """Retrieve Telegram bot token and chat ID from environment."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise EnvironmentError(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set. "
            "Copy .env.example to .env and fill in your values."
        )
    return token, chat_id


def _markdown_to_html(text: str) -> str:
    """
    Convert common markdown bold (**text**) to HTML bold (<b>text</b>).
    Telegram sendMessage with parse_mode=HTML expects HTML tags.
    """
    # Convert **bold** → <b>bold</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Convert *italic* → <i>italic</i>
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    return text


def _split_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """
    Split a long message into chunks that fit within Telegram's limit.
    Tries to split on newlines to keep formatting intact.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        # Find the last newline before the limit
        split_idx = text.rfind("\n", 0, max_length)
        if split_idx == -1:
            # No newline found — hard split
            split_idx = max_length

        chunks.append(text[:split_idx])
        text = text[split_idx:].lstrip("\n")

    return chunks


def send_to_telegram(message: str) -> bool:
    """
    Send an analysis report to Telegram.

    Args:
        message: The report text to send.

    Returns:
        True if all message chunks were sent successfully, False otherwise.
    """
    try:
        token, chat_id = _get_credentials()
    except EnvironmentError as exc:
        _log(f"FAILED — {exc}")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    html_message = _markdown_to_html(message)
    chunks = _split_message(html_message)

    _log(f"Sending {len(chunks)} message(s) to Telegram...")
    all_ok = True

    for i, chunk in enumerate(chunks, 1):
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "HTML",
        }
        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.ok:
                _log(f"  ✅ Chunk {i}/{len(chunks)} sent successfully")
            else:
                _log(f"  ❌ Chunk {i}/{len(chunks)} failed: {resp.status_code} {resp.text}")
                all_ok = False
        except requests.RequestException as exc:
            _log(f"  ❌ Chunk {i}/{len(chunks)} request error: {exc}")
            all_ok = False

    if all_ok:
        _log("All messages delivered to Telegram ✅")
    else:
        _log("Some messages failed to deliver ❌")

    return all_ok


def test_telegram_connection() -> bool:
    """
    Send a quick test ping to confirm the bot and chat ID are working.
    """
    test_msg = (
        "🔔 <b>GLD LEAP Agent — Connection Test</b>\n\n"
        "✅ Telegram bot is connected and operational.\n"
        f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S CST')}"
    )
    _log("Testing Telegram connection...")
    return send_to_telegram(test_msg)


# ---------------------------------------------------------------------------
# CLI entry-point for testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    _log("Running Telegram sender test...")
    success = test_telegram_connection()
    if success:
        _log("Test passed — you should see a message in Telegram.")
    else:
        _log("Test failed — check your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
