"""Daily reminder job for BachzTab bot."""

import logging
from datetime import timedelta

from telegram.ext import ContextTypes

from bot.db import get_all_active_trips, get_families, get_families_with_activity
from bot.i18n import t

logger = logging.getLogger(__name__)


async def send_daily_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send reminder to groups where not all expected families have contributed."""
    db_path = context.bot_data["db_path"]
    trips = await get_all_active_trips(db_path)

    for trip in trips:
        expected = trip.get("expected_families")
        if not expected:
            continue  # No expected count set, skip reminder

        families = await get_families(db_path, trip["id"])
        active_ids = await get_families_with_activity(db_path, trip["id"])

        # If enough families have contributed, skip
        if len(active_ids) >= expected:
            continue

        # Determine language (use first family's lang or default to en)
        lang = "en"
        if families:
            lang = families[0].get("language", "en")

        text = t("reminder", lang,
                 trip_name=trip["name"],
                 active=len(active_ids),
                 expected=expected)

        try:
            message = await context.bot.send_message(
                chat_id=trip["chat_id"],
                text=text,
                parse_mode="Markdown",
            )
            # Schedule auto-delete after 1 hour
            context.job_queue.run_once(
                _delete_reminder_message,
                when=timedelta(hours=1),
                data={"chat_id": trip["chat_id"], "message_id": message.message_id},
                name=f"delete_reminder_{trip['id']}_{message.message_id}",
            )
        except Exception as e:
            logger.warning(f"Failed to send reminder for trip {trip['id']}: {e}")


async def _delete_reminder_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a reminder message after timeout."""
    data = context.job.data
    try:
        await context.bot.delete_message(
            chat_id=data["chat_id"],
            message_id=data["message_id"],
        )
    except Exception as e:
        logger.debug(f"Could not delete reminder message: {e}")
