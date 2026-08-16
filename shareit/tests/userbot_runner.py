"""Live Telethon Userbot UI Test Suite for BachzTab."""

import os
import sys
import asyncio

try:
    from telethon import TelegramClient, events
    from telethon.tl.custom import Button
    HAS_TELETHON = True
except ImportError:
    HAS_TELETHON = False

API_ID = os.environ.get("TELEGRAM_API_ID")
API_HASH = os.environ.get("TELEGRAM_API_HASH")
SESSION_NAME = os.environ.get("TELEGRAM_SESSION", "userbot_test_session")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "@BachzTabBot")
GROUP_CHAT_ID = os.environ.get("TEST_GROUP_CHAT")


async def run_userbot_ui_tests():
    if not HAS_TELETHON:
        print("ℹ️ Telethon is not installed. Install with `pip install telethon` to run live Telegram userbot tests.")
        return

    if not API_ID or not API_HASH:
        print("ℹ️ TELEGRAM_API_ID and TELEGRAM_API_HASH environment variables are required for live userbot tests.")
        print("Example: TELEGRAM_API_ID=12345 TELEGRAM_API_HASH=abcdef12345 python3 tests/userbot_runner.py")
        return

    print("=== Starting Live Telethon Userbot UI Test Suite ===")
    async with TelegramClient(SESSION_NAME, int(API_ID), API_HASH) as client:
        print("✅ Logged in as Telegram Userbot")
        entity = await client.get_entity(GROUP_CHAT_ID or BOT_USERNAME)

        # UI Test 1: Send /start or /menu
        print("\n▶️ UI Test 1: Sending /menu command...")
        await client.send_message(entity, "/menu")
        await asyncio.sleep(2)

        # UI Test 2: Click persistent status button
        print("▶️ UI Test 2: Tapping Status button...")
        await client.send_message(entity, "🏕 Status")
        await asyncio.sleep(2)

        # UI Test 3: Log general expense custom amount
        print("▶️ UI Test 3: Logging custom amount expense...")
        await client.send_message(entity, "45.50")
        await asyncio.sleep(2)

        print("\n✅ Live Telethon Userbot UI Tests Complete!")


if __name__ == "__main__":
    asyncio.run(run_userbot_ui_tests())
