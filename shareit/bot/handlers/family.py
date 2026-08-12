from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db import get_active_trip, get_family, add_family, update_family_weight
from bot.i18n import t
from bot.handlers._helpers import get_lang, require_group, reply_ephemeral

WEIGHT_OPTIONS = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5]


async def join_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /join [weight] command. Shows buttons if no weight given."""
    if not await require_group(update, context):
        return
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await reply_ephemeral(update, context, t("no_active_trip", lang))
        return

    if not context.args:
        # Show weight selection buttons
        buttons = []
        row = []
        for w in WEIGHT_OPTIONS:
            label = str(w) if w != int(w) else str(int(w))
            row.append(InlineKeyboardButton(label, callback_data=f"join_{w}"))
            if len(row) == 5:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        await update.effective_message.reply_text(
            t("join_select_weight", lang), reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    try:
        weight = float(context.args[0])
    except ValueError:
        await reply_ephemeral(update, context, t("usage_join", lang))
        return

    if weight <= 0:
        await reply_ephemeral(update, context, t("usage_join", lang))
        return

    await _do_join(update, context, db_path, trip, weight)


async def join_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button press for weight selection."""
    from datetime import timedelta
    from bot.handlers._helpers import _delete_message_job, EPHEMERAL_DELETE_SECONDS

    query = update.callback_query
    await query.answer()

    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        return

    try:
        weight = float(query.data.replace("join_", ""))
    except ValueError:
        return
    if weight <= 0:
        return

    user = update.effective_user
    name = user.full_name + "'s family"

    existing = await get_family(db_path, trip["id"], user_id)
    lang = existing.get("language", "en") if existing else "en"

    if existing:
        await update_family_weight(db_path, existing["id"], weight)
        text = t("family_updated", lang, name=existing["name"], weight=weight)
    else:
        await add_family(db_path, trip["id"], name, weight, user_id)
        text = t("family_joined", lang, name=name, weight=weight)

    menu_button = InlineKeyboardMarkup([[InlineKeyboardButton("🏕 Open Main Menu", callback_data="menu_open")]])
    await query.edit_message_text(text, reply_markup=menu_button)
    # Schedule deletion
    context.job_queue.run_once(
        _delete_message_job,
        when=timedelta(seconds=EPHEMERAL_DELETE_SECONDS),
        data={"chat_id": chat_id, "message_id": query.message.message_id},
        name=f"ephemeral_{chat_id}_{query.message.message_id}",
    )


async def _do_join(update, context, db_path, trip, weight):
    """Execute the join logic."""
    user_id = update.effective_user.id
    lang = await get_lang(update, context)
    user = update.effective_user
    name = user.full_name + "'s family"

    existing = await get_family(db_path, trip["id"], user_id)
    if existing:
        await update_family_weight(db_path, existing["id"], weight)
        await reply_ephemeral(update, context, t("family_updated", lang, name=existing["name"], weight=weight))
    else:
        await add_family(db_path, trip["id"], name, weight, user_id)
        await reply_ephemeral(update, context, t("family_joined", lang, name=name, weight=weight))
