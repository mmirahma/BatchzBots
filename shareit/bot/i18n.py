"""Bilingual string management for BachzTab bot."""

STRINGS = {
    "menu_title": {
        "en": "🏕 *BachzTab keyboard active!*",
        "fa": "🏕 *کیبورد BachzTab فعال شد!*",
    },
    "btn_join": {"en": "➕ Join Trip", "fa": "➕ عضویت در سفر"},
    "btn_status": {"en": "🏕 Status", "fa": "🏕 خلاصه سفر"},
    "btn_log_expense": {"en": "💸 Log Expense", "fa": "💸 ثبت هزینه"},
    "btn_edit_my_expenses": {"en": "✏️ Edit My Expenses", "fa": "✏️ ویرایش هزینه‌های من"},
    "no_expenses_to_edit": {
        "en": "⚠️ You haven't logged any expenses yet in this trip.",
        "fa": "⚠️ شما هنوز هیچ هزینه‌ای در این سفر ثبت نکرده‌اید.",
    },
    "edit_expenses_title": {
        "en": "✏️ *Edit Your Logged Expenses*\n\nSelect an expense below to edit its amount or delete it:",
        "fa": "✏️ *ویرایش هزینه‌های ثبت شده شما*\n\nبرای ویرایش یا حذف، یک هزینه را از زیر انتخاب کنید:",
    },
    "edit_expense_prompt": {
        "en": "✏️ *Editing: {name}*\n💰 Current Amount: *${amount:.2f}*\n\nSelect new amount below or type a number:",
        "fa": "✏️ *ویرایش: {name}*\n💰 مبلغ فعلی: *${amount:.2f}*\n\nمبلغ جدید را از زیر انتخاب کنید یا یک عدد تایپ کنید:",
    },
    "btn_delete_expense": {"en": "❌ Delete Expense", "fa": "❌ حذف هزینه"},
    "btn_back": {"en": "🔙 Back", "fa": "🔙 بازگشت"},
    "btn_back_to_list": {"en": "🔙 Back to Expenses", "fa": "🔙 بازگشت به لیست هزینه‌ها"},
    "no_families": {
        "en": "⚠️ No members have joined this trip yet.",
        "fa": "⚠️ هنوز هیچ عضوی به این سفر ملحق نشده است.",
    },
    "invalid_weight": {
        "en": "⚠️ Invalid weight. Please enter a positive number (e.g. 1.5):",
        "fa": "⚠️ ضریب نامعتبر است. لطفاً یک عدد مثبت وارد کنید (مثلاً 1.5):",
    },
    "join_summary_table_header": {
        "en": "📋 *Meal Attendance Status:*",
        "fa": "📋 *وضعیت حضور در وعده‌ها:*",
    },
    "expense_updated": {
        "en": "✅ Updated '{name}' to ${amount:.2f}",
        "fa": "✅ مبلغ '{name}' به ${amount:.2f} ویرایش شد",
    },
    "expense_deleted": {
        "en": "✅ Deleted '{name}'.",
        "fa": "✅ هزینه '{name}' حذف شد.",
    },
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
    "btn_help": {"en": "❓ Help", "fa": "❓ راهنما"},
    "btn_my_share": {"en": "📊 My Share", "fa": "📊 سهم من"},
    "btn_export_excel": {"en": "📊 Export Excel", "fa": "📊 خروجی اکسل"},
    "btn_admin": {"en": "👑 Admin", "fa": "👑 پنل مدیریت"},
    "admin_menu_title": {
        "en": "👑 *Admin Panel*\nTrip: *{trip_name}*\n\nSelect an administrative action below:",
        "fa": "👑 *پنل مدیریت*\nسفر: *{trip_name}*\n\nیک عملیات مدیریتی را انتخاب کنید:",
    },
    "admin_only": {
        "en": "⚠️ This action is only available to the group owner and Maysam Mir.",
        "fa": "⚠️ این عملیات فقط برای مالک گروه و میثم میر مجاز است.",
    },
    "btn_back_admin": {"en": "🔙 Back to Admin", "fa": "🔙 بازگشت به پنل مدیریت"},
    "btn_members": {"en": "👥 Trip Members", "fa": "👥 اعضای سفر"},
    "btn_edit_all_expenses": {"en": "📝 Manage All Expenses", "fa": "📝 مدیریت تمام هزینه‌ها"},
    "btn_back_all_expenses": {"en": "🔙 Back to All Expenses", "fa": "🔙 بازگشت به لیست تمام هزینه‌ها"},
    "btn_admin_log_expense": {"en": "➕ Log Expense for Member", "fa": "➕ ثبت هزینه برای اعضا"},
    "admin_log_select_family_title": {
        "en": "👤 *Log Expense for Member*\nTrip: *{trip_name}*\n\nSelect the member who paid for this expense:",
        "fa": "👤 *ثبت هزینه برای اعضا*\nسفر: *{trip_name}*\n\nعضوی که هزینه را پرداخت کرده انتخاب کنید:",
    },
    "admin_log_choose_type_title": {
        "en": "➕ *Log Expense for {family_name}*\n\nSelect an existing meal to contribute to, or choose a new expense type:",
        "fa": "➕ *ثبت هزینه برای {family_name}*\n\nیک وعده موجود را برای مشارکت انتخاب کنید یا نوع هزینه جدید را انتخاب نمایید:",
    },
    "btn_log_meal_for_member": {"en": "🍽 New Meal Expense", "fa": "🍽 ثبت وعده غذایی جدید"},
    "btn_log_shared_for_member": {"en": "🪵 General Shared Expense", "fa": "🪵 هزینه عمومی مشترک"},
    "btn_log_targeted_for_member": {"en": "🎯 Specific Family Expense / Custom Split", "fa": "🎯 هزینه برای خانواده‌های خاص / تقسیم سفارشی"},
    "admin_log_ask_meal_name": {
        "en": "🍽 *Log New Meal for {family_name}*\n\nSelect meal or type custom name in chat:",
        "fa": "🍽 *ثبت وعده جدید برای {family_name}*\n\nنوع وعده را انتخاب کنید یا نام دلخواه تایپ کنید:",
    },
    "admin_log_ask_shared_cat": {
        "en": "🪵 *Log Shared Expense for {family_name}*\n\nSelect category or type description in chat:",
        "fa": "🪵 *ثبت هزینه مشترک برای {family_name}*\n\nدسته‌بندی را انتخاب کنید یا شرح دلخواه تایپ کنید:",
    },
    "admin_log_ask_targeted_desc": {
        "en": "🎯 *Custom Split Expense for {family_name}*\n\nSelect category or type description in chat:",
        "fa": "🎯 *هزینه با تقسیم سفارشی برای {family_name}*\n\nدسته‌بندی را انتخاب کنید یا شرح دلخواه تایپ کنید:",
    },
    "admin_log_ask_amount": {
        "en": "💰 *Amount for {name}*\nPaid by: *{family_name}*\n\nSelect amount or type a number in chat:",
        "fa": "💰 *مبلغ برای {name}*\nپرداخت‌کننده: *{family_name}*\n\nمبلغ را انتخاب کنید یا عدد دلخواه تایپ کنید:",
    },
    "admin_log_ask_contrib_amount": {
        "en": "💰 *Contribute to Meal #{number} '{name}'*\nPaid by: *{family_name}*\n\nSelect amount or type a number in chat:",
        "fa": "💰 *مشارکت در وعده #{number} '{name}'*\nپرداخت‌کننده: *{family_name}*\n\nمبلغ را انتخاب کنید یا عدد دلخواه تایپ کنید:",
    },
    "admin_contrib_logged_success": {
        "en": "✅ Added contribution of *${amount:.2f}* to meal #{number} *{name}* for *{family_name}*. Total meal cost: *${total:.2f}*",
        "fa": "✅ مبلغ *${amount:.2f}* به عنوان مشارکت در وعده #{number} *{name}* برای *{family_name}* ثبت شد. مجموع هزینه وعده: *${total:.2f}*",
    },
    "admin_expense_logged_success": {
        "en": "✅ Successfully logged *{description}* (*${amount:.2f}*) for *{family_name}*.",
        "fa": "✅ هزینه *{description}* (*${amount:.2f}*) با موفقیت برای *{family_name}* ثبت شد.",
    },
    "admin_meal_logged_success": {
        "en": "✅ Successfully logged Meal #{meal_num} *{name}* (*${amount:.2f}*) for *{family_name}*.",
        "fa": "✅ وعده #{meal_num} *{name}* (*${amount:.2f}*) با موفقیت برای *{family_name}* ثبت شد.",
    },
    "admin_edit_expenses_title": {
        "en": "📝 *Manage All Trip Expenses*\nTrip: *{trip_name}*\n\nSelect an expense below to modify its amount or delete it:",
        "fa": "📝 *مدیریت تمام هزینه‌های سفر*\nسفر: *{trip_name}*\n\nبرای تغییر مبلغ یا حذف، یک هزینه را انتخاب کنید:",
    },
    "admin_edit_expense_prompt": {
        "en": "✏️ *Edit Expense*\nItem: *{name}*\nPaid by: *{family_name}*\n💰 Current Amount: *${amount:.2f}*\n\nSelect a new amount or type a number:",
        "fa": "✏️ *ویرایش هزینه*\nمورد: *{name}*\nپرداخت‌کننده: *{family_name}*\n💰 مبلغ فعلی: *${amount:.2f}*\n\nمبلغ جدید را انتخاب کنید یا یک عدد تایپ کنید:",
    },
    "members_title": {
        "en": "👥 *Trip Members & Roster*\nTrip: *{trip_name}*\n\nTap a member below to add them to the trip, adjust their weight, or skip/remove them:",
        "fa": "👥 *اعضای سفر و لیست حاضرین*\nسفر: *{trip_name}*\n\nبرای عضویت در سفر، تنظیم سهم، یا حذف/رد کردن روی نام هر فرد کلیک کنید:",
    },
    "member_config_title": {
        "en": "👤 *Manage Member: {name}*\nStatus: *{status}*\n\nSelect a share weight to add/update, or skip/remove from this trip:",
        "fa": "👤 *مدیریت عضو: {name}*\nوضعیت: *{status}*\n\nبرای عضویت/ویرایش یک سهم انتخاب کنید، یا از این سفر حذف کنید:",
    },
    "status_joined": {"en": "In Trip (Weight: {weight})", "fa": "عضو در سفر (سهم: {weight})"},
    "status_not_joined": {"en": "Not in trip (Skipped)", "fa": "عدم حضور در سفر (رد شده)"},
    "btn_add_to_trip": {"en": "➕ Add to Trip (Default w=2.0)", "fa": "➕ افزودن به سفر (پیش‌فرض سهم ۲.۰)"},
    "btn_remove_member": {"en": "🚫 Skip / Remove from Trip", "fa": "🚫 حذف از سفر / رد کردن"},
    "btn_custom_member": {"en": "➕ Add Custom Family Name", "fa": "➕ افزودن نام دلخواه خانواده"},
    "btn_refresh_members": {"en": "🔄 Refresh Trip Members", "fa": "🔄 بروزرسانی اعضای سفر"},
    "btn_back_members": {"en": "🔙 Back to Trip Members", "fa": "🔙 بازگشت به لیست اعضای سفر"},
    "btn_custom_weight": {"en": "✏️ Custom Weight", "fa": "✏️ سهم دلخواه"},
    "member_added_success": {"en": "✅ Added *{name}* with weight {weight}.", "fa": "✅ *{name}* با سهم {weight} به سفر اضافه شد."},
    "member_updated_success": {"en": "✅ Updated *{name}* weight to {weight}.", "fa": "✅ سهم *{name}* به {weight} تغییر یافت."},
    "member_removed_success": {"en": "✅ Removed *{name}* from the trip.", "fa": "✅ *{name}* از سفر حذف شد."},
    "member_and_expenses_deleted_success": {
        "en": "✅ Removed *{name}* and deleted all of their logged expenses from the trip.",
        "fa": "✅ *{name}* و تمام هزینه‌های ثبت‌شده توسط او از سفر حذف شدند.",
    },
    "member_delete_with_expenses_warning": {
        "en": "⚠️ *Remove {name} from Trip?*\n\nThis member has logged the following expenses (*${total:.2f}* total):\n\n{expenses}\n\nProceeding will *permanently delete* this member and all of their logged expenses and contributions.\n\nAre you sure you want to proceed?",
        "fa": "⚠️ *حذف {name} از سفر؟*\n\nاین عضو هزینه‌های زیر را ثبت کرده است (مجموعاً *${total:.2f}*):\n\n{expenses}\n\nبا تایید، این عضو و تمام هزینه‌ها و پرداخت‌های ثبت‌شده توسط او *به‌طور دائم حذف خواهند شد*.\n\nآیا مطمئن هستید؟",
    },
    "btn_confirm_remove_member_expenses": {
        "en": "🗑 Delete Member & Expenses",
        "fa": "🗑 حذف عضو و هزینه‌ها",
    },
    "member_cannot_remove_active": {
        "en": "⚠️ Cannot remove *{name}* because they have logged expenses or contributions.",
        "fa": "⚠️ امکان حذف *{name}* وجود ندارد چون هزینه یا پرداختی ثبت کرده است.",
    },
    "prompt_custom_member_name": {
        "en": "✏️ *Add Custom Family*\n\nPlease type the name of the family to add (e.g. *Smith Family*):",
        "fa": "✏️ *افزودن نام دلخواه خانواده*\n\nلطفاً نام خانواده مورد نظر را تایپ کنید (مثلاً *خانواده احمدی*):",
    },
    "prompt_custom_member_weight": {
        "en": "✏️ Type the share weight number (e.g. 2.25) for *{name}*:",
        "fa": "✏️ لطفاً ضریب سهم (مثلاً ۲.۲۵) را برای *{name}* تایپ کنید:",
    },
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
    "btn_open_menu": {"en": "⌨️ Activate Keyboard", "fa": "⌨️ فعال‌سازی کیبورد"},
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
    "btn_targeted_expense": {
        "en": "🎯 Custom-Weighted / Specific Family Expense",
        "fa": "🎯 هزینه اختصاصی / سهم‌بندی سفارشی خانواده‌ها",
    },
    "targeted_ask_desc": {
        "en": "🎯 *Custom Multi-Family Expense*\n\nPlease type the description for this expense (e.g., *Boat Rental*, *Cab Driver*, *Gifts*):",
        "fa": "🎯 *هزینه اختصاصی با سهم‌بندی سفارشی*\n\nلطفاً توضیحات این هزینه را تایپ کنید (مثلاً *اجاره قایق*، *تاکسی*، *هدیه*):",
    },
    "targeted_ask_amount": {
        "en": "💰 *Amount for '{desc}'*\n\nSelect payment amount below or type a custom number in chat:",
        "fa": "💰 *مبلغ برای '{desc}'*\n\nمبلغ پرداخت را از دکمه‌های زیر انتخاب کنید یا یک عدد تایپ کنید:",
    },
    "targeted_setup_title": {
        "en": "🎯 *Custom Expense Share Setup — {desc} (${amount:.2f})*\n\nTap any family below to adjust their share weight or exclude them:",
        "fa": "🎯 *تنظیم سهم‌بندی سفارشی — {desc} (${amount:.2f})*\n\nبرای تغییر وزن سهم یا حذف، روی خانواده مورد نظر کلیک کنید:",
    },
    "targeted_set_weight_title": {
        "en": "👥 *Select Share Weight for {family_name}* (Current: {weight}):",
        "fa": "👥 *انتخاب وزن سهم برای {family_name}* (فعلی: {weight}):",
    },
    "btn_exclude_family": {"en": "🚫 Exclude / Skip", "fa": "🚫 حذف / غایب"},
    "btn_save_expense": {"en": "✅ Save & Log Expense", "fa": "✅ ثبت نهایی هزینه"},
    "targeted_logged_summary": {
        "en": "✅ *Custom Expense Logged!*\n\n📝 Item: *{desc}*\n💰 Amount: *${amount:.2f}*\n💳 Paid by: *{payer}*\n\n👥 *Cost Share Breakdown:*\n{breakdown}",
        "fa": "✅ *هزینه سفارشی ثبت شد!*\n\n📝 عنوان: *{desc}*\n💰 مبلغ: *${amount:.2f}*\n💳 پرداخت‌کننده: *{payer}*\n\n👥 *توزیع سهم هزینه‌ها:*\n{breakdown}",
    },
    "expense_ask_desc": {
        "en": "💸 *{category} Selected*\n\nSelect payment amount below or type a custom number in chat:",
        "fa": "💸 *{category} انتخاب شد*\n\nمبلغ پرداخت را از دکمه‌های زیر انتخاب کنید یا یک عدد تایپ کنید:",
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
        "en": "💸 *Log General Shared Expense*\n\nSelect a preset category below OR type your custom description in chat:",
        "fa": "💸 *ثبت هزینه مشترک عمومی*\n\nیک دسته‌بندی از دکمه‌های زیر انتخاب کنید یا عنوان دلخواه را در چت تایپ کنید:",
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
    "trip_ended_leave_48h": {
        "en": "✅ *Trip '{name}' ended.*\n\n⏳ BachzTab bot will automatically leave this group in 48 hours (unless a new trip is started with /newtrip).",
        "fa": "✅ *سفر '{name}' پایان یافت.*\n\n⏳ ربات BachzTab تا ۴۸ ساعت آینده به طور خودکار گروه را ترک می‌کند (مگر اینکه سفر جدیدی با /newtrip آغاز شود).",
    },
    "btn_resume_trip": {"en": "▶️ Resume Trip", "fa": "▶️ از سرگیری سفر"},
    "trip_resumed": {
        "en": "▶️ *Trip '{name}' resumed!*\n\nYou can now log new expenses, edit existing expenses with /editmyexpenses, or make corrections. When finished, use /endtrip.",
        "fa": "▶️ *سفر '{name}' دوباره فعال شد!*\n\nاکنون می‌توانید هزینه‌های جدید ثبت کنید، هزینه‌ها را با /editmyexpenses ویرایش کنید یا اصلاحات انجام دهید. پس از اتمام /endtrip بزنید.",
    },
    "no_trip_to_resume": {
        "en": "⚠️ No recently ended trip found to resume.",
        "fa": "⚠️ هیچ سفر پایان‌یافته اخیر برای از سرگیری یافت نشد.",
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
        "en": "⚠️ Duplicate! You already have a ${amount:.2f} contribution to Meal/Event #{number}. Not added.",
        "fa": "⚠️ تکراری! شما قبلاً ${amount:.2f} به وعده/رویداد #{number} پرداخت کرده‌اید. اضافه نشد.",
    },
    "contribute_select_meal": {
        "en": "Which meal/event do you want to contribute to?",
        "fa": "به کدام وعده/رویداد می‌خواهید پرداخت اضافه کنید؟",
    },
    "contribute_ask_amount": {
        "en": "How much did you pay for #{number} {name}? (just type the number)",
        "fa": "چقدر برای #{number} {name} پرداخت کردید؟ (فقط عدد بزنید)",
    },
    "meal_logged": {
        "en": "✅ Meal/Event #{number} '{name}' (${amount:.2f}) logged by {family}",
        "fa": "✅ وعده/رویداد #{number} '{name}' (${amount:.2f}) توسط {family} ثبت شد",
    },
    "meal_created": {
        "en": "✅ Meal/Event #{number} '{name}' created. Use /contribute {number} <amount> to add payments.",
        "fa": "✅ وعده/رویداد #{number} '{name}' ساخته شد. با /contribute {number} <مبلغ> پرداخت اضافه کنید.",
    },
    "meal_already_exists": {
        "en": "ℹ️ Meal/Event #{number} '{name}' already exists. Use /contribute {number} <amount> to add your payment.",
        "fa": "ℹ️ وعده/رویداد #{number} '{name}' قبلاً وجود دارد. با /contribute {number} <مبلغ> پرداختتان را اضافه کنید.",
    },
    "contribution_added": {
        "en": "✅ {family} added ${amount:.2f} to Meal/Event #{number} '{name}'\n📊 Total: ${total:.2f}",
        "fa": "✅ {family} مبلغ ${amount:.2f} به وعده/رویداد #{number} '{name}' اضافه کرد\n📊 جمع: ${total:.2f}",
    },
    "meal_not_found": {
        "en": "⚠️ Meal/Event #{number} not found.",
        "fa": "⚠️ وعده/رویداد #{number} پیدا نشد.",
    },
    "skip_prompt": {
        "en": "Which meal/event did your family skip?",
        "fa": "خانواده شما کدام وعده/رویداد را نخورد؟",
    },
    "skip_confirmed": {
        "en": "✅ {family} marked as absent from Meal/Event #{number} '{name}'",
        "fa": "✅ {family} از وعده/رویداد #{number} '{name}' غایب ثبت شد",
    },
    "skip_confirmed_with_grouping": {
        "en": "✅ {family} marked absent from Meal/Event #{number} '{name}'\n\n👥 *Updated Grouping for Meal/Event #{number} '{name}':*\n{members_list}\n📊 Total Group Weight: {total_weight}",
        "fa": "✅ {family} از وعده/رویداد #{number} '{name}' غایب ثبت شد\n\n👥 *گروه‌بندی به‌روزرسانی‌شده برای وعده/رویداد #{number} '{name}':*\n{members_list}\n📊 وزن کل گروه: {total_weight}",
    },
    "grouping_header": {
        "en": "\n\n👥 *Active Grouping for Meal/Event #{number} '{name}':*\n{members_list}\n📊 Total Group Weight: {total_weight}",
        "fa": "\n\n👥 *گروه‌بندی فعال برای وعده/رویداد #{number} '{name}':*\n{members_list}\n📊 وزن کل گروه: {total_weight}",
    },
    "expense_logged": {
        "en": "✅ Shared expense '{description}' (${amount:.2f}) logged by {family}",
        "fa": "✅ هزینه مشترک '{description}' (${amount:.2f}) توسط {family} ثبت شد",
    },
    "settle_header": {
        "en": "🏕 {trip_name} — Final Settlement\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📊 Summary:\n• {family_count} families, {meal_count} meals/events, {expense_count} shared expenses\n• Total spent: ${total_spent:.2f}",
        "fa": "🏕 {trip_name} — تسویه نهایی\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📊 خلاصه:\n• {family_count} خانواده، {meal_count} وعده/رویداد، {expense_count} هزینه مشترک\n• کل هزینه: ${total_spent:.2f}",
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
        "en": "⚠️ Nothing to settle yet. Log some meals/events or expenses first.",
        "fa": "⚠️ چیزی برای تسویه نیست. اول وعده/رویداد یا هزینه ثبت کنید.",
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
        "en": "✅ Meal/Event #{number} '{name}' deleted.",
        "fa": "✅ وعده/رویداد #{number} '{name}' حذف شد.",
    },
    "btn_delete_meal": {"en": "🗑 Delete Meal/Event", "fa": "🗑 حذف وعده/رویداد"},
    "delmeal_select_prompt": {
        "en": "🗑 *Delete Meal/Event*\n\nSelect a meal/event below to delete it:",
        "fa": "🗑 *حذف وعده/رویداد*\n\nیک وعده/رویداد را برای حذف از لیست زیر انتخاب کنید:",
    },
    "delmeal_warning": {
        "en": "⚠️ *Warning: Meal/Event #{number} '{name}' has ${total:.2f} in logged payments!*\n\nDeleting this meal/event will permanently remove all logged payments and contributions associated with it. Are you sure you want to proceed?",
        "fa": "⚠️ *هشدار: وعده/رویداد #{number} '{name}' دارای ${total:.2f} پرداخت ثبت‌شده است!*\n\nحذف این وعده/رویداد باعث حذف همیشگی تمام پرداخت‌ها و سهم‌های ثبت‌شده آن می‌شود. آیا مطمئن هستید؟",
    },
    "btn_confirm_delmeal": {
        "en": "⚠️ Yes, Delete Meal/Event & All Payments",
        "fa": "⚠️ بله، حذف وعده/رویداد و تمام پرداخت‌ها",
    },
    "meal_deleted_with_payments": {
        "en": "✅ Meal/Event #{number} '{name}' and all associated payments (${total:.2f}) deleted.",
        "fa": "✅ وعده/رویداد #{number} '{name}' و تمام پرداخت‌های آن (${total:.2f}) حذف شدند.",
    },
    "meal_delete_denied": {
        "en": "⚠️ Only the family who logged this meal/event can delete it.",
        "fa": "⚠️ فقط خانواده‌ای که این وعده/رویداد را ثبت کرده می‌تواند حذفش کند.",
    },
    "meal_edited": {
        "en": "✅ Your contribution to Meal/Event #{number} updated to ${amount:.2f}",
        "fa": "✅ سهم شما در وعده/رویداد #{number} به ${amount:.2f} تغییر کرد",
    },
    "no_contribution_to_edit": {
        "en": "⚠️ You haven't contributed to Meal/Event #{number}.",
        "fa": "⚠️ شما سهمی در وعده/رویداد #{number} ندارید.",
    },
    "contribution_removed": {
        "en": "✅ Your contribution to Meal/Event #{number} '{name}' removed.",
        "fa": "✅ سهم شما از وعده/رویداد #{number} '{name}' حذف شد.",
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
            "/menu /start — Activate bottom keyboard menu\n"
            "/status — Show trip summary & live status\n"
            "/endtrip — End trip & send Excel report\n"
            "/resumetrip — Reactivate recently ended trip (within 48h)\n\n"
            "*Meals & Expenses:*\n"
            "/meal <name> [amount] — Create a meal (or add payment)\n"
            "/contribute <meal#> <amount> — Add payment to a meal\n"
            "/skip — Manage your meal/event attendance\n"
            "/expense <desc> <amount> — Log a shared expense\n"
            "/meals — Meals management & status breakdown\n"
            "/myshare — View your family's itemized cost share\n\n"
            "*Settlement & Reports:*\n"
            "/settle — Calculate final debt settlement transfers\n"
            "/export — Generate and download itemized Excel report\n"
            "/history — View past trip settlements\n\n"
            "*Corrections:*\n"
            "/editmyexpenses — Interactive menu to edit/delete your logged expenses\n"
            "/editmeal <meal#> <amount> — Update meal contribution (0 = remove)\n"
            "/deletemeal <meal#> — Delete a meal you logged\n"
            "/undo — Undo your last action\n\n"
            "*Settings:*\n"
            "/lang <en|fa> — Switch language\n"
            "/help — Show this user guide"
        ),
        "fa": (
            "🏕 *BachzTab — تقسیم هزینه کمپ*\n\n"
            "*مدیریت سفر:*\n"
            "/newtrip <نام> [تعداد] — ساخت سفر (تعداد = خانواده\u200cهای مورد انتظار)\n"
            "/join <وزن> — عضویت با وزن سهم خانواده\n"
            "/menu /start — فعال‌سازی کیبورد و منوی اصلی\n"
            "/status — خلاصه وضعیت سفر\n"
            "/endtrip — پایان سفر و ارسال گزارش اکسل\n"
            "/resumetrip — بازگردانی سفر پایان‌یافته (تا ۴۸ ساعت)\n\n"
            "*وعده‌ها و هزینه‌ها:*\n"
            "/meal <نام> [مبلغ] — ساخت وعده (یا پرداخت)\n"
            "/contribute <شماره\u200cوعده> <مبلغ> — اضافه کردن پرداخت به وعده\n"
            "/skip — مدیریت حضور/غیبت در وعده‌ها\n"
            "/expense <توضیح> <مبلغ> — ثبت هزینه مشترک\n"
            "/meals — مدیریت وعده‌ها و گزارش کامل\n"
            "/myshare — مشاهده سهم دقیق و ریزهزینه‌های خانواده شما\n\n"
            "*تسویه و گزارش‌ها:*\n"
            "/settle — محاسبه انتقال‌های تسویه نهایی\n"
            "/export — دریافت فایل اکسل ریزهزینه‌ها\n"
            "/history — مشاهده تسویه سفرهای قبلی\n\n"
            "*اصلاحات:*\n"
            "/editmyexpenses — منوی ویرایش و حذف هزینه‌های شما\n"
            "/editmeal <شماره\u200cوعده> <مبلغ> — ویرایش سهم (۰ = حذف)\n"
            "/deletemeal <شماره\u200cوعده> — حذف وعده‌ای که ثبت کردید\n"
            "/undo — برگرداندن آخرین عملیات\n\n"
            "*تنظیمات:*\n"
            "/lang <en|fa> — تغییر زبان\n"
            "/help — نمایش این راهنما"
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
        "en": "\n🍽 *Meals/Events ({count}):*",
        "fa": "\n🍽 *وعده‌ها/رویدادها ({count}):*",
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
        "fa": "\n💸 *هزینه‌های مشترک ({count}):*",
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
        "en": "\n_No meals/events or expenses logged yet._",
        "fa": "\n_هنوز وعده/رویداد یا هزینه‌ای ثبت نشده._",
    },
    "my_share_header": {
        "en": "📊 *Personal Cost Share Breakdown — {family_name}*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👥 Your Share Weight: *{weight}*",
        "fa": "📊 *ریزهزینه‌ها و سهم اختصاصی — {family_name}*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👥 وزن سهم خانواده شما: *{weight}*",
    },
    "my_share_meals_header": {
        "en": "\n\n🍽 *Meals/Events Shares:*",
        "fa": "\n\n🍽 *سهم از وعده‌ها/رویدادها:*",
    },
    "my_share_expenses_header": {
        "en": "\n\n💸 *General Expense Shares:*",
        "fa": "\n\n💸 *سهم از هزینه‌های عمومی:*",
    },
    "my_share_item": {
        "en": "  • {name} (${total:.2f} total) ➔ *Your Share: ${share:.2f}*",
        "fa": "  • {name} (${total:.2f} کل) ➔ *سهم شما: ${share:.2f}*",
    },
    "my_share_skipped_item": {
        "en": "  • {name} — *Skipped ($0.00)*",
        "fa": "  • {name} — *غایب ($0.00)*",
    },
    "my_share_summary": {
        "en": "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📈 *Your Family Financial Summary:*\n  • *Total Cost Share Owed:* ${owed:.2f}\n  • *Total Paid by You:* ${paid:.2f}\n  • *Your Net Balance:* {status}",
        "fa": "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📈 *خلاصه تراز مالی خانواده شما:*\n  • *مجموع سهم پرداختی عهده شما:* ${owed:.2f}\n  • *مجموع پرداختی‌های شما:* ${paid:.2f}\n  • *تراز نهایی شما:* {status}",
    },
    "group_only": {
        "en": "⚠️ This command works in group chats only.",
        "fa": "⚠️ این دستور فقط در گروه کار می‌کند.",
    },
    "reminder": {
        "en": (
            "⏰ *Daily Reminder — {trip_name}*\n\n"
            "Not all families have logged their expenses yet! "
            "({active}/{expected} families contributed so far)\n\n"
            "*Quick guide:*\n"
            "• `/join 2.5` — join with your family weight\n"
            "• `/contribute 1 20` — add payment to meal/event #1\n"
            "• `/skip` — mark absent from a meal/event\n"
            "• `/expense Firewood 15` — log a shared expense\n\n"
            "_This message will auto-delete in 1 hour._"
        ),
        "fa": (
            "⏰ *یادآوری روزانه — {trip_name}*\n\n"
            "هنوز همه خانواده‌ها هزینه‌هایشان را ثبت نکرده‌اند! "
            "({active}/{expected} خانواده تا الان ثبت کرده‌اند)\n\n"
            "*راهنمای سریع:*\n"
            "• `/join 2.5` — عضویت با وزن خانواده\n"
            "• `/contribute 1 20` — اضافه کردن پرداخت به وعده/رویداد ۱\n"
            "• `/skip` — غیبت از یک وعده/رویداد\n"
            "• `/expense هیزم 15` — ثبت هزینه مشترک\n\n"
            "_این پیام بعد از ۱ ساعت حذف می‌شود._"
        ),
    },
    "meals_header": {
        "en": "🍽 *Meals/Events — {trip_name}* ({count} total)",
        "fa": "🍽 *وعده‌ها/رویدادها — {trip_name}* ({count} عدد)",
    },
    "no_meals_yet": {
        "en": "⚠️ No meals/events logged yet.",
        "fa": "⚠️ هنوز وعده/رویدادی ثبت نشده.",
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
    "btn_lock_trip": {
        "en": "🔒 Lock Entries",
        "fa": "🔒 قفل ثبت هزینه",
    },
    "btn_unlock_trip": {
        "en": "🔓 Unlock Entries",
        "fa": "🔓 باز کردن قفل ثبت هزینه",
    },
    "trip_locked": {
        "en": "🔒 Trip entries are currently locked by an admin. No modifications are allowed.",
        "fa": "🔒 ثبت تغییرات سفر توسط مدیر قفل شده است. امکان ثبت یا ویرایش هزینه وجود ندارد.",
    },
    "trip_locked_banner": {
        "en": "🔒 *Entries are currently LOCKED.* No changes are admitted until unlocked.",
        "fa": "🔒 *ثبت تغییرات در حال حاضر قفل است.* امکان ثبت هیچ تغییری وجود ندارد.",
    },
    "trip_lock_success": {
        "en": "🔒 *Trip entries are now locked.* No new expenses or modifications can be made until unlocked by an admin.",
        "fa": "🔒 *ثبت تغییرات سفر قفل شد.* تا زمان باز شدن توسط مدیر، امکان ثبت یا ویرایش هزینه وجود ندارد.",
    },
    "trip_unlock_success": {
        "en": "🔓 *Trip entries are now unlocked.* Members and admins can now log and edit expenses.",
        "fa": "🔓 *قفل ثبت تغییرات سفر باز شد.* اعضا و مدیران می‌توانند هزینه‌ها را ثبت و ویرایش کنند.",
    },
    "admin_only_lock": {
        "en": "⛔️ Only group administrators can lock or unlock trip entries.",
        "fa": "⛔️ فقط مدیران گروه می‌توانند ثبت هزینه را قفل یا باز کنند.",
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
