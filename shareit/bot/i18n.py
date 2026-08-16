"""Bilingual string management for BachzTab bot."""

STRINGS = {
    "menu_title": {
        "en": "🏕 *BachzTab — Main Dashboard*\n\nTap a button below to perform an action:",
        "fa": "🏕 *BachzTab — داشبورد اصلی*\n\nبرای انجام عملیات، دکمه مورد نظر را لمس کنید:",
    },
    "btn_join": {"en": "➕ Join Trip", "fa": "➕ عضویت در سفر"},
    "btn_status": {"en": "🏕 Status", "fa": "🏕 خلاصه سفر"},
    "btn_log_expense": {"en": "💸 Log Expense", "fa": "💸 ثبت هزینه"},
    "btn_log_meal": {"en": "🍽 Log Meal/Event", "fa": "🍽 ثبت وعده/رویداد"},
    "btn_contribute": {"en": "💳 Contribute", "fa": "💳 اضافه پرداخت"},
    "btn_add_meal": {"en": "➕ Add New Meal/Event", "fa": "➕ اضافه کردن وعده/رویداد جدید"},
    "btn_manage_meals": {"en": "🍽 Manage Meals/Events", "fa": "🍽 مدیریت وعده‌ها/رویدادها"},
    "btn_meals_status": {"en": "📊 Meals/Events Status", "fa": "📊 وضعیت وعده‌ها/رویدادها"},
    "btn_skip": {"en": "🍽 Manage Meals/Events", "fa": "🍽 مدیریت وعده‌ها/رویدادها"},
    "btn_expense": {"en": "💸 Expense", "fa": "💸 هزینه مشترک"},
    "btn_meals": {"en": "📋 Meals/Events", "fa": "📋 لیست وعده‌ها/رویدادها"},
    "meals_menu_prompt": {
        "en": "📋 *Meals/Events Management*\n\nChoose an action below:",
        "fa": "📋 *مدیریت وعده‌ها/رویدادها*\n\nیک عملیات را از دکمه‌های زیر انتخاب کنید:",
    },
    "btn_settle": {"en": "💰 Settle", "fa": "💰 تسویه نهایی"},
    "btn_lang": {"en": "🌐 Language", "fa": "🌐 تغییر زبان"},
    "btn_my_share": {"en": "📊 My Share", "fa": "📊 سهم من"},
    "btn_export_excel": {"en": "📊 Export Excel", "fa": "📊 خروجی اکسل"},
    "export_caption": {
        "en": "📊 *Excel Expense Report — {trip_name}*\n\nIncludes detailed itemized breakdown, family cost shares, and bank balance reconciliation.",
        "fa": "📊 *گزارش اکسل هزینه‌ها — {trip_name}*\n\nشامل جزئیات کامل هزینه‌ها، سهم هر خانواده و تراز نهایی بانک.",
    },
    "not_implemented": {"en": "ℹ️ This feature is not implemented yet.", "fa": "ℹ️ این قابلیت هنوز پیاده‌سازی نشده است."},
    "join_meal_toggle_title": {
        "en": "📋 *Select Meal/Event Attendance*\n\nTap any meal/event to toggle between Attending (✅) and Skipping (🚫):",
        "fa": "📋 *انتخاب حضور در وعده‌ها/رویدادها*\n\nبرای تغییر بین شرکت (✅) و غیبت (🚫) روی هر مورد کلیک کنید:",
    },
    "btn_done": {"en": "✅ Done", "fa": "✅ تایید نهایی"},
    "btn_attending": {"en": "✅ Attending", "fa": "✅ حاضر (شرکت)"},
    "btn_skipping": {"en": "🚫 Skipping", "fa": "🚫 غایب (انصراف)"},
    "join_summary_title": {
        "en": "🏕 *Family Setup Summary — {family_name}*\n\n👥 Family Share Weight: *{weight}*",
        "fa": "🏕 *خلاصه ثبت خانواده — {family_name}*\n\n👥 وزن سهم خانواده: *{weight}*",
    },
    "join_summary_no_meals": {
        "en": "\n\nℹ️ *No meals/events recorded yet in this trip.*",
        "fa": "\n\nℹ️ *هنوز وعده/رویدادی برای این سفر ثبت نشده است.*",
    },
    "btn_open_menu": {"en": "🏕 Open Main Menu", "fa": "🏕 باز کردن منوی اصلی"},
    "expense_menu_title": {
        "en": "💸 *Log Expense*\n\nChoose an existing meal/event to add payment, or log a new expense:",
        "fa": "💸 *ثبت هزینه*\n\nیک وعده/رویداد موجود را برای اضافه پرداخت انتخاب کنید یا گزینه جدید را بزنید:",
    },
    "btn_new_meal_expense": {
        "en": "➕ New Meal/Event Expense",
        "fa": "➕ وعده/رویداد جدید",
    },
    "btn_general_expense": {
        "en": "🪵 General Shared Expense (Firewood, Pass, etc.)",
        "fa": "🪵 هزینه عمومی (هیزم، ورودی، بنزین و...)",
    },
    "expense_ask_desc": {
        "en": "💸 *{category} Selected*\n\nPlease type a specific description (e.g., *2 Bundles from Store*) or select payment amount below:",
        "fa": "💸 *{category} انتخاب شد*\n\nلطفاً توضیحات (مثلاً *۲ بسته از فروشگاه*) را تایپ کنید یا مبلغ را از دکمه‌های زیر انتخاب کنید:",
    },
    "expense_ask_custom_desc": {
        "en": "✏️ *Custom Expense*\n\nPlease type the description for this expense (e.g., *Kayak Rental*):",
        "fa": "✏️ *هزینه سفارشی*\n\nلطفاً توضیحات این هزینه را تایپ کنید (مثلاً *اجاره قایق*):",
    },
    "meal_select_preset": {
        "en": "🍽 Select a meal/event name preset:",
        "fa": "🍽 نام وعده/رویداد را انتخاب کنید:",
    },
    "meal_ask_desc_explicit": {
        "en": "🍽 *{category} Selected*\n\nPlease type a description for this meal/event (e.g., *Pancakes & Bacon*) or tap **Skip Description** below:",
        "fa": "🍽 *{category} انتخاب شد*\n\nلطفاً توضیحات این وعده/رویداد را تایپ کنید (مثلاً *پنکیک و بیکن*) یا دکمه **رد کردن توضیحات** را بزنید:",
    },
    "btn_skip_desc": {
        "en": "⏩ Skip Description",
        "fa": "⏩ رد کردن توضیحات",
    },
    "meal_ask_custom_desc": {
        "en": "✏️ *Custom Meal/Event*\n\nPlease type the description for this meal/event (e.g., Campfire Pizza):",
        "fa": "✏️ *وعده/رویداد سفارشی*\n\nلطفاً توضیحات این وعده/رویداد را تایپ کنید (مثلاً پیتزا آتشین):",
    },
    "expense_select_preset": {
        "en": "💸 Select a shared expense category:",
        "fa": "💸 دسته‌بندی هزینه مشترک را انتخاب کنید:",
    },
    "select_amount_preset": {
        "en": "💵 Select payment amount for '{name}' (or type a custom number):",
        "fa": "💵 مبلغ پرداخت برای '{name}' را انتخاب کنید (یا عدد تایپ کنید):",
    },
    "lang_prompt": {
        "en": "🌐 Select your preferred language:",
        "fa": "🌐 زبان خود را انتخاب کنید:",
    },
    "trip_created": {
        "en": "🏕 Trip '{name}' created! Families can join with /join <weight>\n\nExample: /join 2.5 (2 adults + 1 kid)",
        "fa": "🏕 سفر '{name}' ساخته شد! خانواده\u200cها با /join <وزن> عضو شوند\n\nمثال: /join 2.5 (۲ بزرگسال + ۱ بچه)",
    },
    "trip_already_active": {
        "en": "⚠️ A trip is already active. Use /endtrip first.",
        "fa": "⚠️ یک سفر فعال وجود دارد. اول /endtrip بزنید.",
    },
    "trip_ended": {
        "en": "✅ Trip '{name}' ended.",
        "fa": "✅ سفر '{name}' پایان یافت.",
    },
    "no_active_trip": {
        "en": "⚠️ No active trip. Create one with /newtrip <name>",
        "fa": "⚠️ سفر فعالی نیست. با /newtrip <نام> بسازید.",
    },
    "family_joined": {
        "en": "✅ {name} joined with weight {weight}",
        "fa": "✅ {name} با وزن {weight} عضو شد",
    },
    "family_updated": {
        "en": "✅ {name} weight updated to {weight}",
        "fa": "✅ وزن {name} به {weight} تغییر کرد",
    },
    "join_first": {
        "en": "⚠️ Join the trip first with /join <weight>",
        "fa": "⚠️ اول با /join <وزن> عضو شوید",
    },
    "join_select_weight": {
        "en": "Select your family's share weight:\n(1 adult = 1, 1 kid = 0.5)",
        "fa": "وزن سهم خانواده‌تان را انتخاب کنید:\n(۱ بزرگسال = ۱، ۱ بچه = ۰.۵)",
    },
    "duplicate_contribution": {
        "en": "⚠️ Duplicate! You already have a ${amount:.2f} contribution to Meal #{number}. Not added.",
        "fa": "⚠️ تکراری! شما قبلاً ${amount:.2f} به وعده #{number} پرداخت کرده‌اید. اضافه نشد.",
    },
    "contribute_select_meal": {
        "en": "Which meal do you want to contribute to?",
        "fa": "به کدام وعده می‌خواهید پرداخت اضافه کنید؟",
    },
    "contribute_ask_amount": {
        "en": "How much did you pay for #{number} {name}? (just type the number)",
        "fa": "چقدر برای #{number} {name} پرداخت کردید؟ (فقط عدد بزنید)",
    },
    "meal_logged": {
        "en": "✅ Meal #{number} '{name}' (${amount:.2f}) logged by {family}",
        "fa": "✅ وعده #{number} '{name}' (${amount:.2f}) توسط {family} ثبت شد",
    },
    "meal_created": {
        "en": "✅ Meal #{number} '{name}' created. Use /contribute {number} <amount> to add payments.",
        "fa": "✅ وعده #{number} '{name}' ساخته شد. با /contribute {number} <مبلغ> پرداخت اضافه کنید.",
    },
    "meal_already_exists": {
        "en": "ℹ️ Meal #{number} '{name}' already exists. Use /contribute {number} <amount> to add your payment.",
        "fa": "ℹ️ وعده #{number} '{name}' قبلاً وجود دارد. با /contribute {number} <مبلغ> پرداختتان را اضافه کنید.",
    },
    "contribution_added": {
        "en": "✅ {family} added ${amount:.2f} to Meal #{number} '{name}'\n📊 Total: ${total:.2f}",
        "fa": "✅ {family} مبلغ ${amount:.2f} به وعده #{number} '{name}' اضافه کرد\n📊 جمع: ${total:.2f}",
    },
    "meal_not_found": {
        "en": "⚠️ Meal #{number} not found.",
        "fa": "⚠️ وعده #{number} پیدا نشد.",
    },
    "skip_prompt": {
        "en": "Which meal did your family skip?",
        "fa": "خانواده شما کدام وعده را نخورد؟",
    },
    "skip_confirmed": {
        "en": "✅ {family} marked as absent from Meal #{number} '{name}'",
        "fa": "✅ {family} از وعده #{number} '{name}' غایب ثبت شد",
    },
    "skip_confirmed_with_grouping": {
        "en": "✅ {family} marked absent from Meal #{number} '{name}'\n\n👥 *Updated Grouping for Meal #{number} '{name}':*\n{members_list}\n📊 Total Group Weight: {total_weight}",
        "fa": "✅ {family} از وعده #{number} '{name}' غایب ثبت شد\n\n👥 *گروه‌بندی به‌روزرسانی‌شده برای وعده #{number} '{name}':*\n{members_list}\n📊 وزن کل گروه: {total_weight}",
    },
    "grouping_header": {
        "en": "\n\n👥 *Active Grouping for Meal #{number} '{name}':*\n{members_list}\n📊 Total Group Weight: {total_weight}",
        "fa": "\n\n👥 *گروه‌بندی فعال برای وعده #{number} '{name}':*\n{members_list}\n📊 وزن کل گروه: {total_weight}",
    },
    "expense_logged": {
        "en": "✅ Shared expense '{description}' (${amount:.2f}) logged by {family}",
        "fa": "✅ هزینه مشترک '{description}' (${amount:.2f}) توسط {family} ثبت شد",
    },
    "settle_header": {
        "en": "🏕 {trip_name} — Final Settlement\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📊 Summary:\n• {family_count} families, {meal_count} meals, {expense_count} shared expenses\n• Total spent: ${total_spent:.2f}",
        "fa": "🏕 {trip_name} — تسویه نهایی\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📊 خلاصه:\n• {family_count} خانواده، {meal_count} وعده، {expense_count} هزینه مشترک\n• کل هزینه: ${total_spent:.2f}",
    },
    "settle_transfers_header": {
        "en": "\n💰 Transfers needed ({count}):",
        "fa": "\n💰 انتقال\u200cهای لازم ({count}):",
    },
    "settle_transfer": {
        "en": "  {index}. {from_name} → {to_name}: ${amount:.2f}",
        "fa": "  {index}. {from_name} → {to_name}: ${amount:.2f}",
    },
    "settle_footer": {
        "en": "\n✅ After these transfers, everyone is settled!",
        "fa": "\n✅ بعد از این انتقال\u200cها، حساب همه صاف است!",
    },
    "settle_no_transfers": {
        "en": "\n✅ Everyone is already settled! No transfers needed.",
        "fa": "\n✅ حساب همه صاف است! نیازی به انتقال نیست.",
    },
    "nothing_to_settle": {
        "en": "⚠️ Nothing to settle yet. Log some meals or expenses first.",
        "fa": "⚠️ چیزی برای تسویه نیست. اول وعده یا هزینه ثبت کنید.",
    },
    "undo_success": {
        "en": "✅ Last action undone.",
        "fa": "✅ آخرین عملیات برگردانده شد.",
    },
    "undo_nothing": {
        "en": "⚠️ Nothing to undo.",
        "fa": "⚠️ چیزی برای برگرداندن نیست.",
    },
    "meal_deleted": {
        "en": "✅ Meal #{number} '{name}' deleted.",
        "fa": "✅ وعده #{number} '{name}' حذف شد.",
    },
    "meal_delete_denied": {
        "en": "⚠️ Only the family who logged this meal can delete it.",
        "fa": "⚠️ فقط خانواده\u200cای که این وعده را ثبت کرده می\u200cتواند حذفش کند.",
    },
    "meal_edited": {
        "en": "✅ Your contribution to Meal #{number} updated to ${amount:.2f}",
        "fa": "✅ سهم شما در وعده #{number} به ${amount:.2f} تغییر کرد",
    },
    "no_contribution_to_edit": {
        "en": "⚠️ You haven't contributed to Meal #{number}.",
        "fa": "⚠️ شما سهمی در وعده #{number} ندارید.",
    },
    "contribution_removed": {
        "en": "✅ Your contribution to Meal #{number} '{name}' removed.",
        "fa": "✅ سهم شما از وعده #{number} '{name}' حذف شد.",
    },
    "lang_switched": {
        "en": "✅ Language switched to English.",
        "fa": "✅ زبان به فارسی تغییر کرد.",
    },
    "usage_newtrip": {
        "en": "Usage: /newtrip <trip name> [family_count]\nExample: /newtrip Camp Darband July 2026 8",
        "fa": "استفاده: /newtrip <نام سفر> [تعداد خانواده]\nمثال: /newtrip کمپ دربند تیر ۱۴۰۵ 8",
    },
    "usage_join": {
        "en": "Usage: /join <weight>\nExample: /join 2.5 (2 adults + 1 kid = 2.5)",
        "fa": "استفاده: /join <وزن>\nمثال: /join 2.5 (۲ بزرگسال + ۱ بچه = ۲.۵)",
    },
    "usage_meal": {
        "en": "Usage: /meal <name> [amount]\nExamples:\n  /meal Saturday BBQ 45.50\n  /meal Saturday BBQ (creates slot, no payment)",
        "fa": "استفاده: /meal <نام> [مبلغ]\nمثال:\n  /meal باربیکیو شنبه 45.50\n  /meal باربیکیو شنبه (فقط ساخت وعده)",
    },
    "usage_contribute": {
        "en": "Usage: /contribute <meal#> <amount>\nExample: /contribute 3 25.00",
        "fa": "استفاده: /contribute <شماره\u200cوعده> <مبلغ>\nمثال: /contribute 3 25.00",
    },
    "usage_expense": {
        "en": "Usage: /expense <description> <amount>\nExample: /expense Firewood 20",
        "fa": "استفاده: /expense <توضیح> <مبلغ>\nمثال: /expense هیزم 20",
    },
    "usage_deletemeal": {
        "en": "Usage: /deletemeal <meal#>\nExample: /deletemeal 3",
        "fa": "استفاده: /deletemeal <شماره\u200cوعده>\nمثال: /deletemeal 3",
    },
    "usage_editmeal": {
        "en": "Usage: /editmeal <meal#> <new amount>\nExample: /editmeal 3 60",
        "fa": "استفاده: /editmeal <شماره\u200cوعده> <مبلغ جدید>\nمثال: /editmeal 3 60",
    },
    "help": {
        "en": (
            "🏕 *BachzTab — Camp Expense Splitter*\n\n"
            "*Trip Management:*\n"
            "/newtrip <name> [count] — Create a trip (count = expected families)\n"
            "/join <weight> — Join with your family's share weight\n"
            "/endtrip — End the current trip\n"
            "/status — Show trip summary\n\n"
            "*Meals & Expenses:*\n"
            "/meal <name> [amount] — Create a meal (or add payment if exists)\n"
            "/contribute <meal#> <amount> — Add to an existing meal\n"
            "/skip — Mark your family absent from a meal\n"
            "/expense <desc> <amount> — Log a shared expense\n"
            "/meals — Detailed meal breakdown\n\n"
            "*Settlement:*\n"
            "/settle — Calculate final transfers\n"
            "/history — View past trip settlements\n\n"
            "*Corrections:*\n"
            "/editmeal <meal#> <amount> — Update contribution (0 = remove)\n"
            "/deletemeal <meal#> — Delete a meal you logged\n"
            "/undo — Undo your last action\n\n"
            "*Settings:*\n"
            "/lang <en|fa> — Switch language\n"
            "/help — Show this message"
        ),
        "fa": (
            "🏕 *BachzTab — تقسیم هزینه کمپ*\n\n"
            "*مدیریت سفر:*\n"
            "/newtrip <نام> [تعداد] — ساخت سفر (تعداد = خانواده\u200cهای مورد انتظار)\n"
            "/join <وزن> — عضویت با وزن سهم خانواده\n"
            "/endtrip — پایان سفر فعلی\n"
            "/status — خلاصه سفر\n\n"
            "*وعده\u200cها و هزینه\u200cها:*\n"
            "/meal <نام> [مبلغ] — ساخت وعده (یا اضافه کردن اگر وجود دارد)\n"
            "/contribute <شماره\u200cوعده> <مبلغ> — اضافه کردن به وعده موجود\n"
            "/skip — غیبت خانواده از یک وعده\n"
            "/expense <توضیح> <مبلغ> — ثبت هزینه مشترک\n"
            "/meals — جزئیات وعده\u200cها\n\n"
            "*تسویه:*\n"
            "/settle — محاسبه انتقال\u200cهای نهایی\n"
            "/history — مشاهده تسویه سفرهای قبلی\n\n"
            "*اصلاحات:*\n"
            "/editmeal <شماره\u200cوعده> <مبلغ> — ویرایش سهم (۰ = حذف)\n"
            "/deletemeal <شماره\u200cوعده> — حذف وعده\u200cای که ثبت کردید\n"
            "/undo — برگرداندن آخرین عملیات\n\n"
            "*تنظیمات:*\n"
            "/lang <en|fa> — تغییر زبان\n"
            "/help — نمایش این پیام"
        ),
    },
    "status_header": {
        "en": "🏕 *{trip_name}*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "fa": "🏕 *{trip_name}*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    },
    "status_families": {
        "en": "\n👨\u200d👩\u200d👧 *Families ({count}):*",
        "fa": "\n👨\u200d👩\u200d👧 *خانواده\u200cها ({count}):*",
    },
    "status_family_item": {
        "en": "  • {name} (weight: {weight})",
        "fa": "  • {name} (وزن: {weight})",
    },
    "status_meals": {
        "en": "\n🍽 *Meals ({count}):*",
        "fa": "\n🍽 *وعده\u200cها ({count}):*",
    },
    "status_meal_item": {
        "en": "  #{number} {name} — ${total:.2f}",
        "fa": "  #{number} {name} — ${total:.2f}",
    },
    "status_meal_paid_by": {
        "en": "\n     💳 Paid by: {paid_list}",
        "fa": "\n     💳 پرداختی‌ها: {paid_list}",
    },
    "status_expenses": {
        "en": "\n💸 *Shared Expenses ({count}):*",
        "fa": "\n💸 *هزینه\u200cهای مشترک ({count}):*",
    },
    "status_expense_item": {
        "en": "  • {description} — ${amount:.2f} (by {family})",
        "fa": "  • {description} — ${amount:.2f} (توسط {family})",
    },
    "status_bank_header": {
        "en": "\n\n🏦 *Bank Status & Family Balances:*",
        "fa": "\n\n🏦 *وضعیت تراز مالی و بانک خانواده‌ها:*",
    },
    "status_no_data": {
        "en": "\n_No meals or expenses logged yet._",
        "fa": "\n_هنوز وعده یا هزینه\u200cای ثبت نشده._",
    },
    "group_only": {
        "en": "⚠️ This command works in group chats only.",
        "fa": "⚠️ این دستور فقط در گروه کار می\u200cکند.",
    },
    "reminder": {
        "en": (
            "⏰ *Daily Reminder — {trip_name}*\n\n"
            "Not all families have logged their expenses yet! "
            "({active}/{expected} families contributed so far)\n\n"
            "*Quick guide:*\n"
            "• `/join 2.5` — join with your family weight\n"
            "• `/contribute 1 20` — add payment to meal #1\n"
            "• `/skip` — mark absent from a meal\n"
            "• `/expense Firewood 15` — log a shared expense\n\n"
            "_This message will auto-delete in 1 hour._"
        ),
        "fa": (
            "⏰ *یادآوری روزانه — {trip_name}*\n\n"
            "هنوز همه خانواده\u200cها هزینه\u200cهایشان را ثبت نکرده\u200cاند! "
            "({active}/{expected} خانواده تا الان ثبت کرده\u200cاند)\n\n"
            "*راهنمای سریع:*\n"
            "• `/join 2.5` — عضویت با وزن خانواده\n"
            "• `/contribute 1 20` — اضافه کردن پرداخت به وعده ۱\n"
            "• `/skip` — غیبت از یک وعده\n"
            "• `/expense هیزم 15` — ثبت هزینه مشترک\n\n"
            "_این پیام بعد از ۱ ساعت حذف می\u200cشود._"
        ),
    },
    "meals_header": {
        "en": "🍽 *Meals — {trip_name}* ({count} total)",
        "fa": "🍽 *وعده\u200cها — {trip_name}* ({count} عدد)",
    },
    "no_meals_yet": {
        "en": "⚠️ No meals logged yet.",
        "fa": "⚠️ هنوز وعده\u200cای ثبت نشده.",
    },
    "no_history": {
        "en": "⚠️ No past trips found.",
        "fa": "⚠️ سفر قبلی یافت نشد.",
    },
    "history_list": {
        "en": "📋 *Past Trips* ({count}):",
        "fa": "📋 *سفرهای قبلی* ({count}):",
    },
    "history_hint": {
        "en": "\n\n_Use /history <number> to see details._",
        "fa": "\n\n_برای جزئیات: /history <شماره>_",
    },
    "history_invalid": {
        "en": "⚠️ Invalid trip number. Use 1 to {count}.",
        "fa": "⚠️ شماره نامعتبر. از ۱ تا {count} وارد کنید.",
    },
    "history_usage": {
        "en": "Usage: /history [number]\nExample: /history 1",
        "fa": "استفاده: /history [شماره]\nمثال: /history 1",
    },
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Translate a string key to the given language with format args."""
    strings = STRINGS.get(key)
    if strings is None:
        return f"[Missing string: {key}]"
    text = strings.get(lang, strings.get("en", f"[Missing: {key}/{lang}]"))
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text
