import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from bot.db import delete_meal, get_meal_by_number, get_meal_contributions, update_contribution_amount
from bot.i18n import t
from bot.handlers._helpers import require_group, require_family, reply_ephemeral


async def undo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /undo — removes the user's last action."""
    if not await require_group(update, context):
        return
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    last_action = context.user_data.get("last_action")
    if not last_action:
        await reply_ephemeral(update, context, t("undo_nothing", lang))
        return

    # Verify the action belongs to this trip (user_data is global per user)
    if last_action.get("trip_id") != trip["id"]:
        await reply_ephemeral(update, context, t("undo_nothing", lang))
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
    await reply_ephemeral(update, context, t("undo_success", lang))


async def deletemeal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /deletemeal <meal#> — only creator can delete."""
    if not await require_group(update, context):
        return
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    if not context.args:
        await reply_ephemeral(update, context, t("usage_deletemeal", lang))
        return

    try:
        meal_number = int(context.args[0].lstrip("#"))
    except ValueError:
        await reply_ephemeral(update, context, t("usage_deletemeal", lang))
        return

    db_path = context.bot_data["db_path"]
    meal = await get_meal_by_number(db_path, trip["id"], meal_number)
    if not meal:
        await reply_ephemeral(update, context, t("meal_not_found", lang, number=meal_number))
        return

    # Check if this family is the original creator (first contributor) or meal has no contributions
    contributions = await get_meal_contributions(db_path, meal["id"])
    if contributions and contributions[0]["family_id"] != family["id"]:
        await reply_ephemeral(update, context, t("meal_delete_denied", lang))
        return

    meal_name = meal["name"]
    await delete_meal(db_path, meal["id"])
    await reply_ephemeral(update, context, t("meal_deleted", lang, number=meal_number, name=meal_name))


async def editmeal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /editmeal <meal#> <new amount> — update your own contribution."""
    if not await require_group(update, context):
        return
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    if not context.args or len(context.args) < 2:
        await reply_ephemeral(update, context, t("usage_editmeal", lang))
        return

    try:
        meal_number = int(context.args[0].lstrip("#"))
        amount = float(context.args[1])
    except (ValueError, IndexError):
        await reply_ephemeral(update, context, t("usage_editmeal", lang))
        return

    if amount < 0:
        await reply_ephemeral(update, context, t("usage_editmeal", lang))
        return

    db_path = context.bot_data["db_path"]
    meal = await get_meal_by_number(db_path, trip["id"], meal_number)
    if not meal:
        await reply_ephemeral(update, context, t("meal_not_found", lang, number=meal_number))
        return

    contributions = await get_meal_contributions(db_path, meal["id"])
    if not any(c["family_id"] == family["id"] for c in contributions):
        await reply_ephemeral(update, context, t("no_contribution_to_edit", lang, number=meal_number))
        return

    if amount == 0:
        # Remove this family's contribution(s) from the meal
        import aiosqlite
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "DELETE FROM meal_contributions WHERE meal_id = ? AND family_id = ?",
                (meal["id"], family["id"]),
            )
            await db.commit()
        await reply_ephemeral(update, context, t("contribution_removed", lang, number=meal_number, name=meal["name"]))
    else:
        # Consolidate: delete all contributions for this family, insert one with new amount
        import aiosqlite
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "DELETE FROM meal_contributions WHERE meal_id = ? AND family_id = ?",
                (meal["id"], family["id"]),
            )
            await db.execute(
                "INSERT INTO meal_contributions (meal_id, family_id, amount) VALUES (?, ?, ?)",
                (meal["id"], family["id"], amount),
            )
            await db.commit()
        await reply_ephemeral(update, context, t("meal_edited", lang, number=meal_number, amount=amount))


async def delete_meal_prompt_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle tap on delete event button (delmeal_prompt_{meal_id})."""
    query = update.callback_query
    await query.answer()

    data = query.data
    try:
        meal_id = int(data.replace("delmeal_prompt_", ""))
    except ValueError:
        return

    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    from bot.db import get_active_trip, get_family, get_meals, get_meal_contributions, delete_meal
    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        return
    family = await get_family(db_path, trip["id"], user_id)
    lang = family.get("language", "en") if family else "en"

    meals = await get_meals(db_path, trip["id"])
    meal = next((m for m in meals if m["id"] == meal_id), None)
    if not meal:
        return

    contributions = await get_meal_contributions(db_path, meal_id)
    total_paid = sum(c["amount"] for c in contributions)

    if total_paid <= 0:
        # No payments logged — delete event immediately
        await delete_meal(db_path, meal_id)
        msg_text = t("meal_deleted", lang, number=meal["meal_number"], name=meal["name"])
        await query.edit_message_text(msg_text, parse_mode="Markdown")
        return

    # Warning: Event has payments logged — ask for explicit confirmation
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    buttons = [
        [InlineKeyboardButton(t("btn_confirm_delmeal", lang), callback_data=f"delmeal_confirm_{meal_id}")],
        [InlineKeyboardButton(t("btn_back_to_list", lang), callback_data="menu_delete_meal")],
    ]

    warn_msg = t("delmeal_warning", lang, number=meal["meal_number"], name=meal["name"], total=total_paid)
    await query.edit_message_text(warn_msg, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")


async def delete_meal_confirm_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle explicit confirmed deletion of an event and all associated payments (delmeal_confirm_{meal_id})."""
    query = update.callback_query
    await query.answer()

    data = query.data
    try:
        meal_id = int(data.replace("delmeal_confirm_", ""))
    except ValueError:
        return

    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    from bot.db import get_active_trip, get_family, get_meals, get_meal_contributions, delete_meal
    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        return
    family = await get_family(db_path, trip["id"], user_id)
    lang = family.get("language", "en") if family else "en"

    meals = await get_meals(db_path, trip["id"])
    meal = next((m for m in meals if m["id"] == meal_id), None)
    if not meal:
        return

    contributions = await get_meal_contributions(db_path, meal_id)
    total_paid = sum(c["amount"] for c in contributions)

    await delete_meal(db_path, meal_id)

    msg_text = t("meal_deleted_with_payments", lang, number=meal["meal_number"], name=meal["name"], total=total_paid)
    await query.edit_message_text(msg_text, parse_mode="Markdown")
