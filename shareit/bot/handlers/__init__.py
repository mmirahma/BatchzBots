"""Register all command handlers with the bot application."""

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from bot.handlers.trip import newtrip_handler, endtrip_handler, status_handler
from bot.handlers.family import join_handler, join_callback_handler
from bot.handlers.meal import meal_handler, contribute_handler, contribute_callback_handler, contribute_amount_handler, skip_handler, skip_callback_handler
from bot.handlers.expense import expense_handler
from bot.handlers.settle import settle_handler
from bot.handlers.corrections import undo_handler, deletemeal_handler, editmeal_handler
from bot.handlers.utility import lang_handler, help_handler
from bot.handlers.info import meals_handler, history_handler


def register_handlers(app: Application) -> None:
    """Register all command and callback handlers."""
    app.add_handler(CommandHandler("newtrip", newtrip_handler))
    app.add_handler(CommandHandler("endtrip", endtrip_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("join", join_handler))
    app.add_handler(CallbackQueryHandler(join_callback_handler, pattern=r"^join_"))
    app.add_handler(CommandHandler("meal", meal_handler))
    app.add_handler(CommandHandler("contribute", contribute_handler))
    app.add_handler(CallbackQueryHandler(contribute_callback_handler, pattern=r"^contrib_"))
    app.add_handler(CommandHandler("skip", skip_handler))
    app.add_handler(CallbackQueryHandler(skip_callback_handler, pattern=r"^skip_"))
    app.add_handler(CommandHandler("expense", expense_handler))
    app.add_handler(CommandHandler("settle", settle_handler))
    app.add_handler(CommandHandler("meals", meals_handler))
    app.add_handler(CommandHandler("history", history_handler))
    app.add_handler(CommandHandler("undo", undo_handler))
    app.add_handler(CommandHandler("deletemeal", deletemeal_handler))
    app.add_handler(CommandHandler("editmeal", editmeal_handler))
    app.add_handler(CommandHandler("lang", lang_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("start", help_handler))

    # Plain text handler for pending contribute amount (must be last — lowest priority)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, contribute_amount_handler))
