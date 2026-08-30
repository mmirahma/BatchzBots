from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db import add_shared_expense
from bot.i18n import t
from bot.handlers._helpers import (
    require_group, require_family, reply_ephemeral, get_lang,
    require_unlocked_trip,
)

EXPENSE_PRESETS = [
    [("Firewood 🪵", "pexp_Firewood"), ("Park Entry 🏞", "pexp_Park Entry")],
    [("Groceries 🛒", "pexp_Groceries"), ("Ice 🧊", "pexp_Ice")],
    [("Campsite Fee ⛺️", "pexp_Campsite Fee"), ("Gas / Fuel ⛽️", "pexp_Gas")],
]

AMOUNT_PRESETS = [10.0, 20.0, 30.0, 50.0, 100.0]


async def expense_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /expense <description> <amount> command."""
    if not await require_group(update, context):
        return
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    if not context.args or len(context.args) < 2:
        await prompt_expense_preset(update, context)
        return

    try:
        amount = float(context.args[-1])
    except ValueError:
        await reply_ephemeral(update, context, t("usage_expense", lang))
        return

    if amount <= 0:
        await reply_ephemeral(update, context, t("usage_expense", lang))
        return

    description = " ".join(context.args[:-1])
    db_path = context.bot_data["db_path"]
    expense_id = await add_shared_expense(db_path, trip["id"], family["id"], description, amount)

    context.user_data["last_action"] = {"type": "expense", "expense_id": expense_id, "trip_id": trip["id"]}
    await reply_ephemeral(update, context,
        t("expense_logged", lang, description=description, amount=amount, family=family["name"])
    )


async def prompt_expense_preset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user with unified expense menu: existing meals, new meal, or general expense."""
    if not await require_unlocked_trip(update, context):
        return
    from bot.db import get_active_trip, get_meals
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id

    trip = await get_active_trip(db_path, chat_id)
    meals = await get_meals(db_path, trip["id"]) if trip else []

    buttons = []
    # Add buttons for existing meals if any
    for m in meals:
        label = f"💳 #{m['meal_number']} {m['name']}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"contrib_{m['meal_number']}")])

    buttons.append([InlineKeyboardButton(t("btn_new_meal_expense", lang), callback_data="exp_new_meal")])
    buttons.append([InlineKeyboardButton(t("btn_general_expense", lang), callback_data="exp_general")])
    buttons.append([InlineKeyboardButton(t("btn_targeted_expense", lang), callback_data="exp_targeted")])

    title = t("expense_menu_title", lang)
    if update.callback_query:
        await update.callback_query.edit_message_text(title, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
    else:
        await reply_ephemeral(update, context, title, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")


async def expense_menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle choice between New Meal Expense, General Shared Expense, and Specific Family Expense."""
    query = update.callback_query
    await query.answer()

    if not await require_unlocked_trip(update, context):
        return

    data = query.data

    if data == "exp_new_meal":
        from bot.handlers.meal import prompt_meal_preset
        await prompt_meal_preset(update, context)
    elif data == "exp_general":
        await prompt_general_expense_categories(update, context)
    elif data == "exp_targeted":
        await prompt_targeted_expense_desc(update, context)


async def prompt_targeted_expense_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user to type description for a specific targeted expense."""
    import time as _time
    lang = await get_lang(update, context)
    chat_id = update.effective_chat.id

    context.user_data["pending_targeted_expense_desc"] = {
        "chat_id": chat_id,
        "timestamp": _time.time(),
    }

    text = t("targeted_ask_desc", lang)
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown")
    else:
        await reply_ephemeral(update, context, text, parse_mode="Markdown")


async def prompt_targeted_expense_family(update: Update, context: ContextTypes.DEFAULT_TYPE, desc: str, amount: float) -> None:
    """Show interactive list of families with weights to configure custom expense allocation."""
    from bot.db import get_active_trip, get_families
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        return
    families = await get_families(db_path, trip["id"])

    # Initialize weights dictionary in user_data if not set yet
    if "pending_targeted_expense_weights" not in context.user_data or context.user_data.get("pending_targeted_desc") != desc:
        context.user_data["pending_targeted_desc"] = desc
        context.user_data["pending_targeted_amount"] = amount
        # By default, all families participate with their default trip weight
        context.user_data["pending_targeted_expense_weights"] = {f["id"]: f["weight"] for f in families}

    weights_map = context.user_data["pending_targeted_expense_weights"]

    buttons = []
    for f in families:
        fid = f["id"]
        w = weights_map.get(fid, f["weight"])
        if w > 0:
            label = f"✅ {f['name']} (w={w})"
        else:
            label = f"🚫 {f['name']} (Excluded)"
        cb_data = f"ptgtfam_{fid}"
        buttons.append([InlineKeyboardButton(label, callback_data=cb_data)])

    buttons.append([InlineKeyboardButton(t("btn_save_expense", lang), callback_data="ptgt_save")])

    msg_text = t("targeted_setup_title", lang, desc=desc, amount=amount)
    if update.callback_query:
        await update.callback_query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
    else:
        await reply_ephemeral(update, context, msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")


async def targeted_expense_family_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle clicking on a family button to open weight adjustment menu or save expense."""
    query = update.callback_query
    await query.answer()

    data = query.data
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if data == "ptgt_save":
        # Save the expense with custom weights
        desc = context.user_data.get("pending_targeted_desc", "Custom Expense")
        amount = context.user_data.get("pending_targeted_amount", 0.0)
        weights_map = context.user_data.pop("pending_targeted_expense_weights", {})
        context.user_data.pop("pending_targeted_desc", None)
        context.user_data.pop("pending_targeted_amount", None)

        from bot.db import (
            get_active_trip, get_family, get_family_by_id, get_families,
            create_grouping, add_or_update_grouping_member, add_shared_expense
        )
        trip = await get_active_trip(db_path, chat_id)
        if not trip:
            return
        payer_fid = context.user_data.pop("pending_targeted_payer_fid", None)
        if payer_fid:
            payer_family = await get_family_by_id(db_path, payer_fid)
        else:
            payer_family = await get_family(db_path, trip["id"], user_id)
        if not payer_family:
            return
        families = await get_families(db_path, trip["id"])

        # Check active members
        active_fids = [fid for fid, w in weights_map.items() if w > 0]
        if not active_fids:
            await query.edit_message_text("⚠️ At least one family must be included in the expense!")
            return

        # Create grouping and set custom weights
        grouping_id = await create_grouping(db_path, trip["id"], f"Custom Expense: {desc}")
        total_w = sum(weights_map[fid] for fid in active_fids)
        breakdown_lines = []

        for f in families:
            fid = f["id"]
            w = weights_map.get(fid, 0.0)
            if w > 0:
                await add_or_update_grouping_member(db_path, grouping_id, fid, weight=w, is_active=1)
                cost_share = amount * (w / total_w)
                breakdown_lines.append(f"• *{f['name']}* (w={w}): *${cost_share:.2f}*")
            else:
                await add_or_update_grouping_member(db_path, grouping_id, fid, weight=0.0, is_active=0)
                breakdown_lines.append(f"• *{f['name']}*: 🚫 Skipped ($0.00)")

        expense_id = await add_shared_expense(
            db_path, trip["id"], payer_family["id"], desc, amount, grouping_id=grouping_id
        )

        context.user_data["last_action"] = {"type": "expense", "expense_id": expense_id, "trip_id": trip["id"]}
        breakdown_str = "\n".join(breakdown_lines)
        await query.edit_message_text(
            t("targeted_logged_summary", lang, desc=desc, amount=amount, payer=payer_family["name"], breakdown=breakdown_str),
            parse_mode="Markdown",
        )
        if update.effective_chat and query.message:
            from datetime import timedelta
            from bot.handlers._helpers import _delete_message_job, EPHEMERAL_DELETE_SECONDS
            chat_id = update.effective_chat.id
            msg_id = query.message.message_id
            context.job_queue.run_once(
                _delete_message_job,
                when=timedelta(seconds=EPHEMERAL_DELETE_SECONDS),
                data={"chat_id": chat_id, "message_id": msg_id},
                name=f"ephemeral_{chat_id}_{msg_id}",
            )
        return

    if data.startswith("ptgtfam_"):
        target_fid = int(data.replace("ptargetfam_", "").replace("ptgtfam_", ""))
        from bot.db import get_active_trip, get_families
        trip = await get_active_trip(db_path, chat_id)
        families = await get_families(db_path, trip["id"]) if trip else []
        target_family = next((f for f in families if f["id"] == target_fid), None)
        if not target_family:
            return

        weights_map = context.user_data.get("pending_targeted_expense_weights", {})
        curr_w = weights_map.get(target_fid, target_family["weight"])

        # Display weight choice buttons for this family
        WEIGHT_OPTIONS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
        buttons = []
        row = []
        for w in WEIGHT_OPTIONS:
            label = f"{w}" if w != int(w) else f"{int(w)}"
            if w == curr_w:
                label = f"✅ {label}"
            cb_data = f"ptgtsetw_{target_fid}_{w}"
            row.append(InlineKeyboardButton(label, callback_data=cb_data))
            if len(row) == 4:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        # Add Custom Weight and Exclude buttons
        buttons.append([
            InlineKeyboardButton(t("btn_custom_weight", lang), callback_data=f"ptgtcustw_{target_fid}"),
            InlineKeyboardButton(t("btn_exclude_family", lang), callback_data=f"ptgtsetw_{target_fid}_0.0"),
        ])
        buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data="ptgt_back")])

        msg_text = t("targeted_set_weight_title", lang, family_name=target_family["name"], weight=curr_w)
        await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        return

    if data.startswith("ptgtcustw_"):
        import time as _time
        target_fid = int(data.replace("ptgtcustw_", ""))
        from bot.db import get_active_trip, get_families
        trip = await get_active_trip(db_path, chat_id)
        families = await get_families(db_path, trip["id"]) if trip else []
        target_family = next((f for f in families if f["id"] == target_fid), None)
        if not target_family:
            return

        context.user_data["pending_targeted_custom_weight"] = {
            "family_id": target_fid,
            "family_name": target_family["name"],
            "chat_id": chat_id,
            "timestamp": _time.time(),
        }
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_back", lang), callback_data=f"ptgtfam_{target_fid}")]])
        msg_text = t("prompt_custom_member_weight", lang, name=target_family["name"])
        await query.edit_message_text(msg_text, reply_markup=back_btn, parse_mode="Markdown")
        return

    if data == "ptgt_back":
        desc = context.user_data.get("pending_targeted_desc", "Custom Expense")
        amount = context.user_data.get("pending_targeted_amount", 0.0)
        await prompt_targeted_expense_family(update, context, desc, amount)
        return

    if data.startswith("ptgtsetw_"):
        parts = data.split("_")
        target_fid = int(parts[1])
        new_w = float(parts[2])

        if "pending_targeted_expense_weights" not in context.user_data:
            context.user_data["pending_targeted_expense_weights"] = {}
        context.user_data["pending_targeted_expense_weights"][target_fid] = new_w

        desc = context.user_data.get("pending_targeted_desc", "Custom Expense")
        amount = context.user_data.get("pending_targeted_amount", 0.0)
        await prompt_targeted_expense_family(update, context, desc, amount)


async def pending_targeted_weight_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle plain text number entered for custom family weight in targeted expense flow."""
    if not update.message or not update.message.text:
        return False
    pending = context.user_data.get("pending_targeted_custom_weight")
    if not pending:
        return False
    if update.effective_chat.id != pending.get("chat_id"):
        return False
    import time as _time
    if _time.time() - pending.get("timestamp", 0) > 180:
        context.user_data.pop("pending_targeted_custom_weight", None)
        return False

    from bot.handlers.edit_expenses import _parse_amount
    text = update.message.text.strip()
    weight = _parse_amount(text)
    lang = await get_lang(update, context)

    if weight is None or weight <= 0:
        await reply_ephemeral(update, context, t("invalid_weight", lang))
        return True

    state = context.user_data.pop("pending_targeted_custom_weight")
    target_fid = state["family_id"]

    if "pending_targeted_expense_weights" not in context.user_data:
        context.user_data["pending_targeted_expense_weights"] = {}
    context.user_data["pending_targeted_expense_weights"][target_fid] = weight

    desc = context.user_data.get("pending_targeted_desc", "Custom Expense")
    amount = context.user_data.get("pending_targeted_amount", 0.0)

    await prompt_targeted_expense_family(update, context, desc, amount)
    return True


async def targeted_amount_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle amount preset selection for targeted expense."""
    query = update.callback_query
    await query.answer()
    try:
        amount = float(query.data.replace("ptgtamt_", ""))
    except ValueError:
        return

    pending_tgt_amt = context.user_data.pop("pending_targeted_expense_amt_prompt", None)
    desc = pending_tgt_amt.get("desc", "Specific Expense") if pending_tgt_amt else "Specific Expense"
    await prompt_targeted_expense_family(update, context, desc, amount)


async def prompt_general_expense_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show general shared expense category preset buttons and enable direct typed custom description."""
    import time as _time
    lang = await get_lang(update, context)
    chat_id = update.effective_chat.id

    context.user_data["pending_expense_prompt"] = {
        "category": "Custom",
        "chat_id": chat_id,
        "timestamp": _time.time(),
    }

    buttons = [
        [InlineKeyboardButton(label, callback_data=cb) for label, cb in row]
        for row in EXPENSE_PRESETS
    ]
    await update.callback_query.edit_message_text(
        t("expense_select_preset", lang),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )


async def expense_preset_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle expense preset category selection."""
    import time as _time
    query = update.callback_query
    await query.answer()
    category = query.data.replace("pexp_", "")
    lang = await get_lang(update, context)
    chat_id = update.effective_chat.id

    context.user_data.pop("pending_expense_prompt", None)
    context.user_data["pending_expense_desc"] = category
    context.user_data["pending_expense_amount_prompt"] = {
        "desc": category,
        "chat_id": chat_id,
        "timestamp": _time.time(),
    }

    buttons = []
    row = []
    for amt in AMOUNT_PRESETS:
        label = f"${int(amt)}"
        row.append(InlineKeyboardButton(label, callback_data=f"pexpamt_{amt:.2f}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    await query.edit_message_text(
        t("expense_ask_desc", lang, category=category),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )


async def expense_amount_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle expense amount preset selection."""
    query = update.callback_query
    await query.answer()
    try:
        amount = float(query.data.replace("pexpamt_", ""))
    except ValueError:
        return

    description = context.user_data.pop("pending_expense_desc", "Shared Expense")
    context.user_data.pop("pending_expense_amount_prompt", None)
    context.user_data.pop("pending_expense_prompt", None)

    trip, family, lang = await require_family(update, context)
    if not family:
        return

    db_path = context.bot_data["db_path"]
    expense_id = await add_shared_expense(db_path, trip["id"], family["id"], description, amount)

    context.user_data["last_action"] = {"type": "expense", "expense_id": expense_id, "trip_id": trip["id"]}
    await query.edit_message_text(
        t("expense_logged", lang, description=description, amount=amount, family=family["name"])
    )
    if update.effective_chat and query.message:
        from datetime import timedelta
        from bot.handlers._helpers import _delete_message_job, EPHEMERAL_DELETE_SECONDS
        chat_id = update.effective_chat.id
        msg_id = query.message.message_id
        context.job_queue.run_once(
            _delete_message_job,
            when=timedelta(seconds=EPHEMERAL_DELETE_SECONDS),
            data={"chat_id": chat_id, "message_id": msg_id},
            name=f"ephemeral_{chat_id}_{msg_id}",
        )

