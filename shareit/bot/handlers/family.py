from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db import (
    get_active_trip, get_family, get_family_by_id, get_families, add_family, update_family_weight,
    assign_member_to_family,
    get_meals, get_meal_absences, add_meal_absence, remove_meal_absence,
)
from bot.i18n import t
from bot.handlers._helpers import (
    get_lang, require_group, reply_ephemeral, refresh_callback_message_deletion,
    require_unlocked_trip,
)

WEIGHT_OPTIONS = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5]


async def prompt_join_family_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, trip: dict, lang: str) -> None:
    """Prompt user to select an existing family to join or create a new family."""
    db_path = context.bot_data["db_path"]
    families = await get_families(db_path, trip["id"])

    if not families:
        # No families yet: directly show weight selection buttons
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
        msg_text = f"🏕 *{trip['name']}*\n\n{t('join_select_weight', lang)}"
        if update.callback_query:
            await update.callback_query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
            refresh_callback_message_deletion(update, context)
        else:
            await reply_ephemeral(update, context, msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        return

    # Existing families present: list each family, and as the LAST option, 'Create New Family'
    buttons = []
    for fam in families:
        label = f"👨‍👩‍👧 {fam['name']} (w={fam['weight']})"
        buttons.append([InlineKeyboardButton(label, callback_data=f"join_existing_fam_{fam['id']}")])

    buttons.append([InlineKeyboardButton(t("btn_create_new_family", lang), callback_data="join_new_family_prompt")])

    msg_text = t("join_choose_family_title", lang, trip_name=trip["name"])
    if update.callback_query:
        await update.callback_query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        refresh_callback_message_deletion(update, context)
    else:
        await reply_ephemeral(update, context, msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")


async def join_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /join [weight] command. Shows list of families (and create option) if no weight given."""
    if not await require_group(update, context):
        return
    if not await require_unlocked_trip(update, context):
        return
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await reply_ephemeral(update, context, t("no_active_trip", lang))
        return

    if not context.args:
        await prompt_join_family_choice(update, context, trip, lang)
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
    """Handle inline button press for family selection, create new family prompt, or weight selection."""
    query = update.callback_query
    await query.answer()

    if not await require_unlocked_trip(update, context):
        return

    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    lang = await get_lang(update, context)

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        return

    data = query.data

    # A. User clicked 'Create New Family' -> show weight buttons
    if data == "join_new_family_prompt":
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
        buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data="join_menu_prompt")])
        await query.edit_message_text(t("join_select_weight", lang), reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        refresh_callback_message_deletion(update, context)
        return

    # B. Back to join selection
    if data == "join_menu_prompt":
        await prompt_join_family_choice(update, context, trip, lang)
        return

    # C. User clicked an existing family to join
    if data.startswith("join_existing_fam_"):
        family_id = int(data.replace("join_existing_fam_", ""))
        await assign_member_to_family(db_path, trip["id"], family_id, user_id, chat_id)
        target_fam = await get_family_by_id(db_path, family_id)
        fam_name = target_fam["name"] if target_fam else "Family"
        await query.edit_message_text(
            t("joined_family_success", lang, family_name=fam_name),
            parse_mode="Markdown",
        )
        refresh_callback_message_deletion(update, context)

        from bot.handlers.menu import get_reply_keyboard
        from bot.handlers._helpers import is_admin_or_owner, schedule_message_deletion
        is_admin = await is_admin_or_owner(context.bot, chat_id, update.effective_user)
        reply_kbd = get_reply_keyboard(lang, is_joined=True, is_admin=is_admin)
        msg = await context.bot.send_message(chat_id=chat_id, text=t("menu_title", lang), reply_markup=reply_kbd, parse_mode="Markdown")
        schedule_message_deletion(chat_id, msg.message_id, context)
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
    if existing:
        await update_family_weight(db_path, existing["id"], weight)
        family = existing
    else:
        family_id = await add_family(db_path, trip["id"], name, weight, user_id)
        family = await get_family(db_path, trip["id"], user_id)

    # Move to meal attendance toggle flow
    context.user_data.pop("join_attendance_state", None)
    await prompt_join_meal_toggles(update, context)


async def _do_join(update: Update, context: ContextTypes.DEFAULT_TYPE, db_path: str, trip: dict, weight: float) -> None:
    """Execute the join logic for slash command with weight arg."""
    user_id = update.effective_user.id
    user = update.effective_user
    name = user.full_name + "'s family"

    existing = await get_family(db_path, trip["id"], user_id)
    if existing:
        await update_family_weight(db_path, existing["id"], weight)
    else:
        await add_family(db_path, trip["id"], name, weight, user_id)

    context.user_data.pop("join_attendance_state", None)
    await prompt_join_meal_toggles(update, context)


async def prompt_join_meal_toggles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show list of all meals with inline toggle buttons (✅ / 🚫) and a Done button."""
    from telegram.error import BadRequest

    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    lang = await get_lang(update, context)

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        return

    family = await get_family(db_path, trip["id"], user_id)
    if not family:
        return

    meals = await get_meals(db_path, trip["id"])
    if not meals:
        await show_join_summary(update, context, family, family["weight"], trip)
        return

    if "join_attendance_state" not in context.user_data:
        state = {}
        for m in meals:
            absences = await get_meal_absences(db_path, m["id"])
            state[m["id"]] = family["id"] not in absences
        context.user_data["join_attendance_state"] = state
    else:
        state = context.user_data["join_attendance_state"]

    buttons = []
    for m in meals:
        is_attending = state.get(m["id"], True)
        icon = "✅" if is_attending else "🚫"
        label = f"{icon} #{m['meal_number']} {m['name']}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"jmat_toggle_{m['id']}")])

    buttons.append([InlineKeyboardButton(t("btn_done", lang), callback_data="jmat_done")])
    reply_markup = InlineKeyboardMarkup(buttons)
    text = t("join_meal_toggle_title", lang)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
            refresh_callback_message_deletion(update, context)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                pass
            else:
                raise
    else:
        await reply_ephemeral(update, context, text, reply_markup=reply_markup, parse_mode="Markdown")


async def join_meal_attendance_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle toggle button tap (jmat_toggle_X) or Done button tap (jmat_done)."""
    query = update.callback_query
    await query.answer()

    if not await require_unlocked_trip(update, context):
        return

    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        return

    family = await get_family(db_path, trip["id"], user_id)
    if not family:
        return

    data = query.data

    if data == "jmat_done":
        # Finalize input: commit all toggles to DB
        state = context.user_data.pop("join_attendance_state", {})
        meals = await get_meals(db_path, trip["id"])
        for m in meals:
            is_attending = state.get(m["id"], True)
            if is_attending:
                await remove_meal_absence(db_path, m["id"], family["id"])
            else:
                await add_meal_absence(db_path, m["id"], family["id"])

        await show_join_summary(update, context, family, family["weight"], trip)
        return

    if data.startswith("jmat_toggle_"):
        meal_id = int(data.replace("jmat_toggle_", ""))
        state = context.user_data.get("join_attendance_state", {})
        state[meal_id] = not state.get(meal_id, True)
        context.user_data["join_attendance_state"] = state
        await prompt_join_meal_toggles(update, context)


async def show_join_summary(update: Update, context: ContextTypes.DEFAULT_TYPE, family: dict, weight: float, trip: dict) -> None:
    """Render the final Family Setup Summary table."""
    db_path = context.bot_data["db_path"]
    lang = await get_lang(update, context)

    meals = await get_meals(db_path, trip["id"])
    family_name = family["name"] if family else "Family"

    text = t("join_summary_title", lang, family_name=family_name, weight=weight)

    if not meals:
        text += t("join_summary_no_meals", lang)
    else:
        text += "\n\n" + t("join_summary_table_header", lang) + "\n"
        for m in meals:
            absences = await get_meal_absences(db_path, m["id"])
            status = "🚫 Skipped" if family and family["id"] in absences else "✅ Joined"
            text += f"• *#{m['meal_number']} {m['name']}*: {status}\n"

    menu_button = InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_open_menu", lang), callback_data="menu_open")]])

    from datetime import timedelta
    from bot.handlers._helpers import _delete_message_job, EPHEMERAL_DELETE_SECONDS

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=menu_button, parse_mode="Markdown")
        if update.effective_chat and update.callback_query.message:
            chat_id = update.effective_chat.id
            msg_id = update.callback_query.message.message_id
            context.job_queue.run_once(
                _delete_message_job,
                when=timedelta(seconds=EPHEMERAL_DELETE_SECONDS),
                data={"chat_id": chat_id, "message_id": msg_id},
                name=f"ephemeral_{chat_id}_{msg_id}",
            )
    else:
        await reply_ephemeral(update, context, text, reply_markup=menu_button, parse_mode="Markdown")
