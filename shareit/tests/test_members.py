import pytest
import pytest_asyncio
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock

from bot.db import (
    init_db, create_trip, add_family, get_families, get_family,
    save_chat_member, add_shared_expense,
)
from bot.handlers._helpers import is_admin_or_owner
from bot.handlers.menu import get_reply_keyboard, admin_menu_handler
from bot.handlers.trip import status_handler
from bot.handlers.members import (
    get_all_group_members, build_members_keyboard,
    members_handler, member_select_callback_handler,
    member_action_callback_handler, pending_member_text_handler,
)
from bot.i18n import t


@pytest_asyncio.fixture
async def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    await init_db(path)
    yield path
    os.unlink(path)


def create_mock_user(user_id: int, full_name: str, username: str = None, is_bot: bool = False):
    user = MagicMock()
    user.id = user_id
    user.full_name = full_name
    user.first_name = full_name.split()[0]
    user.last_name = " ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else ""
    user.username = username
    user.is_bot = is_bot
    return user


def create_mock_admin(user_id: int, full_name: str, username: str = None, is_bot: bool = False, status: str = "administrator"):
    admin = MagicMock()
    admin.status = status
    admin.user = create_mock_user(user_id, full_name, username, is_bot)
    return admin


@pytest.mark.asyncio
async def test_is_admin_or_owner():
    mock_bot = MagicMock()

    # 1. Maysam Mir by full name
    u1 = create_mock_user(101, "Maysam Mir", "some_user")
    assert await is_admin_or_owner(mock_bot, 1000, u1) is True

    # 2. Maysam Mir by username
    u2 = create_mock_user(102, "John Doe", "mmirahma")
    assert await is_admin_or_owner(mock_bot, 1000, u2) is True

    # 3. Chat Owner / Creator via get_chat_member
    u3 = create_mock_user(103, "Alice Owner", "alice")
    owner_member = MagicMock()
    owner_member.status = "creator"
    mock_bot.get_chat_member = AsyncMock(return_value=owner_member)
    assert await is_admin_or_owner(mock_bot, 1000, u3) is True

    # 4. Regular user (not Maysam, not creator)
    u4 = create_mock_user(104, "Bob Member", "bob")
    regular_member = MagicMock()
    regular_member.status = "member"
    mock_bot.get_chat_member = AsyncMock(return_value=regular_member)
    mock_bot.get_chat_administrators = AsyncMock(return_value=[])
    assert await is_admin_or_owner(mock_bot, 1000, u4) is False


@pytest.mark.asyncio
async def test_reply_keyboards_for_admin_and_member():
    # Admin joined keyboard has btn_admin and no btn_members
    kb_admin = get_reply_keyboard(lang="en", is_joined=True, is_admin=True)
    flat_admin = [btn.text for row in kb_admin.keyboard for btn in row]
    assert t("btn_admin", "en") in flat_admin
    assert t("btn_members", "en") not in flat_admin

    # Regular member joined keyboard has neither btn_admin nor btn_members
    kb_member = get_reply_keyboard(lang="en", is_joined=True, is_admin=False)
    flat_member = [btn.text for row in kb_member.keyboard for btn in row]
    assert t("btn_admin", "en") not in flat_member
    assert t("btn_members", "en") not in flat_member


@pytest.mark.asyncio
async def test_get_all_group_members_merges_admins_and_db(db_path):
    # Save a known non-admin user in DB
    await save_chat_member(db_path, chat_id=1000, telegram_user_id=201, name="Charlie", username="charlie_tg")

    # Mock Telegram Bot with admins (one human, one bot)
    mock_bot = MagicMock()
    admin_human = create_mock_admin(101, "Alice Admin", "alice_admin", is_bot=False)
    admin_bot = create_mock_admin(999, "ShareIt Bot", "shareit_bot", is_bot=True)
    mock_bot.get_chat_administrators = AsyncMock(return_value=[admin_human, admin_bot])

    members = await get_all_group_members(mock_bot, db_path, chat_id=1000)

    # Bot should be excluded, human admin + DB member included
    member_uids = {m["telegram_user_id"] for m in members}
    assert 101 in member_uids
    assert 201 in member_uids
    assert 999 not in member_uids
    assert len(members) == 2


