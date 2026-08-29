from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ChatMemberHandler, TypeHandler, filters,
)

from bot.handlers._helpers import record_user_activity
from bot.handlers.menu import menu_handler, menu_callback_handler, text_menu_handler, admin_menu_handler
from bot.handlers.trip import newtrip_handler, endtrip_handler, status_handler, resumetrip_handler
from bot.handlers.family import join_handler, join_callback_handler, join_meal_attendance_callback_handler
from bot.handlers.meal import (
    meal_handler, contribute_handler, contribute_callback_handler, contribute_amount_handler,
    skip_handler, skip_callback_handler, meal_preset_callback_handler, meal_amount_callback_handler,
    meal_skip_desc_callback_handler,
)
from bot.handlers.expense import (
    expense_handler, expense_preset_callback_handler, expense_amount_callback_handler,
    expense_menu_callback_handler, targeted_expense_family_callback_handler, targeted_amount_callback_handler,
)
from bot.handlers.settle import settle_handler
from bot.handlers.corrections import (
    undo_handler, deletemeal_handler, editmeal_handler,
    delete_meal_prompt_callback_handler, delete_meal_confirm_callback_handler,
)
from bot.handlers.utility import lang_handler, help_handler, lang_callback_handler, export_handler
from bot.handlers.info import meals_handler, history_handler, my_share_handler
from bot.handlers.members import (
    members_handler,
    member_select_callback_handler,
    member_action_callback_handler,
)


from bot.handlers.edit_expenses import (
    edit_my_expenses_handler,
    edit_expense_select_callback_handler,
    edit_expense_action_callback_handler,
    admin_edit_all_expenses_handler,
    admin_expense_select_callback_handler,
    admin_expense_action_callback_handler,
    admin_log_flow_callback_handler,
)


def register_handlers(app: Application) -> None:
    """Register all command and callback handlers."""
    # Group -1: Global silent recorder capturing users from any update (messages, mentions, replies, joins)
    app.add_handler(TypeHandler(Update, record_user_activity), group=-1)
    app.add_handler(ChatMemberHandler(record_user_activity, ChatMemberHandler.CHAT_MEMBER), group=-1)
    app.add_handler(ChatMemberHandler(record_user_activity, ChatMemberHandler.MY_CHAT_MEMBER), group=-1)

    app.add_handler(CommandHandler("menu", menu_handler))
    app.add_handler(CommandHandler("start", menu_handler))
    app.add_handler(CommandHandler("admin", admin_menu_handler))
    app.add_handler(CommandHandler("newtrip", newtrip_handler))
    app.add_handler(CommandHandler("endtrip", endtrip_handler))
    app.add_handler(CommandHandler("resumetrip", resumetrip_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("join", join_handler))
    app.add_handler(CommandHandler("members", members_handler))
    app.add_handler(CommandHandler("addmembers", members_handler))
    app.add_handler(CommandHandler("meal", meal_handler))
    app.add_handler(CommandHandler("contribute", contribute_handler))
    app.add_handler(CommandHandler("skip", skip_handler))
    app.add_handler(CommandHandler("expense", expense_handler))
    app.add_handler(CommandHandler("editmyexpenses", edit_my_expenses_handler))
    app.add_handler(CommandHandler("adminexpenses", admin_edit_all_expenses_handler))
    app.add_handler(CommandHandler("editexpenses", admin_edit_all_expenses_handler))
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
    app.add_handler(CallbackQueryHandler(member_select_callback_handler, pattern=r"^mem_sel_"))
    app.add_handler(CallbackQueryHandler(member_action_callback_handler, pattern=r"^(mem_list|mem_refresh|mem_done|mem_custom|mem_custw_|mem_setw_|mem_add_|mem_del_|mem_delforce_|mem_custfam_w_)"))
    app.add_handler(CallbackQueryHandler(contribute_callback_handler, pattern=r"^contrib_"))
    app.add_handler(CallbackQueryHandler(skip_callback_handler, pattern=r"^skip_"))
    app.add_handler(CallbackQueryHandler(meal_preset_callback_handler, pattern=r"^pmeal_"))
    app.add_handler(CallbackQueryHandler(meal_skip_desc_callback_handler, pattern=r"^pdesc_skip$"))
    app.add_handler(CallbackQueryHandler(meal_amount_callback_handler, pattern=r"^pamt_"))
    app.add_handler(CallbackQueryHandler(expense_menu_callback_handler, pattern=r"^exp_"))
    app.add_handler(CallbackQueryHandler(expense_preset_callback_handler, pattern=r"^pexp_"))
    app.add_handler(CallbackQueryHandler(expense_amount_callback_handler, pattern=r"^pexpamt_"))
    app.add_handler(CallbackQueryHandler(targeted_expense_family_callback_handler, pattern=r"^(ptargetfam_|ptgtfam_|ptgtsetw_|ptgt_save)"))
    app.add_handler(CallbackQueryHandler(targeted_amount_callback_handler, pattern=r"^ptgtamt_"))
    app.add_handler(CallbackQueryHandler(edit_expense_select_callback_handler, pattern=r"^edexp_(meal|expense)_\d+$"))
    app.add_handler(CallbackQueryHandler(edit_expense_action_callback_handler, pattern=r"^(edexpamt_|edexpdel_|edexp_list)"))
    app.add_handler(CallbackQueryHandler(admin_log_flow_callback_handler, pattern=r"^(admexp_log_prompt|admlog_)"))
    app.add_handler(CallbackQueryHandler(admin_expense_action_callback_handler, pattern=r"^(admexpamt_|admexpdel_|admexp_list)"))
    app.add_handler(CallbackQueryHandler(admin_expense_select_callback_handler, pattern=r"^admexp_(meal|expense)_\d+$"))
    app.add_handler(CallbackQueryHandler(lang_callback_handler, pattern=r"^plang_"))
    app.add_handler(CallbackQueryHandler(delete_meal_prompt_callback_handler, pattern=r"^delmeal_prompt_"))
    app.add_handler(CallbackQueryHandler(delete_meal_confirm_callback_handler, pattern=r"^delmeal_confirm_"))
    app.add_handler(CallbackQueryHandler(resumetrip_handler, pattern=r"^resumetrip_"))
    app.add_handler(CallbackQueryHandler(export_handler, pattern=r"^export_excel$"))

    # Plain text handler for bottom ReplyKeyboard buttons & pending inputs (must be last — lowest priority)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_menu_handler))

