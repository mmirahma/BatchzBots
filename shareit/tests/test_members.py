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