@pytest.mark.asyncio
async def test_build_members_keyboard(db_path):
    trip = {"id": 1, "name": "Camp", "chat_id": 1000}
    members = [
        {"telegram_user_id": 101, "name": "Alice"},
        {"telegram_user_id": 102, "name": "Bob"},
    ]
    families = [
        {"id": 1, "trip_id": 1, "name": "Alice's family", "weight": 2.5, "telegram_user_id": 101},
    ]

    kb = build_members_keyboard(trip, members, families, lang="en")
    buttons = kb.inline_keyboard

    # First row: Alice (joined)
    assert "✅ Alice" in buttons[0][0].text
    assert "w=2.5" in buttons[0][0].text
    assert buttons[0][0].callback_data == "mem_sel_101"

    # Second row: Bob (not in trip)
    assert "➕ Bob" in buttons[1][0].text
    assert "(Not in trip)" in buttons[1][0].text
    assert buttons[1][0].callback_data == "mem_sel_102"

    # Action buttons contain Back to Admin
    flat_callbacks = [btn.callback_data for row in buttons for btn in row]
    assert "menu_admin" in flat_callbacks


@pytest.mark.asyncio
async def test_members_handler_admin_permission_check(db_path):
    trip_id = await create_trip(db_path, "Summer Trip", chat_id=1000)

    mock_update = MagicMock()
    mock_update.effective_chat.type = "group"
    mock_update.effective_chat.id = 1000
    mock_update.effective_user = create_mock_user(202, "Regular Bob", "reg_bob")
    mock_update.callback_query = None
    mock_update.effective_message.reply_text = AsyncMock()

    mock_context = MagicMock()
    mock_context.bot_data = {"db_path": db_path}
    mock_context.bot.get_chat_member = AsyncMock(return_value=MagicMock(status="member"))
    mock_context.bot.get_chat_administrators = AsyncMock(return_value=[])

    # Regular user is rejected with admin_only message
    await members_handler(mock_update, mock_context)
    mock_update.effective_message.reply_text.assert_called_once()
    assert "only available to the group owner and Maysam Mir" in mock_update.effective_message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_member_select_and_add_to_trip(db_path):
    trip_id = await create_trip(db_path, "Summer Trip", chat_id=1000)
    await save_chat_member(db_path, 1000, 102, "Bob Vance")

    # 1. Admin clicks on Bob (who is not in the trip)
    mock_update = MagicMock()
    mock_query = MagicMock()
    mock_query.data = "mem_sel_102"
    mock_query.answer = AsyncMock()
    mock_query.edit_message_text = AsyncMock()
    mock_update.callback_query = mock_query
    mock_update.effective_chat.id = 1000
    mock_update.effective_user = create_mock_user(101, "Maysam Mir", "maysammir")

    mock_context = MagicMock()
    mock_context.bot_data = {"db_path": db_path}
    mock_context.user_data = {}
    mock_context.bot.get_chat_administrators = AsyncMock(return_value=[])
    mock_context.bot.send_message = AsyncMock()

    await member_select_callback_handler(mock_update, mock_context)
    mock_query.edit_message_text.assert_called_once()
    reply_markup = mock_query.edit_message_text.call_args[1]["reply_markup"]
    flat_callbacks = [btn.callback_data for row in reply_markup.inline_keyboard for btn in row]
    assert "mem_add_102" in flat_callbacks

    # 2. Admin clicks Add to Trip button (mem_add_102)
    mock_query.reset_mock()
    mock_query.data = "mem_add_102"
    await member_action_callback_handler(mock_update, mock_context)

    # Verify Bob was added to families table with default weight 2.0
    family = await get_family(db_path, trip_id, 102)
    assert family is not None
    assert family["weight"] == 2.0
    assert "Bob Vance" in family["name"]


