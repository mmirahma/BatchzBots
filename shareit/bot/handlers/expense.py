from telegram import Update
from telegram.ext import ContextTypes

from bot.db import add_shared_expense
from bot.i18n import t
from bot.handlers._helpers import require_group, require_family, reply_ephemeral


async def expense_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /expense <description> <amount> command."""
    if not await require_group(update, context):
        return
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    if not context.args or len(context.args) < 2:
        await reply_ephemeral(update, context, t("usage_expense", lang))
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
