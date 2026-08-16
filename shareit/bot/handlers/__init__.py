from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, TypeHandler, ContextTypes, filters

from bot.handlers._helpers import schedule_user_message_deletion, schedule_message_deletion


async def global_user_message_logger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global pre-handler to schedule self-destruction for all user text messages and inline button interactions (60s)."""
    if update.effective_message and update.effective_chat and not update.callback_query:
        if update.effective_user and not update.effective_user.is_bot:
            schedule_message_deletion(update.effective_chat.id, update.effective_message.message_id, context)
    elif update.callback_query and update.callback_query.message and update.effective_chat:
        data = update.callback_query.data or ""
        if data not in ("menu_settle", "menu_status"):
            schedule_message_deletion(update.effective_chat.id, update.callback_query.message.message_id, context)
from bot.handlers.menu import menu_handler, menu_callback_handler, text_menu_handler
from bot.handlers.trip import newtrip_handler, endtrip_handler, status_handler
from bot.handlers.family import join_handler, join_callback_handler, join_meal_attendance_callback_handler
from bot.handlers.meal import (
    meal_handler, contribute_handler, contribute_callback_handler, contribute_amount_handler,
    skip_handler, skip_callback_handler, meal_preset_callback_handler, meal_amount_callback_handler,
    meal_skip_desc_callback_handler,
)
from bot.handlers.expense import (
    expense_handler, expense_preset_callback_handler, expense_amount_callback_handler,
    expense_menu_callback_handler,
)
from bot.handlers.settle import settle_handler
from bot.handlers.corrections import undo_handler, deletemeal_handler, editmeal_handler
from bot.handlers.utility import lang_handler, help_handler, lang_callback_handler, export_handler
from bot.handlers.info import meals_handler, history_handler, my_share_handler


async def global_user_message_logger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global pre-handler to schedule self-destruction for all incoming user messages (60s)."""
    schedule_user_message_deletion(update, context)


def register_handlers(app: Application) -> None:
    """Register all command and callback handlers."""
    app.add_handler(TypeHandler(Update, global_user_message_logger), group=-1)
    app.add_handler(CommandHandler("menu", menu_handler))
    app.add_handler(CommandHandler("start", menu_handler))
    app.add_handler(CommandHandler("newtrip", newtrip_handler))
    app.add_handler(CommandHandler("endtrip", endtrip_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("join", join_handler))
    app.add_handler(CommandHandler("meal", meal_handler))
    app.add_handler(CommandHandler("contribute", contribute_handler))
    app.add_handler(CommandHandler("skip", skip_handler))
    app.add_handler(CommandHandler("expense", expense_handler))
    app.add_handler(CommandHandler("settle", settle_handler))
    app.add_handler(CommandHandler("meals", meals_handler))
    app.add_handler(CommandHandler("myshare", my_share_handler))
    app.add_handler(CommandHandler("history", history_handler))
    app.add_handler(CommandHandler("undo", undo_handler))
    app.add_handler(CommandHandler("deletemeal", deletemeal_handler))
    app.add_handler(CommandHandler("editmeal", editmeal_handler))
    app.add_handler(CommandHandler("lang", lang_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("export", export_handler))

    # Callback Query Handlers
    app.add_handler(CallbackQueryHandler(menu_callback_handler, pattern=r"^menu_"))
    app.add_handler(CallbackQueryHandler(join_callback_handler, pattern=r"^join_"))
    app.add_handler(CallbackQueryHandler(join_meal_attendance_callback_handler, pattern=r"^jmat_"))
    app.add_handler(CallbackQueryHandler(contribute_callback_handler, pattern=r"^contrib_"))
    app.add_handler(CallbackQueryHandler(skip_callback_handler, pattern=r"^skip_"))
    app.add_handler(CallbackQueryHandler(meal_preset_callback_handler, pattern=r"^pmeal_"))
    app.add_handler(CallbackQueryHandler(meal_skip_desc_callback_handler, pattern=r"^pdesc_skip$"))
    app.add_handler(CallbackQueryHandler(meal_amount_callback_handler, pattern=r"^pamt_"))
    app.add_handler(CallbackQueryHandler(expense_menu_callback_handler, pattern=r"^exp_"))
    app.add_handler(CallbackQueryHandler(expense_preset_callback_handler, pattern=r"^pexp_"))
    app.add_handler(CallbackQueryHandler(expense_amount_callback_handler, pattern=r"^pexpamt_"))
    app.add_handler(CallbackQueryHandler(lang_callback_handler, pattern=r"^plang_"))
    app.add_handler(CallbackQueryHandler(export_handler, pattern=r"^export_excel$"))

    # Plain text handler for bottom ReplyKeyboard buttons & pending inputs (must be last — lowest priority)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_menu_handler))