@pytest.mark.asyncio
async def test_member_select_and_set_weight(db_path):
    trip_id = await create_trip(db_path, "Summer Trip", chat_id=1000)
    trip = {"id": trip_id, "name": "Summer Trip", "chat_id": 1000}
    await save_chat_member(db_path, 1000, 102, "Bob Vance")

    # Simulate admin setting weight for Bob (102) with weight 3.0
    mock_update = MagicMock()
    mock_query = MagicMock()
    mock_query.data = "mem_setw_102_3.0"
    mock_query.answer = AsyncMock()
    mock_query.edit_message_text = AsyncMock()
    mock_update.callback_query = mock_query
    mock_update.effective_chat.id = 1000
    # Maysam Mir as admin
    mock_update.effective_user = create_mock_user(101, "Maysam Mir", "maysammir")

    mock_context = MagicMock()
    mock_context.bot_data = {"db_path": db_path}
    mock_context.user_data = {}
    mock_context.bot.get_chat_administrators = AsyncMock(return_value=[])
    mock_context.bot.send_message = AsyncMock()

    await member_action_callback_handler(mock_update, mock_context)

    # Verify Bob was added to families table with weight 3.0
    family = await get_family(db_path, trip_id, 102)
    assert family is not None
    assert family["weight"] == 3.0
    assert "Bob Vance" in family["name"]

    # Update Bob's weight to 4.5
    mock_query.data = "mem_setw_102_4.5"
    await member_action_callback_handler(mock_update, mock_context)
    updated_family = await get_family(db_path, trip_id, 102)
    assert updated_family["weight"] == 4.5


@pytest.mark.asyncio
async def test_member_removal_and_skip(db_path):
    trip_id = await create_trip(db_path, "Summer Trip", chat_id=1000)
    f1 = await add_family(db_path, trip_id, "Bob's family", 2.0, telegram_user_id=102)

    mock_update = MagicMock()
    mock_query = MagicMock()
    mock_query.data = "mem_del_102"
    mock_query.answer = AsyncMock()
    mock_query.edit_message_text = AsyncMock()
    mock_update.callback_query = mock_query
    mock_update.effective_chat.id = 1000
    mock_update.effective_user = create_mock_user(101, "Maysam Mir", "maysammir")

    mock_context = MagicMock()
    mock_context.bot_data = {"db_path": db_path}
    mock_context.user_data = {}
    mock_context.bot.get_chat_administrators = AsyncMock(return_value=[])
    mock_context.bot.send_message = AsyncMock()

    # Remove Bob (should succeed since no expenses)
    await member_action_callback_handler(mock_update, mock_context)
    fam_after = await get_family(db_path, trip_id, 102)
    assert fam_after is None


@pytest.mark.asyncio
async def test_member_removal_with_expenses_confirmation(db_path):
    trip_id = await create_trip(db_path, "Summer Trip", chat_id=1000)
    f1 = await add_family(db_path, trip_id, "Bob's family", 2.0, telegram_user_id=102)
    await add_shared_expense(db_path, trip_id, f1, "Charcoal & Firewood", 35.0)

    mock_update = MagicMock()
    mock_query = MagicMock()
    mock_query.data = "mem_del_102"
    mock_query.answer = AsyncMock()
    mock_query.edit_message_text = AsyncMock()
    mock_update.callback_query = mock_query
    mock_update.effective_chat.id = 1000
    mock_update.effective_user = create_mock_user(101, "Maysam Mir", "maysammir")

    mock_context = MagicMock()
    mock_context.bot_data = {"db_path": db_path}
    mock_context.user_data = {}
    mock_context.bot.get_chat_administrators = AsyncMock(return_value=[])
    mock_context.bot.send_message = AsyncMock()

    # 1. First attempt: Prompt confirmation listing the expense
    await member_action_callback_handler(mock_update, mock_context)
    mock_query.edit_message_text.assert_called_once()
    warn_text = mock_query.edit_message_text.call_args[0][0]
    assert "Charcoal & Firewood" in warn_text
    assert "$35.00" in warn_text
    assert "permanently delete" in warn_text

    # Verify buttons include mem_delforce_102
    reply_markup = mock_query.edit_message_text.call_args[1]["reply_markup"]
    flat_callbacks = [btn.callback_data for row in reply_markup.inline_keyboard for btn in row]
    assert "mem_delforce_102" in flat_callbacks

    # 2. Confirm force deletion
    mock_query.reset_mock()
    mock_query.data = "mem_delforce_102"
    await member_action_callback_handler(mock_update, mock_context)

    # Verify family and their expense are deleted
    fam_after = await get_family(db_path, trip_id, 102)
    assert fam_after is None



