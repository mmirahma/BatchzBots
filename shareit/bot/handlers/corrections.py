import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from bot.db import delete_meal, get_meal_by_number, get_meal_contributions, update_contribution_amount
from bot.i18n import t
from bot.handlers._helpers import require_group, require_family


async def undo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /undo — removes the user's last action."""
    if not await require_group(update):
        return
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    last_action = context.user_data.get("last_action")
    if not last_action:
        await update.message.reply_text(t("undo_nothing", lang))
        return

    # Verify the action belongs to this trip (user_data is global per user)
    if last_action.get("trip_id") != trip["id"]:
        await update.message.reply_text(t("undo_nothing", lang))
        return

    db_path = context.bot_data["db_path"]
    action_type = last_action["type"]

    if action_type == "meal":
        await delete_meal(db_path, last_action["meal_id"])
    elif action_type == "contribution":
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "DELETE FROM meal_contributions WHERE meal_id = ? AND family_id = ? "
                "AND id = (SELECT MAX(id) FROM meal_contributions WHERE meal_id = ? AND family_id = ?)",
                (last_action["meal_id"], last_action["family_id"],
                 last_action["meal_id"], last_action["family_id"]),
            )
            await db.commit()
    elif action_type == "absence":
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "DELETE FROM meal_absences WHERE meal_id = ? AND family_id = ?",
                (last_action["meal_id"], last_action["family_id"]),
            )
            await db.commit()
    elif action_type == "expense":
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "DELETE FROM shared_expenses WHERE id = ?",
                (last_action["expense_id"],),
            )
            await db.commit()

    context.user_data.pop("last_action", None)
    await update.message.reply_text(t("undo_success", lang))


async def deletemeal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /deletemeal <meal#> — only creator can delete."""
    if not await require_group(update):
        return
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    if not context.args:
        await update.message.reply_text(t("usage_deletemeal", lang))
        return

    try:
        meal_number = int(context.args[0].lstrip("#"))
    except ValueError:
        await update.message.reply_text(t("usage_deletemeal", lang))
        return

    db_path = context.bot_data["db_path"]
    meal = await get_meal_by_number(db_path, trip["id"], meal_number)
    if not meal:
        await update.message.reply_text(t("meal_not_found", lang, number=meal_number))
        return

    # Check if this family is the original creator (first contributor)
    contributions = await get_meal_contributions(db_path, meal["id"])
    if not contributions or contributions[0]["family_id"] != family["id"]:
        await update.message.reply_text(t("meal_delete_denied", lang))
        return

    meal_name = meal["name"]
    await delete_meal(db_path, meal["id"])
    await update.message.reply_text(t("meal_deleted", lang, number=meal_number, name=meal_name))


async def editmeal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /editmeal <meal#> <new amount> — update your own contribution."""
    if not await require_group(update):
        return
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(t("usage_editmeal", lang))
        return

    try:
        meal_number = int(context.args[0].lstrip("#"))
        amount = float(context.args[1])
    except (ValueError, IndexError):
        await update.message.reply_text(t("usage_editmeal", lang))
        return

    if amount <= 0:
        await update.message.reply_text(t("usage_editmeal", lang))
        return

    db_path = context.bot_data["db_path"]
    meal = await get_meal_by_number(db_path, trip["id"], meal_number)
    if not meal:
        await update.message.reply_text(t("meal_not_found", lang, number=meal_number))
        return

    contributions = await get_meal_contributions(db_path, meal["id"])
    if not any(c["family_id"] == family["id"] for c in contributions):
        await update.message.reply_text(t("no_contribution_to_edit", lang, number=meal_number))
        return

    await update_contribution_amount(db_path, meal["id"], family["id"], amount)
    await update.message.reply_text(t("meal_edited", lang, number=meal_number, amount=amount))
