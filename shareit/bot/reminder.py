from __future__ import annotations

"""Daily reminder job for BachzTab bot."""

import logging
from datetime import timedelta

from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from bot.db import (
    get_all_active_trips, get_families, get_families_with_activity,
    get_meals, get_meal_contributions, get_meal_absences,
)
from bot.i18n import t

logger = logging.getLogger(__name__)


async def _build_meals_summary(db_path: str, trip: dict, families: list[dict], lang: str) -> str | None:
    """Build a meals summary text for a trip. Returns None if no meals."""
    meals = await get_meals(db_path, trip["id"])
    if not meals:
        return None

    esc = lambda s: escape_markdown(str(s), version=1)
    family_names = {f["id"]: f["name"] for f in families}
    text = t("meals_header", lang, trip_name=esc(trip["name"]), count=len(meals))

    for meal in meals:
        contributions = await get_meal_contributions(db_path, meal["id"])
        absences = await get_meal_absences(db_path, meal["id"])
        total = sum(c["amount"] for c in contributions)

        text += f"\n\n*#{meal['meal_number']} {esc(meal['name'])}*"
        if total > 0:
            text += f" — ${total:.2f}"

        if contributions:
            paid_parts = [f"{esc(family_names.get(c['family_id'], '?'))} ${c['amount']:.2f}" for c in contributions]
            text += "\n  💳 " + ", ".join(paid_parts)

        if absences:
            skipped_names = [esc(family_names.get(fid, "?")) for fid in absences]
            text += "\n  🚫 Skipped: " + ", ".join(skipped_names)

    return text


async def send_daily_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send meals summary + reminder to groups where not all expected families have contributed."""
    db_path = context.bot_data["db_path"]
    trips = await get_all_active_trips(db_path)

    for trip in trips:
        expected = trip.get("expected_families")
        if not expected:
            continue

        families = await get_families(db_path, trip["id"])
        active_ids = await get_families_with_activity(db_path, trip["id"])

        if len(active_ids) >= expected:
            continue

        lang = "en"
        if families:
            lang = families[0].get("language", "en")

        try:
            # Send meals summary first
            meals_text = await _build_meals_summary(db_path, trip, families, lang)
            if meals_text:
                meals_msg = await context.bot.send_message(
                    chat_id=trip["chat_id"],
                    text=meals_text,
                    parse_mode="Markdown",
                )
                context.job_queue.run_once(
                    _delete_reminder_message,
                    when=timedelta(hours=1),
                    data={"chat_id": trip["chat_id"], "message_id": meals_msg.message_id},
                    name=f"delete_meals_{trip['id']}_{meals_msg.message_id}",
                )

            # Send reminder
            text = t("reminder", lang,
                     trip_name=trip["name"],
                     active=len(active_ids),
                     expected=expected)

            message = await context.bot.send_message(
                chat_id=trip["chat_id"],
                text=text,
                parse_mode="Markdown",
            )
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