@pytest.mark.asyncio
async def test_member_custom_name_and_weight_text_flow(db_path):
    trip_id = await create_trip(db_path, "Summer Trip", chat_id=1000)

    # Step 1: Admin triggers custom member prompt
    mock_update = MagicMock()
    mock_query = MagicMock()
    mock_query.data = "mem_custom"
    mock_query.answer = AsyncMock()
    mock_query.edit_message_text = AsyncMock()
    mock_update.callback_query = mock_query
    mock_update.effective_chat.id = 1000
    mock_update.effective_user = create_mock_user(101, "Maysam Mir", "maysammir")

    mock_context = MagicMock()
    mock_context.bot_data = {"db_path": db_path}
    mock_context.user_data = {}
    mock_context.bot.send_message = AsyncMock()

    await member_action_callback_handler(mock_update, mock_context)
    assert mock_context.user_data.get("pending_custom_member_name") is True

    # Step 2: Admin types name "Guest Uncle Joe"
    msg_update = MagicMock()
    msg_update.effective_chat.id = 1000
    msg_update.effective_user = create_mock_user(101, "Maysam Mir", "maysammir")
    msg_update.message.text = "Guest Uncle Joe"
    msg_update.message.reply_text = AsyncMock()
    msg_update.effective_message.reply_text = AsyncMock()
    msg_update.callback_query = None

    handled = await pending_member_text_handler(msg_update, mock_context)
    assert handled is True
    assert mock_context.user_data.get("pending_custom_member_name_val") == "Guest Uncle Joe"

    # Step 3: Admin taps weight button 2.0 for custom member
    btn_update = MagicMock()
    btn_query = MagicMock()
    btn_query.data = "mem_custfam_w_2.0"
    btn_query.answer = AsyncMock()
    btn_query.edit_message_text = AsyncMock()
    btn_update.callback_query = btn_query
    btn_update.effective_chat.id = 1000
    btn_update.effective_user = create_mock_user(101, "Maysam Mir", "maysammir")
    mock_context.bot.get_chat_administrators = AsyncMock(return_value=[])

    await member_action_callback_handler(btn_update, mock_context)

    families = await get_families(db_path, trip_id)
    assert len(families) == 1
    assert families[0]["name"] == "Guest Uncle Joe"
    assert families[0]["weight"] == 2.0


@pytest.mark.asyncio
async def test_record_user_activity_mentions_replies_forwards(db_path):
    from bot.handlers._helpers import record_user_activity
    from bot.db import get_known_chat_members

    mock_context = MagicMock()
    mock_context.bot_data = {"db_path": db_path}
    mock_context.bot.id = 999
    mock_context.bot.username = "shareit_bot"

    # 1. Message with text_mention entity (direct user mention)
    update1 = MagicMock()
    update1.effective_chat.type = "group"
    update1.effective_chat.id = 2000
    update1.effective_user = create_mock_user(10, "Sender Sam", "sam")
    update1.chat_member = None

    entity_mention = MagicMock()
    entity_mention.type = "text_mention"
    entity_mention.user = create_mock_user(20, "Tagged Tina", "tina")

    update1.effective_message.entities = [entity_mention]
    update1.effective_message.caption_entities = []
    update1.effective_message.reply_to_message = None
    update1.effective_message.forward_from = None
    update1.effective_message.new_chat_members = []
    update1.effective_message.text = "Hey Tina!"

    await record_user_activity(update1, mock_context)
    members = await get_known_chat_members(db_path, 2000)
    uids = {m["telegram_user_id"] for m in members}
    assert 10 in uids  # Sender
    assert 20 in uids  # Tagged user

    # 2. Message with reply_to_message
    update2 = MagicMock()
    update2.effective_chat.type = "group"
    update2.effective_chat.id = 2000
    update2.effective_user = create_mock_user(10, "Sender Sam", "sam")
    update2.chat_member = None
    update2.effective_message.entities = []
    update2.effective_message.caption_entities = []
    update2.effective_message.forward_from = None
    update2.effective_message.new_chat_members = []
    update2.effective_message.reply_to_message.from_user = create_mock_user(30, "Replied Ray", "ray")

    await record_user_activity(update2, mock_context)
    members2 = await get_known_chat_members(db_path, 2000)
    uids2 = {m["telegram_user_id"] for m in members2}
    assert 30 in uids2

    # 3. Message with @username mention
    update3 = MagicMock()
    update3.effective_chat.type = "group"
    update3.effective_chat.id = 2000
    update3.effective_user = create_mock_user(10, "Sender Sam", "sam")
    update3.chat_member = None
    update3.effective_message.reply_to_message = None
    update3.effective_message.forward_from = None
    update3.effective_message.new_chat_members = []
    update3.effective_message.text = "Hello @newguy"

    entity_uname = MagicMock()
    entity_uname.type = "mention"
    entity_uname.offset = 6
    entity_uname.length = 7  # "@newguy"
    update3.effective_message.entities = [entity_uname]
    update3.effective_message.caption_entities = []

    await record_user_activity(update3, mock_context)
    members3 = await get_known_chat_members(db_path, 2000)
    unames = {m["username"] for m in members3}
    assert "newguy" in unames


@pytest.mark.asyncio
async def test_admin_edit_all_expenses(db_path):
    from bot.handlers.edit_expenses import (
        admin_edit_all_expenses_handler,
        admin_expense_select_callback_handler,
        admin_expense_action_callback_handler,
        pending_edit_expense_text_handler,
    )
    from bot.db import (
        create_trip, add_family, add_meal, add_shared_expense,
        get_shared_expenses, get_meal_contributions,
    )

    trip_id = await create_trip(db_path, "Summer Trip", chat_id=8000)
    f1 = await add_family(db_path, trip_id, "Alice Family", 2.0, telegram_user_id=101)  # Admin
    f2 = await add_family(db_path, trip_id, "Bob Family", 1.5, telegram_user_id=102)    # Member

    m1_id = await add_meal(db_path, trip_id, "Breakfast", f1, 40.0)
    se1_id = await add_shared_expense(db_path, trip_id, f2, "Firewood", 35.0)

    # 1. Non-admin attempts to access admin expenses -> Blocked
    non_admin_update = MagicMock()
    non_admin_update.effective_chat.id = 8000
    non_admin_update.effective_chat.type = "group"
    non_admin_update.effective_user = create_mock_user(102, "Bob Vance", "bob")
    non_admin_update.callback_query = None

    mock_context = MagicMock()
    mock_context.bot_data = {"db_path": db_path}
    mock_context.user_data = {}
    mock_context.bot.get_chat_administrators = AsyncMock(return_value=[])
    mock_context.bot.send_message = AsyncMock()

    await admin_edit_all_expenses_handler(non_admin_update, mock_context)
    mock_context.bot.send_message.assert_called_once()
    assert "only available to the group owner and Maysam Mir" in mock_context.bot.send_message.call_args[1]["text"]

    # 2. Admin (Maysam Mir) accesses admin expenses -> Sees all expenses
    mock_context.bot.send_message.reset_mock()
    admin_update = MagicMock()
    admin_update.effective_chat.id = 8000
    admin_update.effective_chat.type = "group"
    admin_update.effective_user = create_mock_user(101, "Maysam Mir", "maysammir")
    admin_query = MagicMock()
    admin_query.data = "menu_admin_expenses"
    admin_query.answer = AsyncMock()
    admin_query.edit_message_text = AsyncMock()
    admin_update.callback_query = admin_query

    await admin_edit_all_expenses_handler(admin_update, mock_context)
    admin_query.edit_message_text.assert_called_once()
    text = admin_query.edit_message_text.call_args[0][0]
    assert "Manage All Trip Expenses" in text
    reply_markup = admin_query.edit_message_text.call_args[1]["reply_markup"]
    flat_labels = [btn.text for row in reply_markup.inline_keyboard for btn in row]
    # Check that both Alice's meal and Bob's firewood are listed
    assert any("Breakfast" in l and "Alice Family" in l for l in flat_labels)
    assert any("Firewood" in l and "Bob Family" in l for l in flat_labels)

    # 3. Admin selects Bob's Firewood expense (admexp_expense_<se1_id>)
    sel_update = MagicMock()
    sel_update.effective_chat.id = 8000
    sel_update.effective_chat.type = "group"
    sel_update.effective_user = create_mock_user(101, "Maysam Mir", "maysammir")
    sel_query = MagicMock()
    sel_query.data = f"admexp_expense_{se1_id}"
    sel_query.answer = AsyncMock()
    sel_query.edit_message_text = AsyncMock()
    sel_update.callback_query = sel_query

    await admin_expense_select_callback_handler(sel_update, mock_context)
    sel_query.edit_message_text.assert_called_once()
    sel_text = sel_query.edit_message_text.call_args[0][0]
    assert "Bob Family" in sel_text
    assert "Firewood" in sel_text
    assert "$35.00" in sel_text

    # 4. Admin edits Bob's expense amount to $80.00
    act_update = MagicMock()
    act_update.effective_chat.id = 8000
    act_update.effective_chat.type = "group"
    act_update.effective_user = create_mock_user(101, "Maysam Mir", "maysammir")
    act_query = MagicMock()
    act_query.data = f"admexpamt_expense_{se1_id}_80.00"
    act_query.answer = AsyncMock()
    act_query.edit_message_text = AsyncMock()
    act_update.callback_query = act_query

    await admin_expense_action_callback_handler(act_update, mock_context)
    shared_exps = await get_shared_expenses(db_path, trip_id)
    bob_exp = next(e for e in shared_exps if e["id"] == se1_id)
    assert bob_exp["amount"] == 80.0

    # 5. Admin deletes Alice's meal contribution
    del_query = MagicMock()
    del_query.data = f"admexpdel_meal_{m1_id}"
    del_query.answer = AsyncMock()
    del_query.edit_message_text = AsyncMock()
    act_update.callback_query = del_query

    await admin_expense_action_callback_handler(act_update, mock_context)
    meal_contribs = await get_meal_contributions(db_path, trip_id)
    assert len(meal_contribs) == 0

    # 6. Admin types custom amount using text handler
    mock_context.user_data["pending_edit_expense"] = {
        "type": "expense",
        "item_id": se1_id,
        "name": "Firewood",
        "chat_id": 8000,
        "timestamp": 9999999999,
        "is_admin": True,
    }
    msg_update = MagicMock()
    msg_update.effective_chat.id = 8000
    msg_update.effective_user = create_mock_user(101, "Maysam Mir", "maysammir")
    msg_update.callback_query = None
    msg_update.message.text = "125.50"

    handled = await pending_edit_expense_text_handler(msg_update, mock_context)
    assert handled is True
    shared_exps_after = await get_shared_expenses(db_path, trip_id)
    bob_exp_final = next(e for e in shared_exps_after if e["id"] == se1_id)
    assert bob_exp_final["amount"] == 125.50


